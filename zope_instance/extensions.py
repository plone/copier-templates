"""Jinja2 extension to read project context from pyproject.toml."""

from pathlib import Path

import tomllib
from copier_template_extensions import ContextHook


class ProjectContextHook(ContextHook):
    """Read project settings from pyproject.toml in the destination directory."""

    def hook(self, context):
        dst_path = Path(context.get("_copier_conf", {}).get("dst_path", ""))
        project_context = self._read_context(dst_path)
        context["project_context"] = project_context

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
                .get("project", {})
                .get("settings", {})
            )
            if settings:
                result = dict(settings)
                project = doc.get("project", {})
                if "project_name" not in result and "name" in project:
                    result["project_name"] = project["name"]
                return result
        except Exception:
            pass
        return {}
