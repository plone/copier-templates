#!/usr/bin/env python3
"""Tasks for upgrade_step subtemplate."""
import sys
from pathlib import Path

# Add shared module to path
sys.path.insert(0, str(Path(__file__).parent.parent / "shared"))

from exceptions import AddonContextError, CopierTemplateError  # noqa: E402
from hooks.addon_context import (  # noqa: E402
    find_addon_context,
    resolve_post_copy_context,
)
from hooks.git_check import warn_git_unclean  # noqa: E402
from utils.hidden_profiles import hide_product, register_hidden_profiles  # noqa: E402
from utils.xml_updater import (  # noqa: E402
    MetadataXMLUpdater,
    ParentZCMLUpdater,
    UpgradeZCMLUpdater,
)


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
    source_version: str,
    destination_version: str,
    import_steps: str,
) -> None:
    """Wire the new upgrade step into the addon and print a summary.

    Works for both modern (pyproject.toml) and legacy (bobtemplate.cfg /
    setup.py) packages.
    """
    ctx = resolve_post_copy_context(dest_path)
    if ctx is None:
        print(
            "Warning: could not detect parent addon (no pyproject.toml, "
            "bobtemplate.cfg, or setup.py). Skipping configuration updates."
        )
        return

    if not ctx.package_folder:
        print("Warning: could not determine package_folder. Skipping updates.")
        return

    steps = [step for step in import_steps.split(",") if step]
    pkg = ctx.dest / "src" / ctx.package_folder
    created = [
        f"upgrades/v{destination_version}.py",
        f"upgrades/{destination_version}.zcml",
        f"tests/test_upgrade_step_{destination_version}.py",
    ]
    if steps:
        created.append(f"upgrades/{destination_version}/")
    updated = []
    notes = []

    zcml_updater = UpgradeZCMLUpdater(pkg / "upgrades/configure.zcml")
    zcml_updater.create_if_missing(ctx.package_name or "package")
    step_zcml = f"{destination_version}.zcml"
    if not zcml_updater.has_file_include(step_zcml):
        zcml_updater.add_file_include(step_zcml)
        zcml_updater.save()
        updated.append(f'upgrades/configure.zcml: <include file="{step_zcml}" />')

    parent_zcml = pkg / "configure.zcml"
    if parent_zcml.exists():
        parent_updater = ParentZCMLUpdater(parent_zcml)
        if not parent_updater.has_include(".upgrades"):
            parent_updater.add_include(".upgrades")
            parent_updater.save()
            updated.append('configure.zcml: <include package=".upgrades" />')

    metadata_updater = MetadataXMLUpdater(pkg / "profiles/default/metadata.xml")
    current = metadata_updater.get_version()
    if current and current != destination_version:
        metadata_updater.set_version(destination_version)
        updated.append(f"profiles/default/metadata.xml: {current} -> {destination_version}")
    elif not current:
        notes.append("could not read the version from profiles/default/metadata.xml")

    if steps:
        upgrades_product = f"{ctx.package_name}.upgrades"
        hidden = hide_product(pkg / "setuphandlers.py", upgrades_product)
        if hidden == "added":
            updated.append(f"setuphandlers.py: {upgrades_product} hidden")
        if hidden and register_hidden_profiles(parent_zcml, ctx.package_name):
            updated.append("configure.zcml: HiddenProfiles utility registered")
        if not hidden:
            notes.append(
                f"add {upgrades_product!r} to HiddenProfiles.getNonInstallableProducts "
                "in setuphandlers.py"
            )
        notes.append(
            f"put the XML for {', '.join(steps)} into upgrades/{destination_version}/"
        )
    notes.append(
        f"replace the TODO in tests/test_upgrade_step_{destination_version}.py "
        "with a check of the step's effect"
    )

    print_summary(
        f"Upgrade step {source_version} -> {destination_version}: {upgrade_step_title}",
        created,
        updated,
        notes,
    )


def print_summary(title: str, created: list, updated: list, notes: list) -> None:
    print(f"\n{title}")
    for label, items in (("created", created), ("updated", updated), ("todo", notes)):
        for item in items:
            print(f"  {label:8} {item}")


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
                    "Usage: tasks.py post_copy <dest_path> <title> "
                    "<source_version> <destination_version> <import_steps>"
                )
                sys.exit(1)
            post_copy(*sys.argv[2:7])

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
