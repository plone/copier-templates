# TODO's

- [x] read possible Plone version from PyPi in backend_addon / zope-setup
- [ ] extract the instance out into it's own template. Use it to create a single instance, with all features we currently have in zope-setup's instances: single instance, zeo server, client instances for ZEO and RelStorage. This template should bea able to create a ZEO server in the setup, a zeo client (instance1, instance2 aso), as well as single direct storage instance and relstorage clients (instance1, instance2 aso with relstorage backend).
- [ ] provide a docker compose setup and .devcontainer setup in zope-setup and backend_addon




## Goals

- [ ] the combination of zope-setup and backend_addon should be useful to create the same file structure as cookieplone does:
        backend  # backend_addon with a build-in zope setup
        frontend  # volto frontend

## Not yet implemented bobtemplates.plone subtemplates

Reference: https://github.com/plone/bobtemplates.plone/

Already implemented: `backend_addon` (≈addon), `behavior`, `content_type`, `restapi_service`, `upgrade_step` (plus Plone-specific `zope-setup`, `zope_instance`).

Rule: the generated output must stay as close as possible to the existing bobtemplates.plone structure — no structural deviations without explicit approval.

- [ ] **controlpanel** — Plone control panel (registry-based configuration UI)
- [ ] **form** — z3c.form based form
- [x] **indexer** — custom catalog indexer (`@indexer` decorator + ZCML)
- [ ] **mockup_pattern** — Mockup JS pattern integration
- [ ] **portlet** — classic Plone portlet
- [x] **subscriber** — event subscriber handler
- [ ] **svelte_app** — Svelte application integration
- [ ] **theme** — custom theme package
- [ ] **theme_barceloneta** — Barceloneta-based theme variant
- [ ] **theme_basic** — basic theme variant
- [ ] **view** — custom browser view
- [ ] **viewlet** — viewlet component
- [x] **vocabulary** — named vocabulary