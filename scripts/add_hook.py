#!/usr/bin/env python3
"""Add Cursor hook entries to settings.json one-by-one.

Usage examples:
  python scripts/add_hook.py session-drift-validator
  python scripts/add_hook.py destructive-command-guard
  python scripts/add_hook.py secret-leak-guard
  python scripts/add_hook.py session-handoff-reminder
  python scripts/add_hook.py session-handoff-check

By default this script updates ~/.cursor/settings.json.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def default_settings_path() -> Path:
    # Cursor stores user settings in OS-specific locations.
    if os.name == "nt":
        app_data = os.environ.get("APPDATA")
        if app_data:
            return Path(app_data) / "Cursor" / "User" / "settings.json"

    return Path.home() / ".cursor" / "settings.json"


def hook_specs(python_bin: str) -> dict[str, dict[str, Any]]:
    hooks_dir = repo_root() / "hooks"
    return {
        "session-drift-validator": {
            "event": "SessionStart",
            "matcher": None,
            "entry": {
                "type": "command",
                "command": f'{python_bin} "{(hooks_dir / "session-drift-validator.py").as_posix()}"',
                "statusMessage": "Validating docs/rules drift...",
            },
        },
        "session-handoff-reminder": {
            "event": "Stop",
            "matcher": None,
            "entry": {
                "type": "command",
                "command": f'{python_bin} "{(hooks_dir / "session-handoff-reminder.py").as_posix()}"',
                "statusMessage": "Checking handoff state...",
            },
        },
        "session-handoff-check": {
            "event": "SessionStart",
            "matcher": None,
            "entry": {
                "type": "command",
                "command": f'{python_bin} "{(hooks_dir / "session-handoff-check.py").as_posix()}"',
                "statusMessage": "Checking for handoffs...",
            },
        },
        "destructive-command-guard": {
            "event": "PreToolUse",
            "matcher": "Bash",
            "entry": {
                "type": "command",
                "command": f'{python_bin} "{(hooks_dir / "destructive-command-guard.py").as_posix()}"',
                "statusMessage": "Checking destructive command safety...",
            },
        },
        "secret-leak-guard": {
            "event": "PreToolUse",
            "matcher": "Write|Edit",
            "entry": {
                "type": "command",
                "command": f'{python_bin} "{(hooks_dir / "secret-leak-guard.py").as_posix()}"',
                "statusMessage": "Checking secret leakage...",
            },
        },
    }


def load_settings(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return {}
    return json.loads(text)


def save_settings(path: Path, settings: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")


def ensure_block(event_list: list[dict[str, Any]], matcher: str | None) -> dict[str, Any]:
    for block in event_list:
        if matcher is None and "matcher" not in block:
            return block
        if matcher is not None and block.get("matcher") == matcher:
            return block

    new_block: dict[str, Any] = {"hooks": []}
    if matcher is not None:
        new_block["matcher"] = matcher
    event_list.append(new_block)
    return new_block


def hook_exists(block: dict[str, Any], hook_entry: dict[str, Any]) -> bool:
    hooks = block.get("hooks", [])
    for existing in hooks:
        if existing.get("type") == hook_entry["type"] and existing.get("command") == hook_entry["command"]:
            return True
    return False


def add_hook(settings: dict[str, Any], spec: dict[str, Any]) -> bool:
    hooks_obj = settings.setdefault("hooks", {})
    event = spec["event"]
    matcher = spec["matcher"]
    entry = spec["entry"]

    event_list = hooks_obj.setdefault(event, [])
    if not isinstance(event_list, list):
        raise ValueError(f"Invalid hooks.{event}: expected list")

    block = ensure_block(event_list, matcher)
    if "hooks" not in block or not isinstance(block["hooks"], list):
        block["hooks"] = []

    if hook_exists(block, entry):
        return False

    block["hooks"].append(entry)
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Add a single Cursor hook entry.")
    parser.add_argument(
        "hook_name",
        choices=[
            "session-drift-validator",
            "session-handoff-reminder",
            "session-handoff-check",
            "destructive-command-guard",
            "secret-leak-guard",
        ],
        help="Hook to add",
    )
    parser.add_argument(
        "--settings",
        default=str(default_settings_path()),
        help=f"Path to Cursor settings.json (default: {default_settings_path()})",
    )
    parser.add_argument(
        "--python-bin",
        default="python",
        help="Python executable used in hook commands (default: python)",
    )
    args = parser.parse_args()

    settings_path = Path(args.settings).expanduser()
    settings = load_settings(settings_path)
    specs = hook_specs(args.python_bin)
    changed = add_hook(settings, specs[args.hook_name])

    save_settings(settings_path, settings)

    if changed:
        print(f"[add-hook] Added '{args.hook_name}' to {settings_path}")
    else:
        print(f"[add-hook] '{args.hook_name}' already present in {settings_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
