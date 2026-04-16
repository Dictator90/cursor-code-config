#!/usr/bin/env python3
import json
from pathlib import Path

from runtime_contract import EXPECTED_RUNTIME_HOOKS, RUNTIME_RULE_FILES


def _hooks_config_has_expected_entries(path: Path) -> bool:
    if not path.exists():
        return False
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False
    hooks_obj = payload.get("hooks")
    if not isinstance(hooks_obj, dict):
        return False

    for event, expected_commands in EXPECTED_RUNTIME_HOOKS.items():
        event_entries = hooks_obj.get(event)
        if not isinstance(event_entries, list):
            return False
        event_commands = {
            str(entry.get("command", ""))
            for entry in event_entries
            if isinstance(entry, dict)
        }
        for expected_fragments in expected_commands:
            if not any(
                all(fragment in command for fragment in expected_fragments)
                for command in event_commands
            ):
                return False
    return True


def main() -> int:
    root = Path.cwd()
    policy_path = root / ".cursor/.supply-chain-policy.json"
    stamp_path = root / ".cursor/.code-config-install.json"
    policy_ok = False
    if policy_path.exists():
        try:
            policy = json.loads(policy_path.read_text(encoding="utf-8"))
            policy_ok = isinstance(policy, dict) and isinstance(policy.get("supplyChain"), dict)
        except json.JSONDecodeError:
            policy_ok = False
    stamp_ok = False
    stamp_profile_ok = False
    if stamp_path.exists():
        try:
            stamp = json.loads(stamp_path.read_text(encoding="utf-8"))
            stamp_ok = isinstance(stamp, dict)
            stamp_profile_ok = stamp_ok and stamp.get("profile") == "full"
        except json.JSONDecodeError:
            stamp_ok = False
            stamp_profile_ok = False
    rules_dir = root / ".cursor/rules"
    required_rules_ok = all((rules_dir / rule).exists() for rule in RUNTIME_RULE_FILES)
    hooks_config = root / ".cursor/hooks.json"
    hooks_runtime_ok = _hooks_config_has_expected_entries(hooks_config)
    checks = {
        "supply_chain_policy_file": policy_ok,
        "runtime_rules_full_profile": required_rules_ok,
        "install_stamp_file": stamp_ok,
        "install_stamp_profile_full": stamp_profile_ok,
        "hooks_runtime_entries_present": hooks_runtime_ok,
    }
    status = "PASS" if all(checks.values()) else "FAIL"
    print(json.dumps({"status": status, "checks": checks}, indent=2))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
