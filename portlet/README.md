# portlet

Adds a classic Plone portlet (assignment + renderer + add/edit forms) to
an existing `backend_addon` package. Must be run inside an addon directory.

## What it generates

- `src/<package_folder>/portlets/__init__.py`
- `src/<package_folder>/portlets/<module>.py` -- `I<Name>Portlet` schema,
  `Assignment`, `Renderer`, `AddForm`, `EditForm`
- `src/<package_folder>/portlets/<module>.pt` -- render template
- `src/<package_folder>/portlets/configure.zcml` -- `plone:portlet` entry
- `src/<package_folder>/profiles/default/portlets.xml` -- GenericSetup
  portlet entry
- Adds `<include package=".portlets" />` to the parent `configure.zcml`
- Records the portlet in `[tool.plone.backend_addon.settings.subtemplates]`

## Options

| Option | Description | Default |
|--------|-------------|---------|
| `portlet_name` | Portlet display name (PascalCase) | `Weather` |
| `portlet_description` | Short description | `A custom portlet` |
| `package_name` | Parent addon package name | (required) |

## Usage

```bash
cd my-addon
copier copy <templates>/portlet . \
  --data portlet_name=Weather \
  --data package_name=collective.mypackage
```
