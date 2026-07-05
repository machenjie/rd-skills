# Observability Benchmarks And Patterns

Use this reference when `observability` needs more depth than the main `SKILL.md` can carry efficiently. Keep the main body focused on routing, evidence, output, and gates; use this file for signal matrices, SLI/SLO templates, trace-span coverage, burn-rate alerting, dashboard patterns, graph/memory/trajectory coupling, and validation checklists.
## Benchmark Anchors

- **Google SRE Book and Workbook:** Four Golden Signals, SLI/SLO/error-budget practice, symptom-based alerting, and multi-window multi-burn-rate alerts.
- **OpenTelemetry:** vendor-neutral logs, metrics, traces, semantic conventions, resource attributes, baggage, sampling, and collector pipelines.
- **W3C Trace Context:** `traceparent` propagation across HTTP, queues, jobs, and outbound dependency calls.
- **Prometheus and Alertmanager:** counters, gauges, histograms, bounded labels, recording rules, alert inhibition, and burn-rate alerts.
- **RED and USE methods:** service rate/errors/duration plus resource utilization/saturation/errors.
- **Grafana/Loki/Jaeger/Tempo/Zipkin/X-Ray:** dashboard, log query, and trace investigation paths.
- **Elastic Common Schema and OpenTelemetry log model:** consistent field names for errors, requests, users, resources, and traces.
- **NIST SP 800-92 and privacy-by-design:** log integrity, retention, access control, and exclusion of sensitive data.
## Observability Signal Matrix

| Layer | Latency | Traffic / Rate | Errors | Saturation |
| --- | --- | --- | --- | --- |
| HTTP API | `p99(http_request_duration_seconds)` | `rate(http_requests_total[5m])` | `rate(http_requests_total{status=~"5.."}[5m])` | connection pool utilization |
| Background job | `p99(job_duration_seconds)` | `rate(job_executions_total[5m])` | `rate(job_failures_total[5m])` | worker pool utilization |
| Queue consumer | event-to-commit latency | messages consumed per second | `rate(consumer_errors_total[5m])` | consumer lag and oldest message age |
| Database | `p99(db_query_duration_seconds)` | `rate(db_queries_total[5m])` | `rate(db_errors_total[5m])` | active/max pool and wait time |
| External dependency | `p99(external_call_duration_seconds)` | `rate(external_calls_total[5m])` | error rate by provider/status class | circuit state and pool saturation |
| Frontend browser | LCP, INP, CLS, long task duration | page loads and interactions | JS error rate | long task count and resource timing |
## SLI/SLO Template

```yaml
service: orders-api
journey: place-order
sli:
  name: order_api_availability
  formula: |
    rate(http_requests_total{route="/orders",status!~"5.."}[28d])
    / rate(http_requests_total{route="/orders"}[28d])
slo:
  target: 99.5%
  window: 28d
error_budget: 0.5%
alerts:
  - name: fast_burn
    condition: burn_rate > 14 for 1h
    severity: page
  - name: slow_burn
    condition: burn_rate > 6 for 6h
    severity: ticket_or_page_by_service_tier
dashboard: orders-slo
runbook: orders-api-high-error-rate
owner: orders-oncall
```

## Trace And Correlation Coverage

Required boundaries:

- HTTP ingress extracts or creates `traceparent` and binds `trace_id` / `span_id` to logs.
- Application service spans use stable names such as `OrderService.createOrder`.
- Database spans use stable operation names and bounded attributes such as `db.system`, `db.name`, and query name.
- Outbound HTTP/gRPC calls inject `traceparent` and record provider, operation, status class, retry, timeout, and circuit state.
- Queue publishes inject `traceparent` into message headers or attributes, not only payload.
- Queue consumers extract trace context before business logic and link worker spans to producer context.
- Scheduled jobs create a job root span with job name, run id, attempt, and owner.

Anti-patterns:

- span names include raw IDs, full URLs, user names, emails, or request-specific values;
- async worker logs have a different trace from the request that enqueued the job;
- metric labels duplicate trace-only dimensions such as request id, user id, or payload hash;
- spans are emitted but no dashboard or trace query can find the changed path.

## Alert And Dashboard Patterns

| Pattern | Use when | Evidence |
| --- | --- | --- |
| SLO burn-rate page | Critical user journey has an SLO. | Alert query, burn-rate math, on-call owner, runbook action. |
| Ticket alert | Slow degradation or non-critical job issue. | Threshold, owner queue, remediation deadline. |
| Dead-man switch | Scheduled job, pipeline, or heartbeat may fail silently. | Last-success metric, freshness threshold, synthetic miss test. |
| North Star dashboard | Service has user-facing impact. | First panel is SLI/SLO burn or success rate, not CPU/memory. |
| Dependency panel | External provider or database can dominate latency/error. | Per-provider latency/error, circuit state, retry count. |
| Release watch panel | Canary, rollout, or feature flag changes behavior. | Before/after baseline, rollback threshold, watch owner. |

## Graph, Memory, And Trajectory Coupling

| Input | Accept when | Reject or downgrade when |
| --- | --- | --- |
| Repository graph | Current routes, jobs, producers, consumers, dependencies, and signal emitters are inspected. | Graph proximity is used as proof that telemetry covers the changed path. |
| Project memory | Incident, dashboard, SLO, or runbook has timestamp, owner, and unchanged path. | Memory predates route, schema, metric, dashboard, or ownership changes. |
| Execution trajectory | Validator/query output is after the final material edit and names the changed signal. | Output is stale, partial, from another environment, or lacks exit/outcome. |
| Dashboard/runbook | Query, panel, owner, and remediation action are current. | Link exists but query no longer returns data or owner is unknown. |
| Generated docs | Generated metric or trace docs match current source and build artifacts. | Docs are generated before the final edit or from a different profile. |

## Validation Checklist

- run or name a validator command for changed source/config where telemetry is emitted;
- execute or inspect at least one metric query for changed metrics;
- execute or inspect at least one log query for changed structured fields and redaction;
- execute or inspect at least one trace lookup for changed cross-boundary flows;
- validate alert expressions syntactically and against a sample or synthetic event when feasible;
- confirm dashboard panels reference current metric names and bounded labels;
- confirm runbook owner, severity, and action are current;
- mark production-scale cardinality, sampling behavior, provider outages, and rare incident paths as residual risk when not verified.
