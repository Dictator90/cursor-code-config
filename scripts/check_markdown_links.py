#!/usr/bin/env python3
"""Validate local markdown links for selected active docs."""

from __future__ import annotations

import re
import sys
from pathlib import Path

LINK_PATTERN = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
TARGETS = [
    Path("README.md"),
    Path("AGENTS.md"),
    Path("templates/README.md"),
    Path("hooks/README.md"),
    Path("rules/session-handoff.md"),
    Path(".cursor/rules/cursor-only-baseline.md"),
    Path(".cursor/rules/session-handoff.md"),
]


def is_ignorable(link: str) -> bool:
    return link.startswith(("http://", "https://", "mailto:", "#"))


def resolve_exists(base: Path, raw_link: str) -> bool:
    clean = raw_link.split("#", 1)[0].strip()
    if not clean:
        return True
    target = (base.parent / clean).resolve()
    return target.exists()


def main() -> int:
    root = Path.cwd()
    issues: list[str] = []
    for target in TARGETS:
        abs_path = root / target
        if not abs_path.exists():
            issues.append(f"missing-file: {target}")
            continue
        text = abs_path.read_text(encoding="utf-8", errors="replace")
        for link in LINK_PATTERN.findall(text):
            if is_ignorable(link):
                continue
            if not resolve_exists(abs_path, link):
                issues.append(f"{target}: {link}")

    if issues:
        print("[markdown-links] FAIL")
        for issue in issues:
            print(f"- {issue}")
        return 1

    print("[markdown-links] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
