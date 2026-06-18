---
name: reliability-observability-gate
description: Defines reliability and observability expectations for changes, including SLI/SLO impact, performance and cost budgets, capacity planning, profiling, concurrency, rate limits, circuit breakers, fallback, logs, metrics, traces, alerts, incident readiness, backup, and recovery.
license: MIT
changeforge_kind: professional-skill
changeforge_version: 0.1.0
---

# Reliability Observability Gate

## Mission
Ensure every production-bound change has explicit reliability expectations, observable behavior, bounded failure modes, proportional alerting, and tested recovery paths — so that degradation is detected before users report it, incidents are diagnosed in minutes not hours, and rollback is executable without guesswork.

## When To Use
- Any change that modifies a production service's latency, throughput, error rate, or resource consumption.
- Async processing changes: background jobs, queues, event processing, scheduled tasks.
- Changes that depend on external services, caches, queues, or databases on the critical user path.
- New or modified SLI/SLO targets, error budgets, or availability commitments.
- Infrastructure and configuration changes that affect service capacity or resource limits.
- Cloud cost, FinOps, autoscaling, reservation, egress, storage growth, or capacity forecast changes.
- Database migrations, reindexing, or data processing that affects production query performance.
- Incident response tooling, runbook, alerting rule, or on-call routing changes.
- Changes that introduce or modify circuit breakers, rate limiters, throttling, or fallback behavior.
- Agent-assisted reliability investigation or incident closure that needs verified cause, metric evidence, and residual-risk statement.

## Do Not Use When
- The change is a static documentation edit or cosmetic UI change with zero runtime behavior impact.
- The change is a test-only addition with no production deployment.

## Stage Fit
Launched for debugging-diagnosis and release-delivery production-risk review. Per-stage focus:
- **debugging-diagnosis**: SLI/SLO signals, logs/metrics/traces, and error-budget burn to locate degradation.
- **release-delivery**: performance and capacity budgets, alerts, rollback signals, and recovery readiness.

## Non-Negotiable Rules
- **Direct use still runs the runtime prompt flow.** When `reliability-observability-gate` is invoked directly and router reclassification is skipped, target-project engineering work must still clarify requirements before action, inspect relevant code/tests/config/docs before planning, name a TDD or validation signal before implementation, map each action to an owner skill and a different review skill, repair and re-review findings, and hand off with validation evidence, residual risk, and route/stage manifests when routed.
- **Every user-facing path must have an SLI**: if there is no measurable signal, there is no way to detect degradation before users report it.
- **SLOs must be defined before the feature ships**: an SLO added after an incident is a post-hoc measurement, not a reliability commitment.
- **Error budgets must be tracked and acted on**: when the error budget is exhausted, feature development stops until reliability is restored — this is the SRE error budget policy.
- **Unbounded queues are a reliability anti-pattern**: every queue must have a defined capacity limit, DLQ routing, and backpressure mechanism — an unbounded queue will OOM the consumer.
- **Alerts must page on user-impacting signals, not on noisy technical metrics**: alert on SLO burn rate (multi-window, multi-burn-rate), not on CPU percentage or error count thresholds that fire during non-impacting spikes.
- **Structured logging is required for production services**: unstructured log lines are unsearchable at scale; every log event must have `timestamp`, `level`, `service`, `trace_id`, and a consistent JSON schema.
- **Trace context must propagate across service boundaries**: a trace that terminates at the first service boundary cannot diagnose cross-service latency issues.
- **Recovery plans must be tested before they are needed**: a runbook that has never been executed will fail under incident pressure — conduct game days or chaos engineering exercises.
- **Cardinality limits on metric labels**: high-cardinality labels (user_id, request_id, URL path with IDs) destroy time-series databases — use aggregated label values (endpoint name, status class) instead.
- **Cost and capacity budgets are reliability budgets**: an autoscaling rule, storage growth pattern, query scan, or egress path that can exceed budget without alerting is an operational risk, not only a finance concern.
- **Reliability closure requires verified cause**: do not accept environment blame, intermittent flakiness claims, or incident closure without evidence tied to metrics, logs, traces, configuration, dependency version, or input.
- **Production tools require permission and sandbox evidence**: before running incident, diagnostic, cloud, deploy, rollback, migration, load, profiling, connector/MCP, or network-write actions, record the tool, permission state, sandbox boundary, dry-run/read-only scope, rollback/revert path, and output redaction rule.

## Industry Benchmarks
- **Google SRE Book (Beyer et al.) — Chapters 3, 4, 6**: SLIs, SLOs, error budgets, toil reduction. The canonical reference for production reliability engineering. SLO = reliability commitment; error budget = innovation vs. stability balance.
- **DORA Metrics (Accelerate)**: Deployment frequency, lead time, MTTR, change failure rate. MTTR < 1 hour for elite teams. Change failure rate < 5%. Measure these to know if reliability investments are working.
- **RED Method (Tom Wilkie — Weave Works)**: Rate, Errors, Duration — the three golden signals for every service. Start with RED before adding USE or custom metrics.
- **USE Method (Brendan Gregg)**: Utilization, Saturation, Errors — for every resource (CPU, memory, disk, network). Diagnoses resource exhaustion and capacity issues.
- **OpenTelemetry (CNCF)**: Unified specification for traces, metrics, and logs. The industry standard for vendor-neutral observability instrumentation. Use OpenTelemetry SDK, not vendor-specific SDKs.
- **Multi-Window Multi-Burn-Rate Alerting (Google SRE Workbook Chapter 5)**: Alert on fast burn (critical page: 1h window, 14x burn rate) and slow burn (warning page: 6h window, 6x burn rate) simultaneously — reduces both false positives and missed incidents.
- **Chaos Engineering (Principles of Chaos)**: Inject failures in controlled environments (Chaos Monkey, Gremlin) to verify that resilience controls (circuit breakers, fallback, retry) work as designed.
- **Distributed Systems Observability (Cindy Sridharan)**: The three pillars — logs, metrics, traces — are insufficient alone; correlation (trace_id across all three) is what enables incident diagnosis.

### SLI/SLO Selection Matrix

| User Expectation | SLI | SLO Target (Starting Point) |
|---|---|---|
| API response time | p99 latency of successful requests | < 300ms p99 over 28-day rolling window |
| API availability | Proportion of successful requests (2xx+3xx / total) | 99.9% (43m downtime/month) |
| Data processing freshness | Event-to-processed latency (p95) | < 30s p95 over 1-hour window |
| Search result quality | Proportion of queries with relevance score ≥ threshold | 95% over 24-hour window |
| Job success rate | Proportion of scheduled jobs completing successfully | 99.5% over 7-day rolling window |
| Payment success rate | Proportion of payment attempts succeeding | 99.0% (gateway + app combined) |

## Technical Selection Criteria
Evaluate every production change against:
- **SLI/SLO impact**: Does this change affect any SLI? Does it require a new SLI? Is the current SLO budget sufficient to absorb the rollout risk?
- **Latency budget**: What is the expected p50/p95/p99 latency for the changed path? Is it within budget? Has it been profiled under realistic load?
- **Throughput and capacity**: What is the expected request rate? What are the resource limits (CPU, memory, connections, file descriptors)? Is there headroom?
- **Concurrency design**: Are there shared resources (connection pools, locks, semaphores)? What is the maximum concurrency? Is there backpressure?
- **Queue and async safety**: Are queue depths bounded? Are DLQs configured? Is consumer scaling proportional to queue depth?
- **Circuit breaker configuration**: Is the circuit breaker failure threshold calibrated? Is the half-open probe configured? Is fallback behavior defined?
- **Structured logging**: Are log events structured (JSON schema)? Is PII excluded from logs? Are trace_id and span_id included?
- **Metrics cardinality**: Are label values bounded (no user_id, no raw URL paths with IDs)? Is the cardinality increase estimated before deployment?
- **Alert quality**: Are alerts firing on SLO burn rate, not on raw metric thresholds? Are alert thresholds calibrated to avoid false positives?
- **Recovery readiness**: Is there a runbook for the most likely failure mode? Has it been tested? Who is on-call when this change is deployed?
- **Cost and capacity guardrails**: What is the unit cost per request, tenant, and batch job? What is the storage growth rate, egress exposure, autoscaling cost impact, reservation risk, and cost anomaly alert?
- **Incident response readiness**: If this change causes a SEV0/SEV1/SEV2 incident, are severity, roles, mitigation criteria, communication cadence, and postmortem ownership defined?

## Mode Matrix
Select the reliability mode before approving production behavior, performance work, observability, or incident closure.

| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities | Skip by default |
|---|---|---|---|---|---|
| New production path | New endpoint, job, dependency, queue, dashboard, SLO path, or resource. | SLI/SLO, RED/USE telemetry, capacity, fallback, alert, runbook. | Traffic estimate, latency/error/saturation budget, dashboard/alert owner. | `observability`, `performance-budgeting`, `delivery-release-gate` | Chaos/load testing unless high-risk. |
| Modify existing path | Query, dependency, retry, queue, metric, log, or resource limit changes. | Preserve SLO and prevent cardinality, retry, fallback, or saturation regressions. | Before/after metrics, dependency/resource boundaries, rollback signal. | `profiling`, `concurrency-control`, `quality-test-gate` | New SLO unless user impact changes. |
| Performance/reliability bug fix | Latency spike, error-rate increase, queue lag, OOM, retry storm, pool exhaustion. | Verify cause, mitigation vs resolution, regression proof. | Baseline, cause, false hypotheses, fix evidence, watch signal. | `failure-diagnosis`, `agent-execution-discipline`, `regression-testing` | Optimization unrelated to measured bottleneck. |
| Observability/alerting change | Logs, metrics, traces, labels, dashboards, alerts, runbooks. | Symptom-based alerts, bounded cardinality, dashboard usefulness, on-call actionability. | Metric schema, label budget, alert query, dashboard screenshot/query, runbook. | `observability`, `code-clarity-maintainability` | Paging on raw counts without burn rate. |
| Release readiness | Canary, rollout monitoring, rollback threshold, capacity/cost guardrail. | Watch windows, rollback triggers, owner handoff, error budget. | Error budget, canary thresholds, dashboard, rollback signal, owner. | `delivery-release-gate`, `performance-budgeting` | Release approval without live watch owner. |
| Incident closure | SEV, mitigation, root cause, customer impact, postmortem, corrective action. | Verified cause, timeline, mitigation evidence, residual risk, follow-up ownership. | Incident timeline, metrics/logs, action items, runbook/doc updates. | `failure-diagnosis`, `change-documentation-gate`, `agent-execution-discipline` | Closure before customer impact and residual risk are named. |

## Proactive Professional Triggers

- **Signal:** new endpoint/job/dependency lacks SLI, SLO target, RED/USE metrics, or dashboard owner. **Hidden risk:** production degradation is invisible. **Required professional action:** add observability before release. **Route to:** `observability`, `delivery-release-gate`. **Evidence required:** metric names, dashboard, owner, alert/runbook.
- **Signal:** retry count/backoff/circuit breaker changes without traffic budget or idempotency proof. **Hidden risk:** retry storm and cascading failure. **Required professional action:** model retry amplification and fallback. **Route to:** `idempotency-retry-design`, `degradation-circuit-breaking`. **Evidence required:** retry budget, backoff, fallback test, metric.
- **Signal:** metric labels include user/session/raw path/error message/tenant without cardinality budget. **Hidden risk:** telemetry cost/OOM and lost observability. **Required professional action:** bound labels or aggregate. **Route to:** `observability`, `performance-budgeting`. **Evidence required:** label set, cardinality estimate, query sample.
- **Signal:** alert fires on fixed count or low-level symptom with no user impact/runbook. **Hidden risk:** noisy or silent alert. **Required professional action:** convert to SLO burn or actionable symptom. **Route to:** `observability`, `change-documentation-gate`. **Evidence required:** alert query, threshold rationale, runbook action.
- **Signal:** queue/async path lacks DLQ depth, lag, retry, or poison-message alert. **Hidden risk:** invisible backlog or lost work. **Required professional action:** instrument worker failure modes. **Route to:** `message-queue-design`, `data-middleware-change-builder`. **Evidence required:** lag/DLQ metrics and failure test.
- **Signal:** fallback returns empty/default data without user/metric distinction. **Hidden risk:** degraded mode looks like correctness. **Required professional action:** design explicit degradation semantics and observability. **Route to:** `degradation-circuit-breaking`, `frontend-change-builder` when UI affected. **Evidence required:** fallback contract, log/metric, UX state.
- **Signal:** HTTP, DB, Redis, Kafka, SDK, pool, timer, subscription, file, or socket lifecycle is unclear. **Hidden risk:** per-operation clients, leaked handles, pool exhaustion, or shutdown failures degrade production. **Required professional action:** define dependency wiring, lifecycle scope, startup validation, and cleanup owner. **Route to:** `dependency-wiring-lifecycle`, `backend-change-builder`. **Evidence required:** dependency graph, lifecycle scope, construction owner, shutdown owner, and pool/client metrics.
- **Signal:** retry, fallback, timeout, cancellation, or partial failure is observable only as a generic error. **Hidden risk:** incidents cannot distinguish dependency failure, validation error, conflict, degraded response, or terminal failure. **Required professional action:** define the failure contract and telemetry fields. **Route to:** `failure-contract-design`, `observability`. **Evidence required:** error taxonomy, retryability, fallback/degradation, log/metric/trace fields, and cause preservation.
- **Signal:** hot path processes unbounded inputs, nested scans, top-K, grouping, sorting, or load-all batches with no scale budget. **Hidden risk:** latency, memory, queue lag, or cost regression under real input distribution. **Required professional action:** require an algorithm/data-structure decision and performance evidence. **Route to:** `algorithm-data-structure-selection`, `performance-budgeting`. **Evidence required:** input size, worst case, memory budget, streaming/chunking decision, benchmark/profile output.
- **Signal:** mapper/getter/policy/domain logic writes DB/cache/events/external I/O or publishes events before commit. **Hidden risk:** hidden side effects bypass telemetry, transaction ordering, idempotency, and compensation. **Required professional action:** trace side-effect flow and attach observability at the visible boundary. **Route to:** `data-side-effect-flow-tracing`, `data-middleware-change-builder`. **Evidence required:** ordering, transaction boundary, publish-after-commit decision, idempotency/compensation, and metrics/logs.
- **Signal:** feature flag, kill switch, runtime mode, or config default changes reliability behavior without typed validation, owner, or rollout/rollback evidence. **Hidden risk:** production mitigation or degradation policy depends on ungoverned config. **Required professional action:** apply runtime configuration policy before accepting reliability readiness. **Route to:** `configuration-runtime-policy`, `delivery-release-gate`. **Evidence required:** config schema, default, validation, owner, kill-switch behavior, rollout/rollback, and cleanup path.
- **Signal:** incident closure lacks verified cause, false hypotheses, customer impact, or corrective action owner. **Hidden risk:** missing verified cause repeats the incident and weakens the postmortem. **Required professional action:** keep the incident open or route diagnosis/docs until cause and owner are proven. **Route to:** `failure-diagnosis`, `change-documentation-gate`. **Evidence required:** incident timeline, metric/log proof, false-hypothesis notes, and corrective-action owner.
- **Signal:** autoscaling, storage, egress, full scan, or batch retry can exceed budget without anomaly alert. **Hidden risk:** unbounded spend, cost leak, or budget incident as a reliability failure. **Required professional action:** add cost/capacity guardrail with alertable threshold and owner. **Route to:** `performance-budgeting`, `delivery-release-gate`. **Evidence required:** unit-cost report, capacity forecast, anomaly alert query, and alert owner.
- **Signal:** reliability diagnosis, load/profile, cloud, deploy, rollback, migration, or incident command can mutate state, stress production, call a connector, or expose sensitive output without permission/sandbox classification. **Hidden risk:** the investigation or fix becomes a production incident. **Required professional action:** classify tool permission/sandbox before execution. **Route to:** `agent-tool-permission-sandbox`, `security-privacy-gate`. **Evidence required:** tool/action class, permission state, sandbox/read-only boundary, rollback/revert path, and output redaction rule.

## Cost And Capacity Guardrails

Every production-facing change with material resource impact must define cost and capacity guardrails:

- **Cost per request**: expected steady-state and peak unit cost for the changed request path.
- **Cost per tenant**: tenant-level cost attribution for multi-tenant or high-variance workloads.
- **Cost per batch job**: compute, warehouse, queue, and retry cost per run and per schedule window.
- **Storage growth rate**: daily and monthly growth, retention policy, lifecycle tiering, and deletion pressure.
- **Egress cost**: cross-region, internet, CDN, third-party, and data export cost exposure.
- **Autoscaling trigger cost impact**: how HPA/KEDA/serverless scaling thresholds translate into spend at peak and during runaway input.
- **Resource reservation / commitment risk**: reserved instances, savings plans, committed use discounts, or spot capacity exposure, including lock-in and underutilization risk.
- **2x peak headroom vs cost cap**: whether the service can absorb 2x expected peak without violating the approved cost cap.
- **Cost anomaly alert**: alert owner, threshold, burn-rate window, and response path for unexpected spend or usage growth.

### Decision Tree: Observability Coverage Level

```
Does the change add a new user-facing endpoint or modify response latency?
├── Yes → RED metrics required (rate, errors, duration) + SLO impact assessment
Does the change add async processing (queue consumer, background job)?
├── Yes → Queue depth metric + DLQ depth alert + consumer lag metric
Does the change depend on an external service?
├── Yes → Circuit breaker metric + per-provider error rate + timeout metric
Does the change affect a database query on the critical path?
├── Yes → Query latency metric + slow query log + connection pool saturation
Does the change emit new log lines in production?
├── Yes → Structured log schema review + cardinality check + PII exclusion
Change is infrastructure-only with no behavior change?
└── USE method metrics for affected resources + capacity headroom check
```

## Solution Optimality Self-Check
Apply when designing SLI/SLO targets, alert strategies, capacity budgets, and instrumentation — these are reliability contracts. Answer the **Three-Challenge Rule**: (1) why this SLI/SLO/alert design (state the user impact), (2) is it the simplest sufficient observability (Rate/Errors/Duration cover most services; more alerts need justification), (3) what is the strongest alternative and why is it rejected (burn-rate over fixed-count). Define the per-dimension budgets (CPU saturation, memory headroom, metric cardinality, connection-pool, RED, consumer lag, multi-burn-rate latency) — a missing budget is an unenforceable SLO.

Load [references/solution-optimality.md](references/solution-optimality.md) for the full performance-dimension budget matrix and additional considerations (error-budget policy, symptom-based alerting, cardinality budget, chaos game days) when the change affects a production service. Method compiled from `solution-optimality-evaluation`.

## Risk Escalation Rules
- Escalate when a change is deployed to a critical path with no existing SLI — the deployment is unobservable.
- Escalate when the error budget for an affected SLO is already exhausted — feature deployment is blocked per error budget policy.
- Escalate when a new metric label value has unbounded cardinality (user_id, session_id, raw URL path) — will cause time-series database OOM or cost explosion.
- Escalate when an alert threshold is defined as a fixed count (e.g. "500 errors/minute") rather than a burn rate — fixed-count alerts are unreliable under variable traffic.
- Escalate when a circuit breaker does not have a tested fallback behavior — a tripped circuit breaker with no fallback causes a hard dependency failure cascade.
- Escalate when a queue consumer has no DLQ and no depth monitoring — poison messages cause consumer loops; depth spikes are invisible.
- Escalate when a change introduces unbounded memory growth (unlimited cache, unbounded list accumulation, session state with no TTL) — will cause OOM in production.
- Escalate when recovery procedures (runbook, rollback, manual remediation) have never been tested and the change affects a P1-eligible service.
- Escalate when a cloud resource, autoscaling policy, query scan, storage lifecycle, or egress path can exceed budget without a cost anomaly alert and owner.
- Escalate when capacity forecast shows less than 2x peak headroom or when the only path to headroom requires unapproved spend.
- Escalate when incident severity, incident commander, technical lead, communications lead, or customer communication cadence is undefined for a production-critical path.
- Escalate to `agent-execution-discipline` when an agent repeats the same diagnosis path twice, skips evidence collection, or hands off an incident without boundary and validation results.

## Critical Details
- **Multi-window multi-burn-rate alerting math**: a 1% error rate on an SLO of 99.9% burns the 28-day error budget in 28 hours. Fast-burn alert: if burn rate > 14x over 1 hour, page immediately. Slow-burn alert: if burn rate > 6x over 6 hours, page with lower urgency.
- **Trace sampling strategy**: 100% sampling is too expensive at high throughput; head-based sampling loses all information about sampled-out requests; use tail-based sampling (Jaeger tail-based, OpenTelemetry tail sampling processor) to retain high-latency and error traces at 100% and sample normal traces at 1%.
- **Log level discipline**: ERROR = requires action; WARN = anomaly, self-recovers; INFO = significant business events; DEBUG = development only (disabled in production). Logging at ERROR for expected conditions creates alert noise that masks real errors.
- **PII in logs is a compliance violation**: user IDs, email addresses, IP addresses (in some jurisdictions), and session tokens must be excluded from log lines or tokenized — GDPR Article 5 (data minimization).
- **Connection pool exhaustion is the most common production cause of latency spikes**: monitor `pool_size`, `pool_waiting`, `pool_checkout_timeout` as first-class metrics alongside request latency.
- **Graceful degradation requires explicit fallback design**: a fallback of "return empty response" is often indistinguishable from "feature not working" to the user. Design fallback states with appropriate UX and observability.
- **Capacity planning at 2× peak**: design for 2× the expected peak traffic. Anything less means a viral moment or a DDoS causes an availability incident.
- **Unit economics as a production signal**: cost per request, tenant, and job should be tracked like latency and error rate. Sudden cost-per-unit growth often indicates a reliability issue such as retry storms, cache misses, full table scans, or runaway fan-out.
- **Mitigation vs. resolution**: during an incident, mitigation reduces customer impact now; resolution removes the underlying defect. A rollback, traffic shift, feature flag disable, or capacity increase may be mitigation even when root cause remains open.

### Anti-Examples

| Observability Pattern | Problem | Corrected Approach |
|---|---|---|
| Alert: `if error_count > 500` | Fires during low-traffic with 1% error rate; silent during high-traffic with 0.5% | Alert on SLO burn rate: `error_rate > 14 * (1-SLO_target)` over 1-hour window |
| Log: `logger.error(f"Failed: {user_email}")` | PII in production log; GDPR violation | `logger.error("Payment failed", extra={"user_id": user_id, "order_id": order_id})` |
| Metric label: `http_requests{path="/users/12345/orders"}` | Cardinality explosion — one label value per user ID | `http_requests{endpoint="/users/{id}/orders", status_class="2xx"}` |
| Circuit breaker with no fallback | On trip, all requests return 500 | Circuit breaker with fallback: return cached data or degraded response |
| Queue consumer with no DLQ | Poison message crashes consumer loop; queue depth grows unbounded | DLQ routing + depth alert + consumer restart policy |

## Failure Modes
- **No SLI hides degradation**: p99 latency climbs from 200ms to 4000ms — no alert fires; users report slowness 2 hours later.
- **Unbounded retries create retry storms**: a downstream service returns 503; the upstream retries 100x/second per instance; 50 instances × 100 retries = 5000 RPS to an already-failing service.
- **Missing traces obscure failure root cause**: a request fails; it involved 4 services; without trace propagation, each service's logs show a failure in isolation — diagnosis takes hours.
- **High-cardinality metric label destroys telemetry**: a `user_id` label added to a high-frequency metric creates 10M unique time series — Prometheus runs out of memory; the entire metrics pipeline fails.
- **Alert threshold not calibrated to traffic**: an error count alert set to 1000/minute fires during normal traffic growth and is silenced; it never fires during a real 5% error rate incident because absolute count is below threshold.
- **No recovery plan extends incidents**: a database runs out of connections; the on-call engineer has never seen this failure mode; they spend 45 minutes diagnosing what a 5-minute runbook would resolve.
- **Connection pool exhaustion starves all requests**: a slow external call holds connections; the pool fills; all requests wait; the service appears to be down.

## Reference Loading Policy
Do not load every reference by default. Treat references as targeted support selected by the router and the task risk.

- L1 changes: do not read references unless the task touches security, data, auth, external integration, performance, release, or irreversible behavior.
- L2 changes: read `references/capabilities/index.md` and only capability files explicitly selected by `change-forge-router`.
- L3 changes: read all selected capability references and `references/checklist.md` when present.
- L4/L5 changes: read all selected capability references, `references/checklist.md` when present, and domain extension references when selected.
- Selected capability reference path format: `references/capabilities/<capability-id>-<capability-name>.md`.

Examples:
- `42 idempotency-retry-design` -> `references/capabilities/42-idempotency-retry-design.md`
- `82 solution-optimality-evaluation` -> `references/capabilities/82-solution-optimality-evaluation.md`

## Output Contract
Return a reliability and observability plan with:
- **Mode selected**: new production path, modify existing path, reliability bug fix, observability change, release readiness, or incident closure, with trigger signal.
- **Boundaries inspected**: request path, dependencies, queues, pools, resource limits, dashboards, alerts, runbooks, release watch, incident timeline, and cost/capacity boundaries inspected or skipped with reason.
- **Professional judgment**: SLI/SLO, capacity, fallback, alert, incident, or cost decision, including risks ruled out and risks still possible.
- **SLI/SLO impact assessment**: affected SLIs, SLO target confirmation, error budget headroom.
- **Performance budget**: expected p50/p95/p99 latency, throughput, resource utilization bounds.
- **Resilience controls**: circuit breaker configuration, rate limits, timeouts, retry policy, fallback behavior.
- **Dependency lifecycle controls**: composition root, lifecycle scope, client/pool ownership, startup validation, shutdown cleanup, and leak-sensitive resources.
- **Failure contract telemetry**: retryability, terminal/validation/permission/conflict/cancellation states, degraded response, partial failure, safe user message, and diagnostic cause correlation.
- **Algorithmic scale guardrail**: expected input distribution, worst-case complexity, memory budget, streaming/chunking choice, and benchmark/profile evidence for hot paths.
- **Side-effect flow observability**: transaction, persistence, cache, event, external I/O, publish-after-commit, idempotency, compensation, and ordering evidence.
- **Telemetry plan**: structured log schema, metric names with label cardinality analysis, trace propagation strategy.
- **Alerting design**: burn-rate alert thresholds, paging urgency levels, on-call routing.
- **Capacity analysis**: current headroom, expected growth, scaling triggers.
- **Cost and capacity guardrails**: `cost_per_request`, `cost_per_tenant`, `cost_per_batch_job`, `storage_growth_rate`, `egress_cost`, `autoscaling_cost_impact`, `reservation_commitment_risk`, `capacity_forecast`, and `cost_anomaly_alert`.
- **Incident readiness**: severity classification, incident roles, mitigation criteria, customer communication cadence, status page criteria, and postmortem ownership.
- **Model operations signals**: when ML is involved, model version, drift metric, training-serving skew signal, and rollback model version.
- **Reuse and placement rationale**: why each metric, log field, span, alert, dashboard, runbook, fallback, or capacity guardrail belongs at the selected boundary.
- **Recovery plan**: runbook location, tested recovery steps, rollback decision criteria.
- **Execution discipline evidence**: Verified-cause statement, evidence inventory, false hypotheses, route-repair ledger when repeated investigation failed, and closure package.
- **Tool permission/sandbox evidence**: diagnostic/load/profile/cloud/deploy/rollback/migration/connector action class, permission state, sandbox or read-only boundary, rollback/revert path, and redaction rule.
- **Validation evidence**: load/profile/query/dashboard/alert/incident artifacts run or inspected, with outcomes tied to the reliability obligation.
- **Behavior preservation**: SLO semantics, alert meaning, fallback behavior, logging privacy, and existing runbook actions preserved or intentionally changed.
- **Chaos/game day obligations**: failure mode scenarios to test in staging before production deployment.
- **Evidence limits**: what each load/profile/query/dashboard/incident artifact proves and what it does not prove about peak load, rare dependencies, recovery, or cost anomalies.
- **Residual risks**: accepted gaps with justification and mitigation.
- **Next gate/handoff**: release, backend, data middleware, integration, security, documentation, or no-next-gate rationale.

## Evidence Contract
Close a reliability and observability plan only when all five canonical answers are concrete (answer schema: `agent-execution-discipline`):
- **Basis**: the selected mode, SLI/SLO target, error-budget headroom, RED/USE signal set, or incident severity model the plan rests on.
- **Files and boundaries inspected**: request paths, dependencies, queues, pools, resource limits, dashboards, alerts, runbooks, release watch, cost/capacity guardrails, and incident timeline examined, and the saturation or contention point identified.
- **Placement rationale**: where each log field, metric, trace span, and burn-rate alert attaches, and which alert owner and runbook it routes to.
- **Validation commands**: load test, profile, chaos/game-day scenario, burn-rate query, dashboard/alert query, or incident evidence check run, each with its outcome, what evidence proves, and what evidence does not prove.
- **Reliability judgment and handoff**: mode selected, SLO/capacity/alert judgment, behavior preservation, evidence limits, and next gate.
- **Residual risk**: capacity, cost, recovery, dashboard, alert, fallback, or incident-corrective-action path that remains unverified, with the scaling/rollback trigger and named owner.

## Quality Gate
1. Every user-facing path has an SLI with a documented SLO target.
2. Error budget headroom is confirmed before deployment — feature is blocked if budget is exhausted.
3. Multi-window multi-burn-rate alerts are configured for every SLO.
4. Structured logging with trace_id propagation is implemented — no unstructured log lines in production.
5. No metric label values have unbounded cardinality.
6. Circuit breakers are configured with tested fallback behavior for all external dependencies on the critical path.
7. Queue consumers have DLQ routing, depth monitoring, and consumer lag alerting.
8. Connection pool and resource saturation metrics are instrumented.
9. Recovery runbook exists, is current, and has been tested within the last 90 days (or since last significant architecture change).
10. Rollback decision criteria are explicit: which signals, at which thresholds, trigger an immediate rollback.
11. Cost and capacity guardrails are defined for material resource changes, including unit costs, egress/storage exposure, capacity forecast, and anomaly alert owner.
12. Incident roles, severity, customer communication cadence, and postmortem ownership are defined for production-critical paths.
13. Agent-assisted reliability closure includes verified cause, evidence, residual risks, and no third same-path retry.
14. Reusable clients and pools are long-lived at the narrowest correct lifecycle and have startup validation, saturation metrics, and shutdown cleanup.
15. Retry, fallback, timeout, cancellation, and partial-failure states are distinguishable in logs, metrics, traces, alerts, and user-safe responses.
16. Hot paths with unbounded or high-volume inputs have explicit complexity, memory, streaming/chunking, and benchmark/profile evidence.
17. Side effects are visible at service, adapter, repository, job, or message-consumer boundaries and preserve transaction/event ordering.
18. Reliability-affecting tools have permission/sandbox evidence before execution, including read-only scope or dry-run where available, rollback/revert path, and output redaction rules.

## Handoff
- **delivery-release-gate** — for canary traffic thresholds, rollout monitoring windows, and rollback decision signals.
- **backend-change-builder** — for circuit breaker implementation, timeout configuration, and structured logging.
- **data-middleware-change-builder** — for connection pool monitoring, query latency metrics, and DLQ configuration.
- **integration-change-builder** — for integration error rate metrics, circuit breaker state, and reconciliation monitoring.
- **quality-test-gate** — for chaos engineering test obligations, load test requirements, and SLO regression testing.
- **security-privacy-gate** — for PII exclusion from logs and audit log requirements.
- **failure-diagnosis** — for SEV incident evidence collection, timeline reconstruction, root cause analysis, and postmortem action items.
- **change-documentation-gate** — for customer advisories, status page entries, runbook updates, incident reports, and postmortem summaries.
- **agent-execution-discipline** — when incident or reliability closure lacks evidence, verified cause, route repair, or handoff boundary.
- **dependency-wiring-lifecycle** — when client, pool, subscription, timer, file, socket, or shutdown lifecycle ownership is unclear.
- **failure-contract-design** — when retryability, fallback, degradation, partial failure, or cause-preserving error translation is unclear.
- **algorithm-data-structure-selection** — when scale-sensitive code needs complexity, memory, streaming/chunking, or benchmark evidence.
- **data-side-effect-flow-tracing** — when transaction, cache, event, external I/O, or hidden side-effect ordering affects reliability.
- **configuration-runtime-policy** — when flags, kill switches, runtime modes, config defaults, or cleanup policy affect production reliability behavior.

## Completion Criteria
The change is production-ready from a reliability and observability perspective when every user-facing path has an SLI, error budget headroom is confirmed, multi-burn-rate alerts are configured, structured logging with trace propagation is implemented, cardinality of new metrics is bounded, circuit breakers have tested fallback behavior, queue consumers have DLQ and depth alerts, cost and capacity guardrails are owned and alertable, incident handoff is defined, a tested recovery runbook exists, and rollback decision criteria are explicit.
