# indexer

Adds a custom catalog indexer (`@indexer` decorated function) to an existing
`backend_addon` package. Must be run inside an addon directory.

## What it generates

- `src/<package_folder>/indexers/__init__.py`
- `src/<package_folder>/indexers/<indexer_name>.py` -- the indexer function
  (plus a `dummy` guard indexer matching bobtemplates.plone upstream)
- `src/<package_folder>/indexers/configure.zcml` -- `zope:adapter`
  registrations for both
- Adds `<include package=".indexers" />` to the parent `configure.zcml`
- Records the indexer in `[tool.plone.backend_addon.settings.subtemplates]`

## Options

| Option | Description | Default |
|--------|-------------|---------|
| `indexer_name` | Indexer name (snake_case) | `my_custom_index` |
| `indexer_description` | Short description | `A custom catalog indexer` |
| `package_name` | Parent addon package name | (required) |

## Usage

```bash
cd my-addon
copier copy <templates>/indexer . \
  --data indexer_name=my_score \
  --data package_name=collective.mypackage
```
