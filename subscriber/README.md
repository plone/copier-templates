# subscriber

Adds a zope event subscriber (`zope:subscriber` with a `handler` function)
to an existing `backend_addon` package. Must be run inside an addon
directory.

## What it generates

- `src/<package_folder>/subscribers/__init__.py`
- `src/<package_folder>/subscribers/<handler_name>.py` -- `handler(obj, event)`
  function with a logger line as a placeholder
- `src/<package_folder>/subscribers/configure.zcml` -- `zope:subscriber`
  registering the handler for `(subscriber_for, subscriber_event)`
- Adds `<include package=".subscribers" />` to the parent `configure.zcml`
- Records the subscriber in `[tool.plone.backend_addon.settings.subtemplates]`

## Options

| Option | Description | Default |
|--------|-------------|---------|
| `subscriber_handler_name` | Handler module / slug (snake_case) | `obj_modified_do_something` |
| `subscriber_event` | Dotted name of the event interface | `zope.lifecycleevent.interfaces.IObjectModifiedEvent` |
| `subscriber_for` | Dotted name of the context interface | `plone.dexterity.interfaces.IDexterityContent` |
| `subscriber_description` | Short description | `A custom event subscriber` |
| `package_name` | Parent addon package name | (required) |

## Usage

```bash
cd my-addon
copier copy <templates>/subscriber . \
  --data subscriber_handler_name=on_document_added \
  --data subscriber_event=zope.lifecycleevent.interfaces.IObjectAddedEvent \
  --data subscriber_for=plone.app.contenttypes.interfaces.IDocument \
  --data package_name=collective.mypackage
```
