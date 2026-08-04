---
name: tenant-isolation
description: "Use when tenant isolation spans data, caches, queues, runtime, search, telemetry, deletion, or export. Skip policy-only authorization, billing, customization, and SaaS lifecycle."
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

Compose cross-layer isolation mechanisms and proof; consume, but do not redefine, trusted context or permissions.

## High-Value Rules

- Derive tenant context at a trusted entry and reject tenant fields that are claims rather than authority.
- Choose dedicated, partitioned, or shared isolation and bind tenant identity into keys, relationships, paths, caches, indexes, and derivatives.
- Enforce tenant scope before reads and writes, including owner, superuser, service, and policy-bypass paths.
- Define cache keys and invalidation with tenant, permission/freshness variant, and schema while rejecting global fallback.
- Preserve immutable provenance through messages, jobs, retries, DLQs, replays, and callbacks, failing closed on conflict or absence.
- Isolate reused workers, connections, sessions, buffers, and temporary storage by clearing prior tenant state.
- Define admin, support, telemetry, control-plane, migration, export, deletion, and restore scope with attributable per-tenant outcomes.
- Prove same-tenant success, wrong-tenant denial, forged keys, mixed batches, privileged paths, deletion, and recovery.

## Anti-Patterns

- Missing tenant predicate exposes another tenant's row.
- Attacker-controlled tenant key selects another tenant.
- Cache key collision returns another tenant's value.
- Async context loss uses no tenant or the previous tenant.
- Shared admin or support tooling bypasses isolation.
- Mixed-tenant batch or migration applies one scope to all items.
- Delete or restore leaks or resurrects another tenant's data.
- Telemetry exposes cross-tenant data.

## Execution Checklist

- Map stores, caches, objects, indexes, queues, jobs, compute, telemetry, tools, exports, deletion, backups, and restores.
- Inspect queries, policies, keys, paths, envelopes, workers, dashboards, and privileged configurations.
- Exercise wrong-tenant, missing-context, forged-key, mixed-batch, replay, admin, delete, and restore cases at enforcement.

## Stop Conditions

- Stop on unknown tenant authority, unscoped data, context loss, privileged bypass, or unowned deletion and restore.
- Stop shared mechanisms without cross-tenant and mixed-tenant evidence.
- Route authorization policy to its owner. For SaaS product lifecycle without an installed Domain owner, retain only proven isolation work and escalate the unresolved lifecycle boundary to `engineering-change-analysis`.

## Output Contract

- tenant-isolation decision with context authority surfaces mechanisms privileged lifecycle negative proof limits and residual owners

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [data storage cache and search isolation](references/data-storage-cache-and-search-isolation.md) | targeted | Database key query cache object or search-index isolation remains unresolved | No stored cached object or indexed tenant boundary changes | analysis-agent, task-agent, review-agent | boundary-decision, validation-plan, residual-risk |
| [async queue and execution context isolation](references/async-queue-and-execution-context-isolation.md) | targeted | Tenant provenance crosses messages jobs callbacks workers retries replays or shared compute | No asynchronous or compute-context tenant boundary changes | analysis-agent, task-agent, review-agent | boundary-decision, validation-plan, proof-limit |
| [operations telemetry and lifecycle isolation](references/operations-telemetry-and-lifecycle-isolation.md) | targeted | Admin support telemetry migration backfill export deletion restore or control-plane paths change | No privileged operational or tenant lifecycle data path changes | analysis-agent, task-agent, review-agent | boundary-decision, validation-plan, residual-risk |
