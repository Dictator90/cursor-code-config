#!/usr/bin/env python3
"""Pre-submission checks for plugin discoverability and docs drift."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = ROOT / ".cursor-plugin" / "plugin.json"
README_PATH = ROOT / "README.md"
COMMANDS_DIR = ROOT / "commands"


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

    overall = "PASS" if all(item["status"] == "PASS" for item in checks) else "FAIL"
    result = {"overall_status": overall, "checks": checks}
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if overall == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
