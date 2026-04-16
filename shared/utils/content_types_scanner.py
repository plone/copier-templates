#!/usr/bin/env python3
"""Scan an addon package for Dexterity content type interfaces.

Used by subtemplates (e.g. ``view``) to offer a choice list of interfaces
the new artifact can be registered for.
"""
from __future__ import annotations

import ast
import xml.etree.ElementTree as ET
from pathlib import Path

# Default Plone portal types that ship with plone.app.contenttypes.
DEFAULT_PORTAL_TYPES: list[str] = [
    "Document",
    "File",
    "Image",
    "News Item",
    "Event",
    "Link",
    "Folder",
    "Collection",
]

# Default Plone content type interfaces that are always available
# regardless of what the current package provides.
DEFAULT_CONTENT_TYPE_INTERFACES: list[str] = [
    "*",
    "plone.dexterity.interfaces.IDexterityContent",
    "plone.dexterity.interfaces.IDexterityContainer",
    "plone.dexterity.interfaces.IDexterityItem",
    "plone.app.contenttypes.interfaces.IDocument",
    "plone.app.contenttypes.interfaces.IFile",
    "plone.app.contenttypes.interfaces.IImage",
    "plone.app.contenttypes.interfaces.INewsItem",
    "plone.app.contenttypes.interfaces.IEvent",
    "plone.app.contenttypes.interfaces.ILink",
    "plone.app.contenttypes.interfaces.IFolder",
    "plone.app.contenttypes.interfaces.ICollection",
    "Products.CMFCore.interfaces.IContentish",
    "Products.CMFCore.interfaces.IFolderish",
    "Products.CMFPlone.interfaces.IPloneSiteRoot",
]


def _package_folder_from_pyproject(dest: Path) -> str | None:
    """Read ``package_folder`` from the addon's pyproject.toml settings."""
    pyproject = dest / "pyproject.toml"
    if not pyproject.exists():
        return None
    try:
        import tomllib
    except ModuleNotFoundError:  # pragma: no cover - py<3.11 fallback
        import tomli as tomllib  # type: ignore
    try:
        with open(pyproject, "rb") as f:
            doc = tomllib.load(f)
    except (OSError, tomllib.TOMLDecodeError):
        return None
    settings = (
        doc.get("tool", {})
        .get("plone", {})
        .get("backend_addon", {})
        .get("settings", {})
    )
    folder = settings.get("package_folder")
    if folder:
        return folder
    name = settings.get("package_name")
    if name:
        return name.replace(".", "/")
    return None


def _extract_schema_interfaces(py_file: Path) -> list[tuple[str, str]]:
    """Return ``(module, class_name)`` pairs for schema interfaces in ``py_file``.

    A "schema interface" is a class whose base contains ``model.Schema`` or
    ``Interface`` — the convention used by Dexterity content types.
    """
    try:
        source = py_file.read_text(encoding="utf-8")
    except OSError:
        return []
    try:
        tree = ast.parse(source, filename=str(py_file))
    except SyntaxError:
        return []

    results: list[tuple[str, str]] = []
    module_stem = py_file.stem
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        is_schema = False
        for base in node.bases:
            base_repr = ast.unparse(base) if hasattr(ast, "unparse") else ""
            if base_repr.endswith("model.Schema") or base_repr == "Interface":
                is_schema = True
                break
        if is_schema and node.name.startswith("I"):
            results.append((module_stem, node.name))
    return results


def scan_package_content_types(
    dest: Path, package_folder: str | None = None
) -> list[str]:
    """Return dotted interface names for content types in the current package.

    Scans ``src/{package_folder}/content/*.py`` for Dexterity schema
    interfaces and returns their fully qualified dotted names, derived from
    the package name + content submodule + interface class name.
    """
    dest = Path(dest)
    if package_folder is None:
        package_folder = _package_folder_from_pyproject(dest)
    if not package_folder:
        return []

    content_dir = dest / "src" / package_folder / "content"
    if not content_dir.is_dir():
        return []

    package_dotted = package_folder.replace("/", ".")
    found: list[str] = []
    for py_file in sorted(content_dir.glob("*.py")):
        if py_file.name == "__init__.py":
            continue
        for module_stem, iface in _extract_schema_interfaces(py_file):
            found.append(f"{package_dotted}.content.{module_stem}.{iface}")
    return found


def all_content_type_interfaces(
    dest: Path, package_folder: str | None = None
) -> list[str]:
    """Default Plone interfaces + interfaces discovered in the current package."""
    found = scan_package_content_types(dest, package_folder)
    # Preserve order, avoid duplicates
    combined: list[str] = []
    seen: set[str] = set()
    for item in list(DEFAULT_CONTENT_TYPE_INTERFACES) + found:
        if item not in seen:
            seen.add(item)
            combined.append(item)
    return combined


def scan_package_portal_types(
    dest: Path, package_folder: str | None = None
) -> list[str]:
    """Return portal type names registered in the current package.

    Reads the ``name`` attribute of the root object in every
    ``src/{package_folder}/profiles/default/types/*.xml`` FTI file.
    """
    dest = Path(dest)
    if package_folder is None:
        package_folder = _package_folder_from_pyproject(dest)
    if not package_folder:
        return []

    types_dir = dest / "src" / package_folder / "profiles" / "default" / "types"
    if not types_dir.is_dir():
        return []

    found: list[str] = []
    for xml_file in sorted(types_dir.glob("*.xml")):
        try:
            root = ET.parse(xml_file).getroot()
        except ET.ParseError:
            continue
        name = root.get("name")
        if name:
            found.append(name)
    return found


def all_portal_types(
    dest: Path, package_folder: str | None = None
) -> list[str]:
    """Default Plone portal types + portal types discovered in the current package."""
    found = scan_package_portal_types(dest, package_folder)
    combined: list[str] = []
    seen: set[str] = set()
    for item in list(DEFAULT_PORTAL_TYPES) + found:
        if item not in seen:
            seen.add(item)
            combined.append(item)
    return combined


def main() -> None:
    """CLI entry point: print discovered interfaces, one per line."""
    import sys

    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    for iface in all_content_type_interfaces(dest):
        print(iface)


if __name__ == "__main__":
    main()
