# Observability Benchmarks And Patterns

Load for a named signal, SLI, alert, correlation, dashboard, or runbook decision on a changed path. Select only families traversed by that path.

## Signal Selection

| Surface | Decision-bearing signals | Guardrail |
| --- | --- | --- |
| Request/user path | Rate, outcome/error, tail latency, saturation, visible result. | Bounded route/operation/outcome labels. |
| Dependency/store | Calls/queries, failure/timeout/circuit, latency, pool/lock/connection pressure. | No raw URL/query/id/user/tenant labels. |
| Host/runtime/resource | Applicable utilization, saturation, errors, throttling, queue/pool, memory/GC/process health. | Add only panels answering the named risk/action. |
| Queue/job/workflow | Enqueue/consume, age/lag/depth, in-flight, outcome, retry/DLQ/heartbeat/replay. | Depth needs arrival/service context and owner action. |
| Release/change | Version/config/flag/deploy identity and before/after health. | Avoid high-cardinality correlation labels. |

## Operating Contract

- Define SLI formula/distribution, population, source/query, target/window, budget owner, and exclusions from current objective evidence; no fixed value is a default.
- Define each alert’s intent, threshold/source/window, owner/escalation, dedupe/silence, and safe action from objective, traffic, failure duration, budget semantics, and maturity.
- Propagate correlation across only the synchronous/asynchronous boundaries needed for causal linking; preserve async causation before its first log and disclose unavailable/external boundaries.
- Link dashboard user outcome to dependency/resource cause and release identity; bind runbook trigger, diagnosis, safe/unsafe action, rollback/escalation, and recovery signal.

## Proof Limits

| Claim | Current evidence | Limit |
| --- | --- | --- |
| Signal exists | Instrumentation plus intended backend/schema query. | Not ingestion, retention, permissions, or panels. |
| Cardinality/sampling safe | Representative values and backend/provider limits. | Not production skew or rare loss. |
| Alert actionable | Rule/query evaluation mapped to owner/runbook action. | Not paging quality or production threshold. |
| Path correlated | Test across each changed sync/async boundary. | Not every branch or tail sampling. |
| Fresh | Final instrumentation/config plus current queries, panels, alerts, runbooks, owners. | Not later edits. |

Route log/redaction to `logging-error-handling`, objectives/incidents to `reliability-observability-gate`, capacity to `performance-budgeting`, and sensitive telemetry to `security-privacy-gate`. Reject unbounded labels, averages-only latency, infrastructure-only user-risk dashboards, actionless alerts, logs-only SLI, dropped async context, copied burn thresholds, and local emission claimed as live proof.
