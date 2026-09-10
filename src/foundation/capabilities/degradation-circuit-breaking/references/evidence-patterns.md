# Degradation Circuit Breaking Evidence Patterns

Use this evidence map for a named degradation claim whose freshness, execution evidence, permission boundary, or proof limit remains open; it is not a second resilience catalog.

## Degradation-To-Validation Map

| Claim | Minimum current evidence | Proves / limit |
| --- | --- | --- |
| Criticality | Caller/dependency, protected flow, fail-open/closed decision, required approval. | Named flow only; not unseen callers, tenants, or fallbacks. |
| Dependency phase timeouts beneath ceilings | Current gateway/local ceiling, allocation, phase config/code, cancellation/cleanup test. | Inspected path only; not future topology or provider tail. |
| Retry bounded | Attempt/backoff/jitter config, idempotency/outcome classes, amplification calculation, fault result. | Named outcomes/load; not every provider failure or traffic mix. |
| Circuit recovery safe | Signal/window/threshold, open/probe/close config, transition test, recovery metric. | Named transition; not production recovery timing. |
| Fallback truthful/safe | Source, freshness/quality, tenant/permission, degraded marker, invalidation, owner, negative test. | Inspected fallback; not future data, policy, or callers. |
| Isolation/shedding bounded | Pool/queue/concurrency limits, admission/priority rule, saturation test, cleanup. | Inspected resource; not scheduler or all workloads. |
| Evidence fresh | Final-source test/drill/dashboard/report, timestamp and claim mapping. | Named decision; not live provider, all regions, or later edits. |

## Freshness And Tool Boundaries

- Treat repository inspection, prior task evidence, incidents, dashboards, and validation as discovery until current source and fresh evidence confirm them.
- Reopen after changes to ceiling inputs, calls, timeout/retry/circuit settings, fallback, flags, pools, metrics, dashboards, tests, reports, or build outputs.
- Map each final claim to current command/test/report/dashboard/owner evidence or record not-run residual risk.
- Fault injection, load/chaos, circuit toggles, flags, and kill switches require environment, permission, stop, rollback/disable, owner, and redaction.
- Production telemetry stays read-only or approved-connector-scoped with sensitive labels aggregated/redacted.
