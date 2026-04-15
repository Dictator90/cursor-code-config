#!/usr/bin/env python3
"""Fail when active surfaces contain forbidden legacy references."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

FORBIDDEN_PATTERNS = [
    r"\b\x63\x6c\x61\x75\x64\x65\.md\b",
    r"\.\x63\x6c\x61\x75\x64\x65[\\/]+",
    r"\x63\x6c\x61\x75\x64\x65\s+\x63\x6f\x64\x65",
]

ACTIVE_SURFACES = [
    "README.md",
    "AGENTS.md",
    "HOW-IT-WORKS.md",
    "principles/README.md",
    "alternatives/README.md",
    "templates/README.md",
    "hooks/README.md",
    "rules/session-handoff.mdc",
    "rules/memory-crosslinks.mdc",
    "scripts/validate_config.py",
    "hooks/session-drift-validator.py",
    ".cursor-plugin/plugin.json",
    ".cursor-plugin/marketplace.json",
]


def scan_file(path: Path) -> list[str]:
    content = path.read_text(encoding="utf-8", errors="replace")
    findings: list[str] = []
    for pattern in FORBIDDEN_PATTERNS:
        if re.search(pattern, content, re.IGNORECASE):
            findings.append(pattern)
    return findings


def main() -> int:
    root = Path.cwd()
    violations: dict[str, list[str]] = {}

    for relative_path in ACTIVE_SURFACES:
        path = root / relative_path
        if not path.exists():
            violations[relative_path] = ["missing-active-surface"]
            continue
        matches = scan_file(path)
        if matches:
            violations[relative_path] = matches

    payload = {
        "overall_status": "PASS" if not violations else "FAIL",
        "violations": violations,
    }
    print(json.dumps(payload, indent=2))
    return 0 if not violations else 1


if __name__ == "__main__":
    sys.exit(main())
