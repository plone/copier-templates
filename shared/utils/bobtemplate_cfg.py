#!/usr/bin/env python3
"""Read/write helpers for legacy bobtemplate.cfg files.

bobtemplates.plone packages store package metadata in bobtemplate.cfg
under a [variables] section. We add a [subtemplates] section to track
which subtemplates have been applied, mirroring what
[tool.plone.backend_addon.settings.subtemplates] does in pyproject.toml
for modern packages.
"""
import configparser
from pathlib import Path

SUBTEMPLATES_SECTION = "subtemplates"


def register_subtemplate(
    cfg_path: Path, subtemplate_type: str, name: str
) -> bool:
    """Add ``name`` to the [subtemplates] section under ``subtemplate_type``.

    Values are stored as a comma-separated list (configparser does not
    support multi-key sections).

    Returns:
        True if the entry was newly added, False if it already existed.
    """
    config = configparser.ConfigParser()
    if cfg_path.exists():
        config.read(cfg_path)

    if not config.has_section(SUBTEMPLATES_SECTION):
        config.add_section(SUBTEMPLATES_SECTION)

    existing = config.get(
        SUBTEMPLATES_SECTION, subtemplate_type, fallback=""
    )
    items = [s.strip() for s in existing.split(",") if s.strip()]
    if name in items:
        return False

    items.append(name)
    config.set(SUBTEMPLATES_SECTION, subtemplate_type, ", ".join(items))

    with open(cfg_path, "w") as f:
        config.write(f)
    return True


def get_subtemplates(cfg_path: Path, subtemplate_type: str) -> list[str]:
    """Return the list of registered names for ``subtemplate_type``."""
    if not cfg_path.exists():
        return []
    config = configparser.ConfigParser()
    config.read(cfg_path)
    raw = config.get(
        SUBTEMPLATES_SECTION, subtemplate_type, fallback=""
    )
    return [s.strip() for s in raw.split(",") if s.strip()]
