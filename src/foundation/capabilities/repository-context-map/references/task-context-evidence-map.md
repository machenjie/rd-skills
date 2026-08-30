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
4. Unknown ownership or stale graph freshness blocks implementation planning or requires explicit fallback.
5. Stop after current source confirms the relevant owner/change role; keep locator correction local to a same-owner/route/contract mismatch.
6. Without an accepted Brief, return a material owner/placement/contract contradiction through Main for initial Analysis.
7. Return a current-source contradiction of an accepted Brief's protected decision through Main for bounded Delta.
8. Task and Review keep their fixed route.
9. Brief revision authority remains with Main through Analysis.
10. Limit current-source claims to current repository facts rather than Desired Behavior, Acceptance, Non-goals, or target architecture.
11. Accept multiple necessary enforcement points when current source establishes their roles.
12. Choose structural, textual, registry, config, generated, dynamic, or FFI evidence by artifact effectiveness without imposing a fixed structural priority.
13. When structural or LSP capability is unavailable, fall back to bounded read/search.
14. A declared, non-truncated structural/symbol capability may perform one bounded same-owner locator correction.
15. Bounded correction discovery closes after the corrected-source read.
