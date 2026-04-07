#!/usr/bin/env python3
"""Tasks for upgrade_step subtemplate."""
import re
import sys
from pathlib import Path

# Add shared module to path
sys.path.insert(0, str(Path(__file__).parent.parent / "shared"))

from exceptions import AddonContextError, CopierTemplateError
from hooks.addon_context import find_addon_context
from hooks.git_check import warn_git_unclean
from utils.pyproject_updater import PyprojectUpdater
from utils.xml_updater import MetadataXMLUpdater, UpgradeZCMLUpdater


def validate(dest_path: str) -> None:
    """Validate that parent addon exists."""
    dest = Path(dest_path)

    # Warn about git state (non-blocking)
    warn_git_unclean(dest)

    # Check addon context (blocking - raises exception)
    context = find_addon_context(dest)
    if not context:
        raise AddonContextError(
            f"No parent addon detected at {dest}. "
            "This template must be run inside an existing backend_addon."
        )


def post_copy(
    dest_path: str,
    upgrade_step_title: str,
    upgrade_step_description: str,
    source_version: str,
    destination_version: str,
) -> None:
    """
    Post-copy tasks:
    1. Register upgrade step in addon settings
    2. Update upgrades/configure.zcml with upgrade step entry
    3. Add include for upgrades subpackage in parent configure.zcml
    4. Bump profile version in metadata.xml
    """
    cwd = Path.cwd()
    dest = Path(dest_path)

    if (cwd / "pyproject.toml").exists():
        dest = cwd
    elif not dest.is_absolute():
        dest = dest.resolve()

    pyproject_path = dest / "pyproject.toml"

    if not pyproject_path.exists():
        print(f"Warning: pyproject.toml not found at {pyproject_path}")
        return

    # Compute handler values
    handler_module = upgrade_step_title.lower().replace(" ", "_").replace("-", "_")
    handler_function = handler_module

    # Get package info from pyproject.toml
    updater = PyprojectUpdater(pyproject_path)
    addon_settings = updater.get_addon_settings()
    package_name = addon_settings.get("package_name", "")

    if not package_name:
        pyproject_content = pyproject_path.read_text()
        match = re.search(
            r'^\s*package_name\s*=\s*["\']([^"\']+)["\']',
            pyproject_content,
            re.MULTILINE,
        )
        if match:
            package_name = match.group(1)
        else:
            match = re.search(
                r'^\s*name\s*=\s*["\']([^"\']+)["\']',
                pyproject_content,
                re.MULTILINE,
            )
            if match:
                package_name = match.group(1)

    if not package_name:
        print("Warning: Could not determine package_name from pyproject.toml")
        return

    package_folder = addon_settings.get(
        "package_folder", package_name.replace(".", "/")
    )

    # 1. Register upgrade step in addon settings
    updater.register_subtemplate("upgrade_steps", upgrade_step_title)
    updater.save()
    print(f"Registered upgrade step '{upgrade_step_title}' in addon settings.")

    # 2. Update upgrades/configure.zcml with upgrade step entry
    zcml_path = dest / f"src/{package_folder}/upgrades/configure.zcml"
    zcml_updater = UpgradeZCMLUpdater(zcml_path)
    zcml_updater.create_if_missing(package_name)
    if not zcml_updater.has_upgrade_step(source_version, destination_version):
        zcml_updater.add_upgrade_step(
            title=upgrade_step_title,
            description=upgrade_step_description,
            source=source_version,
            destination=destination_version,
            handler_module=handler_module,
            handler_function=handler_function,
            package_name=package_name,
        )
        zcml_updater.save()
        print(
            f"Updated {zcml_path.relative_to(dest)} with upgrade step "
            f"{source_version} -> {destination_version}."
        )
    else:
        print(
            f"Upgrade step {source_version} -> {destination_version} "
            f"already exists in {zcml_path.relative_to(dest)}."
        )

    # 3. Add include for upgrades subpackage in parent configure.zcml
    parent_zcml = dest / f"src/{package_folder}/configure.zcml"
    if parent_zcml.exists():
        from utils.xml_updater import ParentZCMLUpdater

        parent_updater = ParentZCMLUpdater(parent_zcml)
        if not parent_updater.has_include(".upgrades"):
            parent_updater.add_include(".upgrades")
            parent_updater.save()
            print('Added <include package=".upgrades" /> to parent configure.zcml.')

    # 4. Bump profile version in metadata.xml
    metadata_path = dest / f"src/{package_folder}/profiles/default/metadata.xml"
    metadata_updater = MetadataXMLUpdater(metadata_path)
    current = metadata_updater.get_version()
    if current and current != destination_version:
        metadata_updater.set_version(destination_version)
        print(f"Updated profile version in metadata.xml: {current} -> {destination_version}.")
    elif not current:
        print("Warning: Could not read current profile version from metadata.xml.")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: tasks.py <command> [args...]")
        print("Commands: validate, post_copy")
        sys.exit(1)

    command = sys.argv[1]

    try:
        if command == "validate":
            if len(sys.argv) < 3:
                print("Usage: tasks.py validate <dest_path>")
                sys.exit(1)
            validate(sys.argv[2])

        elif command == "post_copy":
            if len(sys.argv) < 7:
                print(
                    "Usage: tasks.py post_copy <dest_path> <title> <description> "
                    "<source_version> <destination_version>"
                )
                sys.exit(1)
            post_copy(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6])

        else:
            print(f"Unknown command: {command}")
            sys.exit(1)

    except CopierTemplateError as e:
        print("\n" + "=" * 60)
        print(f"ERROR: {e}")
        print("=" * 60)
        print("\nFirst create an addon with:")
        print(
            "  copier copy ~/.copier-templates/plone-copier-templates/backend_addon my-addon"
        )
        print("\nThen run this subtemplate inside that directory:")
        print("  cd my-addon")
        print(
            "  copier copy ~/.copier-templates/plone-copier-templates/upgrade_step ."
        )
        print("=" * 60 + "\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
