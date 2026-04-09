"""Tests for the theme subtemplate.

Mirrors bobtemplates.plone theme — the full theme variant. Shares the
theme_basic layout but adds a webpack.config.js and a
scss/_variables.scss partial.
"""
from helpers import apply_subtemplate, assert_file_exists, read_toml, run_copier


class TestThemeRequiresAddon:
    def test_fails_without_parent_addon(self, temp_dir, theme_template):
        result = run_copier(
            theme_template,
            temp_dir,
            data={"theme_name": "My Theme"},
        )
        assert not (temp_dir / "src").exists() or result.returncode != 0


class TestThemeCreation:
    def _apply(self, fresh_addon, theme_template, **extra):
        data = {
            "theme_name": "My Theme",
            "package_name": "collective.mypackage",
        }
        data.update(extra)
        result = apply_subtemplate(theme_template, fresh_addon, data=data)
        assert result.returncode == 0, f"copier failed: {result.stderr}"

    def test_creates_manifest(self, fresh_addon, theme_template):
        self._apply(fresh_addon, theme_template)
        manifest = fresh_addon / "src/collective/mypackage/theme/manifest.cfg"
        assert_file_exists(manifest, content_contains="[theme]")

    def test_creates_webpack_config(self, fresh_addon, theme_template):
        self._apply(fresh_addon, theme_template)
        webpack = fresh_addon / "src/collective/mypackage/theme/webpack.config.js"
        assert_file_exists(webpack, content_contains="module.exports")

    def test_creates_variables_partial(self, fresh_addon, theme_template):
        self._apply(fresh_addon, theme_template)
        variables = (
            fresh_addon / "src/collective/mypackage/theme/scss/_variables.scss"
        )
        assert_file_exists(variables)

    def test_creates_theme_scss(self, fresh_addon, theme_template):
        self._apply(fresh_addon, theme_template)
        scss = fresh_addon / "src/collective/mypackage/theme/scss/theme.scss"
        assert_file_exists(scss, content_contains="variables")

    def test_creates_theme_profile_xml(self, fresh_addon, theme_template):
        self._apply(fresh_addon, theme_template)
        xml = fresh_addon / "src/collective/mypackage/profiles/default/theme.xml"
        assert_file_exists(xml, content_contains="My Theme")


class TestThemeIntegration:
    def test_registers_in_pyproject(self, fresh_addon, theme_template):
        result = apply_subtemplate(
            theme_template,
            fresh_addon,
            data={
                "theme_name": "Full Theme",
                "package_name": "collective.mypackage",
            },
        )
        assert result.returncode == 0, f"copier failed: {result.stderr}"
        data = read_toml(fresh_addon / "pyproject.toml")
        subtemplates = data["tool"]["plone"]["backend_addon"]["settings"][
            "subtemplates"
        ]
        assert "Full Theme" in subtemplates["themes"]
