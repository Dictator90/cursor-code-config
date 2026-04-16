#!/usr/bin/env python3
"""Pre-submission checks for plugin discoverability and docs drift."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

from runtime_contract import RUNTIME_RULE_FILES


ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = ROOT / ".cursor-plugin" / "plugin.json"
LEGACY_MANIFEST_PATH = ROOT / ".cursor" / "plugin.json"
README_PATH = ROOT / "README.md"
COMMANDS_DIR = ROOT / "commands"
RULES_DIR = ROOT / "rules"
APPLY_BASELINE_PATH = ROOT / "scripts" / "apply_baseline.py"
CORE_RUNTIME_RULE_PATH = ROOT / "rules" / "core-runtime.mdc"


def _check(condition: bool, name: str, details: str) -> dict[str, Any]:
    return {"name": name, "status": "PASS" if condition else "FAIL", "details": details}


def _load_json(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    if not path.exists():
        return None, f"missing file: {path}"
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except json.JSONDecodeError as exc:
        return None, f"invalid json in {path}: {exc}"


def main() -> int:
    checks: list[dict[str, Any]] = []
    manifest, manifest_error = _load_json(MANIFEST_PATH)
    if manifest is None:
        checks.append(_check(False, "manifest_load", manifest_error or "manifest load error"))
    else:
        checks.append(_check(True, "manifest_load", str(MANIFEST_PATH)))
        if LEGACY_MANIFEST_PATH.exists():
            legacy_manifest, legacy_error = _load_json(LEGACY_MANIFEST_PATH)
            if legacy_manifest is None:
                checks.append(
                    _check(
                        False,
                        "legacy_manifest_load",
                        legacy_error or f"invalid json in {LEGACY_MANIFEST_PATH}",
                    )
                )
            else:
                checks.append(
                    _check(
                        legacy_manifest == manifest,
                        "legacy_manifest_synced_with_canonical",
                        f"{LEGACY_MANIFEST_PATH} must match {MANIFEST_PATH}",
                    )
                )
        for field, kind in (("commands", "dir"), ("skills", "dir"), ("hooks", "file"), ("apps", "file")):
            value = str(manifest.get(field, "")).strip()
            posix_style = value.startswith("./") and ("\\" not in value)
            checks.append(
                _check(
                    posix_style,
                    f"manifest_path_style_{field}",
                    f"{field}={value!r} (expected ./... POSIX-like path)",
                )
            )
            target = (ROOT / value).resolve() if value else None
            exists = bool(target and target.exists())
            checks.append(_check(exists, f"manifest_path_exists_{field}", str(target) if target else "missing value"))
            if exists:
                if kind == "dir":
                    checks.append(_check(target.is_dir(), f"manifest_path_kind_{field}", f"{target}"))
                else:
                    checks.append(_check(target.is_file(), f"manifest_path_kind_{field}", f"{target}"))
        default_prompt = manifest.get("interface", {}).get("defaultPrompt", [])
        prompt_text = "\n".join(default_prompt) if isinstance(default_prompt, list) else ""
        checks.append(
            _check(
                "Guide the user to run /install-code-config" in prompt_text,
                "manifest_default_prompt_user_only_install",
                "defaultPrompt should guide user-run install and verification",
            )
        )
        checks.append(
            _check(
                "Apply Cursor-only baseline" not in prompt_text and "Create missing baseline files" not in prompt_text,
                "manifest_default_prompt_no_auto_install_language",
                "defaultPrompt must not instruct autonomous baseline apply/create actions",
            )
        )

        commands_path = ROOT / str(manifest.get("commands", "")).strip()
        command_files = sorted(commands_path.glob("*.md")) if commands_path.is_dir() else []
        checks.append(
            _check(
                len(command_files) > 0,
                "commands_non_empty",
                f"{len(command_files)} command files in {commands_path}",
            )
        )
        install_command = commands_path / "install-code-config.md"
        checks.append(_check(install_command.exists(), "install_command_exists", str(install_command)))
        if install_command.exists():
            install_text = install_command.read_text(encoding="utf-8")
            checks.append(
                _check(
                    "check_deterministic_gates.py --evidence-mode auto" in install_text,
                    "install_command_mentions_deterministic_gates",
                    "install command should require deterministic gates check",
                )
            )
        legacy_commands = [
            "apply-baseline.md",
            "doctor.md",
            "add-hooks-baseline.md",
            "add-hook-destructive-command-guard.md",
            "add-hook-secret-leak-guard.md",
            "add-hook-session-drift-validator.md",
            "add-hook-session-handoff-check.md",
            "add-hook-session-handoff-reminder.md",
        ]
        legacy_present = [name for name in legacy_commands if (commands_path / name).exists()]
        checks.append(
            _check(
                len(legacy_present) == 0,
                "legacy_granular_commands_absent",
                f"present: {legacy_present}" if legacy_present else "no legacy granular commands",
            )
        )

        skills_path = ROOT / str(manifest.get("skills", "")).strip()
        skill_files: list[Path] = []
        if skills_path.is_dir():
            # Support both flat (<category>-<name>/SKILL.md) and nested
            # (<category>/<name>/SKILL.md) layouts while validating discoverability.
            seen: set[Path] = set()
            for pattern in ("*/SKILL.md", "*/*/SKILL.md"):
                for file in skills_path.glob(pattern):
                    resolved = file.resolve()
                    if resolved not in seen:
                        seen.add(resolved)
                        skill_files.append(file)
        checks.append(
            _check(
                len(skill_files) > 0,
                "skills_non_empty",
                f"{len(skill_files)} skills discovered in {skills_path}",
            )
        )

        hooks_path = ROOT / str(manifest.get("hooks", "")).strip()
        hooks_json, hooks_error = _load_json(hooks_path)
        if hooks_json is None:
            checks.append(_check(False, "hooks_component_valid_json", hooks_error or "invalid hooks file"))
        else:
            hooks_obj = hooks_json.get("hooks")
            is_map = isinstance(hooks_obj, dict)
            non_empty = bool(is_map and hooks_obj)
            checks.append(_check(is_map, "hooks_component_schema", "hooks must be an object keyed by event"))
            checks.append(_check(non_empty, "hooks_component_non_empty", f"events: {list(hooks_obj.keys()) if is_map else []}"))
            has_precompact = bool(is_map and "preCompact" in hooks_obj)
            checks.append(
                _check(
                    has_precompact,
                    "hooks_component_has_precompact_handoff",
                    "hooks/hooks.json should register a preCompact handoff reminder",
                )
            )

    if README_PATH.exists():
        readme_text = README_PATH.read_text(encoding="utf-8")
        has_legacy_path = ".cursor/commands/" in readme_text
        mentions_commands = bool(re.search(r"`commands/`", readme_text))
        mentions_install = "/install-code-config" in readme_text
        removed_command_patterns = (
            r"(?<![A-Za-z0-9_.-])/apply-baseline(?![A-Za-z0-9_.-])",
            r"(?<![A-Za-z0-9_.-])/doctor(?![A-Za-z0-9_.-])",
            r"(?<![A-Za-z0-9_.-])/add-hooks-baseline(?![A-Za-z0-9_.-])",
            r"(?<![A-Za-z0-9_.-])/add-hook-[a-z0-9-]+(?![A-Za-z0-9_.-])",
        )
        mentions_removed = any(re.search(pattern, readme_text) for pattern in removed_command_patterns)
        checks.append(_check(not has_legacy_path, "readme_no_legacy_commands_path", "README must not refer to .cursor/commands/"))
        checks.append(_check(mentions_commands, "readme_mentions_plugin_commands_path", "README should document commands/"))
        checks.append(_check(mentions_install, "readme_mentions_install_command", "README should document /install-code-config"))
        checks.append(_check(not mentions_removed, "readme_no_removed_granular_commands", "README must not mention removed granular commands"))
        checks.append(
            _check(
                "Install commands are executed by the user" in readme_text,
                "readme_user_only_install_policy",
                "README should state that install commands are user-run only",
            )
        )
        checks.append(
            _check(
                "CURSOR-HARDENING" not in readme_text,
                "readme_no_removed_cursor_hardening_skill",
                "README must not reference removed CURSOR-HARDENING skill",
            )
        )
    else:
        checks.append(_check(False, "readme_exists", f"missing file: {README_PATH}"))

    hardcoded_local_pattern = ".cursor/plugins/local/"
    hardcoded_hits: list[str] = []
    if COMMANDS_DIR.is_dir():
        for command_file in sorted(COMMANDS_DIR.glob("*.md")):
            text = command_file.read_text(encoding="utf-8")
            if hardcoded_local_pattern in text:
                hardcoded_hits.append(str(command_file.relative_to(ROOT)))
    checks.append(
        _check(
            len(hardcoded_hits) == 0,
            "commands_no_hardcoded_local_plugin_paths",
            f"violations: {hardcoded_hits}" if hardcoded_hits else "no hardcoded local plugin paths",
        )
    )
    missing_rules = [name for name in RUNTIME_RULE_FILES if not (RULES_DIR / name).exists()]
    checks.append(
        _check(
            len(missing_rules) == 0,
            "runtime_rule_pack_complete",
            f"missing: {missing_rules}" if missing_rules else "full runtime rule pack exists",
        )
    )
    if APPLY_BASELINE_PATH.exists():
        apply_text = APPLY_BASELINE_PATH.read_text(encoding="utf-8")
        checks.append(
            _check(
                "RUNTIME_RULE_FILES" in apply_text and ".code-config-install.json" in apply_text,
                "apply_baseline_projects_rules_and_stamp",
                "apply_baseline.py should project rules and write install stamp",
            )
        )
    else:
        checks.append(_check(False, "apply_baseline_exists", f"missing file: {APPLY_BASELINE_PATH}"))

    if CORE_RUNTIME_RULE_PATH.exists():
        core_runtime_text = CORE_RUNTIME_RULE_PATH.read_text(encoding="utf-8")
        checks.append(
            _check(
                "user-run only" in core_runtime_text and "do not execute it automatically" in core_runtime_text,
                "core_runtime_user_only_install_policy",
                "core-runtime rule should explicitly enforce user-only install execution",
            )
        )
    else:
        checks.append(_check(False, "core_runtime_rule_exists", f"missing file: {CORE_RUNTIME_RULE_PATH}"))

    skill_file = ROOT / "skills" / "CURSOR-HARDENING" / "SKILL.md"
    checks.append(
        _check(
            not skill_file.exists(),
            "cursor_hardening_skill_removed",
            "skills/CURSOR-HARDENING/SKILL.md should be removed from plugin surface",
        )
    )

    overall = "PASS" if all(item["status"] == "PASS" for item in checks) else "FAIL"
    result = {"overall_status": overall, "checks": checks}
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if overall == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
