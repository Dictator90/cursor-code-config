#!/usr/bin/env python3
"""Config drift validator for Cursor-only active surfaces.

Scans active entrypoints and rule surfaces for markdown path references and
reports broken links deterministically.
"""
from __future__ import annotations

import re
import sys
import os
from pathlib import Path

# Patterns that look like REAL file path references in markdown.
# We only check paths that are structurally unambiguous:
#   - Windows absolute:  C:\Users\...  or  C:/Users/...
#   - Unix absolute:     /home/..., /etc/...
#   - Home-relative:     ~/config/...
#   - Explicit relative: ./foo, ../foo
#   - Multi-segment:     foo/bar/baz.ext  (has at least one slash)
#
# We DO NOT check bare filenames (e.g. `README.md`, `foo.py`) because
# they are almost always used as concepts/examples, not as verifiable refs.
PATH_PATTERN = re.compile(
    r"`("
    r"[A-Za-z]:[\\/][^\s`]+?"          # C:\... or C:/...
    r"|~[/\\][^\s`]+?"                  # ~/...
    r"|/[A-Za-z][^\s`]*?/[^\s`]+?"      # /usr/bin/... (avoid lone /)
    r"|\.{1,2}[/\\][^\s`]+?"            # ./foo, ../foo
    r"|[\w\-]+[/\\][\w\-/\\\.]+?"       # foo/bar/baz.ext (must have /)
    r")`"
)

# Skip these even if they match the pattern (known placeholders/examples)
SKIP_PATTERNS = [
    "path/to/",
    "foo/",
    "bar/",
    "example.",
    "your-",
    "my-",
    "<",   # <placeholder>
    "$",   # $VAR
    "{",   # {template}
    "ds_",  # ds_id in SQL examples
    "0N",   # placeholder like 0N-name.md
    "...",  # placeholder like foo/.../bar
    "{{",   # template variable
]


def extract_paths(content: str) -> set[str]:
    """Extract file path references from markdown text."""
    matches = PATH_PATTERN.findall(content)
    paths = set()
    for match in matches:
        path = match[0] if isinstance(match, tuple) else match
        if any(skip in path for skip in SKIP_PATTERNS):
            continue
        paths.add(path)
    return paths


def check_path(path_str: str, base: Path) -> tuple[bool, str]:
    """Check if a path exists. Returns (exists, resolved_path_str).

    Tries (in order): expand ~, absolute, relative to base, relative to cwd,
    and contextual lookup under common workspace roots (Desktop, home).
    """
    # Expand home directory (~/foo)
    if path_str.startswith("~"):
        expanded = Path(path_str).expanduser()
        return expanded.exists(), str(expanded)

    p = Path(path_str)

    if p.is_absolute():
        return p.exists(), str(p)

    # Relative to base (the file containing the reference)
    rel_to_base = base / path_str
    if rel_to_base.exists():
        return True, str(rel_to_base)

    # Relative to cwd
    if Path(path_str).exists():
        return True, path_str

    # Contextual lookup - path might be a suffix like "project-name/file.md".
    # Check under common roots: Desktop, home.
    workspace_roots = [
        Path.home() / "Desktop",
        Path.home(),
    ]
    for root in workspace_roots:
        if not root.exists():
            continue
        candidate = root / path_str
        if candidate.exists():
            return True, str(candidate)

    return False, path_str


def validate_file(md_file: Path) -> list[str]:
    """Validate all path references in a markdown file. Returns list of drift issues."""
    if not md_file.exists():
        return [f"MISSING FILE: {md_file}"]

    content = md_file.read_text(encoding="utf-8", errors="replace")
    paths = extract_paths(content)
    issues = []

    for path_ref in paths:
        exists, _ = check_path(path_ref, md_file.parent)
        if not exists:
            issues.append(f"{md_file.name}: broken ref -> {path_ref}")

    return issues


def main() -> int:
    cwd = Path.cwd()
    strict_mode = (
        "--strict" in sys.argv
        or os.environ.get("CONFIG_VALIDATOR_STRICT", "").lower() in {"1", "true", "yes"}
        or os.environ.get("CI", "").lower() in {"1", "true", "yes"}
    )

    # Files to validate
    targets = []
    candidate_paths = [
        cwd / "README.md",
        cwd / "AGENTS.md",
        cwd / "hooks" / "README.md",
        cwd / "templates" / "README.md",
    ]
    targets.extend([p for p in candidate_paths if p.exists()])

    project_rules = cwd / ".cursor" / "rules"
    if project_rules.exists():
        targets.extend(project_rules.glob("*.md"))

    # Validate
    all_issues = []
    for target in targets:
        issues = validate_file(target)
        all_issues.extend(issues)

    # Report
    if not all_issues:
        print(f"[config-validator] OK: {len(targets)} files, no drift detected")
        return 0

    print(f"[config-validator] DRIFT DETECTED: {len(all_issues)} broken references")
    print(f"[config-validator] Files scanned: {len(targets)}")
    for issue in all_issues[:10]:
        print(f"  - {issue}")
    if len(all_issues) > 10:
        print(f"  ... and {len(all_issues) - 10} more")

    # Write detailed report
    report_path = cwd / ".cursor" / "drift-report.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        "# Config Drift Report\n\n"
        f"Scanned {len(targets)} files, found {len(all_issues)} broken references.\n\n"
        + "\n".join(f"- {i}" for i in all_issues)
        + "\n",
        encoding="utf-8",
    )
    print(f"[config-validator] Full report: {report_path}")

    # In CI/strict mode drift blocks the run.
    if strict_mode:
        print("[config-validator] Strict mode enabled -> exiting with code 1")
        return 1

    # Local default remains non-blocking.
    print(
        "[config-validator] Non-strict mode -> exiting with code 0 "
        "(use --strict or CONFIG_VALIDATOR_STRICT=1 to fail on drift)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
