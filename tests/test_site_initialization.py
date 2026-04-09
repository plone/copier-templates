"""Tests for the site_initialization subtemplate.

Mirrors bobtemplates.plone site_initialization. Generates GenericSetup
registry records that configure initial Plone site state (site name,
language, mail schema) under profiles/default/registry/.
"""
from helpers import apply_subtemplate, assert_file_exists, read_toml, run_copier


class TestSiteInitializationRequiresAddon:
    def test_fails_without_parent_addon(
        self, temp_dir, site_initialization_template
    ):
        result = run_copier(
            site_initialization_template,
            temp_dir,
            data={"site_name": "Test Site"},
        )
        assert not (temp_dir / "src").exists() or result.returncode != 0


class TestSiteInitializationCreation:
    def _apply(self, fresh_addon, site_initialization_template, **extra):
        data = {
            "site_name": "New Plone Site",
            "language": "en",
            "package_name": "collective.mypackage",
        }
        data.update(extra)
        result = apply_subtemplate(
            site_initialization_template, fresh_addon, data=data
        )
        assert result.returncode == 0, f"copier failed: {result.stderr}"

    def test_creates_site_schema_registry(
        self, fresh_addon, site_initialization_template
    ):
        self._apply(fresh_addon, site_initialization_template)
        xml = (
            fresh_addon
            / "src/collective/mypackage/profiles/default/registry"
            / "plone.base.interfaces.controlpanel.ISiteSchema.xml"
        )
        assert_file_exists(xml, content_contains="New Plone Site")

    def test_creates_language_schema_registry(
        self, fresh_addon, site_initialization_template
    ):
        self._apply(fresh_addon, site_initialization_template)
        xml = (
            fresh_addon
            / "src/collective/mypackage/profiles/default/registry"
            / "plone.i18n.interfaces.ILanguageSchema.xml"
        )
        assert_file_exists(xml, content_contains=">en<")

    def test_creates_mail_schema_registry(
        self, fresh_addon, site_initialization_template
    ):
        self._apply(fresh_addon, site_initialization_template)
        xml = (
            fresh_addon
            / "src/collective/mypackage/profiles/default/registry"
            / "plone.base.interfaces.controlpanel.IMailSchema.xml"
        )
        assert_file_exists(xml, content_contains="IMailSchema")


class TestSiteInitializationIntegration:
    def test_registers_in_pyproject(
        self, fresh_addon, site_initialization_template
    ):
        result = apply_subtemplate(
            site_initialization_template,
            fresh_addon,
            data={
                "site_name": "My Site",
                "language": "de",
                "package_name": "collective.mypackage",
            },
        )
        assert result.returncode == 0, f"copier failed: {result.stderr}"
        data = read_toml(fresh_addon / "pyproject.toml")
        subtemplates = data["tool"]["plone"]["backend_addon"]["settings"][
            "subtemplates"
        ]
        assert "site_initialization" in subtemplates
