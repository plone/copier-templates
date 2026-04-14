"""Tests for the theme_basic subtemplate.

Mirrors bobtemplates.plone theme_basic — generates a minimal theme
(manifest, theme.css/js/scss, package.json, theme.xml profile,
browser overrides) inside an existing backend_addon.
"""
from helpers import apply_subtemplate, assert_file_exists, read_toml, run_copier


class TestThemeBasicRequiresAddon:
    def test_fails_without_parent_addon(self, temp_dir, theme_basic_template):
        result = run_copier(
            theme_basic_template,
            temp_dir,
            data={"theme_name": "My Theme"},
        )
        assert not (temp_dir / "src").exists() or result.returncode != 0


class TestThemeBasicCreation:
    def _apply(self, fresh_addon, theme_basic_template, **extra):
        data = {
            "theme_name": "My Theme",
            "package_name": "collective.mypackage",
        }
        data.update(extra)
        result = apply_subtemplate(
            theme_basic_template, fresh_addon, data=data
        )
        assert result.returncode == 0, f"copier failed: {result.stderr}"

    def test_creates_manifest(self, fresh_addon, theme_basic_template):
        self._apply(fresh_addon, theme_basic_template)
        manifest = fresh_addon / "src/collective/mypackage/theme/manifest.cfg"
        assert_file_exists(manifest, content_contains=["[theme]", "My Theme"])

    def test_creates_package_json(self, fresh_addon, theme_basic_template):
        self._apply(fresh_addon, theme_basic_template)
        pkg_json = fresh_addon / "src/collective/mypackage/theme/package.json"
        assert_file_exists(pkg_json, content_contains='"name"')

    def test_creates_theme_scss(self, fresh_addon, theme_basic_template):
        self._apply(fresh_addon, theme_basic_template)
        scss = fresh_addon / "src/collective/mypackage/theme/scss/theme.scss"
        assert_file_exists(scss)

    def test_creates_theme_css(self, fresh_addon, theme_basic_template):
        self._apply(fresh_addon, theme_basic_template)
        css = fresh_addon / "src/collective/mypackage/theme/css/theme.css"
        assert_file_exists(css)

    def test_creates_theme_js(self, fresh_addon, theme_basic_template):
        self._apply(fresh_addon, theme_basic_template)
        js = fresh_addon / "src/collective/mypackage/theme/js/theme.js"
        assert_file_exists(js)

    def test_creates_theme_profile_xml(
        self, fresh_addon, theme_basic_template
    ):
        self._apply(fresh_addon, theme_basic_template)
        xml = fresh_addon / "src/collective/mypackage/profiles/default/theme.xml"
        assert_file_exists(xml, content_contains="my-theme")


class TestThemeBasicIntegration:
    def test_registers_in_pyproject(self, fresh_addon, theme_basic_template):
        result = apply_subtemplate(
            theme_basic_template,
            fresh_addon,
            data={
                "theme_name": "Test Theme",
                "package_name": "collective.mypackage",
            },
        )
        assert result.returncode == 0, f"copier failed: {result.stderr}"
        data = read_toml(fresh_addon / "pyproject.toml")
        subtemplates = data["tool"]["plone"]["backend_addon"]["settings"][
            "subtemplates"
        ]
        assert "Test Theme" in subtemplates["themes"]
