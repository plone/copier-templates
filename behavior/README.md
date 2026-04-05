# behavior

Adds a Dexterity behavior to an existing `backend_addon` package. Must be run inside an addon directory.

## What it generates

- `src/<package_folder>/behaviors/<module>.py` -- Behavior interface with schema, optional marker interface and adapter
- `src/<package_folder>/behaviors/configure.zcml` -- ZCML registration
- Registers the behavior in the parent addon's `configure.zcml`
- Records the behavior in `[tool.plone.backend_addon.settings.subtemplates]`

## Options

| Option | Description | Default |
|--------|-------------|---------|
| `behavior_name` | Behavior interface name (e.g., `IFeatured`, `ITaggable`) | (required) |
| `behavior_description` | Short description | `A custom Dexterity behavior` |
| `package_name` | Parent addon package name | (required) |
| `behavior_marker` | Create a marker interface | `true` |
| `behavior_factory` | Create a behavior factory/adapter | `true` |

## Usage

```bash
cd my-addon
copier copy ~/.copier-templates/plone-copier-templates/behavior . \
  --data behavior_name=IFeatured \
  --data package_name=collective.news
```
