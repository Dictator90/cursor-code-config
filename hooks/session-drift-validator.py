#!/usr/bin/env python3
"""SessionStart hook: validate file path references in active docs/rules.

Scans active markdown docs and .cursor/rules/*.md for file path references, checks if
they exist on disk. Reports drift (stale paths) so the agent sees warnings
at the start of every session.

Register in Cursor settings:
{
  "hooks": {
    "SessionStart": [{
      "hooks": [{
        "type": "command",
        "command": "python path/to/session-drift-validator.py",
        "statusMessage": "Checking config drift..."
      }]
    }]
  }
}
"""

import json
import os
import re
import sys
from pathlib import Path


def find_config_files(root: str) -> list[str]:
    """Find active docs and .cursor/rules/*.md files."""
    files = []
    candidates = [
        "README.md",
        "AGENTS.md",
        os.path.join("hooks", "README.md"),
        os.path.join("templates", "README.md"),
    ]
    for candidate in candidates:
        path = os.path.join(root, candidate)
        if os.path.isfile(path):
            files.append(path)

    rules_dir = os.path.join(root, ".cursor", "rules")
    if os.path.isdir(rules_dir):
        for f in os.listdir(rules_dir):
            if f.endswith(".md"):
                files.append(os.path.join(rules_dir, f))

    return files


# Patterns that look like real file paths (not concepts or examples)
PATH_PATTERN = re.compile(
    r'(?:'
    r'[A-Za-z]:[/\\][^\s`"\')>]+'       # Windows absolute: C:/foo or C:\foo
    r'|~/[^\s`"\')>]+'                    # Home-relative: ~/foo
    r'|(?:\./|\.\./)[\w./-]+'             # Relative: ./foo or ../foo
    r'|[\w.-]+(?:/[\w.-]+){2,}'           # Multi-segment: foo/bar/baz
    r')'
)

# Skip patterns (template placeholders, URLs, etc.)
SKIP_PATTERNS = [
    r'\{\{',           # Template: {{path}}
    r'https?://',      # URLs
    r'example\.com',   # Example domains
    r'<[^>]+>',        # Angle-bracket placeholders
    r'\$\{',           # Variable expansion
]


def extract_paths(text: str) -> list[str]:
    """Extract file path references from markdown text."""
    paths = []
    for match in PATH_PATTERN.finditer(text):
        path = match.group(0).rstrip('.,;:)')
        if any(re.search(skip, path) for skip in SKIP_PATTERNS):
            continue
        paths.append(path)
    return paths


def resolve_path(path: str, source_file: str, cwd: str) -> str | None:
    """Try multiple strategies to resolve a path reference."""
    # Expand ~ to home
    expanded = os.path.expanduser(path)

    # Strategy 1: absolute path
    if os.path.isabs(expanded) and os.path.exists(expanded):
        return expanded

    # Strategy 2: relative to the file containing the reference
    source_dir = os.path.dirname(source_file)
    candidate = os.path.join(source_dir, path)
    if os.path.exists(candidate):
        return os.path.abspath(candidate)

    # Strategy 3: relative to cwd
    candidate = os.path.join(cwd, path)
    if os.path.exists(candidate):
        return os.path.abspath(candidate)

    return None


def main():
    cwd = os.getcwd()
    config_files = find_config_files(cwd)

    if not config_files:
        print(json.dumps({"decision": "allow", "reason": "[config-drift] no config files found"}))
        return

    drift_found = []

    for config_file in config_files:
        try:
            text = Path(config_file).read_text(encoding="utf-8", errors="ignore")
        except (OSError, IOError):
            continue

        paths = extract_paths(text)
        for path in paths:
            if resolve_path(path, config_file, cwd) is None:
                rel_config = os.path.relpath(config_file, cwd)
                drift_found.append(f"  {rel_config}: {path}")

    if drift_found:
        preview = "; ".join(drift_found[:3])
        if len(drift_found) > 3:
            preview += f"; ... and {len(drift_found) - 3} more"
        print(
            json.dumps(
                {
                    "decision": "allow",
                    "reason": f"[config-drift] stale references found: {len(drift_found)} ({preview})",
                }
            )
        )
    else:
        summary = f"[config-drift] OK: {len(config_files)} files, no drift detected"
        print(json.dumps({"decision": "allow", "reason": summary}))


if __name__ == "__main__":
    main()
