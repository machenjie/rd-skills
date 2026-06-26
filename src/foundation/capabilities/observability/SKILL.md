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

# Stage Fit

Use during planning when user impact, SLI/SLO, signal ownership, telemetry privacy, or release-watch evidence is being decided. Use during implementation and code review when logs, metrics, traces, dashboards, alert rules, runbooks, correlation propagation, or metric labels change. Use during testing and release when validator commands, dashboard queries, synthetic events, alert-rule checks, project memory, repository graph, or prior incident evidence must prove observability is fresh enough to support rollout or incident response.

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

Anchor against Google SRE Four Golden Signals, SLI/SLO/error-budget practice, multi-window burn-rate alerting, OpenTelemetry logs/metrics/traces, W3C Trace Context, Prometheus label-cardinality discipline, RED/USE methods, dashboard and runbook ownership, NIST log-management integrity, and privacy-safe telemetry design. Keep the default body focused on routing, evidence, output, and gates; load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) when signal matrices, SLO templates, trace coverage, burn-rate examples, or validation checklists need detail.

# Selection Rules

Select this capability when: **production diagnosis, SLI/SLO definition, alert design, distributed tracing, or dashboard construction** is the primary concern. Route elsewhere when: **logging-error-handling** is primary (error taxonomy, exception mapping, sensitive data redaction rules, RFC 7807 response design); **performance-budgeting** is primary (defining latency and throughput thresholds for a specific change); **degradation-circuit-breaking** is primary (circuit breaker thresholds, fallback behavior, shed load strategy); **reliability-observability-gate** is primary (gate review of whether observability requirements are met for a change).

# Proactive Professional Triggers

- **Signal:** a new or changed endpoint, job, queue consumer, dependency, data pipeline, or critical user journey lacks an SLI/SLO, RED/USE metrics, dashboard, alert owner, or release-watch signal. **Hidden risk:** degradation is invisible until users report it, and rollback has no objective trigger. **Required professional action:** define user-impact SLI, signal inventory, dashboard owner, alert threshold, and watch/rollback evidence before handoff. **Route to:** `reliability-observability-gate`, `performance-budgeting`, `delivery-release-gate`. **Evidence required:** metric names, SLO target, dashboard/runbook owner, alert query or not-verified disclosure, and changed-path validation map.
- **Signal:** log fields, metric labels, span attributes, dashboard filters, or alert group-by dimensions include user ID, tenant ID, request ID, raw URL, email, token, error message, payload, or other unbounded/sensitive values. **Hidden risk:** telemetry cost/cardinality explosion, backend outage, privacy leak, or unusable queries during incidents. **Required professional action:** bound labels, move high-cardinality data to logs/traces, pseudonymize where needed, and exclude secrets/PII at the source. **Route to:** `logging-error-handling`, `security-privacy-gate`, `performance-budgeting`. **Evidence required:** approved field list, rejected fields, cardinality estimate, privacy/redaction decision, and validation query.
- **Signal:** trace or correlation context crosses HTTP, queue, job, database, cache, file, or external-provider boundaries without current source proof. **Hidden risk:** logs, metrics, and traces cannot join the incident path, especially across async handoff. **Required professional action:** inspect current ingress, outbound injection, message headers, job metadata, and logging context binding before accepting trace continuity. **Route to:** `repository-graph-analysis`, `logging-error-handling`, `message-queue-design`. **Evidence required:** boundary paths inspected, traceparent/correlation propagation point, sample trace/log lookup, and stale/not-verified limit.
- **Signal:** alert, dashboard, runbook, or dead-man switch is copied from project memory, old incident notes, generated docs, or repository graph without current query and owner confirmation. **Hidden risk:** stale observability says a system is safe while alerts page the wrong team, query deleted metrics, or miss the changed path. **Required professional action:** reconcile memory and graph against current source, telemetry names, runbook owner, and validator timing. **Route to:** `project-memory-governance`, `repository-context-map`, `execution-trajectory-analysis`, `validation-broker`. **Evidence required:** accepted/rejected memory, current metric/query path, owner freshness, command/output timestamp, and unknown signals.
- **Signal:** a failure mode is named but no metric/log/trace/dashboard/runbook path shows how an operator detects, diagnoses, and verifies it. **Hidden risk:** instrumentation exists as disconnected noise rather than an investigation workflow. **Required professional action:** build investigation paths from symptom to root-cause candidate and map each signal to validation evidence. **Route to:** `failure-contract-design`, `quality-test-gate`, `reliability-observability-gate`. **Evidence required:** failure-mode-to-signal map, synthetic event or query, alert test, dashboard path, runbook action, and evidence limits.

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

# Reference Loading Policy

The `SKILL.md` body carries L1/L2 routing, stage, trigger, and evidence rules. Load [references/checklist.md](references/checklist.md) when the change affects a production-facing path, SLO, alert, job, queue, external dependency, incident investigation path, or post-release validation. Load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) when detailed signal matrices, SLI/SLO examples, trace-span coverage, burn-rate alerting, graph/memory/trajectory coupling, or validation checklists are needed. Use [examples/example-output.md](examples/example-output.md) only when the final observability plan shape is unclear. Do not load references for local-only instrumentation in non-production code with no operator surface.

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
- `graph_memory_execution_validation` (repository graph, project memory, incident notes, generated docs, prior validation, dashboards, and runbooks accepted/rejected/stale/not verified)
- `changed_signal_to_validation_map` (each changed log, metric, span, label, alert, dashboard, runbook, SLO, synthetic event, and release-watch signal mapped to validator command, query, manual check, or residual risk)
- `validation_evidence` (commands, metric/log/trace queries, alert rule checks, dashboard paths, synthetic events, screenshots if relevant, exit codes/outcomes, and freshness after final edit)
- `evidence_limits` (what remains unproven about production cardinality, rare failure modes, incident actionability, historical baselines, sampling, or provider-specific telemetry)

# Evidence Contract

Close observability work only when the output includes:

- **Boundaries inspected**: user journey, service/API/job/queue/dependency boundary, dashboard, alert, runbook, owner, and privacy boundary inspected or explicitly ruled out.
- **Signal inventory**: structured log fields, metric names, trace spans, dashboard panels, alert expressions, and runbook links named.
- **Graph/memory/execution judgment**: repository graph, project memory, generated docs, incident notes, prior validations, and dashboard/runbook claims accepted, rejected, stale, or not verified.
- **Validation evidence**: metric query, log query, trace lookup, dashboard path, alert rule validation, synthetic event, local config check, or explicit not-verified disclosure.
- **What evidence proves**: which SLI/SLO, diagnostic path, alert path, trace correlation, or operator workflow is observable.
- **What evidence does not prove**: production-scale cardinality, rare failure paths, historical baseline accuracy, alert actionability under load, or incident-response effectiveness.
- **Residual risk**: remaining blind spot, alert owner, review date, and next gate such as `reliability-observability-gate` or `delivery-release-gate`.

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
11. Project memory, repository graph, generated docs, dashboards, runbooks, and prior validations are reconciled with current source/config/query evidence or marked stale/not verified.
12. Every changed observability signal maps to a fresh validator command, metric/log/trace query, alert rule check, synthetic event, manual review artifact, or explicit residual risk.

# Used By

- reliability-observability-gate
- backend-change-builder

# Handoff

Hand off to `logging-error-handling` for error taxonomy, exception mapping, and sensitive data redaction rules; `performance-budgeting` for latency and throughput threshold definition; `degradation-circuit-breaking` for circuit breaker threshold configuration and fallback signal design; `delivery-release-gate` for post-release validation using the defined observability signals.

# Completion Criteria

The capability is complete when **operators can detect user impact within minutes using defined SLI/SLO alerts, diagnose root cause by correlating logs/metrics/traces via propagated correlation IDs, validate that a change is behaving correctly by comparing against baselines on the North Star dashboard, and roll back with confidence using the defined observability evidence — without exposing sensitive data or generating false-positive alert noise**.
