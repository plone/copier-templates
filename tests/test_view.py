"""Tests for the view subtemplate.

Mirrors bobtemplates.plone view. Generates:
  src/<pkg>/views/__init__.py
  src/<pkg>/views/<view_module>.py       (BrowserView-derived class)
  src/<pkg>/views/<view_module>.pt       (page template; optional)
  src/<pkg>/views/configure.zcml         (browser:page registration)

Questions:
  - view_name          (URL, default "my-view")
  - view_class_name    (default "MyView")
  - view_base_class    (BrowserView | DefaultView | CollectionView, default BrowserView)
  - view_template      (bool, default true)
  - view_for           (dotted name or "*", default "*")
"""
import pytest
from helpers import apply_subtemplate, assert_file_exists, read_toml, run_copier


class TestViewRequiresAddon:
    def test_fails_without_parent_addon(self, temp_dir, view_template):
        result = run_copier(
            view_template,
            temp_dir,
            data={"view_name": "my-view"},
        )
        assert not (temp_dir / "src").exists() or result.returncode != 0


class TestViewCreation:
    def _apply(self, fresh_addon, view_template, **extra):
        data = {
            "view_name": "my-view",
            "view_class_name": "MyView",
            "package_name": "collective.mypackage",
        }
        data.update(extra)
        result = apply_subtemplate(view_template, fresh_addon, data=data)
        assert result.returncode == 0, f"copier failed: {result.stderr}"

    def test_creates_views_init(self, fresh_addon, view_template):
        self._apply(fresh_addon, view_template)
        assert_file_exists(
            fresh_addon / "src/collective/mypackage/views/__init__.py"
        )

    def test_creates_view_module(self, fresh_addon, view_template):
        self._apply(fresh_addon, view_template)
        module = fresh_addon / "src/collective/mypackage/views/my_view.py"
        assert_file_exists(
            module,
            content_contains=[
                "class MyView",
                "BrowserView",
            ],
        )

    def test_creates_view_template(self, fresh_addon, view_template):
        self._apply(fresh_addon, view_template)
        pt = fresh_addon / "src/collective/mypackage/views/my_view.pt"
        assert_file_exists(pt, content_contains="metal:use-macro")

    def test_creates_view_configure_zcml(self, fresh_addon, view_template):
        self._apply(fresh_addon, view_template)
        zcml = fresh_addon / "src/collective/mypackage/views/configure.zcml"
        assert_file_exists(
            zcml,
            content_contains=[
                "<browser:page",
                'name="my-view"',
                ".my_view.MyView",
            ],
        )


class TestViewIntegration:
    def _apply(
        self, fresh_addon, view_template, name="my-view", class_name="MyView"
    ):
        result = apply_subtemplate(
            view_template,
            fresh_addon,
            data={
                "view_name": name,
                "view_class_name": class_name,
                "package_name": "collective.mypackage",
            },
        )
        assert result.returncode == 0, f"copier failed: {result.stderr}"

    def test_registers_in_pyproject(self, fresh_addon, view_template):
        self._apply(fresh_addon, view_template)
        data = read_toml(fresh_addon / "pyproject.toml")
        subtemplates = data["tool"]["plone"]["backend_addon"]["settings"][
            "subtemplates"
        ]
        assert "my-view" in subtemplates["views"]

    def test_adds_parent_zcml_include(self, fresh_addon, view_template):
        self._apply(fresh_addon, view_template)
        parent_zcml = fresh_addon / "src/collective/mypackage/configure.zcml"
        assert_file_exists(
            parent_zcml,
            content_contains='<include package=".views" />',
        )

    def test_parent_include_not_duplicated_on_rerun(
        self, fresh_addon, view_template
    ):
        self._apply(fresh_addon, view_template, name="first", class_name="First")
        self._apply(
            fresh_addon, view_template, name="second", class_name="Second"
        )
        parent_zcml = fresh_addon / "src/collective/mypackage/configure.zcml"
        content = parent_zcml.read_text()
        assert content.count('<include package=".views" />') == 1


class TestViewEdgeCases:
    def test_without_template(self, fresh_addon, view_template):
        result = apply_subtemplate(
            view_template,
            fresh_addon,
            data={
                "view_name": "tpl-less",
                "view_class_name": "TplLess",
                "view_template": False,
                "package_name": "collective.mypackage",
            },
        )
        assert result.returncode == 0, f"copier failed: {result.stderr}"
        pt = fresh_addon / "src/collective/mypackage/views/tpl_less.pt"
        assert not pt.exists(), "Page template should NOT be generated"
        module = fresh_addon / "src/collective/mypackage/views/tpl_less.py"
        content = module.read_text()
        assert "def __call__" in content

    @pytest.mark.parametrize(
        "base_class,import_fragment",
        [
            ("BrowserView", "BrowserView"),
            ("DefaultView", "DefaultView"),
            ("CollectionView", "CollectionView"),
        ],
    )
    def test_base_classes(
        self, fresh_addon, view_template, base_class, import_fragment
    ):
        result = apply_subtemplate(
            view_template,
            fresh_addon,
            data={
                "view_name": "my-view",
                "view_class_name": "MyView",
                "view_base_class": base_class,
                "package_name": "collective.mypackage",
            },
        )
        assert result.returncode == 0, f"copier failed: {result.stderr}"
        module = fresh_addon / "src/collective/mypackage/views/my_view.py"
        assert import_fragment in module.read_text()
