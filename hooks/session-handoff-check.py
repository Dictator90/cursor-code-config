#!/usr/bin/env python3
"""SessionStart hook: check for handoffs from previous sessions.

Runs at the start of every Cursor session. If recent handoff files
exist, prints them so the agent sees them and can offer to continue.

Supports both old (.cursor/HANDOFF.md) and new (.cursor/handoffs/*.md) formats.
Canonical protocol is append-only `.cursor/handoffs/*.md` with `INDEX.md`.

Register in ~/.cursor/settings.json:
{
  "hooks": {
    "SessionStart": [{
      "hooks": [{
        "type": "command",
        "command": "python path/to/session-handoff-check.py",
        "statusMessage": "Checking for handoffs..."
      }]
    }]
  }
}
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

# How many recent handoffs to show (by mtime)
MAX_HANDOFFS = 3
# Only show handoffs newer than this (hours)
MAX_AGE_HOURS = 168  # 7 days


def main() -> int:
    cwd = Path.cwd()
    legacyagent_dir = cwd / ".cursor"
    handoffs_dir = legacyagent_dir / "handoffs"
    handoff_index = handoffs_dir / "INDEX.md"

    # Bootstrap handoff structure so context files are visible early.
    legacyagent_dir.mkdir(parents=True, exist_ok=True)
    handoffs_dir.mkdir(parents=True, exist_ok=True)
    if not handoff_index.exists():
        handoff_index.write_text(
            "# Handoffs Index\n\n"
            "Append one line per handoff file:\n"
            "- YYYY-MM-DD_HH-MM_<session-short-id>.md - short topic summary\n",
            encoding="utf-8",
        )

    # Reset per-session markers (so Stop hook can remind again this session)
    for marker in (".handoff-reminded", ".session-start"):
        m = legacyagent_dir / marker
        if m.exists():
            m.unlink()
    # Re-create session-start marker with current time
    (legacyagent_dir / ".session-start").touch()

    lines: list[str] = []

    # Check for handoffs - new multi-session format first
    handoff_old = legacyagent_dir / "HANDOFF.md"
    found_handoffs: list[tuple[float, Path]] = []

    now = time.time()

    if handoffs_dir.exists():
        for p in handoffs_dir.glob("*.md"):
            if p.name == "INDEX.md":
                continue
            age_hours = (now - p.stat().st_mtime) / 3600
            if age_hours <= MAX_AGE_HOURS:
                found_handoffs.append((p.stat().st_mtime, p))

    # Fallback: old single HANDOFF.md
    if not found_handoffs and handoff_old.exists():
        age_hours = (now - handoff_old.stat().st_mtime) / 3600
        if age_hours <= MAX_AGE_HOURS:
            found_handoffs.append((handoff_old.stat().st_mtime, handoff_old))

    if found_handoffs:
        # Sort by mtime descending (newest first), take top N
        found_handoffs.sort(key=lambda x: x[0], reverse=True)
        recent = found_handoffs[:MAX_HANDOFFS]

        lines.append("=" * 60)
        lines.append(
            f"SESSION HANDOFF(S) - {len(found_handoffs)} found, "
            f"showing {len(recent)} most recent"
        )
        lines.append("=" * 60)

        for mtime, path in recent:
            content = path.read_text(encoding="utf-8", errors="replace")
            lines.append(f"\n--- {path.name} ---")
            lines.append(content)

        lines.append("=" * 60)
        lines.append("")
        lines.append(
            "INSTRUCTION: List the handoff(s) briefly to the user "
            "(timestamp, session ID, topic). Ask if they want to continue "
            "one of them or start fresh."
        )
        lines.append("")

    if lines:
        print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
