#!/usr/bin/env python3
"""Utilities for updating XML configuration files."""
import re
import xml.etree.ElementTree as ET
from pathlib import Path


class ConfigureZCMLUpdater:
    """Updates content/configure.zcml with plone:behavior entries."""

    TEMPLATE = '''\
<configure
    xmlns="http://namespaces.zope.org/zope"
    xmlns:plone="http://namespaces.plone.org/plone"
    i18n_domain="{package_name}">

</configure>
'''

    BEHAVIOR_TEMPLATE = '''\
  <plone:behavior
      title="{title}"
      description="{description}"
      provides="{provides}"
      />
'''

    def __init__(self, path: Path | str):
        """
        Initialize the updater.

        Args:
            path: Path to configure.zcml file
        """
        self.path = Path(path)
        self._content = None
        self._modified = False

    def load(self) -> str:
        """Load the configure.zcml file content."""
        if self._content is None:
            if self.path.exists():
                self._content = self.path.read_text()
            else:
                self._content = ""
        return self._content

    def create_if_missing(self, package_name: str) -> None:
        """
        Create the file with initial structure if it doesn't exist.

        Args:
            package_name: The package name for i18n_domain
        """
        if not self.path.exists():
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self._content = self.TEMPLATE.format(package_name=package_name)
            self._modified = True

    def has_behavior(self, provides: str) -> bool:
        """
        Check if a behavior with the given provides attribute exists.

        Args:
            provides: The provides attribute to check for

        Returns:
            True if behavior exists, False otherwise
        """
        content = self.load()
        # Escape dots for regex
        escaped_provides = re.escape(provides)
        pattern = rf'provides\s*=\s*["\']\.?{escaped_provides}["\']'
        return bool(re.search(pattern, content))

    def add_behavior(self, title: str, description: str, provides: str) -> None:
        """
        Add a behavior entry if it doesn't exist.

        Args:
            title: Behavior title (interface name)
            description: Behavior description
            provides: Interface path (e.g., ".article.IArticle")
        """
        if self.has_behavior(provides):
            return

        content = self.load()
        if not content:
            return

        behavior_entry = self.BEHAVIOR_TEMPLATE.format(
            title=title,
            description=description,
            provides=provides,
        )

        # Insert before closing </configure> tag
        closing_tag = "</configure>"
        if closing_tag in content:
            self._content = content.replace(
                closing_tag,
                f"{behavior_entry}\n{closing_tag}"
            )
            self._modified = True

    def save(self) -> None:
        """Save changes to the file."""
        if self._modified and self._content is not None:
            self.path.write_text(self._content)


class ZCMLConfigureExtender:
    """Generic extender for ``<configure>``-based ZCML files.

    This is the canonical way for subtemplates to *extend* (never
    overwrite) an existing ``configure.zcml`` file. It will:

    * create the file with a minimal ``<configure>`` root if it doesn't
      exist (declaring any required xmlns prefixes);
    * ensure additional xmlns prefixes are declared on an existing root;
    * check whether an element already exists (by tag + identifying
      attribute) so re-runs are idempotent;
    * append a raw ZCML element snippet before the closing
      ``</configure>`` tag, preserving all existing entries.
    """

    ZOPE_NS = "http://namespaces.zope.org/zope"

    def __init__(self, path: Path | str):
        self.path = Path(path)
        self._content: str | None = None
        self._modified = False

    def load(self) -> str:
        if self._content is None:
            self._content = self.path.read_text() if self.path.exists() else ""
        return self._content

    def create_if_missing(
        self,
        package_name: str,
        namespaces: dict[str, str] | None = None,
    ) -> None:
        if self.path.exists():
            return
        ns: dict[str, str] = {"": self.ZOPE_NS}
        if namespaces:
            ns.update(namespaces)
        lines = ["<configure"]
        for prefix, uri in ns.items():
            attr = f'xmlns:{prefix}="{uri}"' if prefix else f'xmlns="{uri}"'
            lines.append(f"    {attr}")
        lines[-1] = lines[-1] + f'\n    i18n_domain="{package_name}">'
        header = "\n".join(lines)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._content = f"{header}\n\n</configure>\n"
        self._modified = True

    def ensure_namespaces(self, namespaces: dict[str, str]) -> None:
        content = self.load()
        if not content:
            return
        match = re.search(r"<configure\b[^>]*>", content, re.DOTALL)
        if not match:
            return
        opening = match.group(0)
        new_opening = opening
        for prefix, uri in namespaces.items():
            attr = f'xmlns:{prefix}="{uri}"' if prefix else f'xmlns="{uri}"'
            if attr in new_opening:
                continue
            # Insert the new attribute just before the closing '>'
            new_opening = new_opening[:-1].rstrip() + f"\n    {attr}" + ">"
        if new_opening != opening:
            self._content = content.replace(opening, new_opening, 1)
            self._modified = True

    def has_element(self, tag: str, attr: str, value: str) -> bool:
        """Return True if a ``<tag>`` with ``attr="value"`` already exists."""
        content = self.load()
        if not content:
            return False
        pattern = (
            rf'<{re.escape(tag)}\b[^>]*\b{re.escape(attr)}\s*=\s*'
            rf'["\']{re.escape(value)}["\']'
        )
        return bool(re.search(pattern, content, re.DOTALL))

    def append_element(self, snippet: str) -> None:
        """Append a raw ZCML element snippet before ``</configure>``."""
        content = self.load()
        if not content:
            return
        snippet = snippet.rstrip() + "\n"
        closing = "</configure>"
        if closing not in content:
            return
        self._content = content.replace(closing, f"{snippet}\n{closing}", 1)
        self._modified = True

    def save(self) -> None:
        if self._modified and self._content is not None:
            self.path.write_text(self._content)


def extend_configure_zcml(
    zcml_path: Path | str,
    package_name: str,
    namespaces: dict[str, str],
    element_tag: str,
    identifying_attr: str,
    identifying_value: str,
    snippet: str,
) -> tuple[bool, str]:
    """Create-if-missing and idempotently append a ZCML element.

    Returns ``(changed, message)`` — ``changed`` is True if anything
    was written; ``message`` is a human-readable status string.
    """
    ext = ZCMLConfigureExtender(zcml_path)
    ext.create_if_missing(package_name, namespaces=namespaces)
    ext.ensure_namespaces(namespaces)
    if ext.has_element(element_tag, identifying_attr, identifying_value):
        return False, (
            f"{element_tag} with {identifying_attr}='{identifying_value}' "
            f"already exists in {zcml_path}."
        )
    ext.append_element(snippet)
    ext.save()
    return True, f"Extended {zcml_path} with {element_tag} '{identifying_value}'."


class ParentZCMLUpdater:
    """Updates parent addon configure.zcml with include directives for subpackages."""

    INCLUDE_TEMPLATE = '  <include package="{subpackage}" />\n'

    def __init__(self, path: Path | str):
        self.path = Path(path)
        self._content = None
        self._modified = False

    def load(self) -> str:
        if self._content is None:
            if self.path.exists():
                self._content = self.path.read_text()
            else:
                self._content = ""
        return self._content

    def has_include(self, subpackage: str) -> bool:
        content = self.load()
        escaped = re.escape(subpackage)
        pattern = rf'<include\s+package\s*=\s*["\']\.?{escaped}["\']'
        return bool(re.search(pattern, content))

    def add_include(self, subpackage: str) -> None:
        if self.has_include(subpackage):
            return
        content = self.load()
        if not content:
            return
        include_entry = self.INCLUDE_TEMPLATE.format(subpackage=subpackage)
        closing_tag = "</configure>"
        if closing_tag in content:
            self._content = content.replace(
                closing_tag,
                f"\n{include_entry}\n{closing_tag}"
            )
            self._modified = True

    def save(self) -> None:
        if self._modified and self._content is not None:
            self.path.write_text(self._content)


class TypesXMLUpdater:
    """Updates profiles/default/types.xml with FTI references."""

    TEMPLATE = '''\
<?xml version="1.0" encoding="UTF-8"?>
<object name="portal_types">
</object>
'''

    FTI_TEMPLATE = '  <object name="{content_type_class}" meta_type="Dexterity FTI"/>\n'

    def __init__(self, path: Path | str):
        """
        Initialize the updater.

        Args:
            path: Path to types.xml file
        """
        self.path = Path(path)
        self._content = None
        self._modified = False

    def load(self) -> str:
        """Load the types.xml file content."""
        if self._content is None:
            if self.path.exists():
                self._content = self.path.read_text()
            else:
                self._content = ""
        return self._content

    def create_if_missing(self) -> None:
        """Create the file with initial structure if it doesn't exist."""
        if not self.path.exists():
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self._content = self.TEMPLATE
            self._modified = True

    def has_fti_reference(self, content_type_class: str) -> bool:
        """
        Check if an FTI reference for the content type exists.

        Args:
            content_type_class: The content type class name

        Returns:
            True if FTI reference exists, False otherwise
        """
        content = self.load()
        escaped_name = re.escape(content_type_class)
        pattern = rf'<object\s+name\s*=\s*["\']\.?{escaped_name}["\']'
        return bool(re.search(pattern, content))

    def add_fti_reference(self, content_type_class: str) -> None:
        """
        Add an FTI reference if it doesn't exist.

        Args:
            content_type_class: The content type class name
        """
        if self.has_fti_reference(content_type_class):
            return

        content = self.load()
        if not content:
            return

        fti_entry = self.FTI_TEMPLATE.format(content_type_class=content_type_class)

        # Insert before closing </object> tag
        closing_tag = "</object>"
        if closing_tag in content:
            self._content = content.replace(
                closing_tag,
                f"{fti_entry}{closing_tag}"
            )
            self._modified = True

    def save(self) -> None:
        """Save changes to the file."""
        if self._modified and self._content is not None:
            self.path.write_text(self._content)


class ParentFTIUpdater:
    """Updates a parent type FTI XML to allow a new child portal type.

    Inserts ``<element value="ChildType" />`` inside the parent's
    ``allowed_content_types`` property. If the property is missing or
    self-closing, it is expanded to an opening/closing form.
    """

    def __init__(self, path: Path | str):
        self.path = Path(path)
        self._content: str | None = None
        self._modified = False

    def exists(self) -> bool:
        return self.path.exists()

    def load(self) -> str:
        if self._content is None:
            self._content = self.path.read_text() if self.path.exists() else ""
        return self._content

    def has_allowed_child(self, child_type: str) -> bool:
        content = self.load()
        escaped = re.escape(child_type)
        pattern = (
            r'<property\s+name\s*=\s*"allowed_content_types"[^>]*>'
            r'[\s\S]*?<element\s+value\s*=\s*"' + escaped + r'"\s*/>'
            r'[\s\S]*?</property>'
        )
        return bool(re.search(pattern, content))

    def add_allowed_child(self, child_type: str) -> bool:
        """Add ``child_type`` to ``allowed_content_types``. Return True on change."""
        if not self.path.exists():
            return False
        content = self.load()
        if self.has_allowed_child(child_type):
            return False

        element = f'    <element value="{child_type}"/>'

        # Case 1: self-closing <property name="allowed_content_types"/>
        self_closing = re.compile(
            r'(\s*)<property\s+name\s*=\s*"allowed_content_types"\s*/>'
        )
        match = self_closing.search(content)
        if match:
            indent = match.group(1).lstrip("\n")
            replacement = (
                f'{match.group(1)}<property name="allowed_content_types">\n'
                f'{indent}{element}\n'
                f'{indent}</property>'
            )
            self._content = content[: match.start()] + replacement + content[match.end():]
            self._modified = True
            return True

        # Case 2: existing open/close <property name="allowed_content_types">...</property>
        open_close = re.compile(
            r'(<property\s+name\s*=\s*"allowed_content_types"[^>]*>)'
            r'([\s\S]*?)(</property>)'
        )
        match = open_close.search(content)
        if match:
            inner = match.group(2)
            if inner.strip():
                new_inner = inner.rstrip() + f"\n{element}\n  "
            else:
                new_inner = f"\n{element}\n  "
            self._content = (
                content[: match.start()]
                + match.group(1)
                + new_inner
                + match.group(3)
                + content[match.end():]
            )
            self._modified = True
            return True

        return False

    def save(self) -> None:
        if self._modified and self._content is not None:
            self.path.write_text(self._content)


class MetadataXMLUpdater:
    """Reads and updates profiles/default/metadata.xml version."""

    def __init__(self, path: Path | str):
        self.path = Path(path)

    def get_version(self) -> str | None:
        """Return the current profile version string, or None if not found."""
        if not self.path.exists():
            return None
        try:
            tree = ET.parse(self.path)
            version_el = tree.find("version")
            if version_el is not None and version_el.text:
                return version_el.text.strip()
        except ET.ParseError:
            pass
        return None

    def set_version(self, new_version: str) -> None:
        """Update the profile version in metadata.xml."""
        if not self.path.exists():
            return
        content = self.path.read_text()
        updated = re.sub(
            r"(<version>)\s*\S+\s*(</version>)",
            rf"\g<1>{new_version}\g<2>",
            content,
        )
        if updated != content:
            self.path.write_text(updated)


class UpgradeZCMLUpdater:
    """Manages file includes in upgrades/configure.zcml."""

    TEMPLATE = '''\
<configure
    xmlns="http://namespaces.zope.org/zope"
    xmlns:genericsetup="http://namespaces.zope.org/genericsetup"
    i18n_domain="{package_name}">

</configure>
'''

    INCLUDE_TEMPLATE = '  <include file="{filename}" />\n'

    def __init__(self, path: Path | str):
        self.path = Path(path)
        self._content = None
        self._modified = False

    def load(self) -> str:
        if self._content is None:
            if self.path.exists():
                self._content = self.path.read_text()
            else:
                self._content = ""
        return self._content

    def create_if_missing(self, package_name: str) -> None:
        """Create the file with initial structure if it doesn't exist."""
        if not self.path.exists():
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self._content = self.TEMPLATE.format(package_name=package_name)
            self._modified = True

    def has_file_include(self, filename: str) -> bool:
        """Check if an include for the given filename already exists."""
        content = self.load()
        escaped = re.escape(filename)
        pattern = rf'<include\s+file\s*=\s*["\']\.?{escaped}["\']'
        return bool(re.search(pattern, content))

    def add_file_include(self, filename: str) -> None:
        """Add an <include file="..." /> entry before the closing </configure> tag."""
        if self.has_file_include(filename):
            return

        content = self.load()
        if not content:
            return

        include_entry = self.INCLUDE_TEMPLATE.format(filename=filename)

        closing_tag = "</configure>"
        if closing_tag in content:
            self._content = content.replace(
                closing_tag,
                f"{include_entry}\n{closing_tag}",
            )
            self._modified = True

    def save(self) -> None:
        if self._modified and self._content is not None:
            self.path.write_text(self._content)
