#!/usr/bin/env python3
"""Session lifecycle hook: remind to write a handoff before stop/compact.

Blocks the agent from stopping or compacting context (via JSON response)
if the session has been running long enough and no fresh handoff exists.
Reminds once per trigger per session to avoid infinite loops.

Supports both old (.cursor/HANDOFF.md) and new (.cursor/handoffs/*.md) formats.
Canonical protocol is append-only `.cursor/handoffs/*.md` with `INDEX.md`.

Register in ~/.cursor/settings.json:
{
  "hooks": {
    "Stop": [{
      "hooks": [{
        "type": "command",
        "command": "python path/to/session-handoff-reminder.py",
        "statusMessage": "Checking handoff state..."
      }]
    }]
  }
}
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

# Tunables
SESSION_MIN_MINUTES = 15          # don't remind on short sessions
HANDOFF_STALE_MINUTES = 30        # consider stale after this
STOP_REMINDER_MARKER_NAME = ".handoff-reminded"
PRECOMPACT_REMINDER_MARKER_NAME = ".handoff-reminded-precompact"


def session_age_minutes(marker: Path) -> float:
    """Estimate session age by looking at SessionStart marker mtime."""
    if marker.exists():
        age_sec = time.time() - marker.stat().st_mtime
        return age_sec / 60
    return 0


def _marker_name(trigger: str) -> str:
    return PRECOMPACT_REMINDER_MARKER_NAME if trigger == "precompact" else STOP_REMINDER_MARKER_NAME


def _reason_text(trigger: str, age_minutes: int) -> str:
    if trigger == "precompact":
        return (
            f"This session has been active for ~{age_minutes} minutes and no fresh "
            f"handoff exists. Before compacting context, please write a handoff file in "
            f".cursor/handoffs/ following your project handoff rule format. "
            f"File name: YYYY-MM-DD_HH-MM_<session-short-id>.md. "
            f"Keep it under 1500 tokens. Must include: goal, what was done, "
            f"what did NOT work (with reasons), current state, key decisions, "
            f"single next step. Keep 'What did NOT work' deduplicated and do not "
            f"repeat transient python -c one-liner SyntaxError noise unless it "
            f"changes current state or next step. "
            f"Update .cursor/handoffs/INDEX.md (append). "
            f"After writing, context compaction may proceed normally."
        )
    return (
        f"This session has been active for ~{age_minutes} minutes and no fresh "
        f"handoff exists. Before ending, please write a handoff file in "
        f".cursor/handoffs/ following your project handoff rule format. "
        f"File name: YYYY-MM-DD_HH-MM_<session-short-id>.md. "
        f"Keep it under 1500 tokens. Must include: goal, what was done, "
        f"what did NOT work (with reasons), current state, key decisions, "
        f"single next step. Keep 'What did NOT work' deduplicated and do not "
        f"repeat transient python -c one-liner SyntaxError noise unless it "
        f"changes current state or next step. "
        f"Update .cursor/handoffs/INDEX.md (append). "
        f"After writing, you may end the session normally."
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Block stop/compaction when a handoff is missing.")
    parser.add_argument(
        "--trigger",
        choices=("stop", "precompact"),
        default="stop",
        help="Lifecycle trigger that invoked the reminder.",
    )
    args = parser.parse_args()

    cwd = Path.cwd()
    legacyagent_dir = cwd / ".cursor"
    if not legacyagent_dir.exists():
        return 0  # not a Cursor project

    # Support both old (HANDOFF.md) and new (handoffs/*.md) formats
    handoff_old = legacyagent_dir / "HANDOFF.md"
    handoffs_dir = legacyagent_dir / "handoffs"
    reminder = legacyagent_dir / _marker_name(args.trigger)
    session_marker = legacyagent_dir / ".session-start"

    # Skip if we already reminded this session
    if reminder.exists():
        return 0

    # Create session marker if not present (first Stop of session)
    if not session_marker.exists():
        session_marker.touch()

    age = session_age_minutes(session_marker)
    if age < SESSION_MIN_MINUTES:
        return 0  # short session, no handoff needed

    # Check if handoff is fresh - either format counts
    fresh = False
    # Old format: single HANDOFF.md
    if handoff_old.exists():
        if (time.time() - handoff_old.stat().st_mtime) / 60 < HANDOFF_STALE_MINUTES:
            fresh = True
    # New format: any .md in handoffs/ (except INDEX.md)
    if not fresh and handoffs_dir.exists():
        for p in handoffs_dir.glob("*.md"):
            if p.name == "INDEX.md":
                continue
            if (time.time() - p.stat().st_mtime) / 60 < HANDOFF_STALE_MINUTES:
                fresh = True
                break
    if fresh:
        return 0  # already recent

    # Mark that we've reminded so we don't loop
    reminder.touch()

    # Block the stop and ask Cursor to write handoff
    response = {"decision": "block", "reason": _reason_text(args.trigger, int(age))}
    print(json.dumps(response))
    return 0


if __name__ == "__main__":
    sys.exit(main())
