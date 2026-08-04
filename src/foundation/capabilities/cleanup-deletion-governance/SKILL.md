---
name: cleanup-deletion-governance
description: "`analysis-agent`/`task-agent`/`review-agent`: use when deleting dead code, flags, fallbacks, compatibility, APIs, or generated remnants; skip when no cleanup decision exists."
---

# cleanup-deletion-governance

## Registry Trigger

**Use when**

- cleanup deletion governance deletion path dead code caller search runtime generated reflection references feature flag removal fallback expiry compatibility branch deprecated API expand contract cleanup telemetry unused rollback cleanup issue

**Do not use when**

- no task-local cleanup deletion governance decision is required

## Skill Role

Define deletion reachability, compatibility and state exit conditions, generated and operational residue, cleanup sequencing, rollback limits, and proof of absence. Exclude broad refactoring and contract migration.

## High-Value Rules

- **Name the deletion unit and exit condition.** Distinguish code, public contract, feature path, flag, fallback, data, configuration, metric, job, credential, or generated artifact and identify the evidence that permits removal.
- **Scan producers and consumers across mechanisms.** Inspect static references, dynamic loading, reflection, configuration, templates, generated code, scripts, plugins, persisted identifiers, queues, dashboards, alerts, and external consumers relevant to the surface.
- **Separate unreachable from unused in one sample.** Combine repository evidence with runtime, compatibility, ownership, or policy evidence appropriate to hidden and long-lived consumers; state where absence cannot be proved.
- **Respect state and mixed-version lifecycles.** Account for old records, queued work, cached values, rollback versions, staged rollout, dormant tenants, disaster recovery, and replay before deleting readers, writers, or bridges.
- **Order cleanup around ownership transfer.** Remove production, validation, observation, configuration, documentation, generated, and operational remnants without creating a period where no owner can interpret or recover the state.
- **Preserve a bounded recovery path.** Identify reversible steps, retained source or migration evidence, forward repair, and the point after which deleted data or external state cannot be restored.
- **Verify absence after mutation.** Re-run targeted scans, builds, contract checks, behavior tests, generated-output checks, and relevant runtime or telemetry queries, with explicit evidence freshness and limits.

## Anti-Patterns

- Delete from local text search alone while dynamic, generated, configured, persisted, or external consumption remains possible.
- Remove a flag or fallback while old state, rollback code, queued work, or dormant consumers still require it.
- Leave dead configuration, metrics, alerts, credentials, generated files, documentation, or operator paths after code deletion.

## Stop Conditions

Escalate unbounded consumption, unauthorized exit conditions, unreadable old or rollback state, irreversible deletion, governed data, or loss of the sole observation or recovery path.

## Output Contract

- deletion decision with bounded unit, consumer and state evidence, exit condition, ordered cleanup, rollback or forward-repair limits, post-mutation proof, and residual owners

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | Deletion, staging, conversion, or retention strategies remain viable | The artifact has an accepted removal lifecycle | review-agent, task-agent, analysis-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | Removal crosses public contracts, runtime registration, flags, or rollback | A private artifact has no reachable or generated consumers | review-agent, task-agent, analysis-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | Deletion safety depends on fresh callers, telemetry, or consumer evidence | No unused-or-safe-to-remove claim is being approved | review-agent, task-agent, analysis-agent | evidence-record, proof-limit, residual-risk |
