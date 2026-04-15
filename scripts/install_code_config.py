#!/usr/bin/env python3
"""Install full code-config baseline into the current project."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from runtime_contract import REQUIRED_HOOK_NAMES


def _pick_script(script_name: str, project_root: Path) -> Path:
    local = project_root / "scripts" / script_name
    if local.exists():
        return local

    plugin_root = Path(__file__).resolve().parents[1]
    candidate = plugin_root / "scripts" / script_name
    if candidate.exists():
        return candidate
    raise SystemExit(f"Missing required script: {script_name}")


def _run(script_path: Path, *args: str) -> None:
    subprocess.run([sys.executable, str(script_path), *args], check=True)


def main() -> int:
    project_root = Path.cwd()
    apply_script = _pick_script("apply_baseline.py", project_root)
    add_hook_script = _pick_script("add_hook.py", project_root)
    doctor_script = _pick_script("doctor.py", project_root)
    deterministic_script = _pick_script("check_deterministic_gates.py", project_root)
    hooks_path = project_root / ".cursor" / "hooks.json"

    _run(apply_script)
    for hook_name in REQUIRED_HOOK_NAMES:
        _run(add_hook_script, hook_name, "--hooks-config", str(hooks_path))
    _run(doctor_script)
    _run(deterministic_script, "--evidence-mode", "auto")
    print("install-code-config completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
