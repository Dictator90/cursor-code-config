#!/usr/bin/env python3
import json
from pathlib import Path

from runtime_contract import RUNTIME_RULE_FILES

HANDOFF_INDEX = """# Handoffs Index

Append one line per handoff file:
- YYYY-MM-DD_HH-MM_<session-short-id>.md - short topic summary
"""

SUPPLY_CHAIN_POLICY = {
    "version": 1,
    "supplyChain": {
        "defaults": {
            "enabled": True,
            "minReleaseAgeDays": 7
        },
        "npm": {
            "enabled": True,
            "minReleaseAgeDays": 7,
            "ignore": []
        },
        "composer": {
            "enabled": True,
            "minReleaseAgeDays": 7,
            "ignore": []
        },
        "pypi": {
            "enabled": True,
            "minReleaseAgeDays": 7,
            "ignore": []
        }
    }
}
RUNTIME_PROFILE = "full"
RUNTIME_CONFIG_VERSION = 1

def write_if_missing(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(content, encoding="utf-8")


def write_json_if_missing(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def copy_if_missing(src: Path, dst: Path) -> bool:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists() or not src.exists():
        return False
    raw = src.read_text(encoding="utf-8")
    # Guard against accidental malformed source file in plugin repo.
    try:
        json.loads(raw)
    except json.JSONDecodeError:
        return False
    dst.write_text(raw, encoding="utf-8")
    return True


def sync_text_file(src: Path, dst: Path) -> bool:
    if not src.exists():
        return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    incoming = src.read_text(encoding="utf-8")
    existing = dst.read_text(encoding="utf-8") if dst.exists() else None
    if existing == incoming:
        return False
    dst.write_text(incoming, encoding="utf-8")
    return True


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    root = Path.cwd()
    plugin_root = Path(__file__).resolve().parents[1]
    write_if_missing(root / ".cursor/handoffs/INDEX.md", HANDOFF_INDEX)
    policy_target = root / ".cursor/.supply-chain-policy.json"
    policy_source = plugin_root / ".supply-chain-policy.json"
    copied = copy_if_missing(policy_source, policy_target)
    if not copied:
        # Fallback for environments where plugin source file is unavailable.
        write_json_if_missing(policy_target, SUPPLY_CHAIN_POLICY)
    rules_source_dir = plugin_root / "rules"
    rules_target_dir = root / ".cursor" / "rules"
    projected_rules: list[str] = []
    for filename in RUNTIME_RULE_FILES:
        src = rules_source_dir / filename
        dst = rules_target_dir / filename
        if sync_text_file(src, dst):
            projected_rules.append(filename)
    stamp_path = root / ".cursor" / ".code-config-install.json"
    stamp = {
        "configVersion": RUNTIME_CONFIG_VERSION,
        "profile": RUNTIME_PROFILE,
        "sourcePluginRoot": str(plugin_root),
        "projectedRules": list(RUNTIME_RULE_FILES),
    }
    write_json(stamp_path, stamp)
    # Cleanup legacy location from older baseline versions in target projects.
    # Never delete plugin source policy file when running in plugin repo itself.
    legacy_policy = root / ".supply-chain-policy.json"
    if legacy_policy.exists() and legacy_policy.resolve() != policy_source.resolve():
        legacy_policy.unlink()
    legacy_npmrc = root / ".npmrc"
    if legacy_npmrc.exists():
        legacy_npmrc.unlink()
    legacy_baseline = root / ".cursor/rules/baseline.md"
    if legacy_baseline.exists():
        legacy_baseline.unlink()
    legacy_handoff_rule = root / ".cursor/rules/session-handoff.md"
    if legacy_handoff_rule.exists():
        legacy_handoff_rule.unlink()
    # Cleanup outdated rule filename if present from old layouts.
    legacy_rules = (
        root / ".cursor/rules/session-handoff.md",
        root / ".cursor/rules/memory-crosslinks.md",
    )
    for legacy_rule in legacy_rules:
        if legacy_rule.exists():
            legacy_rule.unlink()
    print("Baseline applied.")
    if projected_rules:
        print("Projected runtime rules:")
        for name in projected_rules:
            print(f"- {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
