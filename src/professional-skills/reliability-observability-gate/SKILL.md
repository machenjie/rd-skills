---
name: reliability-observability-gate
description: Defines reliability and observability expectations for changes, including SLI/SLO impact, performance budget, profiling, concurrency, rate limits, circuit breakers, fallback, logs, metrics, traces, alerts, backup, and recovery.
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
- Database migrations, reindexing, or data processing that affects production query performance.
- Incident response tooling, runbook, alerting rule, or on-call routing changes.
- Changes that introduce or modify circuit breakers, rate limiters, throttling, or fallback behavior.

## Do Not Use When
- The change is a static documentation edit or cosmetic UI change with zero runtime behavior impact.
- The change is a test-only addition with no production deployment.

## Non-Negotiable Rules
- **Every user-facing path must have an SLI**: if there is no measurable signal, there is no way to detect degradation before users report it.
- **SLOs must be defined before the feature ships**: an SLO added after an incident is a post-hoc measurement, not a reliability commitment.
- **Error budgets must be tracked and acted on**: when the error budget is exhausted, feature development stops until reliability is restored — this is the SRE error budget policy.
- **Unbounded queues are a reliability anti-pattern**: every queue must have a defined capacity limit, DLQ routing, and backpressure mechanism — an unbounded queue will OOM the consumer.
- **Alerts must page on user-impacting signals, not on noisy technical metrics**: alert on SLO burn rate (multi-window, multi-burn-rate), not on CPU percentage or error count thresholds that fire during non-impacting spikes.
- **Structured logging is required for production services**: unstructured log lines are unsearchable at scale; every log event must have `timestamp`, `level`, `service`, `trace_id`, and a consistent JSON schema.
- **Trace context must propagate across service boundaries**: a trace that terminates at the first service boundary cannot diagnose cross-service latency issues.
- **Recovery plans must be tested before they are needed**: a runbook that has never been executed will fail under incident pressure — conduct game days or chaos engineering exercises.
- **Cardinality limits on metric labels**: high-cardinality labels (user_id, request_id, URL path with IDs) destroy time-series databases — use aggregated label values (endpoint name, status class) instead.

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

## Risk Escalation Rules
- Escalate when a change is deployed to a critical path with no existing SLI — the deployment is unobservable.
- Escalate when the error budget for an affected SLO is already exhausted — feature deployment is blocked per error budget policy.
- Escalate when a new metric label value has unbounded cardinality (user_id, session_id, raw URL path) — will cause time-series database OOM or cost explosion.
- Escalate when an alert threshold is defined as a fixed count (e.g. "500 errors/minute") rather than a burn rate — fixed-count alerts are unreliable under variable traffic.
- Escalate when a circuit breaker does not have a tested fallback behavior — a tripped circuit breaker with no fallback causes a hard dependency failure cascade.
- Escalate when a queue consumer has no DLQ and no depth monitoring — poison messages cause consumer loops; depth spikes are invisible.
- Escalate when a change introduces unbounded memory growth (unlimited cache, unbounded list accumulation, session state with no TTL) — will cause OOM in production.
- Escalate when recovery procedures (runbook, rollback, manual remediation) have never been tested and the change affects a P1-eligible service.

## Critical Details
- **Multi-window multi-burn-rate alerting math**: a 1% error rate on an SLO of 99.9% burns the 28-day error budget in 28 hours. Fast-burn alert: if burn rate > 14x over 1 hour, page immediately. Slow-burn alert: if burn rate > 6x over 6 hours, page with lower urgency.
- **Trace sampling strategy**: 100% sampling is too expensive at high throughput; head-based sampling loses all information about sampled-out requests; use tail-based sampling (Jaeger tail-based, OpenTelemetry tail sampling processor) to retain high-latency and error traces at 100% and sample normal traces at 1%.
- **Log level discipline**: ERROR = requires action; WARN = anomaly, self-recovers; INFO = significant business events; DEBUG = development only (disabled in production). Logging at ERROR for expected conditions creates alert noise that masks real errors.
- **PII in logs is a compliance violation**: user IDs, email addresses, IP addresses (in some jurisdictions), and session tokens must be excluded from log lines or tokenized — GDPR Article 5 (data minimization).
- **Connection pool exhaustion is the most common production cause of latency spikes**: monitor `pool_size`, `pool_waiting`, `pool_checkout_timeout` as first-class metrics alongside request latency.
- **Graceful degradation requires explicit fallback design**: a fallback of "return empty response" is often indistinguishable from "feature not working" to the user. Design fallback states with appropriate UX and observability.
- **Capacity planning at 2× peak**: design for 2× the expected peak traffic. Anything less means a viral moment or a DDoS causes an availability incident.

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

## Output Contract
Return a reliability and observability plan with:
- **SLI/SLO impact assessment**: affected SLIs, SLO target confirmation, error budget headroom.
- **Performance budget**: expected p50/p95/p99 latency, throughput, resource utilization bounds.
- **Resilience controls**: circuit breaker configuration, rate limits, timeouts, retry policy, fallback behavior.
- **Telemetry plan**: structured log schema, metric names with label cardinality analysis, trace propagation strategy.
- **Alerting design**: burn-rate alert thresholds, paging urgency levels, on-call routing.
- **Capacity analysis**: current headroom, expected growth, scaling triggers.
- **Recovery plan**: runbook location, tested recovery steps, rollback decision criteria.
- **Chaos/game day obligations**: failure mode scenarios to test in staging before production deployment.
- **Residual risks**: accepted gaps with justification and mitigation.

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

## Handoff
- **delivery-release-gate** — for canary traffic thresholds, rollout monitoring windows, and rollback decision signals.
- **backend-change-builder** — for circuit breaker implementation, timeout configuration, and structured logging.
- **data-middleware-change-builder** — for connection pool monitoring, query latency metrics, and DLQ configuration.
- **integration-change-builder** — for integration error rate metrics, circuit breaker state, and reconciliation monitoring.
- **quality-test-gate** — for chaos engineering test obligations, load test requirements, and SLO regression testing.
- **security-privacy-gate** — for PII exclusion from logs and audit log requirements.

## Completion Criteria
The change is production-ready from a reliability and observability perspective when every user-facing path has an SLI, error budget headroom is confirmed, multi-burn-rate alerts are configured, structured logging with trace propagation is implemented, cardinality of new metrics is bounded, circuit breakers have tested fallback behavior, queue consumers have DLQ and depth alerts, a tested recovery runbook exists, and rollback decision criteria are explicit.
