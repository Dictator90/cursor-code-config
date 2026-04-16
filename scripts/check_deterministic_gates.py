#!/usr/bin/env python3
"""Deterministic gate bundle for mandatory project checks."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_REQUIRED_EVIDENCE = (
    "T01-scope-lock.md",
    "T02-evidence-matrix.md",
    "T03-safety-guards.json",
    "T07-supply-chain.json",
)
LATEST_RUN_POINTER_REL = Path(".cursor") / "tasks" / "runs" / "LATEST"


def _run(command: list[str], cwd: Path) -> dict[str, Any]:
    process = subprocess.run(command, cwd=cwd, capture_output=True, text=True)
    return {
        "command": " ".join(command),
        "returncode": process.returncode,
        "stdout": process.stdout.strip(),
        "stderr": process.stderr.strip(),
        "status": "PASS" if process.returncode == 0 else "FAIL",
    }


def _resolve_run_dir(run_dir: Path | None, run_id: str | None, project_root: Path) -> Path | None:
    if run_dir is not None:
        return run_dir if run_dir.is_absolute() else (project_root / run_dir)
    if run_id:
        return project_root / ".cursor" / "tasks" / "runs" / run_id

    latest_run_pointer = project_root / LATEST_RUN_POINTER_REL
    if not latest_run_pointer.exists():
        return None

    lines = [line.strip() for line in latest_run_pointer.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines:
        return None
    candidate = Path(lines[0])
    return candidate if candidate.is_absolute() else (ROOT / candidate)


def _evidence_checks(evidence_dir: Path, required_files: tuple[str, ...]) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    for filename in required_files:
        path = evidence_dir / filename
        checks.append(
            {
                "command": f"exists:{path}",
                "returncode": 0 if path.exists() else 1,
                "stdout": str(path),
                "stderr": "",
                "status": "PASS" if path.exists() else "FAIL",
            }
        )
    return checks


def run_checks(
    project_root: Path,
    run_dir: Path | None,
    evidence_mode: str,
    required_evidence: tuple[str, ...],
) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    scripts_dir = ROOT / "scripts"

    checks.append(_run([sys.executable, str(scripts_dir / "validate_config.py")], cwd=project_root))
    checks.append(_run([sys.executable, str(scripts_dir / "check_safety_guards.py")], cwd=project_root))
    checks.append(_run([sys.executable, str(scripts_dir / "check_supply_chain_gates.py")], cwd=project_root))
    # Plugin-surface checks are meaningful only when validating the plugin repo itself.
    if project_root.resolve() == ROOT.resolve():
        checks.append(_run([sys.executable, str(scripts_dir / "check_markdown_links.py")], cwd=project_root))
        checks.append(_run([sys.executable, str(scripts_dir / "check_cursor_only_surface.py")], cwd=project_root))
        checks.append(_run([sys.executable, str(scripts_dir / "check_plugin_submission.py")], cwd=project_root))

    evidence_status = "skipped"
    evidence_dir = None
    if run_dir is not None:
        evidence_dir = run_dir / "evidence"
    if evidence_mode == "required":
        if evidence_dir is None:
            checks.append(
                {
                    "command": "resolve-run-dir",
                    "returncode": 1,
                    "stdout": "",
                    "stderr": "required evidence mode set but no run directory could be resolved",
                    "status": "FAIL",
                }
            )
            evidence_status = "required-missing-run-dir"
        else:
            checks.extend(_evidence_checks(evidence_dir, required_evidence))
            evidence_status = "required"
    elif evidence_mode == "auto":
        if evidence_dir is not None and evidence_dir.exists():
            checks.extend(_evidence_checks(evidence_dir, required_evidence))
            evidence_status = "checked"
        else:
            evidence_status = "skipped-auto-no-evidence-dir"
    else:
        evidence_status = "skipped-explicit"

    overall = "PASS" if all(check["status"] == "PASS" for check in checks) else "FAIL"
    return {
        "overall_status": overall,
        "checks": checks,
        "run_dir": str(run_dir) if run_dir is not None else "",
        "evidence_mode": evidence_mode,
        "evidence_status": evidence_status,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run deterministic gate checks.")
    parser.add_argument("--run-id", type=str, required=False, help="Run id under .cursor/tasks/runs.")
    parser.add_argument(
        "--run-dir",
        type=Path,
        required=False,
        help="Absolute or repo-relative run directory path.",
    )
    parser.add_argument(
        "--evidence-mode",
        choices=["auto", "required", "skip"],
        default="auto",
        help="auto: check run evidence only when run/evidence dir exists; "
        "required: fail if run/evidence data missing; skip: do not check evidence files.",
    )
    parser.add_argument("--output", type=Path, required=False, help="Optional output JSON path.")
    parser.add_argument(
        "--project-root",
        type=Path,
        required=False,
        help="Project root to validate. Defaults to current working directory.",
    )
    args = parser.parse_args()

    project_root = (args.project_root.resolve() if args.project_root else Path.cwd().resolve())
    resolved_run_dir = _resolve_run_dir(run_dir=args.run_dir, run_id=args.run_id, project_root=project_root)
    result = run_checks(
        project_root=project_root,
        run_dir=resolved_run_dir,
        evidence_mode=args.evidence_mode,
        required_evidence=DEFAULT_REQUIRED_EVIDENCE,
    )
    serialized = json.dumps(result, indent=2)
    print(serialized)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized + "\n", encoding="utf-8")

    return 0 if result["overall_status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
