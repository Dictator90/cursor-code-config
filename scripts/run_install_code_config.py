#!/usr/bin/env python3
"""Locate and run install_code_config.py for the current project.

This is a safer, readable replacement for the long one-line python -c snippet
previously documented in commands/install-code-config.md.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def pick(script_name: str, root: Path, plugin_root: Path | None) -> Path:
    """Find the requested script in the current project or installed plugins."""
    # 1) Project-local scripts/ first
    local = root / "scripts" / script_name
    if local.exists():
        return local

    # 2) Installed plugins under ~/.cursor/plugins/
    plugins = Path.home() / ".cursor" / "plugins"
    candidates: list[Path] = []
    if plugins.exists():
        # local/*/scripts/<script_name>
        candidates.extend(sorted(plugins.glob(f"local/*/scripts/{script_name}")))
        # any/*/scripts/<script_name>
        candidates.extend(sorted(plugins.glob(f"*/scripts/{script_name}")))

    # 3) Fallback to plugin_root/scripts if available (running inside plugin repo)
    if plugin_root is not None:
        candidates.append(plugin_root / "scripts" / script_name)

    found = next((p for p in candidates if p.exists()), None)
    if found is None:
        raise SystemExit(f"Missing required script: {script_name}")
    return found


def main() -> int:
    root = Path.cwd()
    plugin_root = Path(__file__).resolve().parents[1]
    install_script = pick("install_code_config.py", root=root, plugin_root=plugin_root)
    subprocess.run([sys.executable, str(install_script)], check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

