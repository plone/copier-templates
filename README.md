# Plone Copier Templates

A multi-template [Copier](https://copier.readthedocs.io/) repository for modern Plone development. Composable templates for creating Plone projects, addons, and addon components.

## Overview

```
INDEPENDENT TEMPLATES:
├── zope-setup              Creates Plone/Zope project structure
├── backend_addon           Creates standalone addon package
└── zope_instance           Adds Zope instances to an existing project

SUBTEMPLATES (used inside a backend_addon):
├── content_type            Adds Dexterity content type
├── behavior                Adds Dexterity behavior
└── restapi_service         Adds REST API endpoint
```

Each template has its own README with full documentation. See the individual template directories for details.

## Requirements

- Python 3.10+
- [Copier](https://copier.readthedocs.io/) 9.0.0+
- [copier-template-extensions](https://github.com/copier-org/copier-template-extensions)

## Installation

```bash
uv tool install copier --with copier-template-extensions
```

## Quick Start

### Create a Plone project

```bash
copier copy ~/.copier-templates/plone-copier-templates/zope-setup my-project
cd my-project
uv sync
uv run invoke start
```

### Create a standalone addon

```bash
copier copy ~/.copier-templates/plone-copier-templates/backend_addon collective.todos
cd collective.todos
```

### Self-contained addon (addon + zope-setup)

```bash
# Create the addon
copier copy ~/.copier-templates/plone-copier-templates/backend_addon collective.todos \
  --data package_name=collective.todos

# Add zope-setup inside it (project name/title/description auto-detected)
cd collective.todos
copier copy ~/.copier-templates/plone-copier-templates/zope-setup .
```

### Add components to an addon

```bash
cd my-addon
copier copy ~/.copier-templates/plone-copier-templates/content_type .
copier copy ~/.copier-templates/plone-copier-templates/behavior .
copier copy ~/.copier-templates/plone-copier-templates/restapi_service .
```

### Add additional Zope instances

```bash
cd my-project
copier copy ~/.copier-templates/plone-copier-templates/zope_instance . \
  --data instance_name=instance2 \
  --data port=8081
```

## Full Workflow Example

```bash
# 1. Create a new Plone project
copier copy ~/.copier-templates/plone-copier-templates/zope-setup my-intranet
cd my-intranet

# 2. Create a custom addon
copier copy ~/.copier-templates/plone-copier-templates/backend_addon sources/intranet.policy \
  --data package_name=intranet.policy

cd sources/intranet.policy

# 3. Add a content type
copier copy ~/.copier-templates/plone-copier-templates/content_type . \
  --data content_type_name="Department" \
  --data package_name=intranet.policy

# 4. Add a behavior
copier copy ~/.copier-templates/plone-copier-templates/behavior . \
  --data behavior_name=ISocialMedia \
  --data package_name=intranet.policy

# 5. Add a REST API endpoint
copier copy ~/.copier-templates/plone-copier-templates/restapi_service . \
  --data service_name=org-chart \
  --data package_name=intranet.policy

# 6. Install and run
cd ../..
uv sync
uv run invoke start
```

## Architecture

### Context detection

Templates use [copier-template-extensions](https://github.com/copier-org/copier-template-extensions) `ContextHook` to read settings from `pyproject.toml` in the destination directory:

- **zope-setup** reads `[tool.plone.backend_addon.settings]` to auto-detect addon context
- **zope_instance** reads `[tool.plone.project.settings]` to inherit project context
- **Subtemplates** read `[tool.plone.backend_addon.settings]` for package info

### pyproject.toml namespaces

Templates persist settings in custom namespaces, enabling subtemplates to auto-detect parent context:

```toml
[tool.plone.project.settings]
plone_version = "6.1.1"
distribution = "plone.volto"
db_storage = "instance"
instances = ["instance"]

[tool.plone.backend_addon.settings]
package_name = "collective.mypackage"
package_title = "Collective Mypackage"
```

## Development

### Setup

```bash
git clone https://github.com/derico-de/copier-templates.git
cd copier-templates
uv sync --extra dev
```

### Running tests

```bash
uv run pytest tests/ -v
uv run pytest tests/test_backend_addon.py -v
uv run pytest tests/ --cov=shared --cov-report=html
```

## Updating templates

To update an existing project with template changes:

```bash
copier update --trust
```

## License

MIT

## Credits

- Derico - Maik Derstappen - md@derico.de
- Inspired by [bobtemplates.plone](https://github.com/plone/bobtemplates.plone)
