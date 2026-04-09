# vocabulary

Adds a named vocabulary (an `IVocabularyFactory` utility) to an existing
`backend_addon` package. Must be run inside an addon directory.

## What it generates

- `src/<package_folder>/vocabularies/__init__.py`
- `src/<package_folder>/vocabularies/<module>.py` -- `SimpleVocabulary`
  factory implementing `IVocabularyFactory`
- `src/<package_folder>/vocabularies/configure.zcml` -- registers the
  factory as a named utility
- Adds `<include package=".vocabularies" />` to the parent addon's
  `configure.zcml`
- Records the vocabulary in `[tool.plone.backend_addon.settings.subtemplates]`

## Options

| Option | Description | Default |
|--------|-------------|---------|
| `vocabulary_name` | Vocabulary class name in PascalCase | `AvailableThings` |
| `vocabulary_description` | Short description | `A custom named vocabulary` |
| `package_name` | Parent addon package name | (required) |

The ZCML utility is registered under
`{package_name}.{vocabulary_name}` (e.g. `collective.mypackage.AvailableThings`).

## Usage

```bash
cd my-addon
copier copy <templates>/vocabulary . \
  --data vocabulary_name=AvailableThings \
  --data package_name=collective.mypackage
```
