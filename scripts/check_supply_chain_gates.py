#!/usr/bin/env python3
"""Validate supply-chain age-gating for npm and uv."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _check_npm_repo_local() -> dict[str, str]:
    path = ROOT / ".npmrc"
    content = _read(path)
    if "min-release-age=7" in content:
        return {
            "name": "npm_min_release_age",
            "status": "PASS",
            "source": str(path),
            "details": "min-release-age=7",
        }
    return {
        "name": "npm_min_release_age",
        "status": "FAIL",
        "source": str(path),
        "details": "repo-local .npmrc missing min-release-age=7",
    }


def _check_uv_repo_local() -> dict[str, str]:
    path = ROOT / "uv.toml"
    content = _read(path)
    if 'exclude-newer = "7 days"' in content:
        return {
            "name": "uv_exclude_newer",
            "status": "PASS",
            "source": str(path),
            "details": 'exclude-newer = "7 days"',
        }
    return {
        "name": "uv_exclude_newer",
        "status": "FAIL",
        "source": str(path),
        "details": 'repo-local uv.toml missing exclude-newer = "7 days"',
    }


def _check_with_fallback(
    name: str,
    expected: str,
    repo_path: Path,
    user_path: Path,
) -> dict[str, str]:
    for candidate in (repo_path, user_path):
        content = _read(candidate)
        if expected in content:
            source_type = "repo-local" if candidate == repo_path else "user-home"
            return {
                "name": name,
                "status": "PASS",
                "source": str(candidate),
                "details": f"{expected} ({source_type})",
            }
    return {
        "name": name,
        "status": "FAIL",
        "source": str(repo_path),
        "details": f"{expected} not found in repo-local or user-home policy files",
    }


def run_checks(mode: str) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    if mode == "strict":
        checks.append(_check_npm_repo_local())
        checks.append(_check_uv_repo_local())
    else:
        checks.append(
            _check_with_fallback(
                name="npm_min_release_age",
                expected="min-release-age=7",
                repo_path=ROOT / ".npmrc",
                user_path=Path.home() / ".npmrc",
            )
        )
        checks.append(
            _check_with_fallback(
                name="uv_exclude_newer",
                expected='exclude-newer = "7 days"',
                repo_path=ROOT / "uv.toml",
                user_path=Path.home() / ".config" / "uv" / "uv.toml",
            )
        )

    overall = "PASS" if all(check["status"] == "PASS" for check in checks) else "FAIL"
    return {
        "overall_status": overall,
        "mode": mode,
        "ci_env_detected": bool(os.getenv("CI")),
        "checks": checks,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate supply-chain age gates.")
    parser.add_argument(
        "--mode",
        choices=["strict", "advisory"],
        default="strict",
        help="strict: require repo-local policy files only (default, deterministic for CI). "
        "advisory: allow user-home fallback.",
    )
    parser.add_argument("--output", type=Path, required=False, help="Optional output JSON path.")
    args = parser.parse_args()

    result = run_checks(mode=args.mode)
    serialized = json.dumps(result, indent=2)
    print(serialized)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized + "\n", encoding="utf-8")

    return 0 if result["overall_status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
