"""Tests for the subscriber subtemplate.

Mirrors bobtemplates.plone subscriber. Upstream generates:
  src/<pkg>/subscribers/__init__.py
  src/<pkg>/subscribers/<handler_name>.py  (handler(obj, event) function)
  src/<pkg>/subscribers/configure.zcml     (zope:subscriber registration)

Upstream questions:
  - subscriber_handler_name   (default "obj_modified_do_something")
"""
import pytest
from helpers import apply_subtemplate, assert_file_exists, read_toml, run_copier


class TestSubscriberRequiresAddon:
    def test_fails_without_parent_addon(self, temp_dir, subscriber_template):
        result = run_copier(
            subscriber_template,
            temp_dir,
            data={"subscriber_handler_name": "my_handler"},
        )
        assert not (temp_dir / "src").exists() or result.returncode != 0


class TestSubscriberCreation:
    def _apply(self, fresh_addon, subscriber_template, **extra):
        data = {
            "subscriber_handler_name": "obj_modified_do_something",
            "subscriber_event": "zope.lifecycleevent.interfaces.IObjectModifiedEvent",
            "subscriber_for": "plone.dexterity.interfaces.IDexterityContent",
            "package_name": "collective.mypackage",
        }
        data.update(extra)
        result = apply_subtemplate(subscriber_template, fresh_addon, data=data)
        assert result.returncode == 0, f"copier failed: {result.stderr}"

    def test_creates_subscribers_init(self, fresh_addon, subscriber_template):
        self._apply(fresh_addon, subscriber_template)
        assert_file_exists(
            fresh_addon / "src/collective/mypackage/subscribers/__init__.py"
        )

    def test_creates_handler_module(self, fresh_addon, subscriber_template):
        self._apply(fresh_addon, subscriber_template)
        module = (
            fresh_addon
            / "src/collective/mypackage/subscribers/obj_modified_do_something.py"
        )
        assert_file_exists(
            module,
            content_contains=[
                "def handler",
                "obj",
                "event",
            ],
        )

    def test_creates_subscriber_configure_zcml(
        self, fresh_addon, subscriber_template
    ):
        self._apply(fresh_addon, subscriber_template)
        zcml = fresh_addon / "src/collective/mypackage/subscribers/configure.zcml"
        assert_file_exists(
            zcml,
            content_contains=[
                "<subscriber",
                "IObjectModifiedEvent",
                "IDexterityContent",
                ".obj_modified_do_something.handler",
            ],
        )


class TestSubscriberIntegration:
    def _apply(
        self,
        fresh_addon,
        subscriber_template,
        name="obj_modified_do_something",
    ):
        result = apply_subtemplate(
            subscriber_template,
            fresh_addon,
            data={
                "subscriber_handler_name": name,
                "subscriber_event": "zope.lifecycleevent.interfaces.IObjectModifiedEvent",
                "subscriber_for": "plone.dexterity.interfaces.IDexterityContent",
                "package_name": "collective.mypackage",
            },
        )
        assert result.returncode == 0, f"copier failed: {result.stderr}"

    def test_registers_in_pyproject(self, fresh_addon, subscriber_template):
        self._apply(fresh_addon, subscriber_template)
        data = read_toml(fresh_addon / "pyproject.toml")
        subtemplates = data["tool"]["plone"]["backend_addon"]["settings"][
            "subtemplates"
        ]
        assert "obj_modified_do_something" in subtemplates["subscribers"]

    def test_adds_parent_zcml_include(self, fresh_addon, subscriber_template):
        self._apply(fresh_addon, subscriber_template)
        parent_zcml = fresh_addon / "src/collective/mypackage/configure.zcml"
        assert_file_exists(
            parent_zcml,
            content_contains='<include package=".subscribers" />',
        )

    def test_parent_include_not_duplicated_on_rerun(
        self, fresh_addon, subscriber_template
    ):
        self._apply(fresh_addon, subscriber_template, name="first_handler")
        self._apply(fresh_addon, subscriber_template, name="second_handler")
        parent_zcml = fresh_addon / "src/collective/mypackage/configure.zcml"
        content = parent_zcml.read_text()
        assert content.count('<include package=".subscribers" />') == 1


class TestSubscriberEdgeCases:
    @pytest.mark.parametrize(
        "event_interface",
        [
            "zope.lifecycleevent.interfaces.IObjectCreatedEvent",
            "zope.lifecycleevent.interfaces.IObjectModifiedEvent",
            "zope.lifecycleevent.interfaces.IObjectRemovedEvent",
        ],
    )
    def test_different_event_types(
        self, fresh_addon, subscriber_template, event_interface
    ):
        result = apply_subtemplate(
            subscriber_template,
            fresh_addon,
            data={
                "subscriber_handler_name": "my_handler",
                "subscriber_event": event_interface,
                "subscriber_for": "plone.dexterity.interfaces.IDexterityContent",
                "package_name": "collective.mypackage",
            },
        )
        assert result.returncode == 0, f"copier failed: {result.stderr}"
        zcml = fresh_addon / "src/collective/mypackage/subscribers/configure.zcml"
        event_short = event_interface.rsplit(".", 1)[1]
        assert event_short in zcml.read_text()
