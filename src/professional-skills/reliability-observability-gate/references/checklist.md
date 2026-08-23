# Reliability And Observability Checklist

- Identify a user-visible or system indicator only when an owned objective or consequence needs measurement.
- Define latency, throughput, error, or saturation expectations only for a triggered failure, capacity, or operating-objective decision.
- Review concurrency, locking, queue depth, and rate limits only on affected pressure paths.
- Select timeout, retry, circuit-breaker, or fallback behavior only when the current call and failure pattern requires it.
- Check profiling or load-test need when representative capacity evidence is necessary.
- Select structured logs, metrics, or traces only from the diagnostic path, with correlation, cardinality, privacy, and sampling bounds.
- Define alerts or dashboards only when risk or policy requires an owned operator action.
- Require backup, recovery, or incident-runbook updates only for a triggered recovery or readiness obligation.

## Professional Decision Rules

- Define affected failure modes, user impact, recovery owner, and any decision-relevant operating objective.
- Require an SLI or SLO only when an owned objective has a decision consequence.
- Apply timeouts, backpressure, retry budgets, circuit breaking, and degradation only where latency or load risk triggers them.
- Select only actionable signals, alerts, and runbook links justified by current risk.
- Validate triggered restart, failover, replay, rollback, and capacity assumptions proportionally.

## High-Value Gotchas

- Retries can worsen overload.
- An alert without an operator action is noise.
- Average latency hides tail failure.

## Execution Checklist

1. Trace the failure mode through user impact, dependency pressure, telemetry, and recovery ownership.
2. Choose objectives, timeouts, retry budgets, degradation, and alerts only when current risk triggers them.
3. Verify restart, failover, replay, rollback, capacity, and operator-action assumptions where material.
4. **Analysis mode:** select objectives and recovery controls from failure evidence.
5. **Task mode:** apply accepted controls at the affected runtime boundary.
6. **Review mode:** judge restart, failover, capacity, and operator-action evidence.
7. Stop when a material objective or recovery action lacks evidence and ownership.
