---
name: backup-recovery
description: "`task-agent`/`review-agent`: use when protected state, restore objectives, dependency order, or recovery evidence changes; skip backup-job-only work with no recovery decision."
---

# backup-recovery

## Registry Trigger

**Use when**

- define recoverable state restore objectives dependency order failure coverage and current recovery proof

**Do not use when**

- work changes backup job mechanics without changing protected scope restore semantics or a recovery-readiness claim

## Skill Role

Own recoverable state, objectives, artifact lineage, restore order, validation, and proof limits.

## High-Value Rules

- Define authoritative and dependent state for the named recovery unit.
- Derive recovery objectives from consequence, scope, scale, dependencies, and owner.
- Map artifacts to capture, key/schema lineage, target, and restore order.
- For the named recovery, validate restored invariants.
- For the named recovery, reconcile side effects.
- Preserve policy alignment across retention, erasure, replay, drift, and re-exercise.

## Anti-Patterns

- Artifact existence substituted for usable recovery evidence.

## Stop Conditions

Stop when the named restore could produce unsafe state without an owned recovery proof.

## Output Contract

- Return a recoverable-state decision: state objectives, artifact lineage, dependency order, restore validation, evidence limits, and residual owner

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | Recovery unit objectives capture consistency failure isolation or dependency order choices remain open | Root rules and current failure evidence select one bounded restore contract | task-agent, review-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | Recovery spans several authoritative derived key config queue identity retention or replay boundaries | No protected state restore semantic or recovery-readiness claim changes | task-agent, review-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | Artifact lineage restore objective dependency validation or exercise-freshness claims need current proof | Current scoped restore and reconciliation evidence closes the accepted recovery claim | task-agent, review-agent | evidence-record, proof-limit, residual-risk |
