# form

Adds a `z3c.form`-based form (`AutoExtensibleForm` + `form.Form`) to an
existing `backend_addon` package. Must be run inside an addon directory.

## What it generates

- `src/<package_folder>/forms/__init__.py`
- `src/<package_folder>/forms/<form_module>.py` -- form class with a
  schema interface (`I<FormClass>Schema`) and a "Submit" button handler
- `src/<package_folder>/forms/configure.zcml` -- `browser:page` registration
- Adds `<include package=".forms" />` to the parent `configure.zcml`
- Records the form in `[tool.plone.backend_addon.settings.subtemplates]`

## Options

| Option | Description | Default |
|--------|-------------|---------|
| `form_name` | URL identifier (e.g. `my-form`, invoked as `@@my-form`) | `my-form` |
| `form_class_name` | Python class name (PascalCase) | `MyForm` |
| `form_for` | Interface the form is registered for (or `*`) | `*` |
| `form_description` | Short description | `A custom form` |
| `package_name` | Parent addon package name | (required) |

## Usage

```bash
cd my-addon
copier copy <templates>/form . \
  --data form_name=contact \
  --data form_class_name=ContactForm \
  --data package_name=collective.mypackage
```
