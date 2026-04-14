#!/usr/bin/env python3
"""Deterministic checks for local safety guard hooks."""

from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
HOOKS_DIR = ROOT / "hooks"


def _load_python_module_tree(path: Path) -> ast.AST:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _collect_list_values(tree: ast.AST, var_name: str) -> list[str]:
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == var_name:
                    if not isinstance(node.value, ast.List):
                        return []
                    values: list[str] = []
                    for item in node.value.elts:
                        if isinstance(item, ast.Tuple) and item.elts:
                            first = item.elts[0]
                            if isinstance(first, ast.Call) and getattr(first.func, "attr", "") == "compile":
                                if first.args and isinstance(first.args[0], ast.Constant):
                                    values.append(str(first.args[0].value))
                    return values
    return []


def run_checks() -> dict[str, Any]:
    destructive_hook = HOOKS_DIR / "destructive-command-guard.py"
    secret_hook = HOOKS_DIR / "secret-leak-guard.py"

    checks: list[dict[str, Any]] = []

    checks.append(
        {
            "name": "destructive_hook_exists",
            "status": "PASS" if destructive_hook.exists() else "FAIL",
            "details": str(destructive_hook),
        }
    )
    checks.append(
        {
            "name": "secret_hook_exists",
            "status": "PASS" if secret_hook.exists() else "FAIL",
            "details": str(secret_hook),
        }
    )

    destructive_patterns: list[str] = []
    secret_patterns: list[str] = []
    if destructive_hook.exists():
        destructive_patterns = _collect_list_values(
            _load_python_module_tree(destructive_hook), "DESTRUCTIVE_PATTERNS"
        )
    if secret_hook.exists():
        secret_patterns = _collect_list_values(
            _load_python_module_tree(secret_hook), "SECRET_PATTERNS"
        )

    must_destructive = [r"\brm\s+.*-[a-zA-Z]*r[a-zA-Z]*f", r"\bgit\s+reset\s+--hard", r"\bDROP\s+(TABLE|DATABASE)\b"]
    missing_destructive = [p for p in must_destructive if p not in destructive_patterns]
    checks.append(
        {
            "name": "destructive_patterns_present",
            "status": "PASS" if not missing_destructive else "FAIL",
            "details": {"missing": missing_destructive, "expected_count": len(must_destructive)},
        }
    )

    must_secret = [r"\bsk-[a-zA-Z0-9]{20,}", r"-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----", r"(?i)bearer\s+[a-zA-Z0-9\-_.]{20,}"]
    missing_secret = [p for p in must_secret if p not in secret_patterns]
    checks.append(
        {
            "name": "secret_patterns_present",
            "status": "PASS" if not missing_secret else "FAIL",
            "details": {"missing": missing_secret, "expected_count": len(must_secret)},
        }
    )

    overall = "PASS" if all(c["status"] == "PASS" for c in checks) else "FAIL"
    return {"overall_status": overall, "checks": checks}


def main() -> int:
    parser = argparse.ArgumentParser(description="Check mandatory safety guards.")
    parser.add_argument("--output", type=Path, required=False, help="Optional output JSON file path.")
    args = parser.parse_args()

    result = run_checks()
    serialized = json.dumps(result, indent=2)
    print(serialized)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized + "\n", encoding="utf-8")

    return 0 if result["overall_status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
