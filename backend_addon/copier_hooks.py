#!/usr/bin/env python3
"""Post-copy tasks for backend_addon template."""
import sys
from pathlib import Path

# Add shared module to path
sys.path.insert(0, str(Path(__file__).parent.parent / "shared"))

from hooks.legacy_cleanup import cleanup_legacy_files, migrate_pyproject_settings


def post_copy(dest_path: str) -> None:
    """
    Post-copy tasks:
    1. Migrate old pyproject.toml settings (setuptools -> hatchling)
    2. Rename legacy files (bobtemplate.cfg, setup.py, setup.cfg)
    """
    cwd = Path.cwd()
    dest = Path(dest_path)

    if (cwd / "pyproject.toml").exists():
        dest = cwd
    elif not dest.is_absolute():
        dest = dest.resolve()

    # Check if this is a legacy package migration
    has_legacy = any(
        (dest / f).exists()
        for f in ["bobtemplate.cfg", "setup.py", "setup.cfg"]
    )

    if not has_legacy:
        return

    print("\nDetected legacy package files. Running migration...")

    # Migrate pyproject.toml settings first (before cleanup)
    migrate_pyproject_settings(dest)

    # Rename legacy files
    cleanup_legacy_files(dest)

    print("\nMigration complete. Old files have been renamed to .bak")
    print("Please review the changes and remove .bak files when satisfied.\n")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: copier_hooks.py <command> [args...]")
        print("Commands: post_copy")
        sys.exit(1)

    command = sys.argv[1]

    if command == "post_copy":
        if len(sys.argv) < 3:
            print("Usage: copier_hooks.py post_copy <dest_path>")
            sys.exit(1)
        post_copy(sys.argv[2])
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
