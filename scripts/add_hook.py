#!/usr/bin/env python3
"""Add Cursor hook entries to hooks.json one-by-one.

Usage examples:
  python scripts/add_hook.py session-drift-validator
  python scripts/add_hook.py destructive-command-guard
  python scripts/add_hook.py secret-leak-guard
  python scripts/add_hook.py session-handoff-reminder
  python scripts/add_hook.py session-handoff-check

By default this script updates .cursor/hooks.json in current project
and copies required scripts to .cursor/hooks/.
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def default_hooks_config_path() -> Path:
    # Project-local hooks should live with the repo and be versioned.
    return Path.cwd() / ".cursor" / "hooks.json"


def hook_specs() -> dict[str, dict[str, Any]]:
    return {
        "session-drift-validator": {
            "event": "sessionStart",
            "matcher": None,
            "script": "session-drift-validator.py",
        },
        "session-handoff-reminder": {
            "event": "stop",
            "matcher": None,
            "script": "session-handoff-reminder.py",
        },
        "session-handoff-check": {
            "event": "sessionStart",
            "matcher": None,
            "script": "session-handoff-check.py",
        },
        "destructive-command-guard": {
            "event": "preToolUse",
            "matcher": "Shell",
            "script": "destructive-command-guard.py",
        },
        "secret-leak-guard": {
            "event": "preToolUse",
            "matcher": "Write|Edit|TabWrite",
            "script": "secret-leak-guard.py",
        },
    }


def load_hooks_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"version": 1, "hooks": {}}
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return {"version": 1, "hooks": {}}
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError(f"Invalid hooks config at {path}: expected object")
    data.setdefault("version", 1)
    data.setdefault("hooks", {})
    if not isinstance(data["hooks"], dict):
        raise ValueError(f"Invalid hooks config at {path}: expected hooks object")
    return data


def save_hooks_config(path: Path, config: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")


def ensure_project_hook_script(script_name: str, project_root: Path) -> Path:
    source = repo_root() / "hooks" / script_name
    if not source.exists():
        raise FileNotFoundError(f"Hook script not found: {source}")
    dest = project_root / ".cursor" / "hooks" / script_name
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, dest)
    return dest


def hook_exists(event_list: list[dict[str, Any]], hook_entry: dict[str, Any]) -> bool:
    for existing in event_list:
        if (
            existing.get("command") == hook_entry["command"]
            and existing.get("matcher") == hook_entry.get("matcher")
            and existing.get("type", "command") == hook_entry.get("type", "command")
        ):
            return True
    return False


def add_hook(config: dict[str, Any], spec: dict[str, Any], project_root: Path, python_bin: str) -> bool:
    hooks_obj = config.setdefault("hooks", {})
    event = spec["event"]
    matcher = spec["matcher"]
    script_name = spec["script"]

    script_path = ensure_project_hook_script(script_name, project_root)
    entry: dict[str, Any] = {
        "command": f'{python_bin} "{script_path.as_posix()}"',
    }
    if matcher is not None:
        entry["matcher"] = matcher

    event_list = hooks_obj.setdefault(event, [])
    if not isinstance(event_list, list):
        raise ValueError(f"Invalid hooks.{event}: expected list")
    if hook_exists(event_list, entry):
        return False

    event_list.append(entry)
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
        "--hooks-config",
        "--settings",
        dest="hooks_config",
        default=str(default_hooks_config_path()),
        help=f"Path to Cursor hooks.json (default: {default_hooks_config_path()})",
    )
    parser.add_argument(
        "--python-bin",
        default="python",
        help="Python executable used in hook commands (default: python)",
    )
    args = parser.parse_args()

    hooks_config_path = Path(args.hooks_config).expanduser()
    hooks_config = load_hooks_config(hooks_config_path)
    specs = hook_specs()
    project_root = hooks_config_path.parent.parent
    changed = add_hook(hooks_config, specs[args.hook_name], project_root, args.python_bin)

    save_hooks_config(hooks_config_path, hooks_config)

    if changed:
        print(f"[add-hook] Added '{args.hook_name}' to {hooks_config_path}")
    else:
        print(f"[add-hook] '{args.hook_name}' already present in {hooks_config_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
