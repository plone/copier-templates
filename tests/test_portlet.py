"""Tests for the portlet subtemplate.

Mirrors bobtemplates.plone portlet. Generates:
  src/<pkg>/portlets/__init__.py
  src/<pkg>/portlets/<module>.py       (assignment + renderer + add form)
  src/<pkg>/portlets/<module>.pt       (render template)
  src/<pkg>/portlets/configure.zcml    (plone:portlet registration)
  src/<pkg>/profiles/default/portlets.xml (GS portlet entry)
"""
from helpers import apply_subtemplate, assert_file_exists, read_toml, run_copier


class TestPortletRequiresAddon:
    def test_fails_without_parent_addon(self, temp_dir, portlet_template):
        result = run_copier(
            portlet_template,
            temp_dir,
            data={"portlet_name": "Weather"},
        )
        assert not (temp_dir / "src").exists() or result.returncode != 0


class TestPortletCreation:
    def _apply(self, fresh_addon, portlet_template, **extra):
        data = {
            "portlet_name": "Weather",
            "package_name": "collective.mypackage",
        }
        data.update(extra)
        result = apply_subtemplate(portlet_template, fresh_addon, data=data)
        assert result.returncode == 0, f"copier failed: {result.stderr}"

    def test_creates_portlets_init(self, fresh_addon, portlet_template):
        self._apply(fresh_addon, portlet_template)
        assert_file_exists(
            fresh_addon / "src/collective/mypackage/portlets/__init__.py"
        )

    def test_creates_portlet_module(self, fresh_addon, portlet_template):
        self._apply(fresh_addon, portlet_template)
        module = fresh_addon / "src/collective/mypackage/portlets/weather.py"
        assert_file_exists(
            module,
            content_contains=[
                "class IWeatherPortlet",
                "class Assignment",
                "class Renderer",
                "class AddForm",
                "base.Renderer",
            ],
        )

    def test_creates_portlet_template(self, fresh_addon, portlet_template):
        self._apply(fresh_addon, portlet_template)
        pt = fresh_addon / "src/collective/mypackage/portlets/weather.pt"
        assert_file_exists(pt)

    def test_creates_portlet_configure_zcml(self, fresh_addon, portlet_template):
        self._apply(fresh_addon, portlet_template)
        zcml = fresh_addon / "src/collective/mypackage/portlets/configure.zcml"
        assert_file_exists(
            zcml,
            content_contains=[
                "<plone:portlet",
                'name="collective.mypackage.Weather"',
                "IWeatherPortlet",
            ],
        )

    def test_creates_portlets_xml(self, fresh_addon, portlet_template):
        self._apply(fresh_addon, portlet_template)
        xml = fresh_addon / "src/collective/mypackage/profiles/default/portlets.xml"
        assert_file_exists(
            xml,
            content_contains=[
                "collective.mypackage.Weather",
                "<portlet",
            ],
        )


class TestPortletIntegration:
    def _apply(self, fresh_addon, portlet_template, name="Weather"):
        result = apply_subtemplate(
            portlet_template,
            fresh_addon,
            data={
                "portlet_name": name,
                "package_name": "collective.mypackage",
            },
        )
        assert result.returncode == 0, f"copier failed: {result.stderr}"

    def test_registers_in_pyproject(self, fresh_addon, portlet_template):
        self._apply(fresh_addon, portlet_template)
        data = read_toml(fresh_addon / "pyproject.toml")
        subtemplates = data["tool"]["plone"]["backend_addon"]["settings"][
            "subtemplates"
        ]
        assert "Weather" in subtemplates["portlets"]

    def test_adds_parent_zcml_include(self, fresh_addon, portlet_template):
        self._apply(fresh_addon, portlet_template)
        parent_zcml = fresh_addon / "src/collective/mypackage/configure.zcml"
        assert_file_exists(
            parent_zcml,
            content_contains='<include package=".portlets" />',
        )

    def test_parent_include_not_duplicated_on_rerun(
        self, fresh_addon, portlet_template
    ):
        self._apply(fresh_addon, portlet_template, name="Weather")
        self._apply(fresh_addon, portlet_template, name="News")
        parent_zcml = fresh_addon / "src/collective/mypackage/configure.zcml"
        assert parent_zcml.read_text().count(
            '<include package=".portlets" />'
        ) == 1
