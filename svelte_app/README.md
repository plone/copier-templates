# svelte_app

Adds a Svelte application scaffold (vite + main/App + Python mount view)
to an existing `backend_addon` package. Must be run inside an addon
directory.

Mirrors the bobtemplates.plone `svelte_app` layout: a `svelte_src/<app>/`
directory with the frontend source and a small `src/<package>/svelte_apps/`
Python mount view that serves an HTML shell for the built bundle.

## What it generates

### Frontend (`svelte_src/<app>/`)
- `src/App.svelte` -- root component
- `src/main.js` -- entry point that mounts `App` onto `#<app-name>`
- `package.json` -- vite + svelte dev deps
- `vite.config.js` -- sveltekit-less vite config, outputs into
  `src/<package>/svelte_apps/static/<app>/`. Supports a
  `svelte_app_custom_element` switch for Web Components.

### Backend (`src/<package>/svelte_apps/`)
- `__init__.py`
- `<module>.py` -- `BrowserView` subclass serving the mount page
- `<module>.pt` -- HTML shell template with the mount `<div>` and a
  `<script type="module">` loading the built bundle

Records the app in
`[tool.plone.backend_addon.settings.subtemplates.svelte_apps]`.

## Options

| Option | Description | Default |
|--------|-------------|---------|
| `svelte_app_name` | App name (kebab-case) | `my-svelte-app` |
| `svelte_app_description` | Short description | `A custom Svelte application` |
| `svelte_app_custom_element` | Compile as Web Component | `false` |
| `package_name` | Parent addon package name | (required) |

`svelte_app_module` (snake_case) and `svelte_app_class` (PascalCase) are
computed at render time.

## Usage

```bash
cd my-addon
copier copy <templates>/svelte_app . \
  --data svelte_app_name=dashboard-ui \
  --data package_name=collective.mypackage
```

Then, to build the frontend:

```bash
cd svelte_src/dashboard-ui
npm install
npm run build
```

The build output lands inside the Python package under
`src/<package>/svelte_apps/static/<app>/`.
