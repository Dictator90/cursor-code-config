#!/usr/bin/env python3
import json
from pathlib import Path


def contains(path: Path, needle: str) -> bool:
    if not path.exists():
        return False
    return needle in path.read_text(encoding="utf-8")


def main() -> int:
    root = Path.cwd()
    checks = {
        "cursor_baseline_rule": (root / ".cursor/rules/cursor-only-baseline.md").exists(),
        "cursor_handoff_rule": (root / ".cursor/rules/session-handoff.md").exists(),
        "npm_min_release_age": contains(root / ".npmrc", "min-release-age=7"),
        "uv_exclude_newer": contains(root / "uv.toml", 'exclude-newer = "7 days"'),
    }
    status = "PASS" if all(checks.values()) else "FAIL"
    print(json.dumps({"status": status, "checks": checks}, indent=2))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
