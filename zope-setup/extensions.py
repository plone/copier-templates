"""Jinja2 extensions for the zope-setup template."""

import sys
import tomllib
from pathlib import Path

from copier_template_extensions import ContextHook

# Ensure shared package is importable
_repo_root = Path(__file__).resolve().parent.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from shared.utils.plone_versions import fetch_plone_versions, get_major_minor_versions


class PloneVersionsHook(ContextHook):
    """Populate Plone version lists from PyPI for use in copier.yml choices."""

    update = True

    def hook(self, context):
        all_versions = fetch_plone_versions()
        context["plone_versions_full"] = all_versions
        context["plone_versions_minor"] = get_major_minor_versions(all_versions)


class AddonContextHook(ContextHook):
    """Read addon settings from pyproject.toml in the destination directory."""

    def hook(self, context):
        dst_path = Path(context.get("_copier_conf", {}).get("dst_path", ""))
        addon_context = self._read_context(dst_path)
        context["addon_context"] = addon_context

    @staticmethod
    def _read_context(dst_path):
        pyproject = dst_path / "pyproject.toml"
        if not pyproject.exists():
            return {}
        try:
            with open(pyproject, "rb") as f:
                doc = tomllib.load(f)
            settings = (
                doc.get("tool", {})
                .get("plone", {})
                .get("backend_addon", {})
                .get("settings", {})
            )
            if settings:
                project = doc.get("project", {})
                result = dict(settings)
                if "package_title" not in result and "name" in project:
                    result["package_title"] = (
                        project["name"].replace("-", " ").replace(".", " ").title()
                    )
                if "package_description" not in result and "description" in project:
                    result["package_description"] = project["description"]
                return result
        except Exception:
            pass
        return {}
