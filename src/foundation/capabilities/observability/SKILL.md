---
name: observability
description: Designs production-facing logs, metrics, traces, alerts, dashboards, correlation IDs, and privacy-safe diagnostic signals.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "69"
changeforge_version: 0.1.0
---

# Mission

Make **production behavior diagnosable, measurable, and alertable** through privacy-safe, correlated signals — logs, metrics, traces, and alerts — that connect user-visible impact to system-level root cause, enabling operators to detect, investigate, remediate, and validate changes without exposing sensitive data or generating alert noise.

# When To Use

Use this capability when a production-facing change: affects user-visible flows (checkout, login, search, data mutation); adds or modifies APIs, background jobs, data pipelines, or scheduled work; introduces new failure modes, degradation paths, or circuit breakers; has an SLO or error budget commitment; changes infrastructure, deployment topology, or capacity; or is flagged in post-incident review as "we couldn't tell what happened" or "our alerts didn't fire."

# Do Not Use When

Do not use this capability to: log sensitive payloads, PII, secrets, or credentials into any log sink (use `logging-error-handling` for sensitive data redaction rules); create dashboard metrics that do not have alert owners or thresholds; replace correct error handling and testing; or add observability for dead code paths that will never execute in production.

# Non-Negotiable Rules

- **Every production-facing change requires: structured logs, relevant metrics, distributed trace spans, and at least one alert — or an explicit rationale for why each is unnecessary.** "We'll add observability later" has historically been false. Observability must be designed before release, not after the first incident.
- **Correlation IDs / W3C `traceparent` must propagate across all system boundaries.** Every HTTP request, queue message, scheduled job trigger, and outbound external call must carry trace context so log events and spans from different services / workers can be joined. Without this, incident investigation requires manual timestamp correlation across systems — typically impossible under production pressure.
- **Logs must be structured JSON with approved field schema; sensitive fields must be excluded at the call site.** Never log: passwords, tokens, session IDs, full card numbers (PCI DSS Req 3.4), SSNs, private keys. Field-level redaction in a log pipeline is a fallback — the primary control is not passing sensitive data to the logger.
- **Metrics must cover the four golden signals where applicable: Latency, Traffic (Request Rate), Errors (Error Rate), and Saturation (Resource Utilization).** For every user-facing endpoint: `http_request_duration_seconds` histogram (P50/P95/P99), `http_requests_total` counter by method/route/status, `http_errors_total` counter by error type. For background jobs: `job_duration_seconds`, `job_success_total`, `job_failure_total`. For queues: `consumer_lag`, `dlq_depth`.
- **Alerts must be actionable, owned, threshold-based, and linked to a runbook.** An alert that fires with no defined remediation action trains engineers to ignore it. Every alert must specify: condition and threshold, owner (team or rotation), severity (page vs ticket), and runbook link. Alert noise must be reviewed quarterly — any alert with < 50% action rate should be tuned or removed.
- **SLI/SLO definitions must be agreed before the change ships.** SLI: the metric that measures whether the service is meeting its target (e.g., "percentage of API requests completing in < 500ms"). SLO: the target (e.g., "99.5% of requests in 28-day rolling window"). Error budget: `1 - SLO` of production traffic can be spent on failures. Every critical user flow must have at least one SLI/SLO pair.
- **Trace spans must be created at every significant boundary.** HTTP ingress, outbound HTTP call, queue publish, queue consume, database query (named queries), external API call, background job processing. Span name must be stable and human-readable (not auto-generated from URL parameters). Trace must be searchable by correlation ID, error status, and service name.
- **Dashboard must show user impact, not only infrastructure health.** An infrastructure dashboard showing CPU at 40% and disk at 60% does not tell an operator whether users are experiencing errors. A user-impact dashboard shows: request success rate, P99 latency, error rate by type, active user count, and SLO burn rate. Infrastructure signals support the user-impact signals — they are not a substitute.

# Industry Benchmarks

Anchor against: **Google SRE Book (Beyer et al., 2016)** — Four Golden Signals (Latency, Traffic, Errors, Saturation); SLI/SLO/Error Budget framework; alerting on symptoms, not causes. **OpenTelemetry (CNCF)** — unified observability framework: traces, metrics, logs; `OTel SDK` + `OTel Collector` + backends; `traceparent` propagation; semantic conventions for HTTP, DB, messaging. **W3C Trace Context (traceparent)** — distributed tracing header standard; `00-{traceId}-{spanId}-{flags}`. **Prometheus data model** — `Counter`, `Gauge`, `Histogram`, `Summary`; label cardinality discipline; `histogram_quantile(0.99, ...)` for P99 latency. **Grafana / Grafana Loki** — dashboard best practices; USE method (Utilization, Saturation, Errors) for infrastructure; RED method (Rate, Errors, Duration) for services; structured log queries with label filters. **Jaeger / Zipkin / AWS X-Ray** — distributed trace visualization; root span identification; service dependency map. **Elastic Common Schema (ECS)** — standardized log field names: `http.request.method`, `error.message`, `user.id`; enables cross-service log queries. **NIST SP 800-92** — log management; retention (90 days online / 1 year archive baseline); log integrity. **Alertmanager best practices (Robustness Principle)** — alert on symptoms (user-facing error rate elevated) rather than causes (CPU high); inhibition rules to suppress downstream alerts when upstream is alerting; dead-man's switch for critical pipelines.

### Observability Signal Matrix (Four Signals per Layer)

| Layer | Latency | Traffic / Rate | Errors | Saturation |
| --- | --- | --- | --- | --- |
| HTTP API | `p99(http_request_duration_seconds)` | `rate(http_requests_total[5m])` | `rate(http_requests_total{status=~"5.."}[5m])` | Connection pool utilization |
| Background Job | `p99(job_duration_seconds)` | `rate(job_executions_total[5m])` | `rate(job_failures_total[5m])` | Worker thread utilization |
| Queue Consumer | Consumer processing latency (end-to-end) | Messages consumed/sec | `rate(consumer_errors_total[5m])` | Consumer lag (messages behind) |
| Database | `p99(db_query_duration_seconds)` | `rate(db_queries_total[5m])` | `rate(db_errors_total[5m])` | Connection pool active/max |
| External Dependency | `p99(external_call_duration_seconds)` | `rate(external_calls_total[5m])` | `rate(external_call_errors_total[5m])` by partner | Circuit breaker state |
| Frontend (browser) | Core Web Vitals (LCP, INP, CLS) | Page loads / session starts | JS error rate (`window.onerror`) | Long task count |

### SLI/SLO Definition Template

```
Service: orders-api
User Journey: Place Order

SLI:
  Name: Order API Availability
  Definition: Percentage of HTTP POST /orders requests completing
              with status 2xx or 4xx (user error), NOT 5xx
  Measurement: rate(http_requests_total{route="/orders",status!~"5.."}[28d])
             / rate(http_requests_total{route="/orders"}[28d])

SLO: 99.5% over 28-day rolling window
Error Budget: 0.5% of requests may fail (= ~3.5 hours of 100% error rate / 28 days)

Alert: SLO burn rate > 2× for 1 hour → PagerDuty → oncall
Alert: SLO burn rate > 10× for 5 minutes → PagerDuty CRITICAL → oncall + manager

Dashboard: https://grafana.internal/d/orders-slo
Runbook: https://wiki.internal/runbooks/orders-api-high-error-rate
```

### Distributed Trace Span Coverage

```
Mandatory span boundaries:
  ┌─────────────────────────────────────────────────────┐
  │ HTTP Server (root span)                             │
  │   traceparent: 00-{traceId}-{spanId}-01             │
  │                                                     │
  │  ├── Application Service (child span)               │
  │  │    name: "OrderService.createOrder"              │
  │  │                                                  │
  │  │   ├── Database Query (child span)                │
  │  │   │    name: "db.query orders.insert"            │
  │  │   │    attributes: db.system, db.name, db.operation
  │  │   │                                              │
  │  │   ├── External HTTP Call (child span)            │
  │  │        name: "HTTP POST payment-service/charges" │
  │  │        propagate traceparent in outbound headers  │
  │  │                                                  │
  │  └── Queue Publish (child span)                     │
  │       name: "messaging publish order.created"       │
  │       inject traceparent into message header        │
  └─────────────────────────────────────────────────────┘

Queue Consumer side:
  ├── Extract traceparent from message header
  ├── Create new root span linked to producer span
  └── All log statements within consumer carry traceId

Anti-patterns:
  ❌ span name = "/api/v1/orders/o-{orderId}" (high-cardinality → breaks trace aggregation)
  ❌ No outbound traceparent header → separate traces for request + downstream calls
  ❌ Span created but never closed (resource leak in long-running processes)
```

# Selection Rules

Select this capability when: **production diagnosis, SLI/SLO definition, alert design, distributed tracing, or dashboard construction** is the primary concern. Route elsewhere when: **logging-error-handling** is primary (error taxonomy, exception mapping, sensitive data redaction rules, RFC 7807 response design); **performance-budgeting** is primary (defining latency and throughput thresholds for a specific change); **degradation-circuit-breaking** is primary (circuit breaker thresholds, fallback behavior, shed load strategy); **reliability-observability-gate** is primary (gate review of whether observability requirements are met for a change).

# Risk Escalation Rules

Escalate when: a change affects a user flow covered by an SLO and the SLI metric may become inaccurate; an alert threshold is being changed without reviewing current burn rate and error budget; observability for a critical flow (auth, payments, checkout, data mutation) is absent and the change ships without it; sensitive data (PII, PAN, PHI) may be logged without redaction; a new external dependency is added without timeout, error rate, and latency metrics; or a job or pipeline runs without a dead-man's switch alert (i.e., no alert fires if the job stops running entirely).

# Critical Details

- **High-cardinality metric labels cause metrics backend OOM.** Prometheus / Grafana Mimir / Thanos will degrade or crash if label cardinality explodes. Never use `userId`, `orderId`, `requestId`, `sessionId`, or any unbounded value as a metric label. Use labels for bounded, categorical dimensions only: `status_code` (200/400/500), `method` (GET/POST), `service_name`, `environment`, `region`. High-cardinality lookups belong in traces and logs, not metrics.
- **Dead-man's switch alerts detect silent failures.** A cron job that fails to start does not generate an error metric — it generates silence. A dead-man's switch alert fires when an expected event (heartbeat, job completion metric, health check) does not arrive within a window. Every scheduled job must emit a `job_last_success_timestamp` gauge. Alert: `time() - job_last_success_timestamp{job="daily-report"} > 86400` = report job missed last run.
- **p99 vs p95 for SLO measurement.** p50 (median) hides tail latency affecting 50% of users. p95 is a common SLO anchor: 95th percentile requests complete within threshold. p99 is appropriate for critical flows where even 1% of users experiencing slow checkout is unacceptable. p999 is used for financial or payment flows. Always expose and alert on percentiles — mean latency is misleading under skewed distributions.
- **Dashboard "North Star" metric must be user-facing.** The first panel in any service dashboard must be a user-facing signal (request success rate, P99 latency, SLO burn rate) — not CPU or memory. Operators arriving during an incident must immediately see whether users are affected before diagnosing infrastructure causes.

### Anti-examples

| Anti-pattern | Problem | Fix |
| --- | --- | --- |
| Metric label: `user_id={userId}` | Unbounded cardinality; metrics backend OOM; Prometheus refuses to ingest | Remove userId from metric labels; use trace/log for user-level lookups |
| Alert: "CPU > 80%" with no runbook | Noisy; CPU > 80% may not indicate user impact; no action defined | Alert on symptom: error rate > SLO threshold; link to runbook |
| Dashboard shows only CPU/memory | Infrastructure metrics; no user-impact visibility during incident | Add "North Star" panel: request success rate + P99 latency |
| Span name = `/api/v1/users/{userId}` | High-cardinality span name; trace aggregation broken | Span name = `HTTP GET /api/v1/users/:id` (stable, parameterized) |
| No dead-man's switch for nightly billing job | Job silently stops running; no alert fires; billing gap discovered 2 weeks later | Add `billing_job_last_success_timestamp` gauge; alert if > 25 hours old |
| Sensitive field `ssn` logged in `DEBUG` mode | Production sometimes runs with DEBUG enabled; SSN appears in log aggregation | Never pass SSN to logger; excluded at call site, not filtered downstream |

# Failure Modes

- Service deployed without latency histogram — first incident reveals P99 latency is 8 seconds; no historical data to determine when regression was introduced.
- Alert fires for `http_error_rate > 1%` with no owner assigned — alert silenced by everyone on-call; real 3% error rate runs undetected for 48 hours.
- `traceId` not propagated from HTTP handler to queue consumer — payment confirmed at HTTP layer; fulfillment failure in queue consumer; no trace link between them; root cause takes 6 hours to diagnose.
- Metric label includes `tenantId` (10,000+ tenants) — Prometheus cardinality explosion; metrics backend crashes; all dashboards return `no data` during incident.
- Background job fails silently for 3 days — no error metric, no dead-man's switch alert — data inconsistency discovered only in customer complaint.
- Dashboard shows infrastructure is healthy (CPU 30%, memory 40%) while 15% of user requests are failing — no user-facing SLI panel; engineers spend 30 minutes diagnosing infrastructure before checking application error rate.
- Log volume triples after adding debug-level request body logging — log storage costs exceed monthly budget; ops disables all logging for the service; production goes dark.

# Output Contract

Return an observability plan with:

- `sli_slo_definitions` (per user journey: SLI name, SLI formula, SLO target, error budget, measurement window)
- `structured_log_schema` (fields: timestamp, level, service, correlationId, traceId, spanId, message, error.*; excluded fields list)
- `metrics` (per signal × layer: metric name, type [counter/histogram/gauge], labels [bounded only], alert thresholds)
- `trace_spans` (per boundary: span name [stable], attributes [OTel semantic conventions], traceparent propagation points)
- `alert_definitions` (per alert: condition, threshold, severity, owner, runbook URL, inhibition rules)
- `dashboards` (North Star panel: user-facing SLI; supporting panels: error breakdown, latency percentiles, saturation, dependency health)
- `dead_man_switches` (per scheduled job/pipeline: heartbeat metric name, alert threshold)
- `correlation_context` (W3C traceparent propagation: inbound extraction, outbound injection, queue message header, job metadata)
- `privacy_review` (fields audited for PII/PAN/PHI; confirmed excluded from logs and traces; encryption in transit for telemetry)
- `cardinality_review` (metric labels audited for bounded cardinality; high-cardinality fields moved to traces/logs)
- `investigation_paths` (for each failure mode: which metrics/logs/traces reveal it; runbook reference)

# Quality Gate

The plan is complete only when:

1. SLI/SLO defined for every critical user journey; error budget and burn rate alert configured.
2. Four golden signals instrumented (Latency, Traffic, Errors, Saturation) for every HTTP endpoint and background job.
3. Distributed trace spans present at every system boundary; span names are stable (no high-cardinality URL parameters).
4. W3C `traceparent` propagated on all outbound HTTP calls and queue message headers.
5. All metric labels audited for bounded cardinality (no userId, orderId, or other unbounded values as labels).
6. Every alert has an owner, threshold, severity, and runbook link.
7. Dashboard North Star panel shows user-facing SLI/SLO burn rate — not just infrastructure.
8. Dead-man's switch configured for every scheduled job and critical pipeline.
9. Sensitive field exclusion confirmed — no PII/PAN/credentials in any log or trace attribute.
10. Investigation paths documented: for each known failure mode, which signal reveals it.

# Used By

- reliability-observability-gate
- backend-change-builder

# Handoff

Hand off to `logging-error-handling` for error taxonomy, exception mapping, and sensitive data redaction rules; `performance-budgeting` for latency and throughput threshold definition; `degradation-circuit-breaking` for circuit breaker threshold configuration and fallback signal design; `delivery-release-gate` for post-release validation using the defined observability signals.

# Completion Criteria

The capability is complete when **operators can detect user impact within minutes using defined SLI/SLO alerts, diagnose root cause by correlating logs/metrics/traces via propagated correlation IDs, validate that a change is behaving correctly by comparing against baselines on the North Star dashboard, and roll back with confidence using the defined observability evidence — without exposing sensitive data or generating false-positive alert noise**.

# Completion Criteria

The capability is complete when production-facing behavior has actionable, correlated, privacy-safe observability from release through incident response.
