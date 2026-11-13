# Upgrade Step Subtemplate

Adds a GenericSetup upgrade step to an existing `backend_addon`.

## Usage

```bash
cd my-addon
plonecli add upgrade_step
# non-interactive, importing only the registry step:
plonecli add upgrade_step --defaults \
  -d upgrade_step_title="Add settings" \
  -d "upgrade_step_import_steps=[plone.app.registry]"
```

Re-running for the next version only creates the per-version files.
A `destination_version` that already exists is rejected before anything is written.

## What it creates

- `upgrades/__init__.py` (only if missing)
- `upgrades/v<dest>.py`: the handler
- `upgrades/<dest>.zcml`: the `upgradeStep` registration
- `upgrades/<dest>/`: the upgrade profile, only when import steps are chosen
- `tests/test_upgrade_step_<dest>.py`: runs the upgrade from source to destination

## What it updates

- `profiles/default/metadata.xml`: bumps the version to the destination
- `upgrades/configure.zcml`: includes `<dest>.zcml`
- `configure.zcml`: includes `.upgrades` if missing
- `setuphandlers.py`: hides `<package>.upgrades` profiles from the add-ons control panel (only when a profile is created)

A summary of created/updated files and remaining TODOs is printed at the end.

## Questions

| Question | Default | Description |
|----------|---------|-------------|
| `upgrade_step_title` | (required) | Title of the upgrade step |
| `upgrade_step_description` | "A custom upgrade step" | What this step does |
| `source_version` | current metadata.xml version | Source profile version |
| `destination_version` | source + 1 | Target profile version |
| `upgrade_step_import_steps` | `[]` | GenericSetup import steps to run from the upgrade profile (YAML list with `-d`). Empty means a Python-only handler with a TODO. |
