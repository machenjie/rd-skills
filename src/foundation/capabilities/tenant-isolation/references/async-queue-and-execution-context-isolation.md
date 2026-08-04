# Tenant Async, Queue, And Execution-Context Isolation

**Load when:** Tenant provenance crosses messages, jobs, callbacks, workers, retries, DLQs, replays, shared compute, temporary state, or execution-context boundaries.

**Do not load when:** No asynchronous or compute-context tenant boundary changes and current evidence proves context derivation, propagation, reset, and terminal handling.

**Required by:** `analysis-agent`, `task-agent`, `review-agent`

**Required output:** `boundary-decision`, `validation-plan`, `proof-limit`

## One Decision

Select one tenant-context propagation and execution-isolation contract that fails closed across asynchronous ownership and reuse.

## Decision Matrix

| Boundary | Required isolation decision | Failure signal |
|---|---|---|
| Context authority | Trusted source, immutable internal representation, conflict handling, and freshness | Payload tenant field replaces authenticated provenance |
| Message envelope | Tenant identity, schema/version, producer authority, signature or broker trust, and validation | Consumer accepts a missing or forged tenant |
| Queue or topic | Shared/dedicated topology, tenant routing, access, ordering, quotas, and metrics | One tenant can publish to or consume another tenant's entity |
| Job record | Tenant-bound identity, initiator, dedupe key, status lookup, cancellation, and result location | Job status or result is keyed globally |
| Consumer | Revalidation, context installation, cleanup, acknowledgement, and terminal outcome | Reused worker retains the previous tenant |
| Retry and replay | Tenant-preserving identity, DLQ/quarantine scope, operator selection, and late behavior | Replay changes tenant or bypasses current isolation |
| Batch | Homogeneous-tenant requirement or per-item scope, partitioning, failure, and continuation | One batch-level tenant is applied to mixed items |
| Compute state | Worker/pod/namespace choice, local cache, temp path, credentials, pool reset, and resource bounds | Shared scratch, credentials, or memory crosses tenants |

## Verification

- Publish missing, conflicting, forged, stale, and valid tenant envelopes through the real consumer.
- Reuse worker, connection, callback, and temporary-state owners across alternating tenants.
- Exercise retries, DLQ inspection, replay, cancellation, duplicate delivery, and late completion.
- Submit mixed-tenant batches and identical job identifiers under two tenants.
- Verify shared and dedicated queue or compute variants with their actual access identities.

## Primary Sources

- [Azure messaging approaches for multitenant solutions](https://learn.microsoft.com/en-us/azure/architecture/guide/multitenant/approaches/messaging)
- [Azure compute approaches for multitenant solutions](https://learn.microsoft.com/en-us/azure/architecture/guide/multitenant/approaches/compute)
- [Azure tenant integration and data access approaches](https://learn.microsoft.com/en-us/azure/architecture/guide/multitenant/approaches/integration)
- [Kubernetes multi-tenancy](https://kubernetes.io/docs/concepts/security/multi-tenancy/)

Official platform pages were accessed on 2026-07-26.

## Proof Limits

Topology and namespace choices do not prove application context propagation, broker authorization, worker cleanup, or tenant fairness. Tests prove only the exercised producers, consumers, identities, retries, platforms, and shared-resource configurations.
