#!/usr/bin/env python3
"""Tasks for the view subtemplate."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "shared"))

from exceptions import AddonContextError, CopierTemplateError  # noqa: E402
from hooks.addon_context import find_addon_context  # noqa: E402
from hooks.git_check import warn_git_unclean  # noqa: E402
from utils.pyproject_updater import PyprojectUpdater  # noqa: E402
from utils.xml_updater import ParentZCMLUpdater, extend_configure_zcml  # noqa: E402


def validate(dest_path: str) -> None:
    dest = Path(dest_path)
    warn_git_unclean(dest)
    if not find_addon_context(dest):
        raise AddonContextError(
            f"No parent addon detected at {dest}. "
            "This template must be run inside an existing backend_addon."
        )


def _resolve_dest(dest_path: str) -> Path:
    cwd = Path.cwd()
    dest = Path(dest_path)
    if (cwd / "pyproject.toml").exists():
        return cwd
    if not dest.is_absolute():
        return dest.resolve()
    return dest


def post_copy(
    dest_path: str,
    view_name: str,
    view_for_interface: str = "*",
    view_module: str = "",
    view_class_name: str = "",
    view_template: str = "True",
    view_marker: str = "False",
) -> None:
    dest = _resolve_dest(dest_path)
    pyproject_path = dest / "pyproject.toml"
    if not pyproject_path.exists():
        print(f"Warning: pyproject.toml not found at {pyproject_path}")
        return

    updater = PyprojectUpdater(pyproject_path)
    updater.register_subtemplate("views", view_name)
    updater.save()
    print(f"Registered view '{view_name}' in addon settings.")

    addon_settings = updater.get_addon_settings()
    package_name = addon_settings.get("package_name", "")
    package_folder = addon_settings.get("package_folder", "")
    if not package_folder and package_name:
        package_folder = package_name.replace(".", "/")

    if not package_folder:
        return

    # Extend views/configure.zcml (create if missing) with a new browser:page
    views_zcml = dest / f"src/{package_folder}/views/configure.zcml"
    if view_template.lower() == "true":
        snippet = (
            "  <browser:page\n"
            f'      name="{view_name}"\n'
            f'      for="{view_for_interface}"\n'
            f'      class=".{view_module}.{view_class_name}"\n'
            f'      template="{view_module}.pt"\n'
            '      permission="zope2.View"\n'
            "      />\n"
        )
    else:
        snippet = (
            "  <browser:page\n"
            f'      name="{view_name}"\n'
            f'      for="{view_for_interface}"\n'
            f'      class=".{view_module}.{view_class_name}"\n'
            '      permission="zope2.View"\n'
            "      />\n"
        )
    _, msg = extend_configure_zcml(
        views_zcml,
        package_name or "package",
        namespaces={"browser": "http://namespaces.zope.org/browser"},
        element_tag="browser:page",
        identifying_attr="name",
        identifying_value=view_name,
        snippet=snippet,
    )
    print(msg)

    # Add include for views subpackage in parent configure.zcml
    parent_zcml = dest / f"src/{package_folder}/configure.zcml"
    if parent_zcml.exists():
        zcml_updater = ParentZCMLUpdater(parent_zcml)
        if not zcml_updater.has_include(".views"):
            zcml_updater.add_include(".views")
            zcml_updater.save()
            print(
                'Added <include package=".views" /> to parent '
                "configure.zcml."
            )


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: copier_hooks.py <command> [args...]")
        sys.exit(1)

    command = sys.argv[1]
    try:
        if command == "validate":
            validate(sys.argv[2])
        elif command == "post_copy":
            post_copy(*sys.argv[2:])
        else:
            print(f"Unknown command: {command}")
            sys.exit(1)
    except CopierTemplateError as e:
        print(f"\nERROR: {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
