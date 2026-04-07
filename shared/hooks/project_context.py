#!/usr/bin/env python3
"""Detect parent project context for zope_instance subtemplate."""
import sys
from pathlib import Path
from typing import Any

import tomllib
from exceptions import ProjectContextError


def find_project_context(start_path: Path | None = None) -> dict[str, Any] | None:
    """
    Find project context by looking for [tool.plone.project.settings] in pyproject.toml.

    Args:
        start_path: Directory to search in (defaults to current directory)

    Returns:
        Dictionary with project settings or None if not found
    """
    start_path = start_path or Path.cwd()

    pyproject_path = start_path / "pyproject.toml"
    if pyproject_path.exists():
        settings = _read_project_settings(pyproject_path)
        if settings:
            return settings

    return None


def _read_project_settings(pyproject_path: Path) -> dict[str, Any] | None:
    """
    Read project settings from pyproject.toml.

    Args:
        pyproject_path: Path to pyproject.toml

    Returns:
        Dictionary with project settings or None if not found
    """
    try:
        with open(pyproject_path, "rb") as f:
            doc = tomllib.load(f)

        settings = doc.get("tool", {}).get("plone", {}).get("project", {}).get("settings", {})
        if settings:
            result = dict(settings)
            # Also include project name if not already in settings
            project = doc.get("project", {})
            if "project_name" not in result and "name" in project:
                result["project_name"] = project["name"]
            return result
    except (tomllib.TOMLDecodeError, OSError):
        pass

    return None


def require_project_context(start_path: Path | None = None) -> dict[str, Any]:
    """
    Raise ProjectContextError if no parent project found.

    Args:
        start_path: Directory to search in (defaults to current directory)

    Returns:
        Dictionary with project settings

    Raises:
        ProjectContextError: If no parent project is detected
    """
    context = find_project_context(start_path)
    if not context:
        raise ProjectContextError(
            "No parent project detected. This template must be run inside an existing zope-setup project."
        )
    return context


if __name__ == "__main__":
    try:
        require_project_context()
    except ProjectContextError as e:
        print("\n" + "=" * 60)
        print("ERROR: No parent project detected!")
        print("=" * 60)
        print(f"\n{e}")
        print("\nFirst create a project with:")
        print("  copier copy ~/.copier-templates/plone-copier-templates/zope-setup my-project")
        print("\nThen run this subtemplate inside that directory.")
        print("=" * 60 + "\n")
        sys.exit(1)
