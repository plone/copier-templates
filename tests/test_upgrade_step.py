"""Tests for upgrade_step subtemplate."""
import shutil
import subprocess
import textwrap

import pytest
from helpers import assert_file_exists, plone_subprocess_env, run_copier

PKG = "src/my/pkg"


def add_step(addon_dir, template, overwrite=False, **data):
    """Run upgrade_step the way plonecli does: --defaults, no --overwrite."""
    answers = {"upgrade_step_title": "Add catalog index"}
    answers.update(data)
    return run_copier(template, addon_dir, data=answers, overwrite=overwrite)


@pytest.fixture
def addon_dir(temp_dir, backend_addon_template):
    pkg_dir = temp_dir / "pkg"
    result = run_copier(backend_addon_template, pkg_dir, data={"package_name": "my.pkg"})
    assert result.returncode == 0, result.stderr
    return pkg_dir


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

    def test_succeeds_with_parent_addon(self, addon_dir, upgrade_step_template):
        result = add_step(addon_dir, upgrade_step_template)
        assert result.returncode == 0, f"Copier failed: {result.stderr}"


class TestPythonOnlyStep:
    """Without import steps the step is a plain Python handler."""

    @pytest.fixture(autouse=True)
    def _run(self, addon_dir, upgrade_step_template):
        result = add_step(addon_dir, upgrade_step_template)
        assert result.returncode == 0, result.stderr
        self.upgrades = addon_dir / PKG / "upgrades"
        self.addon_dir = addon_dir

    def test_handler_has_todo_and_no_import(self):
        handler = (self.upgrades / "v1001.py").read_text()
        assert "def upgrade(context)" in handler
        assert "TODO" in handler
        assert "runImportStepFromProfile" not in handler
        assert "loadMigrationProfile" not in handler

    def test_no_profile_dir(self):
        assert not (self.upgrades / "1001").exists()

    def test_zcml_registers_step_only(self):
        zcml = (self.upgrades / "1001.zcml").read_text()
        for expected in (
            "genericsetup:upgradeStep",
            'source="1000"',
            'destination="1001"',
            'handler=".v1001.upgrade"',
            'profile="my.pkg:default"',
        ):
            assert expected in zcml
        assert "registerProfile" not in zcml
        assert "upgradeDepends" not in zcml

    def test_no_shared_base_module(self):
        assert not (self.upgrades / "base.py").exists()
        assert (self.upgrades / "__init__.py").exists()

    def test_wires_zcml_and_bumps_metadata(self):
        assert_file_exists(
            self.upgrades / "configure.zcml",
            content_contains='<include file="1001.zcml" />',
        )
        assert_file_exists(
            self.addon_dir / PKG / "configure.zcml",
            content_contains='<include package=".upgrades" />',
        )
        assert_file_exists(
            self.addon_dir / PKG / "profiles/default/metadata.xml",
            content_contains="<version>1001</version>",
        )


class TestStepWithImportSteps:
    """Chosen import steps run from the step's own profile, once."""

    @pytest.fixture(autouse=True)
    def _run(self, addon_dir, upgrade_step_template):
        self.result = add_step(
            addon_dir,
            upgrade_step_template,
            upgrade_step_import_steps="[plone.app.registry, typeinfo]",
        )
        assert self.result.returncode == 0, self.result.stderr
        self.upgrades = addon_dir / PKG / "upgrades"
        self.addon_dir = addon_dir

    def test_handler_imports_only_chosen_steps(self):
        handler = (self.upgrades / "v1001.py").read_text()
        assert 'UPGRADE_PROFILE = "profile-my.pkg.upgrades:1001"' in handler
        assert handler.count("runImportStepFromProfile") == 2
        assert '"plone.app.registry"' in handler
        assert '"typeinfo"' in handler
        assert "run_dependencies=False" in handler
        assert "loadMigrationProfile" not in handler

    def test_profile_dir_without_placeholder_metadata(self):
        profile_dir = self.upgrades / "1001"
        assert (profile_dir / ".gitkeep").exists()
        assert not (profile_dir / "metadata.txt").exists()

    def test_zcml_registers_profile_without_upgrade_depends(self):
        zcml = (self.upgrades / "1001.zcml").read_text()
        assert 'name="1001"' in zcml
        assert 'directory="1001"' in zcml
        assert "upgradeDepends" not in zcml

    def test_upgrade_profiles_hidden(self):
        setuphandlers = (self.addon_dir / PKG / "setuphandlers.py").read_text()
        assert '"my.pkg.upgrades"' in setuphandlers
        assert "setuphandlers.py" not in self.result.stdout, "already hidden by backend_addon"

    def test_summary_printed(self):
        assert "Upgrade step 1000 -> 1001" in self.result.stdout
        assert "upgrades/1001/" in self.result.stdout

    def test_unknown_import_step_rejected(self, upgrade_step_template):
        result = add_step(
            self.addon_dir,
            upgrade_step_template,
            source_version="1001",
            destination_version="1002",
            upgrade_step_import_steps="[nonsense]",
        )
        assert result.returncode != 0
        assert not (self.upgrades / "v1002.py").exists()


class TestGeneratedTest:
    def test_runs_the_real_upgrade_path(self, addon_dir, upgrade_step_template):
        assert add_step(addon_dir, upgrade_step_template).returncode == 0

        test = (addon_dir / PKG / "tests/test_upgrade_step_1001.py").read_text()
        assert 'SOURCE = "1000"' in test
        assert 'DESTINATION = "1001"' in test
        assert "upgradeProfile(PROFILE_ID, dest=DESTINATION)" in test
        assert "getLastVersionForProfile(PROFILE_ID) == (DESTINATION,)" in test
        assert "TODO" in test


class TestRerun:
    """Re-running for the next version must not touch shared files."""

    def test_second_step_keeps_shared_files(self, addon_dir, upgrade_step_template):
        assert add_step(addon_dir, upgrade_step_template).returncode == 0
        upgrades = addon_dir / PKG / "upgrades"
        (upgrades / "__init__.py").write_text("# customised\n")
        (upgrades / "base.py").write_text("# package helpers\n")

        result = add_step(
            addon_dir,
            upgrade_step_template,
            upgrade_step_title="Migrate content",
        )

        assert result.returncode == 0, result.stderr
        assert (upgrades / "__init__.py").read_text() == "# customised\n"
        assert (upgrades / "base.py").read_text() == "# package helpers\n"
        assert_file_exists(upgrades / "1002.zcml", content_contains='source="1001"')
        assert_file_exists(upgrades / "v1002.py", content_contains="Migrate content")
        assert_file_exists(
            upgrades / "configure.zcml",
            content_contains=['<include file="1001.zcml" />', '<include file="1002.zcml" />'],
        )
        assert_file_exists(
            addon_dir / PKG / "profiles/default/metadata.xml",
            content_contains="<version>1002</version>",
        )

    def test_existing_destination_fails_before_rendering(
        self, addon_dir, upgrade_step_template
    ):
        assert add_step(addon_dir, upgrade_step_template).returncode == 0
        handler = addon_dir / PKG / "upgrades/v1001.py"
        handler.write_text("# hand-written\n")

        result = add_step(
            addon_dir,
            upgrade_step_template,
            source_version="1000",
            destination_version="1001",
        )

        assert result.returncode != 0
        assert "upgrades/v1001.py already exists" in result.stderr
        assert handler.read_text() == "# hand-written\n"


class TestHiddenProfilesExistingPackage:
    """Packages without the upgrades product hidden get it added."""

    SETUPHANDLERS = textwrap.dedent('''\
        from Products.CMFPlone.interfaces import INonInstallable
        from zope.interface import implementer


        @implementer(INonInstallable)
        class HiddenProfiles:

            def getNonInstallableProfiles(self):
                return [
                    "my.pkg:uninstall",
                ]
        ''')

    @pytest.fixture
    def old_addon(self, addon_dir):
        (addon_dir / PKG / "setuphandlers.py").write_text(self.SETUPHANDLERS)
        zcml = addon_dir / PKG / "configure.zcml"
        lines = [line for line in zcml.read_text().splitlines() if "HiddenProfiles" not in line]
        zcml.write_text("\n".join(lines) + "\n")
        return addon_dir

    def test_adds_products_method_and_utility(self, old_addon, upgrade_step_template):
        result = add_step(
            old_addon, upgrade_step_template, upgrade_step_import_steps="[catalog]"
        )
        assert result.returncode == 0, result.stderr

        setuphandlers = (old_addon / PKG / "setuphandlers.py").read_text()
        assert "def getNonInstallableProducts(self):" in setuphandlers
        assert '"my.pkg.upgrades",' in setuphandlers
        compile(setuphandlers, "setuphandlers.py", "exec")
        assert_file_exists(
            old_addon / PKG / "configure.zcml",
            content_contains='factory=".setuphandlers.HiddenProfiles"',
        )

    def test_registers_utility_when_product_already_listed(
        self, addon_dir, upgrade_step_template
    ):
        zcml = addon_dir / PKG / "configure.zcml"
        lines = [line for line in zcml.read_text().splitlines() if "HiddenProfiles" not in line]
        zcml.write_text("\n".join(lines) + "\n")

        result = add_step(
            addon_dir, upgrade_step_template, upgrade_step_import_steps="[catalog]"
        )

        assert result.returncode == 0, result.stderr
        assert 'factory=".setuphandlers.HiddenProfiles"' in zcml.read_text()

    def test_python_only_step_leaves_setuphandlers_alone(
        self, old_addon, upgrade_step_template
    ):
        assert add_step(old_addon, upgrade_step_template).returncode == 0
        assert (old_addon / PKG / "setuphandlers.py").read_text() == self.SETUPHANDLERS


@pytest.mark.integration
class TestUpgradeStepInPloneSite:
    """End-to-end: the generated add-on's own tests pass in a real Plone site.

    Adds a registry step (1001) and a Python-only step (1002), then runs the
    generated tests plus a check that the upgrade profile is hidden from the
    add-ons control panel. Slow; opt in with ``pytest -m integration``.
    """

    def test_generated_tests_pass(self, temp_dir, backend_addon_template, upgrade_step_template):
        if shutil.which("uv") is None:
            pytest.skip("uv is required to run the Plone integration test")

        addon_dir = temp_dir / "myaddon"
        result = run_copier(
            backend_addon_template,
            addon_dir,
            data={"package_name": "collective.upgradetest"},
        )
        assert result.returncode == 0, f"backend_addon failed: {result.stderr}"

        result = add_step(
            addon_dir,
            upgrade_step_template,
            upgrade_step_title="Register settings",
            upgrade_step_import_steps="[plone.app.registry]",
        )
        assert result.returncode == 0, f"upgrade_step 1001 failed: {result.stderr}"
        result = add_step(addon_dir, upgrade_step_template, upgrade_step_title="Clean up")
        assert result.returncode == 0, f"upgrade_step 1002 failed: {result.stderr}"

        tests_dir = addon_dir / "src/collective/upgradetest/tests"
        (tests_dir / "test_hidden_upgrades.py").write_text(textwrap.dedent('''\
            from zope.component import getMultiAdapter


            def test_upgrade_profiles_hidden(integration):
                panel = getMultiAdapter(
                    (integration["portal"], integration["request"]),
                    name="prefs_install_products_form",
                )
                addons = panel.get_addons()
                assert "collective.upgradetest" in addons
                assert "collective.upgradetest.upgrades" not in addons
        '''))

        sync = subprocess.run(
            ["uv", "sync", "--extra", "test"],
            cwd=addon_dir,
            env=plone_subprocess_env(),
            capture_output=True,
            text=True,
            timeout=900,
        )
        assert sync.returncode == 0, (
            f"uv sync failed:\nSTDOUT:\n{sync.stdout}\nSTDERR:\n{sync.stderr}"
        )

        run = subprocess.run(
            ["uv", "run", "pytest", str(tests_dir), "-v", "--tb=short"],
            cwd=addon_dir,
            env=plone_subprocess_env(),
            capture_output=True,
            text=True,
            timeout=600,
        )
        assert run.returncode == 0, (
            f"Plone tests failed:\nSTDOUT:\n{run.stdout}\nSTDERR:\n{run.stderr}"
        )
        for name in (
            "test_upgrade_step_1001.py",
            "test_upgrade_step_1002.py",
            "test_profile_version_matches_last_upgrade",
            "test_upgrade_profiles_hidden",
        ):
            assert name in run.stdout
