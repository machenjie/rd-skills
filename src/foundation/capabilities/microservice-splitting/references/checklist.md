# Microservice Splitting Checklist

- Define the proposed service boundary and business capability.
- Confirm why module isolation is insufficient.
- Define API or event contract and compatibility obligations.
- Define service owner, on-call owner, and release authority.
- Define data ownership and remove shared-database assumptions.
- Define consistency, reconciliation, and compensating actions.
- Define timeout, retry, circuit breaker, and degraded-mode behavior.
- Define metrics, logs, traces, alerts, dashboards, and runbook needs.
- Define deployment, rollback, and operational cost.
