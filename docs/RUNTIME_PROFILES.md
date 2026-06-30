# Runtime Profiles

ChangeForge has three runtime profiles. All profiles are generated from authoring source under `src/` into `dist/`.

## Recommended

Use for global installs.

Top-level runtime skills:

- 21 professional skills.

References:

- 134 foundation capabilities are compiled into relevant professional skill references under `references/capabilities/`.
- Compiled references are selectively loaded according to each professional skill's `Reference Loading Policy`; they are not loaded wholesale by default.
- The router includes the domain extension index.

Recommended does not install the 134 foundation capabilities as top-level skills.

Top-level count: 21.

## Full

Use for project installs where domain-specific routing should be visible as top-level skills.

Top-level runtime skills:

- 21 professional skills.
- 7 domain extensions.

References:

- 134 foundation capabilities are compiled into relevant professional skill references and selectively loaded according to each professional skill's `Reference Loading Policy`.

Full does not install the 134 foundation capabilities as top-level skills.

Top-level count: 28.

## Dev

Use only for ChangeForge development and debugging.

Top-level runtime skills:

- 21 professional skills.
- 134 foundation capabilities.
- 7 domain extensions.

Top-level count: 162.

References:

- Professional skills still receive compiled capability references and selectively load them according to each professional skill's `Reference Loading Policy`.
- The router includes routing rules, the skill registry, the capability index, and the domain extension index.

## Generated Router References

Every profile generates these router files:

- `change-forge-router/references/routing-rules.md`
- `change-forge-router/references/skill-registry.md`
- `change-forge-router/references/capability-index.md`
- `change-forge-router/references/domain-extension-index.md`

No profile emits raw registry files, raw `src/` content, personal asset mappings, or `toolbox-mapping.md`.

No profile emits telemetry. Runtime telemetry is an operational fact log written to the user cache (`${XDG_CACHE_HOME:-~/.cache}/changeforge/telemetry/`) by the optional hook runtime; it is never part of a built profile, never installed into `dist/`, and never treated as runtime skill content. See [TELEMETRY.md](TELEMETRY.md).

## Reference Loading

`SKILL.md` is loaded when a skill is selected. Compiled `references/` are targeted support, not automatic context. The router selects capabilities, professional skills read only selected capability references, and L1/L2/L3/L4/L5 policy determines whether indexes, checklists, and domain extension references are required.

Language capabilities are professional engineering rules, not language tutorials or personal technical asset mappings.
