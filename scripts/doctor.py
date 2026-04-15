#!/usr/bin/env python3
import json
from pathlib import Path


def main() -> int:
    root = Path.cwd()
    policy_path = root / ".cursor/.supply-chain-policy.json"
    policy_ok = False
    if policy_path.exists():
        try:
            policy = json.loads(policy_path.read_text(encoding="utf-8"))
            policy_ok = isinstance(policy, dict) and isinstance(policy.get("supplyChain"), dict)
        except json.JSONDecodeError:
            policy_ok = False
    checks = {
        "supply_chain_policy_file": policy_ok,
    }
    status = "PASS" if all(checks.values()) else "FAIL"
    print(json.dumps({"status": status, "checks": checks}, indent=2))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
