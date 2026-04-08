#!/usr/bin/env python3
"""Clean up legacy files after copier template has been applied.

Handles migration from old-style Plone packages:
- Renames bobtemplate.cfg to bobtemplate.cfg.bak
- Renames setup.py to setup.py.bak
- Renames setup.cfg to setup.cfg.bak
- Migrates relevant settings from old pyproject.toml to new format
"""
from pathlib import Path


# Files that should be renamed (not deleted) after migration
LEGACY_FILES = [
    "bobtemplate.cfg",
    "setup.py",
    "setup.cfg",
]


def cleanup_legacy_files(start_path: Path | None = None) -> list[str]:
    """
    Rename legacy files to .bak so they don't interfere.

    Returns:
        List of files that were renamed
    """
    start_path = start_path or Path.cwd()
    renamed = []

    for filename in LEGACY_FILES:
        filepath = start_path / filename
        if filepath.exists():
            backup = filepath.with_suffix(filepath.suffix + ".bak")
            # Don't overwrite existing backup
            if backup.exists():
                counter = 1
                while backup.exists():
                    backup = filepath.with_suffix(f"{filepath.suffix}.bak.{counter}")
                    counter += 1
            filepath.rename(backup)
            renamed.append(f"{filename} -> {backup.name}")
            print(f"Renamed legacy file: {filename} -> {backup.name}")

    return renamed


def migrate_pyproject_settings(start_path: Path | None = None) -> bool:
    """
    Migrate settings from an old-style pyproject.toml to include
    [tool.plone.backend_addon.settings] if missing.

    This handles pyproject.toml files that use setuptools instead of hatchling,
    or that have a [project] section but no plone-specific tool settings.

    Returns:
        True if migration was performed
    """
    try:
        import tomlkit
    except ImportError:
        print("Warning: tomlkit not available, skipping pyproject.toml migration.")
        return False

    start_path = start_path or Path.cwd()
    pyproject_path = start_path / "pyproject.toml"

    if not pyproject_path.exists():
        return False

    with open(pyproject_path) as f:
        doc = tomlkit.parse(f.read())

    # Check if plone settings already exist
    plone_settings = (
        doc.get("tool", {})
        .get("plone", {})
        .get("backend_addon", {})
        .get("settings", {})
    )
    if plone_settings:
        # Already has modern settings, nothing to migrate
        return False

    project = doc.get("project", {})
    package_name = project.get("name")
    if not package_name:
        return False

    # Migrate build system from setuptools to hatchling
    build_system = doc.get("build-system", {})
    build_backend = build_system.get("build-backend", "")
    if "setuptools" in build_backend:
        doc["build-system"] = tomlkit.table()
        doc["build-system"]["requires"] = ["hatchling"]
        doc["build-system"]["build-backend"] = "hatchling.build"
        print("Migrated build-system from setuptools to hatchling.")

        # Add hatch wheel config
        package_folder = package_name.replace(".", "/")
        top_package = package_folder.split("/")[0]
        if "tool" not in doc:
            doc["tool"] = tomlkit.table()
        tool = doc["tool"]
        if "hatch" not in tool:
            tool["hatch"] = tomlkit.table()
        hatch = tool["hatch"]
        if "build" not in hatch:
            hatch["build"] = tomlkit.table()
        build = hatch["build"]
        if "targets" not in build:
            build["targets"] = tomlkit.table()
        targets = build["targets"]
        if "wheel" not in targets:
            targets["wheel"] = tomlkit.table()
        targets["wheel"]["packages"] = [f"src/{top_package}"]

    # Remove old setuptools-specific sections
    tool = doc.get("tool", {})
    for old_section in ["setuptools", "setuptools.packages.find"]:
        parts = old_section.split(".")
        current = tool
        for i, part in enumerate(parts[:-1]):
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                current = None
                break
        if current is not None and isinstance(current, dict) and parts[-1] in current:
            del current[parts[-1]]
            print(f"Removed old [tool.{old_section}] section.")

    with open(pyproject_path, "w") as f:
        f.write(tomlkit.dumps(doc))

    print("Migrated pyproject.toml settings.")
    return True
