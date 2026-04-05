# zope-setup

Creates a complete Plone/Zope project structure. Can be used standalone or inside an existing `backend_addon` package (project name, title, and description are then auto-detected from the addon's `pyproject.toml`).

## What it generates

- `pyproject.toml` with Plone dependencies and `[tool.uv]` constraints
- Invoke tasks for common operations (`install`, `start`, `debug`, `test`, `create_site`, `create_instance`)
- GitHub Actions CI workflow
- `.gitignore` configured for Plone/Zope
- Project settings in `[tool.plone.project.settings]`

After rendering the project files, zope-setup automatically invokes the `zope_instance` template to create the initial Zope instance. You will be prompted for instance name and port.

## Options

| Option | Description | Default |
|--------|-------------|---------|
| `project_name` | Project name | Auto-detected from addon, or required |
| `project_title` | Human-readable title | Auto-detected or auto-generated |
| `project_description` | Short description | Auto-detected or `A Plone project` |
| `plone_version` | Plone version (`6.1.1`, `6.1.0`, `6.0.13`) | `6.1.1` |
| `distribution` | Plone distribution (`plone.volto`, `plone.classicui`) | `plone.volto` |
| `db_storage` | Database backend (`instance`, `relstorage`, `zeo`) | `instance` |
| `zeo_address` | ZEO server address (only when `db_storage=zeo`) | `localhost:8100` |
| `pg_host` | PostgreSQL host (only when `db_storage=relstorage`) | `localhost` |
| `pg_port` | PostgreSQL port (only when `db_storage=relstorage`) | `5432` |
| `pg_dbname` | PostgreSQL database name (only when `db_storage=relstorage`) | `plone_<project_name>` |
| `pg_user` | PostgreSQL user (only when `db_storage=relstorage`) | `plone` |
| `pg_password` | PostgreSQL password (only when `db_storage=relstorage`) | (empty) |
| `author_name` | Author name | `Plone Developer` |
| `author_email` | Author email | `dev@plone.org` |
| `initial_zope_username` | Initial Zope admin username | `admin` |
| `initial_user_password` | Initial Zope admin password (secret) | `admin` |

## Database storage modes

- **instance** -- Single-process FileStorage (ZODB). Simplest setup, good for development.
- **relstorage** -- PostgreSQL-backed RelStorage. Supports multiple concurrent Zope clients sharing one database.
- **zeo** -- ZEO client connecting to a ZEO server. Supports multiple concurrent Zope clients via ZEO protocol.

## Usage

Standalone project:

```bash
copier copy ~/.copier-templates/plone-copier-templates/zope-setup my-project
```

Inside an existing addon (auto-detects project name/title/description):

```bash
cd collective.todos
copier copy ~/.copier-templates/plone-copier-templates/zope-setup .
```

With explicit options:

```bash
copier copy ~/.copier-templates/plone-copier-templates/zope-setup my-project \
  --data project_name=my-project \
  --data plone_version=6.1.1 \
  --data db_storage=relstorage
```
