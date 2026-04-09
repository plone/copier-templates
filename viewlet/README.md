# viewlet

Adds a viewlet (a `browser:viewlet` registration with a `ViewletBase`
subclass) to an existing `backend_addon` package. Must be run inside an
addon directory.

## What it generates

- `src/<package_folder>/viewlets/__init__.py`
- `src/<package_folder>/viewlets/<module>.py` -- viewlet class deriving
  from `plone.app.layout.viewlets.common.ViewletBase`
- `src/<package_folder>/viewlets/<module>.pt` -- page template
  (skipped when `viewlet_template=false`)
- `src/<package_folder>/viewlets/configure.zcml` -- `browser:viewlet`
  registration
- Adds `<include package=".viewlets" />` to the parent `configure.zcml`
- Records the viewlet in `[tool.plone.backend_addon.settings.subtemplates]`

## Options

| Option | Description | Default |
|--------|-------------|---------|
| `viewlet_name` | Viewlet identifier (lowercase) | `myviewlet` |
| `viewlet_class_name` | Python class name | `MyViewlet` |
| `viewlet_manager` | Viewlet manager to register into | `plone.portalheader` |
| `viewlet_for` | Interface the viewlet is registered for | `*` |
| `viewlet_template` | Generate an accompanying `.pt` | `true` |
| `viewlet_description` | Short description | `A custom viewlet` |
| `package_name` | Parent addon package name | (required) |

## Usage

```bash
cd my-addon
copier copy <templates>/viewlet . \
  --data viewlet_name=topbar \
  --data viewlet_class_name=TopBar \
  --data viewlet_manager=plone.portalheader \
  --data package_name=collective.mypackage
```
