# Foundation Capability Library

Foundation Skills are focused source assets for ChangeForge Professional Skills. They capture reusable expert judgment for one concrete engineering decision at a time.

The library contains 150 implemented Foundation Skills plus `_template`. They are not language primers, framework walkthroughs, tool catalogs, or independently selected task owners. Selected entries are compiled into Professional Skill references for the `recommended` and `full` build profiles.

Language capabilities are professional engineering rules, not language tutorials or personal technical asset mappings.

## Build Profile Rules

- `recommended`: compile foundation capabilities into professional skill `references/`.
- `full`: compile foundation capabilities into professional skill `references/`.
- `dev`: may expose foundation capabilities as top-level skills for authoring and debugging.

## Authoring Rules

- Keep every capability professional and decision-oriented.
- Treat each capability as a reusable card used by one or more professional skills.
- Keep implementation-specific examples out unless they demonstrate an output contract.
- Store capability source under `src/foundation/capabilities/`.
- Keep generated built content under `dist/`.

## Registry

The canonical list is `src/registry/foundation-skills.yaml`. Registry entries must point to authored Foundation Skill folders.
