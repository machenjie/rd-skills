# Runtime Profiles

ChangeForge has three runtime profiles. All profiles are generated from authoring source under `src/` into `dist/`.

## Recommended

Use for global installs.

Top-level runtime skills:

- 19 professional skills.

References:

- 82 foundation capabilities are compiled into relevant professional skill references under `references/capabilities/`.
- The router includes the domain extension index.

Recommended does not install the 82 foundation capabilities as top-level skills.

## Full

Use for project installs where domain-specific routing should be visible as top-level skills.

Top-level runtime skills:

- 19 professional skills.
- 7 domain extensions.

References:

- 82 foundation capabilities are compiled into relevant professional skill references.

Full does not install the 82 foundation capabilities as top-level skills.

## Dev

Use only for ChangeForge development and debugging.

Top-level runtime skills:

- 19 professional skills.
- 82 foundation capabilities.
- 7 domain extensions.

References:

- Professional skills still receive compiled capability references.
- The router includes routing rules, the skill registry, the capability index, and the domain extension index.

## Generated Router References

Every profile generates these router files:

- `change-forge-router/references/routing-rules.md`
- `change-forge-router/references/skill-registry.md`
- `change-forge-router/references/capability-index.md`
- `change-forge-router/references/domain-extension-index.md`

No profile emits raw registry files, raw `src/` content, personal asset mappings, or `toolbox-mapping.md`.
