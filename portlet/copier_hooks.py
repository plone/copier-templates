#!/usr/bin/env python3
"""Tasks for the portlet subtemplate."""
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
    portlet_name: str,
    portlet_module: str = "",
) -> None:
    dest = _resolve_dest(dest_path)
    pyproject_path = dest / "pyproject.toml"
    if not pyproject_path.exists():
        print(f"Warning: pyproject.toml not found at {pyproject_path}")
        return

    updater = PyprojectUpdater(pyproject_path)
    updater.register_subtemplate("portlets", portlet_name)
    updater.save()
    print(f"Registered portlet '{portlet_name}' in addon settings.")

    addon_settings = updater.get_addon_settings()
    package_name = addon_settings.get("package_name", "")
    package_folder = addon_settings.get("package_folder", "")
    if not package_folder and package_name:
        package_folder = package_name.replace(".", "/")

    if not package_folder:
        return

    registration_name = f"{package_name}.{portlet_name}"
    snippet = (
        "  <plone:portlet\n"
        f'      name="{registration_name}"\n'
        f'      interface=".{portlet_module}.I{portlet_name}Portlet"\n'
        f'      assignment=".{portlet_module}.Assignment"\n'
        '      view_permission="zope2.View"\n'
        '      edit_permission="cmf.ManagePortal"\n'
        f'      renderer=".{portlet_module}.Renderer"\n'
        f'      addview=".{portlet_module}.AddForm"\n'
        f'      editview=".{portlet_module}.EditForm"\n'
        "      />\n"
    )
    portlets_zcml = dest / f"src/{package_folder}/portlets/configure.zcml"
    _, msg = extend_configure_zcml(
        portlets_zcml,
        package_name or "package",
        namespaces={"plone": "http://namespaces.plone.org/plone"},
        element_tag="plone:portlet",
        identifying_attr="name",
        identifying_value=registration_name,
        snippet=snippet,
    )
    print(msg)

    parent_zcml = dest / f"src/{package_folder}/configure.zcml"
    if parent_zcml.exists():
        zcml_updater = ParentZCMLUpdater(parent_zcml)
        if not zcml_updater.has_include(".portlets"):
            zcml_updater.add_include(".portlets")
            zcml_updater.save()
            print(
                'Added <include package=".portlets" /> to parent '
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
