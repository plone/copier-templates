# site_initialization

Adds GenericSetup registry records that configure initial Plone site
state (site title, default language, mail schema) to an existing
`backend_addon` package. Must be run inside an addon directory.

## What it generates

- `src/<package_folder>/profiles/default/registry/plone.base.interfaces.controlpanel.ISiteSchema.xml`
- `src/<package_folder>/profiles/default/registry/plone.i18n.interfaces.ILanguageSchema.xml`
- `src/<package_folder>/profiles/default/registry/plone.base.interfaces.controlpanel.IMailSchema.xml`
- Records the template in
  `[tool.plone.backend_addon.settings.subtemplates.site_initialization]`

Unlike the code-generating subtemplates, this one does NOT add a
`<include package="..." />` to the parent `configure.zcml` — the records
are picked up via the existing GenericSetup profile.

## Options

| Option | Description | Default |
|--------|-------------|---------|
| `site_name` | Plone site title | `New Plone Site` |
| `language` | ISO 639-1 two-letter language code | `en` |
| `package_name` | Parent addon package name | (required) |

## Usage

```bash
cd my-addon
copier copy <templates>/site_initialization . \
  --data site_name="My Site" \
  --data language=de \
  --data package_name=collective.mypackage
```
