# Reliability And Observability Checklist

- Identify a user-visible or system indicator only when an owned objective or consequence needs measurement.
- Define latency, throughput, error, or saturation expectations only for a triggered failure, capacity, or operating-objective decision.
- Review concurrency, locking, queue depth, and rate limits only on affected pressure paths.
- Select timeout, retry, circuit-breaker, or fallback behavior only when the current call and failure pattern requires it.
- Check profiling or load-test need when representative capacity evidence is necessary.
- Select structured logs, metrics, or traces only from the diagnostic path, with correlation, cardinality, privacy, and sampling bounds.
- Define alerts or dashboards only when risk or policy requires an owned operator action.
- Require backup, recovery, or incident-runbook updates only for a triggered recovery or readiness obligation.
