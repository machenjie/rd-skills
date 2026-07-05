# Reliability Output And Gates

Load this reference when `reliability-observability-gate` needs the full reliability output contract, evidence contract, quality gate list, or handoff routing table. The skill body keeps the default runtime context compact.

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
2. Error budget headroom is confirmed before deployment; feature is blocked if budget is exhausted.
3. Multi-window multi-burn-rate alerts are configured for every SLO.
4. Structured logging with trace_id propagation is implemented; no unstructured log lines in production.
5. No metric label values have unbounded cardinality.
6. Circuit breakers are configured with tested fallback behavior for all external dependencies on the critical path.
7. Queue consumers have DLQ routing, depth monitoring, and consumer lag alerting.
8. Connection pool and resource saturation metrics are instrumented.
9. Recovery runbook exists, is current, and has been tested within the last 90 days or since last significant architecture change.
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
- **delivery-release-gate**: canary traffic thresholds, rollout monitoring windows, and rollback decision signals.
- **backend-change-builder**: circuit breaker implementation, timeout configuration, and structured logging.
- **data-middleware-change-builder**: connection pool monitoring, query latency metrics, and DLQ configuration.
- **integration-change-builder**: integration error rate metrics, circuit breaker state, and reconciliation monitoring.
- **quality-test-gate**: chaos engineering test obligations, load test requirements, and SLO regression testing.
- **security-privacy-gate**: PII exclusion from logs and audit log requirements.
- **failure-diagnosis**: SEV incident evidence collection, timeline reconstruction, root cause analysis, and postmortem action items.
- **change-documentation-gate**: customer advisories, status page entries, runbook updates, incident reports, and postmortem summaries.
- **agent-execution-discipline**: incident or reliability closure lacks evidence, verified cause, route repair, or handoff boundary.
- **dependency-wiring-lifecycle**: client, pool, subscription, timer, file, socket, or shutdown lifecycle ownership is unclear.
- **failure-contract-design**: retryability, fallback, degradation, partial failure, or cause-preserving error translation is unclear.
- **algorithm-data-structure-selection**: scale-sensitive code needs complexity, memory, streaming/chunking, or benchmark evidence.
- **data-side-effect-flow-tracing**: transaction, cache, event, external I/O, or hidden side-effect ordering affects reliability.
- **configuration-runtime-policy**: flags, kill switches, runtime modes, config defaults, or cleanup policy affect production reliability behavior.
