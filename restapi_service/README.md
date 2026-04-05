# restapi_service

Adds a plone.restapi service endpoint to an existing `backend_addon` package. Must be run inside an addon directory.

## What it generates

- `src/<package_folder>/services/<module>.py` -- Service class with configurable HTTP methods
- `src/<package_folder>/services/configure.zcml` -- ZCML registration with permissions
- Registers the service in the parent addon's `configure.zcml`
- Records the service in `[tool.plone.backend_addon.settings.subtemplates]`

## Options

| Option | Description | Default |
|--------|-------------|---------|
| `service_name` | Endpoint name (e.g., `stats`, `my-endpoint`) | (required) |
| `service_description` | Short description | `A custom REST API endpoint` |
| `package_name` | Parent addon package name | (required) |
| `http_get` | Support GET requests | `true` |
| `http_post` | Support POST requests | `false` |
| `http_patch` | Support PATCH requests | `false` |
| `http_delete` | Support DELETE requests | `false` |
| `service_for` | Context interface | `IDexterityContainer` |

Context choices: `IDexterityContainer`, `IDexterityContent`, `IPloneSiteRoot`, `Interface`

## Usage

```bash
cd my-addon
copier copy ~/.copier-templates/plone-copier-templates/restapi_service . \
  --data service_name=analytics \
  --data http_get=true \
  --data http_post=true \
  --data package_name=collective.news
```
