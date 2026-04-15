#!/usr/bin/env python3
import json
from pathlib import Path

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
    dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    return True


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
    # Cleanup legacy location from older baseline versions.
    legacy_policy = root / ".supply-chain-policy.json"
    if legacy_policy.exists():
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
    print("Baseline applied.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
