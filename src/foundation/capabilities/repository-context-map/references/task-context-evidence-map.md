# bounded task context Evidence Map

Use this reference when repository context depends on generated graph evidence, a task bounded task context, source-vs-generated boundaries, affected validation, or placement/reuse decisions.

## Context Fields

| Field | Required Evidence | Limit |
| --- | --- | --- |
| Graph freshness | Graph path/hash, commit or mtime fallback, refresh action. | Stale graph is a selector only. |
| Graph slice | Symbol, import, reference, test, ownership, and generated-artifact edges. | No whole-repository dump. |
| Exact locator | User/AI/Brief/Review/log/search-result path, symbol, or owner. | Direct-read-first selector; never owner proof by precision alone. |
| Source of truth | Editable source files, registries, or scripts that own behavior. | Generated or installed files are impact surfaces unless explicitly source-owned. |
| Inspected files | Target, siblings, parent module, tests, docs, configs, validators, build scripts. | Unread files stay unknown. |
| Searches run | Pattern, path/glob, result, and absence evidence. | Search results do not prove behavior without source reads. |
| Plan inputs | Reuse candidates, rejected locations, placement constraints, validators, docs. | Planning input is not closure evidence. |

## Coupling Rules

1. Repository context feeds `implementation-structure-design` for placement and reuse.
2. Graph/test edges feed `targeted-validation-selection` and `quality-test-gate`.
3. Generated artifact edges feed source-vs-dist and build/install validation.
4. Locate unknown local owners with bounded current-source read/search; stale graph evidence does not prevent this fallback.
5. Stop discovery when current source establishes the source of truth, candidate owner, and change surface; remaining impact, placement, and implementation decisions belong to their existing owners.
6. Deepen analysis only for a concrete unresolved question that can change implementation, such as competing owners or a contradicted shared invariant.
7. Keep small locator corrections and directly resolvable questions within implementation.
8. Task and Review consume their assigned expertise without rerouting or loading a catalog.
9. If new evidence invalidates an important decision, revisit only that decision and its affected consumers; an optional Brief may record the result for cross-agent use.
10. Limit current-source claims to current repository facts rather than Desired Behavior, Acceptance, Non-goals, or target architecture.
11. Accept multiple necessary enforcement points when current source establishes their roles.
12. Choose structural, textual, registry, config, generated, dynamic, or FFI evidence by artifact effectiveness without imposing a fixed structural priority.
13. When structural or LSP capability is unavailable, fall back to bounded read/search.
14. Use complete structural/symbol results as locators and confirm the relevant current source.
15. Bounded correction discovery closes after the corrected-source read.
