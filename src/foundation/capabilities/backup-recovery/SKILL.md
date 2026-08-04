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

Define the recoverable-state inventory, restore contract, dependency order, validation boundary, and proof limits. Exclude data-conversion rollback and release sequencing.

## High-Value Rules

- Define the recoverable product state, not just a storage resource. Its inventory names authoritative data, files, keys, configuration, offsets, identity state, compatible versions, derived rebuilds, and dependencies that agree after restore.
- Derive recovery-point and recovery-time objectives from the named failure consequence, recovery unit, dependency chain, current scale, and accountable risk owner.
- Do not inject universal recovery tiers, cadence, or retention periods.
- Tie each recovery claim to an identifiable backup or log source, capture point, schema and key lineage, restore target, and validator. Backup-job success or artifact existence alone does not establish restorability.
- Preserve consistency across dependency order and crash boundaries. The recovery contract defines quiesce, checkpoint, replay, reconciliation, and duplicate or missing side-effect behavior when components cannot be captured atomically.
- Select isolation, immutability, encryption, deletion protection, and credential separation from the actual operator, corruption, provider, or attacker failure model. A replicated copy in the same failure boundary may repeat the loss.
- Validate restored state through domain invariants and a representative business read/write or reconciliation path. The exercise record states its scale, environment, dependency, key, region, and wall-clock proof limits.
- Align retention, key history, legal hold, erasure, expiry, and late replay so retained data remains decryptable and policy-compliant without silently resurrecting deleted state. Assign drift and re-exercise triggers after material change.

## Anti-Patterns

- Treating snapshot freshness, replication, or a successful restore command as proof that the product is usable.
- Restoring a database while omitting objects, keys, configuration, queue position, identity state, or compatible code.
- Prescribing one copy topology, rehearsal cadence, runbook form, approval chain, or recovery objective for unrelated consequences.
- Claiming production-scale, cross-region, or incident-time recovery from a small local exercise.

## Stop Conditions

- Escalate when authoritative state, key history, restore order, destructive-operation recovery, policy ownership, or a material dependency is unknown and could make restored state unusable or unsafe.

## Output Contract

- Return a recoverable-state decision: state objectives, artifact lineage, dependency order, restore validation, evidence limits, and residual owner

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | Recovery unit objectives capture consistency failure isolation or dependency order choices remain open | Root rules and current failure evidence select one bounded restore contract | task-agent, review-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | Recovery spans several authoritative derived key config queue identity retention or replay boundaries | No protected state restore semantic or recovery-readiness claim changes | task-agent, review-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | Artifact lineage restore objective dependency validation or exercise-freshness claims need current proof | Current scoped restore and reconciliation evidence closes the accepted recovery claim | task-agent, review-agent | evidence-record, proof-limit, residual-risk |
