# Microservice Splitting Checklist

Use this reference after the main skill selects `microservice-splitting` for a concrete service extraction, service split, service merge, runtime boundary, or in-process-to-network-call decision.

## Split Force Scorecard

Score each force as `none`, `weak`, `credible`, or `hard constraint`.

| Force | Evidence that supports a split | Evidence that favors module boundary |
| --- | --- | --- |
| Business capability | Distinct bounded context and language. | Same domain rules and same change owner. |
| Team ownership | Separate team can own lifecycle and incidents. | Same team owns both sides. |
| Deploy cadence | One side needs independent release rhythm. | Changes still ship together. |
| Scaling | Different traffic, resource, or cost curve. | Same scale envelope and capacity plan. |
| Fault isolation | Failure must not cascade across boundary. | Failure modes remain coupled. |
| Compliance | Boundary reduces regulated scope or residency risk. | Same data classification and controls. |
| Latency | Extra network hop fits p95/p99 budget. | Hot path cannot absorb latency/jitter. |
| Cost/on-call | Operating model can absorb service count. | On-call, platform, and support cost dominate benefit. |

If no force is `hard constraint` and fewer than two are `credible`, prefer an in-process module boundary.

## Readiness Matrix

| Dimension | Block | Conditional | Ready evidence |
| --- | --- | --- | --- |
| Data ownership | Shared table/schema/FK or direct DB read. | Read replica, CDC, or dual-read without cutover proof. | Own schema/store and mediated reads through API/event. |
| Contract | No OpenAPI/proto/event schema. | Internal DTO/ORM shape exposed. | Versioned public contract with compatibility policy. |
| Consistency | Existing single transaction split across services. | Saga/outbox designed but untested. | Compensation/reconciliation/idempotency tested. |
| Failure handling | No timeout/circuit/degraded mode. | Timeout only. | Timeout, retry, circuit, bulkhead/degradation, alert. |
| Deployment | Requires lockstep release. | Separate stage in same pipeline. | Independent deploy and mixed-version compatibility. |
| Observability | No service-level telemetry. | Logs only. | Logs, metrics, traces, SLO, alerts, dashboards, runbook. |
| Contract tests | Manual integration only. | Consumer tests planned. | CDCT or equivalent in CI. |
| Ownership | No owner/on-call. | Owner named, no runbook. | Team, on-call, runbook, escalation, release owner. |

## Boundary And Contract Review

- Name what moves out, what stays, and what must remain in-process.
- Name current callers, future consumers, and unknown consumers.
- State public contract type: REST/OpenAPI, gRPC/proto, event schema, GraphQL, SDK, or internal-only deferral.
- Define versioning, deprecation, tolerant-reader behavior, and mixed-version window.
- Reject contracts that expose persistence or domain internals as public response shapes.
- Name compatibility validator: Pact/CDCT, schema compatibility check, generated client check, contract test, or explicit not-verified state.

## Data And Consistency Review

- Assign authoritative owner for every entity/aggregate/table/topic involved.
- Identify shared tables, shared schemas, read replicas, foreign keys, ORM model sharing, direct database reads, and reporting projections.
- Select migration pattern: strangler, expand-contract, CDC, dual-read, dual-write with reconciliation, backfill, or no data move.
- Define consistency strategy: synchronous owner API, Saga orchestration, Saga choreography, transactional outbox, inbox/dedup, eventual consistency with reconciliation, or keep in-process.
- For every Saga step, name compensation, idempotency key, retry class, terminal failure, and reconciliation owner.

## Failure And Performance Review

- For each new synchronous call, state timeout, retry budget, retryable errors, circuit threshold, fallback/degraded response, and user-visible impact.
- Check p95/p99 latency budget with the new hop, including network jitter and downstream saturation.
- For event flows, state ordering, duplication, replay, poison message, DLQ, lag alert, and backpressure behavior.
- Identify availability chain: caller SLO multiplied or bounded by callee SLO; lower-SLO callee requires fallback or async design.
- Name the smoke test, contract test, failure simulation, or not-verified residual risk.

## Migration, Rollback, And Release Review

- Prefer strangler, branch-by-abstraction, parallel run, or shadow traffic over big-bang cutover.
- Define phase gates: contract ready, data path ready, dual-run, read switch, write switch, old path freeze, old path retirement.
- Define traffic switch or feature flag owner and rollback trigger.
- Rollback scope covers route, data writes, event emissions, contract version, consumer config, and database migration/backfill.
- Name old/new compatibility and maximum deployment skew.
- Define retirement exit criteria so legacy and new paths do not run forever.

## Operability Review

- Name service owner, on-call rotation, runbook, escalation path, release owner, and dashboard owner.
- Define SLI/SLO, error budget, alert thresholds, and incident severity.
- Define logs, metrics, traces, correlation IDs, dependency metrics, queue lag, and business KPIs.
- Define secrets/config ownership, TLS/cert, network policy, service identity, capacity plan, and 12-month cost model.
- If the team cannot operate another service, reject or defer the split even if code boundaries look clean.

## Decision Outcomes

- `approved`: all blockers resolved, production readiness has evidence, rollout/rollback is credible.
- `approved-with-conditions`: architecture direction is sound, but named readiness gates block production.
- `deferred`: module/data/contract/observability work must happen before extraction.
- `rejected`: split force is weak or operational cost exceeds benefit; recommend module boundary repair.
- `merge recommended`: service independence never materialized or service cost exceeds isolation value.

## Evidence Limits

Rendered diagrams, ADRs, and source graph searches do not prove production traffic behavior, unknown consumers, real incident response, provider behavior, or data migration reversibility. State those limits in the assessment instead of approving the split from design evidence alone.
