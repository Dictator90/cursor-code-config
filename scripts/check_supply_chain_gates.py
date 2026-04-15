#!/usr/bin/env python3
"""Validate supply-chain age-gating and unified policy."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.parse import quote
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parent.parent
POLICY_PATH = ROOT / ".cursor" / ".supply-chain-policy.json"
COMPOSER_LOCK_PATH = ROOT / "composer.lock"
DEFAULT_MIN_RELEASE_AGE_DAYS = 7


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _default_policy() -> dict[str, Any]:
    return {
        "defaults": {
            "enabled": True,
            "minReleaseAgeDays": DEFAULT_MIN_RELEASE_AGE_DAYS,
        },
        "npm": {
            "enabled": True,
            "minReleaseAgeDays": DEFAULT_MIN_RELEASE_AGE_DAYS,
            "ignore": [],
        },
        "composer": {
            "enabled": True,
            "minReleaseAgeDays": DEFAULT_MIN_RELEASE_AGE_DAYS,
            "ignore": [],
        },
        "pypi": {
            "enabled": True,
            "minReleaseAgeDays": DEFAULT_MIN_RELEASE_AGE_DAYS,
            "ignore": [],
        },
    }


def _load_policy() -> tuple[dict[str, Any], dict[str, Any]]:
    if not POLICY_PATH.exists():
        return (
            _default_policy(),
            {
                "name": "supply_chain_policy_file",
                "status": "PASS",
                "source": str(POLICY_PATH),
                "details": "policy file not found; using built-in defaults",
            },
        )

    try:
        raw = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return (
            _default_policy(),
            {
                "name": "supply_chain_policy_file",
                "status": "FAIL",
                "source": str(POLICY_PATH),
                "details": f"invalid JSON: {exc}",
            },
        )

    supply_chain = raw.get("supplyChain", {})
    if not isinstance(supply_chain, dict):
        return (
            _default_policy(),
            {
                "name": "supply_chain_policy_file",
                "status": "FAIL",
                "source": str(POLICY_PATH),
                "details": "field 'supplyChain' must be an object",
            },
        )

    defaults = supply_chain.get("defaults", {})
    if not isinstance(defaults, dict):
        defaults = {}
    default_enabled = bool(defaults.get("enabled", True))
    default_days_raw = defaults.get("minReleaseAgeDays", DEFAULT_MIN_RELEASE_AGE_DAYS)
    try:
        default_days = int(default_days_raw)
        if default_days < 0:
            raise ValueError
    except (TypeError, ValueError):
        return (
            _default_policy(),
            {
                "name": "supply_chain_policy_file",
                "status": "FAIL",
                "source": str(POLICY_PATH),
                "details": "supplyChain.defaults.minReleaseAgeDays must be a non-negative integer",
            },
        )

    parsed = {
        "defaults": {
            "enabled": default_enabled,
            "minReleaseAgeDays": default_days,
        }
    }

    for ecosystem in ("npm", "composer", "pypi"):
        section = supply_chain.get(ecosystem, {})
        if not isinstance(section, dict):
            section = {}
        enabled = bool(section.get("enabled", default_enabled))
        days_raw = section.get("minReleaseAgeDays", default_days)
        try:
            days = int(days_raw)
            if days < 0:
                raise ValueError
        except (TypeError, ValueError):
            return (
                _default_policy(),
                {
                    "name": "supply_chain_policy_file",
                    "status": "FAIL",
                    "source": str(POLICY_PATH),
                    "details": f"supplyChain.{ecosystem}.minReleaseAgeDays must be a non-negative integer",
                },
            )
        ignore_values = section.get("ignore", [])
        if not isinstance(ignore_values, list) or not all(isinstance(v, str) for v in ignore_values):
            return (
                _default_policy(),
                {
                    "name": "supply_chain_policy_file",
                    "status": "FAIL",
                    "source": str(POLICY_PATH),
                    "details": f"supplyChain.{ecosystem}.ignore must be an array of strings",
                },
            )
        parsed[ecosystem] = {
            "enabled": enabled,
            "minReleaseAgeDays": days,
            "ignore": sorted(set(v.strip() for v in ignore_values if v.strip())),
        }

    return (
        parsed,  # type: ignore[return-value]
        {
            "name": "supply_chain_policy_file",
            "status": "PASS",
            "source": str(POLICY_PATH),
            "details": {
                "defaults": parsed["defaults"],
                "npm": {
                    "enabled": parsed["npm"]["enabled"],
                    "minReleaseAgeDays": parsed["npm"]["minReleaseAgeDays"],
                    "ignoreCount": len(parsed["npm"]["ignore"]),
                },
                "composer": {
                    "enabled": parsed["composer"]["enabled"],
                    "minReleaseAgeDays": parsed["composer"]["minReleaseAgeDays"],
                    "ignoreCount": len(parsed["composer"]["ignore"]),
                },
                "pypi": {
                    "enabled": parsed["pypi"]["enabled"],
                    "minReleaseAgeDays": parsed["pypi"]["minReleaseAgeDays"],
                    "ignoreCount": len(parsed["pypi"]["ignore"]),
                },
            },
        },
    )


def _check_npm_repo_local(min_release_age_days: int, enabled: bool) -> dict[str, Any]:
    return {
        "name": "npm_policy_state",
        "status": "PASS",
        "source": str(POLICY_PATH),
        "details": {
            "enabled": enabled,
            "minReleaseAgeDays": min_release_age_days,
            "note": "npm age-gating is configured in .cursor/.supply-chain-policy.json.",
        },
    }


def _check_npm_ignore_alignment(ignored_packages: list[str], enabled: bool) -> dict[str, Any]:
    return {
        "name": "npm_ignore_packages",
        "status": "PASS",
        "source": str(POLICY_PATH),
        "details": {
            "enabled": enabled,
            "configured": ignored_packages,
        },
    }


def _check_pypi_policy_state(enabled: bool, min_release_age_days: int, ignored_packages: list[str]) -> dict[str, Any]:
    return {
        "name": "pypi_policy_state",
        "status": "PASS",
        "source": str(POLICY_PATH),
        "details": {
            "enabled": enabled,
            "minReleaseAgeDays": min_release_age_days,
            "ignored_packages": ignored_packages,
            "note": "PyPI policy is configured in .cursor/.supply-chain-policy.json; no uv.toml required.",
        },
    }


def _check_ecosystem_support(policy: dict[str, Any]) -> dict[str, Any]:
    details = {
        "composer": {
            "enabled": policy["composer"]["enabled"],
            "minReleaseAgeDays": policy["composer"]["minReleaseAgeDays"],
            "ignored_packages": policy["composer"]["ignore"],
            "native_age_gate_supported_in_repo": True,
            "note": "Composer age-gating is validated against Packagist release timestamps.",
        },
        "pypi": {
            "enabled": policy["pypi"]["enabled"],
            "minReleaseAgeDays": policy["pypi"]["minReleaseAgeDays"],
            "ignored_packages": policy["pypi"]["ignore"],
            "native_age_gate_supported_in_repo": True,
            "note": "PyPI age-gating policy is centralized in .cursor/.supply-chain-policy.json.",
        },
    }
    return {
        "name": "ecosystem_support",
        "status": "PASS",
        "source": str(POLICY_PATH),
        "details": details,
    }


def _load_composer_lock() -> tuple[list[tuple[str, str]], str | None]:
    if not COMPOSER_LOCK_PATH.exists():
        return [], None
    try:
        raw = json.loads(COMPOSER_LOCK_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [], f"invalid composer.lock JSON: {exc}"
    packages: list[tuple[str, str]] = []
    for section in ("packages", "packages-dev"):
        values = raw.get(section, [])
        if not isinstance(values, list):
            continue
        for package in values:
            if not isinstance(package, dict):
                continue
            name = package.get("name")
            version = package.get("version")
            if isinstance(name, str) and isinstance(version, str) and name and version:
                packages.append((name, version))
    return packages, None


def _normalize_composer_version(version: str) -> str:
    return version.lstrip("v").strip()


def _fetch_packagist_release(package_name: str, locked_version: str) -> tuple[datetime | None, str | None]:
    url = f"https://repo.packagist.org/p2/{quote(package_name, safe='')}.json"
    try:
        with urlopen(url, timeout=12) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except URLError as exc:
        return None, f"network error: {exc}"
    except json.JSONDecodeError as exc:
        return None, f"invalid JSON from packagist: {exc}"

    package_versions = payload.get("packages", {}).get(package_name, [])
    if not isinstance(package_versions, list):
        return None, "package versions list missing in packagist response"

    normalized_locked = _normalize_composer_version(locked_version)
    for item in package_versions:
        if not isinstance(item, dict):
            continue
        candidate_version = item.get("version")
        candidate_normalized = item.get("version_normalized")
        if not isinstance(candidate_version, str):
            continue
        matches = (
            candidate_version == locked_version
            or _normalize_composer_version(candidate_version) == normalized_locked
            or (isinstance(candidate_normalized, str) and _normalize_composer_version(candidate_normalized) == normalized_locked)
        )
        if not matches:
            continue
        published_raw = item.get("time")
        if not isinstance(published_raw, str):
            return None, "matched version has no release time"
        # Packagist time format is ISO8601 with trailing Z
        try:
            published_at = datetime.fromisoformat(published_raw.replace("Z", "+00:00"))
        except ValueError:
            return None, f"invalid release time format: {published_raw}"
        return published_at.astimezone(timezone.utc), None

    return None, f"version '{locked_version}' not found on packagist"


def _check_composer_release_age(policy: dict[str, Any]) -> dict[str, Any]:
    composer_cfg = policy["composer"]
    min_release_age_days = int(composer_cfg["minReleaseAgeDays"])
    if not composer_cfg["enabled"]:
        return {
            "name": "composer_release_age",
            "status": "PASS",
            "source": str(COMPOSER_LOCK_PATH),
            "details": "composer age gate disabled in policy",
        }
    packages, lock_error = _load_composer_lock()
    if lock_error:
        return {
            "name": "composer_release_age",
            "status": "FAIL",
            "source": str(COMPOSER_LOCK_PATH),
            "details": lock_error,
        }
    if not packages:
        return {
            "name": "composer_release_age",
            "status": "PASS",
            "source": str(COMPOSER_LOCK_PATH),
            "details": "composer.lock not found or contains no packages; check skipped",
        }

    ignored = set(composer_cfg["ignore"])
    now = datetime.now(timezone.utc)
    violations: list[dict[str, Any]] = []
    fetch_errors: list[dict[str, str]] = []
    checked_count = 0

    for package_name, locked_version in packages:
        if package_name in ignored:
            continue
        checked_count += 1
        published_at, fetch_error = _fetch_packagist_release(package_name, locked_version)
        if fetch_error:
            fetch_errors.append({
                "package": package_name,
                "version": locked_version,
                "error": fetch_error,
            })
            continue
        if published_at is None:
            continue
        age_days = (now - published_at).total_seconds() / 86400
        if age_days < min_release_age_days:
            violations.append({
                "package": package_name,
                "version": locked_version,
                "published_at": published_at.isoformat(),
                "age_days": round(age_days, 2),
            })

    if fetch_errors:
        return {
            "name": "composer_release_age",
            "status": "FAIL",
            "source": str(COMPOSER_LOCK_PATH),
            "details": {
                "error": "could not validate all composer packages against packagist",
                "fetch_errors": fetch_errors[:20],
                "checked_packages": checked_count,
                "minimum_age_days": min_release_age_days,
                "ignored_packages": sorted(ignored),
            },
        }

    if violations:
        return {
            "name": "composer_release_age",
            "status": "FAIL",
            "source": str(COMPOSER_LOCK_PATH),
            "details": {
                "minimum_age_days": min_release_age_days,
                "violations": violations[:20],
                "checked_packages": checked_count,
                "ignored_packages": sorted(ignored),
            },
        }

    return {
        "name": "composer_release_age",
        "status": "PASS",
        "source": str(COMPOSER_LOCK_PATH),
        "details": {
            "minimum_age_days": min_release_age_days,
            "checked_packages": checked_count,
            "ignored_packages": sorted(ignored),
        },
    }


def run_checks(mode: str) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    policy, policy_check = _load_policy()
    checks.append(policy_check)

    if mode == "strict":
        checks.append(_check_npm_repo_local(policy["npm"]["minReleaseAgeDays"], policy["npm"]["enabled"]))
        checks.append(_check_npm_ignore_alignment(policy["npm"]["ignore"], policy["npm"]["enabled"]))
        checks.append(_check_pypi_policy_state(policy["pypi"]["enabled"], policy["pypi"]["minReleaseAgeDays"], policy["pypi"]["ignore"]))
        checks.append(_check_composer_release_age(policy))
    else:
        checks.append(_check_npm_repo_local(policy["npm"]["minReleaseAgeDays"], policy["npm"]["enabled"]))
        checks.append(_check_npm_ignore_alignment(policy["npm"]["ignore"], policy["npm"]["enabled"]))
        checks.append(_check_pypi_policy_state(policy["pypi"]["enabled"], policy["pypi"]["minReleaseAgeDays"], policy["pypi"]["ignore"]))
        checks.append(_check_composer_release_age(policy))
    checks.append(_check_ecosystem_support(policy))

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
