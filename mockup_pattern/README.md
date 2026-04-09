# mockup_pattern

Adds a Mockup JavaScript pattern scaffold (pattern source + webpack,
babel, eslint configs + package.json) to an existing `backend_addon`
package. Must be run inside an addon directory.

This is a minimal, structurally-aligned port of bobtemplates.plone's
`mockup_pattern` — enough to get a `pat-<name>.js` module building with
webpack against `@patternslib/patternslib`. Upstream ships additional
config files (`.prettierignore`, `.release-it.js`, `jest.config.js`,
`prettier.config.js`); those can be added to your generated `patterns/`
directory by hand if needed.

## What it generates

- `src/<package_folder>/patterns/pat-<name>.js` -- pattern source
  extending `@patternslib/patternslib` `Base`
- `src/<package_folder>/patterns/package.json` -- npm manifest with
  webpack/babel/eslint/jest devDependencies
- `src/<package_folder>/patterns/webpack.config.js`
- `src/<package_folder>/patterns/babel.config.js`
- `src/<package_folder>/patterns/.eslintrc.js`
- Records the pattern in
  `[tool.plone.backend_addon.settings.subtemplates.mockup_patterns]`

## Options

| Option | Description | Default |
|--------|-------------|---------|
| `pattern_name` | Pattern name (no `pat-` prefix) | `my-pattern` |
| `pattern_description` | Short description | `A custom Mockup JS pattern` |
| `package_name` | Parent addon package name | (required) |

## Usage

```bash
cd my-addon
copier copy <templates>/mockup_pattern . \
  --data pattern_name=search-box \
  --data package_name=collective.mypackage
```
