# view

Adds a `BrowserView` (with optional page template) to an existing
`backend_addon` package. Must be run inside an addon directory.

## What it generates

- `src/<package_folder>/views/__init__.py`
- `src/<package_folder>/views/<view_module>.py` -- the view class deriving
  from `BrowserView`, `DefaultView` or `CollectionView`
- `src/<package_folder>/views/<view_module>.pt` -- page template
  (skipped when `view_template=false`)
- `src/<package_folder>/views/configure.zcml` -- `browser:page` registration
- Adds `<include package=".views" />` to the parent `configure.zcml`
- Records the view in `[tool.plone.backend_addon.settings.subtemplates]`

## Options

| Option | Description | Default |
|--------|-------------|---------|
| `view_name` | URL identifier (e.g. `my-view`, invoked as `@@my-view`) | `my-view` |
| `view_class_name` | Python class name (PascalCase) | `MyView` |
| `view_base_class` | `BrowserView` / `DefaultView` / `CollectionView` | `BrowserView` |
| `view_template` | Generate an accompanying `.pt` template | `true` |
| `view_for` | Interface the view is registered for (or `*`) | `*` |
| `view_description` | Short description | `A custom browser view` |
| `package_name` | Parent addon package name | (required) |

## Usage

```bash
cd my-addon
copier copy <templates>/view . \
  --data view_name=my-view \
  --data view_class_name=MyView \
  --data package_name=collective.mypackage
```
