"""Fetch available Plone versions from PyPI."""

import json
import urllib.request
from functools import lru_cache

PYPI_URL = "https://pypi.org/pypi/Products.CMFPlone/json"
REQUEST_TIMEOUT = 10

# Hardcoded fallback when PyPI is unreachable
FALLBACK_VERSIONS = ["6.1.1", "6.1.0", "6.0.13"]


@lru_cache(maxsize=1)
def fetch_plone_versions():
    """Fetch all stable Plone 6+ release versions from PyPI.

    Returns a sorted list of version strings (newest first),
    e.g. ["6.1.1", "6.1.0", "6.0.13", ...].
    Falls back to hardcoded list if PyPI is unreachable.
    """
    try:
        req = urllib.request.Request(
            PYPI_URL, headers={"Accept": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            data = json.loads(resp.read())
    except Exception:
        return list(FALLBACK_VERSIONS)

    versions = []
    for version_str in data.get("releases", {}):
        if _is_stable_plone6(version_str):
            versions.append(version_str)

    versions.sort(key=_version_key, reverse=True)
    return versions if versions else list(FALLBACK_VERSIONS)


def get_major_minor_versions(versions=None):
    """Return deduplicated major.minor versions (newest first).

    E.g. ["6.1", "6.0"] from ["6.1.1", "6.1.0", "6.0.13", ...].
    """
    if versions is None:
        versions = fetch_plone_versions()
    seen = set()
    result = []
    for v in versions:
        parts = v.split(".")
        mm = f"{parts[0]}.{parts[1]}"
        if mm not in seen:
            seen.add(mm)
            result.append(mm)
    return result


def _is_stable_plone6(version_str):
    """Check if a version string is a stable Plone 6+ release."""
    # Skip pre-releases, dev, post, etc.
    for marker in ("a", "b", "rc", "dev", "post"):
        if marker in version_str:
            return False
    parts = version_str.split(".")
    if len(parts) < 3:
        return False
    try:
        major = int(parts[0])
        return major >= 6
    except ValueError:
        return False


def _version_key(version_str):
    """Parse version string into tuple for sorting."""
    parts = version_str.split(".")
    result = []
    for p in parts:
        try:
            result.append(int(p))
        except ValueError:
            result.append(0)
    return tuple(result)
