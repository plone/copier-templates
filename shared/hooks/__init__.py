"""Shared hooks for copier-templates."""
import sys
from pathlib import Path

# Ensure the shared directory is importable for bare imports used by submodules
_shared_dir = str(Path(__file__).resolve().parent.parent)
if _shared_dir not in sys.path:
    sys.path.insert(0, _shared_dir)

from exceptions import AddonContextError, CopierTemplateError, ValidationError

from .addon_context import find_addon_context, require_addon_context
from .git_check import check_git_status, require_clean_git, warn_git_unclean

__all__ = [
    "find_addon_context",
    "require_addon_context",
    "check_git_status",
    "require_clean_git",
    "warn_git_unclean",
    "AddonContextError",
    "CopierTemplateError",
    "ValidationError",
]
