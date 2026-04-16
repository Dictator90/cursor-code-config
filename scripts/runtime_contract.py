#!/usr/bin/env python3
"""Shared runtime contract constants used by setup and checks."""

from __future__ import annotations

RUNTIME_RULE_FILES = (
    "core-runtime.mdc",
    "skill-routing.mdc",
    "skill-enforcement.mdc",
    "session-handoff.mdc",
    "memory-crosslinks.mdc",
    "advanced-runtime.mdc",
)

REQUIRED_HOOK_NAMES = (
    "session-drift-validator",
    "session-handoff-check",
    "destructive-command-guard",
    "secret-leak-guard",
    "session-handoff-reminder",
    "session-handoff-precompact",
)

EXPECTED_RUNTIME_HOOKS = {
    "sessionStart": (
        ("session-drift-validator.py",),
        ("session-handoff-check.py",),
    ),
    "preToolUse": (
        ("destructive-command-guard.py",),
        ("secret-leak-guard.py",),
    ),
    "stop": (
        ("session-handoff-reminder.py", "--trigger stop"),
    ),
    "preCompact": (
        ("session-handoff-reminder.py", "--trigger precompact"),
    ),
}
