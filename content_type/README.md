# content_type

Adds a Dexterity content type to an existing `backend_addon` package. Must be run inside an addon directory.

## What it generates

- `src/<package_folder>/content/<module>.py` -- Content type class with schema interface
- `src/<package_folder>/profiles/default/types/<Class>.xml` -- FTI (Factory Type Information)
- Registers the content type in the parent addon's `configure.zcml`
- Records the content type in `[tool.plone.backend_addon.settings.subtemplates]`

## Options

| Option | Description | Default |
|--------|-------------|---------|
| `content_type_name` | Content type name (e.g., `News Item`, `Article`) | (required) |
| `content_type_description` | Short description | `A custom content type` |
| `package_name` | Parent addon package name | (required) |
| `content_type_base` | Base class (`Container` or `Item`) | `Container` |
| `enable_dublin_core` | Enable Dublin Core metadata behavior | `true` |
| `enable_navigation` | Enable navigation behavior | `true` |

## Usage

```bash
cd my-addon
copier copy ~/.copier-templates/plone-copier-templates/content_type . \
  --data content_type_name="News Item" \
  --data package_name=collective.news
```
