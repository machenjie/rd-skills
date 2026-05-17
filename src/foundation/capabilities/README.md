# Foundation Capability Library

Foundation capabilities are mandatory source assets for ChangeForge professional skills. They capture reusable expert judgment for product-change engineering: selection rules, risk gates, benchmark expectations, output contracts, and handoff criteria.

The library contains 100 implemented capabilities plus `_template`. Capabilities are not language primers, framework walkthroughs, tool catalogs, or source-installable runtime skills. They are compiled into professional skill references for the `recommended` and `full` runtime profiles.

Language capabilities are professional engineering rules, not language tutorials or personal technical asset mappings.

## Runtime Profile Rules

- `recommended`: compile foundation capabilities into professional skill `references/`.
- `full`: compile foundation capabilities into professional skill `references/`.
- `dev`: may expose foundation capabilities as top-level skills for authoring and debugging.

## Authoring Rules

- Keep every capability professional and decision-oriented.
- Treat each capability as a reusable card used by one or more professional skills.
- Keep implementation-specific examples out unless they demonstrate an output contract.
- Store capability source under `src/foundation/capabilities/`.
- Keep generated runtime content under `dist/`.

## Registry

The canonical capability list is `src/registry/capabilities.yaml`. Implemented registry entries must point to authored capability folders.
