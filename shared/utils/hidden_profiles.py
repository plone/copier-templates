"""Hide a product from the add-ons control panel via setuphandlers.HiddenProfiles."""
import re
from pathlib import Path

PRODUCTS_METHOD = '''\
{indent}def getNonInstallableProducts(self):
{indent}    """Hide all upgrade step profiles registered in .upgrades."""
{indent}    return [
{indent}        "{product}",
{indent}    ]

'''

UTILITY = '  <utility factory=".setuphandlers.HiddenProfiles" name="{name}" />\n\n'


def hide_product(setuphandlers: Path, product: str) -> str | None:
    """Add ``product`` to ``HiddenProfiles.getNonInstallableProducts``.

    Returns "added", "present", or None if setuphandlers.py has no HiddenProfiles.
    """
    if not setuphandlers.exists():
        return None
    content = setuphandlers.read_text()
    if re.search(rf"[\"']{re.escape(product)}[\"']", content):
        return "present"

    existing = re.search(
        r"def getNonInstallableProducts\(self\):.*?\n([ \t]*)return \[\n", content, re.DOTALL
    )
    if existing:
        indent = existing.group(1) + "    "
        insert_at = existing.end()
        content = f'{content[:insert_at]}{indent}"{product}",\n{content[insert_at:]}'
    else:
        profiles = re.search(
            r"^([ \t]+)def getNonInstallableProfiles\(self\):", content, re.MULTILINE
        )
        if not profiles:
            return None
        method = PRODUCTS_METHOD.format(indent=profiles.group(1), product=product)
        content = content[: profiles.start()] + method + content[profiles.start() :]

    setuphandlers.write_text(content)
    return "added"


def register_hidden_profiles(configure_zcml: Path, package_name: str) -> bool:
    """Register the HiddenProfiles utility if configure.zcml lacks it.

    Returns True if the file was changed.
    """
    if not configure_zcml.exists():
        return False
    content = configure_zcml.read_text()
    if "HiddenProfiles" in content or "</configure>" not in content:
        return False
    utility = UTILITY.format(name=f"{package_name}-hiddenprofiles")
    head, _, tail = content.rpartition("</configure>")
    configure_zcml.write_text(f"{head}{utility}</configure>{tail}")
    return True
