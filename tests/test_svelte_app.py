"""Tests for the svelte_app subtemplate.

Mirrors bobtemplates.plone svelte_app — a Svelte application scaffold
packaged alongside an existing backend_addon. Minimal port: enough to
build a Svelte entry point with vite, plus the Python-side registration.
"""
from helpers import apply_subtemplate, assert_file_exists, read_toml, run_copier


class TestSvelteAppRequiresAddon:
    def test_fails_without_parent_addon(self, temp_dir, svelte_app_template):
        result = run_copier(
            svelte_app_template,
            temp_dir,
            data={"svelte_app_name": "my-svelte-app"},
        )
        assert not (temp_dir / "src").exists() or result.returncode != 0


class TestSvelteAppCreation:
    def _apply(self, fresh_addon, svelte_app_template, **extra):
        data = {
            "svelte_app_name": "my-svelte-app",
            "package_name": "collective.mypackage",
        }
        data.update(extra)
        result = apply_subtemplate(
            svelte_app_template, fresh_addon, data=data
        )
        assert result.returncode == 0, f"copier failed: {result.stderr}"

    def test_creates_svelte_main_component(
        self, fresh_addon, svelte_app_template
    ):
        self._apply(fresh_addon, svelte_app_template)
        app = (
            fresh_addon
            / "svelte_src/my-svelte-app/src/App.svelte"
        )
        assert_file_exists(app, content_contains="<script>")

    def test_creates_svelte_entry_point(
        self, fresh_addon, svelte_app_template
    ):
        self._apply(fresh_addon, svelte_app_template)
        main = fresh_addon / "svelte_src/my-svelte-app/src/main.js"
        assert_file_exists(main, content_contains="import App")

    def test_creates_svelte_package_json(
        self, fresh_addon, svelte_app_template
    ):
        self._apply(fresh_addon, svelte_app_template)
        pkg = fresh_addon / "svelte_src/my-svelte-app/package.json"
        assert_file_exists(pkg, content_contains='"svelte"')

    def test_creates_vite_config(self, fresh_addon, svelte_app_template):
        self._apply(fresh_addon, svelte_app_template)
        vite = fresh_addon / "svelte_src/my-svelte-app/vite.config.js"
        assert_file_exists(vite, content_contains="svelte")

    def test_creates_python_mount_view(
        self, fresh_addon, svelte_app_template
    ):
        """A tiny Python view that serves as the mount point for the Svelte app."""
        self._apply(fresh_addon, svelte_app_template)
        mount = (
            fresh_addon
            / "src/collective/mypackage/svelte_apps/my_svelte_app.py"
        )
        assert_file_exists(
            mount, content_contains="class MySvelteAppView"
        )


class TestSvelteAppIntegration:
    def test_registers_in_pyproject(self, fresh_addon, svelte_app_template):
        result = apply_subtemplate(
            svelte_app_template,
            fresh_addon,
            data={
                "svelte_app_name": "dashboard-ui",
                "package_name": "collective.mypackage",
            },
        )
        assert result.returncode == 0, f"copier failed: {result.stderr}"
        data = read_toml(fresh_addon / "pyproject.toml")
        subtemplates = data["tool"]["plone"]["backend_addon"]["settings"][
            "subtemplates"
        ]
        assert "dashboard-ui" in subtemplates["svelte_apps"]
