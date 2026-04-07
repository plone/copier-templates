"""Jinja2 extensions for the upgrade_step template."""

import sys
from pathlib import Path

import tomllib
from copier_template_extensions import ContextHook

# Ensure shared package is importable
_repo_root = Path(__file__).resolve().parent.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from shared.utils.xml_updater import MetadataXMLUpdater  # noqa: E402


class AddonContextHook(ContextHook):
    """Auto-fill package info from parent addon and read current profile version."""

    update = True

    def hook(self, context):
        dest = Path(context.get("_copier_conf", {}).get("dst_path", "."))
        if not dest.is_absolute():
            dest = Path.cwd() / dest

        pyproject_path = dest / "pyproject.toml"
        if pyproject_path.exists():
            try:
                with open(pyproject_path, "rb") as f:
                    doc = tomllib.load(f)
                settings = (
                    doc.get("tool", {})
                    .get("plone", {})
                    .get("backend_addon", {})
                    .get("settings", {})
                )
                if settings:
                    if settings.get("package_name"):
                        context["package_name"] = settings["package_name"]
                    if settings.get("package_folder"):
                        context["package_folder"] = settings["package_folder"]

                    # Read current profile version from metadata.xml
                    package_folder = settings.get(
                        "package_folder",
                        settings.get("package_name", "").replace(".", "/"),
                    )
                    if package_folder:
                        metadata_path = (
                            dest
                            / f"src/{package_folder}/profiles/default/metadata.xml"
                        )
                        updater = MetadataXMLUpdater(metadata_path)
                        version = updater.get_version()
                        if version:
                            context["current_profile_version"] = version
            except (tomllib.TOMLDecodeError, OSError):
                pass
