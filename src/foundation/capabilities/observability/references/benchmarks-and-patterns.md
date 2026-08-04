# Observability Benchmarks And Patterns

Load this reference when a changed user path, service/dependency, resource, queue/job, SLI/alert, trace boundary or runbook needs an observable contract. Do not require every signal family for a path that does not traverse it.

## Signal Selection

| Surface | Signals that can answer current risk | Guardrail |
| --- | --- | --- |
| Request/user path | Rate, success/error class, latency/tail, saturation and user-visible outcome. | Prefer route/operation templates and bounded outcome labels. |
| Dependency/DB | Call/query rate, failure/timeout/circuit, latency, pool/lock/connection pressure. | Do not place raw URL/query/id/user/tenant in labels. |
| Host/runtime/resource | Utilization, saturation, errors, throttling, queue/pool and memory/GC/process health as applicable. | Treat USE/Golden Signals as selection aids; add panels that answer the named resource risk and operator action. |
| Queue/job/workflow | Enqueue/consume rate, age/lag/depth, in-flight, outcome/failure class, retry/DLQ/heartbeat/replay. | Depth without arrival/service rate and owner action is ambiguous. |
| Release/change | Version/config/flag/deployment identity and before/after health. | Correlation must not become high-cardinality labels. |

## SLI, Alert, Trace, And Runbook Contract

- Define SLI numerator/denominator or distribution, population/scope, data source/query, target, window, error-budget owner and exclusions from current product/SLO evidence. No fixed percentage/window/query in this reference is a default.
- Alerts name intent: urgent burn/user impact, capacity/dependency risk, dead-man/missing work, or ticket/backlog. Record threshold/source/window, owner, escalation, dedupe/silence and the safe action it enables.
- For a changed path that needs causal linking, propagate trace/correlation across the synchronous and asynchronous HTTP/RPC/DB/cache/queue/job boundaries it actually traverses; document external or unavailable boundaries and avoid unrelated propagation. Async work preserves causation/linking before its first log.
- Dashboard panels link user outcome to dependency/resource cause and current release identity; runbook names trigger, diagnosis queries, safe/unsafe actions, rollback/escalation and expected recovery signal.

## Freshness And Proof Limits

| Claim | Evidence | Limit |
| --- | --- | --- |
| Metric/log/trace exists | Current instrumentation plus query against the intended backend/schema. | Local emission does not prove ingestion, retention, permissions or panel correctness. |
| Cardinality/sampling safe | Representative label-value estimate and backend/provider limits. | Small fixtures do not expose production cardinality or rare-path loss. |
| Alert actionable | Rule/query evaluation or fixture maps to current owner/runbook action. | A syntactically valid rule does not prove paging quality or production threshold. |
| Path correlated | Trace/log test covers each changed synchronous/async boundary. | One trace does not prove all branches or tail sampling. |
| Freshness | Queries, panels, alerts, runbooks and owners follow final instrumentation/config edit. | Screenshots and prior task evidence can be stale. |

Route structured logging/redaction to `logging-error-handling`, SLO/incident architecture to `reliability-observability-gate`, budgets/capacity to `performance-budgeting`, and sensitive telemetry to `security-privacy-gate`.

Reject unbounded labels, averages-only latency, infrastructure-only dashboards for user risk, and alerts without owner/action. Also reject logs as a sole SLI and trace context dropped at async boundaries. Reject fixed burn thresholds copied without SLO evidence and local instrumentation reported as live-backend proof.
