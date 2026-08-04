---
name: refactoring
description: "`analysis-agent`/`review-agent`: use when splitting, merging, moving, or deleting code while preserving behavior; skip behavior-changing implementation."
---

# refactoring

## Registry Trigger

**Use when**

- Placement and ownership are already fixed, and code needs reshaping or movement while preserving behavior, tests, contracts, and boundaries.
- Large object/file split, merge, relocation, private-class move, or accepted deletion sequencing needs behavior-preservation proof.
- small file merge refactor merge or split import export preservation module split dead code deprecated API feature flag cleanup compatibility branch complexity evidence

**Do not use when**

- no task-local refactoring decision is required

## Skill Role

Consume the fixed destination from `implementation-structure-design` or `module-boundary-design`, then define observable-behavior boundaries, characterization proof, reversible movement, and rollback. Consume deletion readiness from `cleanup-deletion-governance`; exclude behavior change, existence, pattern, placement, and architecture redesign.

## High-Value Rules

- **Inventory observable behavior before movement.** Include public return and error semantics, side effects, persistence, events, configuration, metrics, logs used as contracts, timing or ordering guarantees, and consumed symbols relevant to the change.
- **Calibrate characterization to uncertainty and consequence.** Add focused pre-change evidence when behavior is weakly specified, incident-prone, stateful, concurrent, externally integrated, or consequential; record known defects rather than silently normalizing them.
- **Separate structural and intentional behavior change.** Keep changed semantics, bug fixes, contract migration, and cleanup policy independently visible with their own authority and proof.
- **Choose reviewable reversible steps.** Preserve a valid build and evidence boundary after each logical move, and separate renames, moves, extraction, rewiring, and deletion when combining them would hide causality.
- **Preserve dependency and ownership direction.** Check imports, initialization, lifecycle, visibility, generated boundaries, side-effect order, and state ownership so a cleaner file shape does not create a broader architectural dependency.
- **Honor accepted deletion readiness.** Consume `cleanup-deletion-governance` exit, residue, absence-proof, and recovery limits; verify that structural sequencing preserves them.
- **Compare before and after with limits.** Use task-relevant behavior, public-surface, dependency, and complexity evidence, and state what hidden consumers, production timing, or external environments remain unproved.

## Anti-Patterns

- Label a default, error, ordering, side effect, schema, metric, or public symbol change as refactoring.
- Combine broad movement and logic change into one diff that prevents causal review or safe rollback.
- Delete apparently unused code from local search alone while dynamic, generated, configured, persisted, or external consumers remain uninspected.

## Stop Conditions

Escalate unknown behavior, an unfixed destination, uncovered consequential paths, compatibility or concurrency shifts, unowned consumers, or structural sequences lacking reviewable reversal. Route unresolved existence to `minimal-correct-implementation`, placement to `implementation-structure-design` or `module-boundary-design`, and unfixed deletion readiness to `cleanup-deletion-governance`.

## Output Contract

- refactoring decision with preserved-behavior boundary, characterization evidence, reversible structural steps, dependency and ownership effects, accepted deletion decision and preservation evidence, rollback limits, and residual risks

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [behavior preservation evidence](references/behavior-preservation-evidence.md) | evidence-pattern | the change claims behavior preservation across a structural rewrite | the task intentionally changes externally observable behavior | review-agent, analysis-agent | evidence-record, proof-limit, residual-risk |
| [checklist](references/checklist.md) | decision-checklist | structural change affects observable behavior contracts ownership steps or rollback | simple local rename preserves behavior and all public boundaries | review-agent, analysis-agent | checklist-result, residual-risk |
| [split merge cleanup](references/split-merge-cleanup-patterns.md) | benchmark-pattern | the diff splits merges relocates responsibilities or must sequence an accepted deletion decision | deletion readiness is unresolved or no structural cleanup or ownership change is proposed | review-agent, analysis-agent | option-comparison, selected-approach |
