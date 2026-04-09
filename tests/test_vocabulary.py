"""Tests for the vocabulary subtemplate.

Mirrors bobtemplates.plone vocabulary:
  https://github.com/plone/bobtemplates.plone/tree/master/bobtemplates/plone/vocabulary

Upstream generates (dynamic vocabulary path — the default):
  src/<pkg>/vocabularies/__init__.py
  src/<pkg>/vocabularies/configure.zcml        (registers a utility for
                                                zope.schema.interfaces.IVocabularyFactory)
  src/<pkg>/vocabularies/<snake_name>.py       (VocabItem + SimpleVocabulary factory)

Upstream questions:
  - vocabulary_name            (PascalCase, default "AvailableThings")
  - is_static_catalog_vocab    (bool, default false)
"""
import pytest
from helpers import (
    apply_subtemplate,
    assert_file_exists,
    read_toml,
    run_copier,
)


class TestVocabularyRequiresAddon:
    """vocabulary fails cleanly outside a backend_addon."""

    def test_fails_without_parent_addon(self, temp_dir, vocabulary_template):
        result = run_copier(
            vocabulary_template,
            temp_dir,
            data={"vocabulary_name": "AvailableThings"},
        )
        # Either the task errors out, or nothing useful is generated.
        generated = temp_dir / "src"
        assert not generated.exists() or result.returncode != 0


class TestVocabularyCreation:
    """Files produced when applied to a valid backend_addon."""

    def _apply(self, fresh_addon, vocabulary_template, **extra):
        data = {
            "vocabulary_name": "AvailableThings",
            "package_name": "collective.mypackage",
        }
        data.update(extra)
        result = apply_subtemplate(vocabulary_template, fresh_addon, data=data)
        assert result.returncode == 0, f"copier failed: {result.stderr}"

    def test_creates_vocabularies_init(self, fresh_addon, vocabulary_template):
        self._apply(fresh_addon, vocabulary_template)
        assert_file_exists(
            fresh_addon / "src/collective/mypackage/vocabularies/__init__.py"
        )

    def test_creates_vocabulary_module(self, fresh_addon, vocabulary_template):
        self._apply(fresh_addon, vocabulary_template)
        module = fresh_addon / "src/collective/mypackage/vocabularies/available_things.py"
        assert_file_exists(
            module,
            content_contains=[
                "AvailableThings",
                "SimpleVocabulary",
                "IVocabularyFactory",
            ],
        )

    def test_creates_vocabularies_configure_zcml(
        self, fresh_addon, vocabulary_template
    ):
        self._apply(fresh_addon, vocabulary_template)
        zcml = fresh_addon / "src/collective/mypackage/vocabularies/configure.zcml"
        assert_file_exists(
            zcml,
            content_contains=[
                "<utility",
                "IVocabularyFactory",
                'name="collective.mypackage.AvailableThings"',
            ],
        )


class TestVocabularyIntegration:
    """Parent addon state after applying vocabulary."""

    def _apply(self, fresh_addon, vocabulary_template, name="AvailableThings"):
        result = apply_subtemplate(
            vocabulary_template,
            fresh_addon,
            data={
                "vocabulary_name": name,
                "package_name": "collective.mypackage",
            },
        )
        assert result.returncode == 0, f"copier failed: {result.stderr}"

    def test_registers_in_pyproject(self, fresh_addon, vocabulary_template):
        self._apply(fresh_addon, vocabulary_template)
        data = read_toml(fresh_addon / "pyproject.toml")
        subtemplates = data["tool"]["plone"]["backend_addon"]["settings"][
            "subtemplates"
        ]
        assert "AvailableThings" in subtemplates["vocabularies"]

    def test_adds_parent_zcml_include(self, fresh_addon, vocabulary_template):
        self._apply(fresh_addon, vocabulary_template)
        parent_zcml = fresh_addon / "src/collective/mypackage/configure.zcml"
        assert_file_exists(
            parent_zcml,
            content_contains='<include package=".vocabularies" />',
        )

    def test_parent_zcml_include_not_duplicated_on_rerun(
        self, fresh_addon, vocabulary_template
    ):
        self._apply(fresh_addon, vocabulary_template, name="AvailableThings")
        self._apply(fresh_addon, vocabulary_template, name="OtherThings")
        parent_zcml = fresh_addon / "src/collective/mypackage/configure.zcml"
        content = parent_zcml.read_text()
        assert content.count('<include package=".vocabularies" />') == 1


class TestVocabularyEdgeCases:
    """Name normalisation and option handling."""

    @pytest.mark.parametrize(
        "vocab_name, expected_module, expected_class",
        [
            ("AvailableThings", "available_things", "AvailableThings"),
            ("MyVocab", "my_vocab", "MyVocab"),
            ("Simple", "simple", "Simple"),
        ],
    )
    def test_name_normalization(
        self,
        fresh_addon,
        vocabulary_template,
        vocab_name,
        expected_module,
        expected_class,
    ):
        result = apply_subtemplate(
            vocabulary_template,
            fresh_addon,
            data={
                "vocabulary_name": vocab_name,
                "package_name": "collective.mypackage",
            },
        )
        assert result.returncode == 0, f"copier failed: {result.stderr}"
        module = (
            fresh_addon
            / f"src/collective/mypackage/vocabularies/{expected_module}.py"
        )
        assert_file_exists(module, content_contains=f"class {expected_class}")
