# Gap Analysis: copier-templates vs bobtemplates.plone

**Date:** 2026-04-12
**Scope:** Addon subtemplates — questions/variables, generated output, features

This document compares the modern copier-templates (this repository) with the
original [bobtemplates.plone](https://github.com/plone/bobtemplates.plone/) to
identify missing features that must be addressed for feature-completeness.

---

## Executive Summary

copier-templates already covers all 18 addon subtemplates that bobtemplates.plone
provides, plus adds new ones (svelte_app). It also brings significant
**improvements** over the original:

- **Automatic ZCML registration** (bobtemplates only generates `.example` files)
- **Automatic parent configure.zcml includes** via post-copy hooks
- **pyproject.toml subtemplate tracking** (`[tool.plone.backend_addon.settings.subtemplates]`)
- **Dynamic content-type interface discovery** (ContentTypeInterfacesHook in view template)
- **Dynamic Plone version fetching** from PyPI
- **Legacy migration support** (bobtemplate.cfg → modern structure)
- **Modern build backend** (hatchling instead of setuptools)

However, several feature gaps remain where bobtemplates.plone provides
functionality that copier-templates does not yet replicate.

---

## Gap 1: No Test Generation for Subtemplates (CRITICAL)

**Severity:** High — affects all subtemplates

bobtemplates.plone generates integration/functional test files for:
content_type, behavior, vocabulary, indexer, view, viewlet, form, portlet,
subscriber, upgrade_step.

copier-templates generates **zero** test files for any subtemplate.

### bobtemplates test coverage per subtemplate

| Subtemplate    | Test File                              | Tests Included                                        |
|----------------|----------------------------------------|-------------------------------------------------------|
| content_type   | test_ct_*.py + robot test              | FTI, schema, factory, adding, global_allow, filtering |
| behavior       | test_behavior_*.py                     | Behavior utility lookup, marker interface check       |
| vocabulary     | test_vocab_*.py                        | IVocabularyFactory, tokenized, term lookup            |
| indexer        | test_indexer_*.py                      | Integration + functional stubs                        |
| view           | test_view_*.py                         | View registration, interface check, functional        |
| viewlet        | test_viewlet_*.py                      | Manager registration, browser layer check             |
| form           | test_form_*.py                         | Form registration                                    |
| portlet        | test_portlet_*.py                      | Portlet type, renderer, add/edit forms                |
| subscriber     | test_subscriber_*.py                   | Integration + functional stubs                        |
| upgrade_step   | test_upgrade_step_*.py                 | Integration stub                                      |

### Action Required
Add test file templates to every addon subtemplate. Each should include at
minimum an integration test that verifies the component is properly registered.

---

## Gap 2: content_type — Limited Questions and FTI Features

**Severity:** High

### Missing Questions

| Question (bobtemplates)              | Default    | Status in copier   |
|--------------------------------------|------------|--------------------|
| `dexterity_type_icon_expr`           | "puzzle"   | Hard-coded to document_icon.png |
| `dexterity_type_supermodel`          | n          | Not available (always Python schema) |
| `dexterity_type_global_allow`        | y          | Hard-coded True    |
| `dexterity_parent_container_type_name` | (conditional) | Not available  |
| `dexterity_type_filter_content_types`| n          | Hard-coded True    |
| `dexterity_type_create_class`        | y          | Always creates class |
| `dexterity_type_activate_default_behaviors` | y   | Only 3 behaviors   |

### Missing FTI Behaviors

bobtemplates includes 11+ configurable behaviors; copier only includes 3:

**Present in copier:** `plone.dublincore`, `plone.excludefromnavigation`, `plone.namefromtitle`

**Missing from copier:**
- `plone.basic`
- `plone.allowdiscussion`
- `plone.shortname`
- `plone.ownership`
- `plone.publication`
- `plone.categorization`
- `plone.locking`
- `plone.textindexer`
- `plone.relateditems`
- `plone.versioning`
- Container-specific: `plone.constraintypes`, `plone.nextprevioustoggle`,
  `plone.nextpreviousenabled`, `plone.navigationroot`

### Missing Files

- `profiles/default/registry/plone.displayed_types.*.xml` — Adds content type
  to the navigation displayed types list

### Action Required
- Add `global_allow` question (boolean, default true)
- Add `filter_content_types` question (conditional on Container base)
- Add `content_type_icon` question (string, default "puzzle")
- Add `activate_default_behaviors` question (boolean, default true) that
  controls the full behavior list in the FTI XML
- Generate `plone.displayed_types` registry XML
- Add more field examples in the schema (commented out)

---

## Gap 3: vocabulary — Missing StaticCatalogVocabulary Option

**Severity:** Medium

bobtemplates has an `is_static_catalog_vocab` toggle that switches between
`SimpleTerm` and `StaticCatalogVocabulary` implementations.

copier-templates always generates the `SimpleTerm` version.

### Action Required
Add `vocabulary_type` choice (simple / catalog) and conditionally generate
the appropriate implementation.

---

## Gap 4: subscriber — Missing Browser Layer Check

**Severity:** Medium

bobtemplates subscriber handler includes a guard that exits early if the
add-on's browser layer is not active:

```python
if not IBrowserLayer.providedBy(getRequest()):
    return
```

copier-templates omits this check.

### Action Required
Add browser layer guard to the generated handler function.

---

## Gap 5: upgrade_step — Missing Helper and GS Profile Registration

**Severity:** Medium

### Missing base.py helper
bobtemplates generates `upgrades/base.py` with a `reload_gs_profile()` utility
function. copier-templates does not.

### Missing ZCML features
bobtemplates ZCML includes:
- `<gs:registerProfile>` for per-version profile directory
- `<gs:upgradeDepends>` that imports the registered profile

copier-templates only generates `<genericsetup:upgradeStep>` — no profile
registration or import dependency.

### Action Required
- Generate `upgrades/base.py` with `reload_gs_profile()` helper
- Add `<gs:registerProfile>` for the version directory in upgrade ZCML
- Add `<gs:upgradeDepends>` for profile import

---

## Gap 6: site_initialization — Missing available_languages

**Severity:** Low

bobtemplates sets both `available_languages` and `default_language` in the
ILanguageSchema registry XML. copier-templates only sets `default_language`.

### Action Required
Add `available_languages` element list to the ILanguageSchema registry XML.

---

## Gap 7: restapi_service — Missing IExpandableElement Pattern

**Severity:** Low-Medium

bobtemplates generates both an `IExpandableElement` adapter and a `Service`
class. The expandable element pattern is a standard plone.restapi extension
mechanism for enriching existing endpoints.

copier-templates only generates a `Service` with `IPublishTraverse`.

### Action Required
Add an `expandable` boolean question. When true, generate the
`IExpandableElement` adapter alongside the service class.

---

## Gap 8: view — Missing Marker Interface

**Severity:** Low

bobtemplates generates a marker interface (`IMyView`) alongside the view
class. copier-templates does not.

### Action Required
Consider adding optional marker interface generation (boolean toggle).

---

## Gap 9: controlpanel — Missing plone.restapi Adapter

**Severity:** Low

bobtemplates generates a `RegistryConfigletPanel` adapter that integrates
the control panel with plone.restapi. copier-templates only generates the
browser page registration.

### Action Required
Add the restapi adapter to the controlpanel template output.

---

## Gaps NOT Being Addressed (By Design)

These are intentional differences where copier-templates takes a better
modern approach:

| Feature | bobtemplates | copier-templates | Reason to keep copier approach |
|---------|-------------|-----------------|-------------------------------|
| ZCML registration | Manual (.example files) | Automatic (post-copy hooks) | Better DX |
| Build backend | setuptools | hatchling | Modern standard |
| Plone versions | Static list | Dynamic from PyPI | Always current |
| Theme build | Sass + PostCSS | webpack | More flexible |
| Robot tests | Generated | Not generated | Robot is being phased out |
| Buildout template | Present | Absent | Buildout is legacy |
| Weather portlet example | Specific example | Generic scaffold | More reusable |

---

## Template Coverage Matrix (Updated 2026-04-12)

| Subtemplate         | bob | copier | Tests | Questions | Output | Notes |
|---------------------|-----|--------|-------|-----------|--------|-------|
| content_type        | ✅  | ✅     | ✅    | ✅         | ✅     | FIXED: FTI behaviors, icon, global_allow, registry XML |
| behavior            | ✅  | ✅     | ✅    | ✅ Better  | ✅     | copier has marker/factory toggles |
| vocabulary          | ✅  | ✅     | ✅    | ✅         | ✅     | FIXED: Added StaticCatalogVocabulary option |
| indexer             | ✅  | ✅     | ✅    | ✅         | ✅     | |
| view                | ✅  | ✅     | ✅    | ✅ Better  | ✅     | Dynamic interface discovery |
| viewlet             | ✅  | ✅     | ✅    | ✅ Better  | ✅     | copier asks for manager |
| form                | ✅  | ✅     | ✅    | ✅         | ✅     | |
| portlet             | ✅  | ✅     | ✅    | ✅         | ✅     | |
| restapi_service     | ✅  | ✅     | ✅    | ✅         | ✅     | FIXED: Added IExpandableElement option |
| subscriber          | ✅  | ✅     | ✅    | ✅ Better  | ✅     | FIXED: Added browser layer guard |
| controlpanel        | ✅  | ✅     | ✅    | ✅         | ⚠️     | Missing restapi adapter (low priority) |
| upgrade_step        | ✅  | ✅     | ✅    | ✅ Better  | ✅     | FIXED: Added base.py, GS profile registration |
| site_initialization | ✅  | ✅     | ✅ Neither | ✅    | ✅     | FIXED: Added available_languages |
| theme               | ✅  | ✅     | ✅ Neither | ✅    | ✅     | Different build approach |
| theme_basic         | ✅  | ✅     | ✅ Neither | ✅    | ✅     | |
| theme_barceloneta   | ✅  | ✅     | ✅ Neither | ✅    | ✅     | |
| mockup_pattern      | ✅  | ✅     | ✅ Neither | ✅    | ✅     | |
| svelte_app          | ✅  | ✅     | ✅ Neither | ✅    | ✅     | |

**Legend:** ✅ Complete | ⚠️ Partial/Missing features | ❌ Not present
