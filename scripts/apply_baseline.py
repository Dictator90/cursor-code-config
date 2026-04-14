#!/usr/bin/env python3
from pathlib import Path

BASELINE_RULE = """# Cursor-only baseline

- Keep this repository Cursor-only.
- Prefer AGENTS.md and .cursor/rules for operational guidance.
- Enforce deterministic checks in CI before merge.
"""

HANDOFF_RULE = """# Session handoff

- Write concise handoff notes for multi-step tasks.
- Include: goal, completed work, blockers, next action.
"""


def write_if_missing(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(content, encoding="utf-8")


def ensure_contains(path: Path, line: str) -> None:
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    if line not in existing:
        path.write_text((existing + ("\n" if existing and not existing.endswith("\n") else "") + line + "\n"), encoding="utf-8")


def main() -> int:
    root = Path.cwd()
    write_if_missing(root / ".cursor/rules/cursor-only-baseline.md", BASELINE_RULE)
    write_if_missing(root / ".cursor/rules/session-handoff.md", HANDOFF_RULE)
    ensure_contains(root / ".npmrc", "min-release-age=7")
    ensure_contains(root / "uv.toml", 'exclude-newer = "7 days"')
    print("Baseline applied.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
