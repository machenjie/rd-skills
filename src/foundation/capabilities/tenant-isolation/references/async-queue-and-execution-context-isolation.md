# Tenant Async, Queue, And Execution-Context Isolation

**Load when:** Tenant provenance crosses messages, jobs, callbacks, workers, retries, DLQs, replays, shared compute, temporary state, or execution-context boundaries.

**Do not load when:** No asynchronous or compute-context tenant boundary changes and current evidence covers derivation, propagation, reset, and terminal handling.

**Required by:** `analysis-agent`, `task-agent`, `review-agent`

**Required output:** `boundary-decision`, `validation-plan`, `proof-limit`

## One Decision

Select a tenant-context propagation and execution-isolation contract that fails closed across asynchronous ownership and reuse.

## Decision Matrix

| Boundary | Required decision | Failure signal |
|---|---|---|
| Authority | Trusted source, immutable tenant, conflict handling, freshness | Payload tenant replaces authenticated provenance |
| Envelope | Tenant, schema/version, producer trust, validation | Consumer accepts missing or forged tenant |
| Queue/topic | Shared/dedicated topology, routing, access, order, quota | Tenant reaches another tenant's entity |
| Job | Tenant-bound ID, initiator, dedupe, status, cancel, result | Status or result uses a global key |
| Consumer | Revalidate, install context, clean up, acknowledge, terminate | Reused worker retains prior tenant |
| Retry/replay | Preserve tenant, scope DLQ/quarantine, authorize selection | Replay changes tenant or bypasses isolation |
| Batch | Homogeneous scope or per-item scope and failure policy | Batch scope covers mixed tenants |
| Compute | Namespace, local cache, temp path, credentials, pool reset | Shared state crosses tenants |

## Verification

Select checks from affected matrix boundaries and supported topologies. Preserve missing, conflicting, forged, stale, and valid context cases for every affected tenant entry; absent brokers, job APIs, or deployment variants are not new implementation requirements.

- For message consumers, publish missing, conflicting, forged, stale, and valid tenant envelopes through the real consumer.
- Reuse affected workers, connections, callbacks, or temporary state across alternating tenants.
- Exercise applicable retry, DLQ, replay, cancellation, duplicate, and late-completion paths.
- For affected batch or job APIs, test mixed-tenant batches or identical job identifiers under two tenants.
- Verify each supported shared or dedicated queue/compute variant with its actual identities.

## Primary Sources

- [Azure messaging approaches for multitenant solutions](https://learn.microsoft.com/en-us/azure/architecture/guide/multitenant/approaches/messaging)
- [Azure compute approaches for multitenant solutions](https://learn.microsoft.com/en-us/azure/architecture/guide/multitenant/approaches/compute)
- [Azure tenant integration and data access approaches](https://learn.microsoft.com/en-us/azure/architecture/guide/multitenant/approaches/integration)
- [Kubernetes multi-tenancy](https://kubernetes.io/docs/concepts/security/multi-tenancy/)

Official platform pages were accessed on 2026-07-26.

## Proof Limits

Topology and namespaces do not prove context propagation, broker authorization, worker cleanup, or fairness. Tests prove only exercised producers, consumers, identities, retries, platforms, and resource configurations.

## Failure Evidence

- Async context loss uses no tenant or the prior tenant.
- If mixed-tenant items would share one tenant scope, reject the work as an isolation failure.
