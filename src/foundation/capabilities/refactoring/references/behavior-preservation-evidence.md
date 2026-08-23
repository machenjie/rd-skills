# Behavior Preservation Evidence

- **Inventory observable behavior before movement.** Include public return and error semantics, side effects, persistence, events, configuration, metrics, logs used as contracts, timing or ordering guarantees, and consumed symbols relevant to the change.

Use this reference when refactor closure depends on behavior equivalence, repository inspection freshness, prior task evidence, generated artifacts, observable action sequence, validation freshness, tool permission boundaries, or evidence limits. Keep the `SKILL.md` body as the routing surface; use this file for the deeper evidence map.

## Behavior Evidence Matrix

| Preservation claim | Minimum evidence | What it proves | What it does not prove |
| --- | --- | --- | --- |
| Outputs are unchanged | Characterization or public-behavior tests with before/after command output and exit code. | Covered inputs still produce the same caller-visible result. | Uncovered branches, hidden consumers, timing, or external side effects are equivalent. |
| Side effects are unchanged | Event, DB mutation, file write, queue publish, cache, log, or metric assertions at the public boundary. | Inspected side effects have the same shape, ordering, and target. | Downstream consumers or production-only integrations are safe unless inspected. |
| Public contract is preserved | Import/export diff, schema/generated-client diff, API snapshot, config key list, or event payload comparison. | The inspected contract surface did not drift. | Unknown external consumers, stale generated clients, or undocumented contracts are compatible. |
| Dependency direction is preserved | repository inspection search, import graph, architecture rule, or cycle check after movement. | Inspected modules still follow declared layer direction. | Runtime reflection, plugin loading, or generated imports are safe without direct checks. |
| Prior claim is current | Prior note, incident note, or handoff claim accepted/rejected against current source and registry. | The selected memory is a valid selector for this refactor. | A prior note alone proves semantic behavior or all runtime callers. |
| Execution evidence is fresh | Validator command, exit code, report path, generated artifact diff, and final-edit ordering. | Validation occurred after the material refactor edits it claims to cover. | Later edits, skipped validators, or environment-only paths are covered. |
| Tool boundary is safe enough | Tool/action class, sandbox, approval policy, write radius, redaction rule, and rollback note. | The inspected command class and output retention were bounded. | Command semantics are correct or destructive rollback was executed unless separately proven. |

## Current Evidence And Freshness

- Treat prior task evidence, prior review notes, old validation reports, generated references, and graph output as selectors until current source confirms them.
- Accept a prior claim only when current files, registry entries, tests, generated artifacts, or owner evidence still match it.
- Reject or downgrade memory when it is undated, ownerless, predates generated/source changes, conflicts with current graph, or names no executable validator.
- Refresh the repository inspection after file moves, import/export edits, generated barrel changes, reflection/dynamic dispatch hints, registry changes, or cleanup deletions.
- Mark validation stale when source, tests, fixtures, configs, generated artifacts, reports, build output, or install output changed after the validator ran.
- Record observable action sequence when command order affects evidence: characterization before movement, formatter separate from movement, validators after final material edit, build/install after generated outputs.
- Preserve a direct-source fallback when graph tooling, generated references, or memory cannot prove current behavior.

## Closure Template

```markdown
## Result

## Preserved Behavior and Intentional Exclusions

## Searched Paths and Dynamic or Generated Edges

## Characterization and Final-edit Validation Order

## Commands, Results, and Proof Limits

## Unverified Scope

## Residual Risk and Recommended Next Step
```

## Anti-Patterns

- Reject behavior changes labeled refactoring, causally hidden broad moves, and local-search-only deletion.
