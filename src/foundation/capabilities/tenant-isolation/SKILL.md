---
name: tenant-isolation
description: "Use for cross-layer tenant isolation. Skip policy-only and SaaS-product lifecycle work."
---

# tenant-isolation

## Registry Trigger

**Use when**

- A tenant boundary crosses data, compute, async, derived, operational, or lifecycle surfaces.
- Shared resources need cross-layer proof.

**Do not use when**

- Route policy-only changes to `permission-boundary-modeling`.
- Treat SaaS lifecycle, billing, entitlements, customization, and control-plane product lifecycle as a deferred or unsupported Domain candidate. Retain only a proven tenant-isolation subproblem and escalate unresolved lifecycle ownership to `engineering-change-analysis`; do not select a nonexistent Domain Skill.

## Skill Role

Select cross-layer tenant isolation from trusted context; permission policy remains with its owner.

## High-Value Rules

- Map active tenant surfaces to trusted context, isolation mechanisms, and pre-effect enforcement.
- Preserve tenant provenance across asynchronous work and keep reused execution tenant-clean.
- Preserve per-tenant attribution for privileged operations and lifecycle effects.
- Prove same-tenant success and wrong-tenant, forged, mixed-batch, privileged, deletion, and recovery failures.

## Anti-Patterns

- Local success substituted for evidence of the tenant isolation contract.

## Execution Checklist

- Map stores, caches, objects, indexes, queues, jobs, compute, telemetry, tools, exports, deletion, backups, and restores.
- Inspect queries, policies, keys, paths, envelopes, workers, dashboards, and privileged configurations.
- Exercise wrong-tenant, missing-context, forged-key, mixed-batch, replay, admin, delete, and restore cases at enforcement.

## Stop Conditions

- Stop on unknown tenant authority, scope, provenance, privileged bypass, or deletion/restore owner.
- Keep authorization policy with its owner; escalate unsupported SaaS lifecycle ownership to `engineering-change-analysis`.

## Output Contract

- tenant-isolation decision with context authority surfaces mechanisms privileged lifecycle negative proof limits and residual owners

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [data storage cache and search isolation](references/data-storage-cache-and-search-isolation.md) | targeted | Database key query cache object or search-index isolation remains unresolved | No stored cached object or indexed tenant boundary changes | analysis-agent, task-agent, review-agent | boundary-decision, validation-plan, residual-risk |
| [async queue and execution context isolation](references/async-queue-and-execution-context-isolation.md) | targeted | Tenant provenance crosses messages jobs callbacks workers retries replays or shared compute | No asynchronous or compute-context tenant boundary changes | analysis-agent, task-agent, review-agent | boundary-decision, validation-plan, proof-limit |
| [operations telemetry and lifecycle isolation](references/operations-telemetry-and-lifecycle-isolation.md) | targeted | Admin support telemetry migration backfill export deletion restore or control-plane paths change | No privileged operational or tenant lifecycle data path changes | analysis-agent, task-agent, review-agent | boundary-decision, validation-plan, residual-risk |
