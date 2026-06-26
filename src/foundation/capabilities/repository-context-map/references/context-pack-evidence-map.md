# Context Pack Evidence Map

Use this reference when repository context depends on generated graph evidence, a task context pack, source-vs-generated boundaries, affected validation, or placement/reuse decisions.

## Context Fields

| Field | Required Evidence | Limit |
| --- | --- | --- |
| Graph freshness | Graph path/hash, commit or mtime fallback, refresh action. | Stale graph is a selector only. |
| Graph slice | Symbol, import, reference, test, ownership, and generated-artifact edges. | No whole-repository dump. |
| Source of truth | Editable source files, registries, or scripts that own behavior. | Generated or installed files are impact surfaces unless explicitly source-owned. |
| Inspected files | Target, siblings, parent module, tests, docs, configs, validators, build scripts. | Unread files stay unknown. |
| Searches run | Pattern, path/glob, result, and absence evidence. | Search results do not prove behavior without source reads. |
| Plan inputs | Reuse candidates, rejected locations, placement constraints, validators, docs. | Planning input is not closure evidence. |

## Coupling Rules

1. Repository context feeds `implementation-structure-design` for placement and reuse.
2. Graph/test edges feed `validation-broker` and `quality-test-gate`.
3. Generated artifact edges feed source-vs-dist and build/install validation.
4. Unknown ownership or stale graph freshness blocks implementation planning or requires explicit fallback.
