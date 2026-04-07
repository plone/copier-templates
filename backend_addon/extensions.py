"""Jinja2 extensions for the backend_addon template."""

import sys
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
