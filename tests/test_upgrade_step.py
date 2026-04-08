"""Tests for upgrade_step subtemplate."""
import pytest
from helpers import assert_file_exists, read_toml, run_copier


class TestUpgradeStepRequiresAddon:
    """Upgrade step subtemplate requires parent addon."""

    def test_fails_without_parent_addon(self, temp_dir, upgrade_step_template):
        """Upgrade step fails if no parent addon detected."""
        result = run_copier(
            upgrade_step_template,
            temp_dir,
            data={"upgrade_step_title": "Add index"},
        )
        assert result.returncode != 0
        error_msg = result.stderr.lower()
        assert (
            "parent addon" in error_msg
            or "no parent addon" in error_msg
            or "package_name" in error_msg
        )

    def test_succeeds_with_parent_addon(
        self, temp_dir, backend_addon_template, upgrade_step_template
    ):
        """Upgrade step succeeds when parent addon exists."""
        run_copier(
            backend_addon_template,
            temp_dir / "mypackage",
            data={"package_name": "collective.mypackage"},
        )

        result = run_copier(
            upgrade_step_template,
            temp_dir / "mypackage",
            data={"upgrade_step_title": "Add catalog index"},
        )
        assert result.returncode == 0, f"Copier failed: {result.stderr}"


class TestUpgradeStepCreation:
    """Test upgrade step file creation."""

    @pytest.fixture
    def addon_dir(self, temp_dir, backend_addon_template):
        """Create a parent addon for testing."""
        pkg_dir = temp_dir / "mypackage"
        run_copier(
            backend_addon_template,
            pkg_dir,
            data={"package_name": "collective.mypackage"},
        )
        return pkg_dir

    def test_creates_handler_module(self, addon_dir, upgrade_step_template):
        """Upgrade step creates versioned handler Python module."""
        run_copier(
            upgrade_step_template,
            addon_dir,
            data={
                "upgrade_step_title": "Add catalog index",
                "source_version": "1000",
                "destination_version": "1001",
            },
        )

        handler = (
            addon_dir
            / "src/collective/mypackage/upgrades/v1001.py"
        )
        assert_file_exists(handler, content_contains="def upgrade")

    def test_creates_per_step_zcml(self, addon_dir, upgrade_step_template):
        """Upgrade step creates per-step ZCML file."""
        run_copier(
            upgrade_step_template,
            addon_dir,
            data={
                "upgrade_step_title": "Add catalog index",
                "source_version": "1000",
                "destination_version": "1001",
            },
        )

        step_zcml = (
            addon_dir
            / "src/collective/mypackage/upgrades/1001.zcml"
        )
        assert_file_exists(step_zcml, content_contains=[
            "genericsetup:upgradeStep",
            'source="1000"',
            'destination="1001"',
            'handler=".v1001.upgrade"',
            'profile="collective.mypackage:default"',
        ])

    def test_creates_per_step_profile_dir(self, addon_dir, upgrade_step_template):
        """Upgrade step creates per-step profile directory with metadata.txt."""
        run_copier(
            upgrade_step_template,
            addon_dir,
            data={
                "upgrade_step_title": "Add catalog index",
                "source_version": "1000",
                "destination_version": "1001",
            },
        )

        metadata = (
            addon_dir
            / "src/collective/mypackage/upgrades/1001/metadata.txt"
        )
        assert metadata.exists()

    def test_creates_upgrades_init(self, addon_dir, upgrade_step_template):
        """Upgrade step creates upgrades __init__.py."""
        run_copier(
            upgrade_step_template,
            addon_dir,
            data={"upgrade_step_title": "Add catalog index"},
        )

        init_file = addon_dir / "src/collective/mypackage/upgrades/__init__.py"
        assert init_file.exists()

    def test_handler_has_logging(self, addon_dir, upgrade_step_template):
        """Handler module includes logging setup."""
        run_copier(
            upgrade_step_template,
            addon_dir,
            data={
                "upgrade_step_title": "Add catalog index",
                "source_version": "1000",
                "destination_version": "1001",
            },
        )

        handler = (
            addon_dir
            / "src/collective/mypackage/upgrades/v1001.py"
        )
        assert_file_exists(handler, content_contains=[
            "import logging",
            "logger = logging.getLogger",
        ])

    def test_handler_has_version_info(self, addon_dir, upgrade_step_template):
        """Handler docstring includes version info."""
        run_copier(
            upgrade_step_template,
            addon_dir,
            data={
                "upgrade_step_title": "Add catalog index",
                "source_version": "1000",
                "destination_version": "1001",
            },
        )

        handler = (
            addon_dir
            / "src/collective/mypackage/upgrades/v1001.py"
        )
        assert_file_exists(handler, content_contains="1000")


class TestUpgradeStepIntegration:
    """Test upgrade step registers in parent addon."""

    @pytest.fixture
    def addon_dir(self, temp_dir, backend_addon_template):
        """Create a parent addon for testing."""
        pkg_dir = temp_dir / "pkg"
        run_copier(
            backend_addon_template,
            pkg_dir,
            data={"package_name": "my.pkg"},
        )
        return pkg_dir

    def test_updates_addon_settings(self, addon_dir, upgrade_step_template):
        """Upgrade step registered in addon settings."""
        run_copier(
            upgrade_step_template,
            addon_dir,
            data={"upgrade_step_title": "Add catalog index"},
        )

        pyproject = addon_dir / "pyproject.toml"
        data = read_toml(pyproject)
        subtemplates = data["tool"]["plone"]["backend_addon"]["settings"][
            "subtemplates"
        ]
        assert "Add catalog index" in subtemplates["upgrade_steps"]

    def test_adds_parent_zcml_include(self, addon_dir, upgrade_step_template):
        """Upgrade step adds include to parent configure.zcml."""
        run_copier(
            upgrade_step_template,
            addon_dir,
            data={"upgrade_step_title": "Add catalog index"},
        )

        parent_zcml = addon_dir / "src/my/pkg/configure.zcml"
        assert_file_exists(
            parent_zcml, content_contains='<include package=".upgrades" />'
        )

    def test_bumps_metadata_version(self, addon_dir, upgrade_step_template):
        """Upgrade step bumps metadata.xml profile version."""
        run_copier(
            upgrade_step_template,
            addon_dir,
            data={
                "upgrade_step_title": "Add catalog index",
                "source_version": "1000",
                "destination_version": "1001",
            },
        )

        metadata = addon_dir / "src/my/pkg/profiles/default/metadata.xml"
        assert_file_exists(metadata, content_contains="<version>1001</version>")

    def test_creates_upgrade_configure_zcml(self, addon_dir, upgrade_step_template):
        """Upgrade step creates upgrades/configure.zcml with file include."""
        run_copier(
            upgrade_step_template,
            addon_dir,
            data={
                "upgrade_step_title": "Add catalog index",
                "source_version": "1000",
                "destination_version": "1001",
            },
        )

        zcml = addon_dir / "src/my/pkg/upgrades/configure.zcml"
        assert_file_exists(zcml, content_contains=[
            '<include file="1001.zcml" />',
        ])

    def test_creates_per_step_zcml_with_registration(
        self, addon_dir, upgrade_step_template
    ):
        """Per-step ZCML contains the upgradeStep registration."""
        run_copier(
            upgrade_step_template,
            addon_dir,
            data={
                "upgrade_step_title": "Add catalog index",
                "source_version": "1000",
                "destination_version": "1001",
            },
        )

        step_zcml = addon_dir / "src/my/pkg/upgrades/1001.zcml"
        assert_file_exists(step_zcml, content_contains=[
            "genericsetup:upgradeStep",
            'source="1000"',
            'destination="1001"',
            'handler=".v1001.upgrade"',
            'profile="my.pkg:default"',
        ])


class TestMultipleUpgradeSteps:
    """Test adding multiple upgrade steps."""

    @pytest.fixture
    def addon_dir(self, temp_dir, backend_addon_template):
        """Create a parent addon for testing."""
        pkg_dir = temp_dir / "pkg"
        run_copier(
            backend_addon_template,
            pkg_dir,
            data={"package_name": "my.pkg"},
        )
        return pkg_dir

    def test_second_step_adds_include_to_zcml(
        self, addon_dir, upgrade_step_template
    ):
        """Second upgrade step adds its include to configure.zcml."""
        # First upgrade step
        run_copier(
            upgrade_step_template,
            addon_dir,
            data={
                "upgrade_step_title": "Add catalog index",
                "source_version": "1000",
                "destination_version": "1001",
            },
        )

        # Second upgrade step
        run_copier(
            upgrade_step_template,
            addon_dir,
            data={
                "upgrade_step_title": "Migrate content",
                "source_version": "1001",
                "destination_version": "1002",
            },
        )

        zcml = addon_dir / "src/my/pkg/upgrades/configure.zcml"
        assert_file_exists(zcml, content_contains=[
            '<include file="1001.zcml" />',
            '<include file="1002.zcml" />',
        ])

    def test_second_step_creates_separate_files(
        self, addon_dir, upgrade_step_template
    ):
        """Each upgrade step gets its own handler, zcml, and profile dir."""
        run_copier(
            upgrade_step_template,
            addon_dir,
            data={
                "upgrade_step_title": "Add catalog index",
                "source_version": "1000",
                "destination_version": "1001",
            },
        )
        run_copier(
            upgrade_step_template,
            addon_dir,
            data={
                "upgrade_step_title": "Migrate content",
                "source_version": "1001",
                "destination_version": "1002",
            },
        )

        handler1 = addon_dir / "src/my/pkg/upgrades/v1001.py"
        handler2 = addon_dir / "src/my/pkg/upgrades/v1002.py"
        assert_file_exists(handler1, content_contains="def upgrade")
        assert_file_exists(handler2, content_contains="def upgrade")

        step_zcml1 = addon_dir / "src/my/pkg/upgrades/1001.zcml"
        step_zcml2 = addon_dir / "src/my/pkg/upgrades/1002.zcml"
        assert_file_exists(step_zcml1, content_contains='destination="1001"')
        assert_file_exists(step_zcml2, content_contains='destination="1002"')

        assert (addon_dir / "src/my/pkg/upgrades/1001/metadata.txt").exists()
        assert (addon_dir / "src/my/pkg/upgrades/1002/metadata.txt").exists()

    def test_metadata_version_is_latest(self, addon_dir, upgrade_step_template):
        """After multiple steps, metadata.xml has the latest version."""
        run_copier(
            upgrade_step_template,
            addon_dir,
            data={
                "upgrade_step_title": "Add catalog index",
                "source_version": "1000",
                "destination_version": "1001",
            },
        )
        run_copier(
            upgrade_step_template,
            addon_dir,
            data={
                "upgrade_step_title": "Migrate content",
                "source_version": "1001",
                "destination_version": "1002",
            },
        )

        metadata = addon_dir / "src/my/pkg/profiles/default/metadata.xml"
        assert_file_exists(metadata, content_contains="<version>1002</version>")
