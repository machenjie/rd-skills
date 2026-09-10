# Reliability Observability Evidence Patterns

Use this reference when reliability closure depends on runtime evidence, operational reports, or incident artifacts. Load only the rows matching the changed reliability surface.

## Evidence Map
- **SLI/SLO or alert change:** capture the signal query, applicable objective or threshold calculation, the selected query/report/view evidence, applicable alert route, owner, test or validator command, exit code, and stale-window risk. Include error-budget denominator, windows, and burn-rate math only for burn-rate alerts; capacity or other threshold alerts need their own calculation and trigger proof.
- **Latency, throughput, or capacity change:** prove baseline, target budget, profile/load/query output, resource headroom, dataset or traffic assumption, and peak-load limit.
- **Retry, timeout, breaker, fallback, or degradation change:** prove the accepted failure and terminal outcomes, selected telemetry fields, negative tests, and applicable recovery trigger.
- **Selected retry or fallback controls:** prove idempotency when retries can repeat effects, and user semantics when fallback or degradation is selected.
- **Queue, pool, cache, or dependency lifecycle change:** prove the affected depth or resource bounds, saturation and rejection behavior, and shutdown cleanup.
- **Selected lifecycle mechanisms:** include DLQ or fallback proof when selected, and source-of-truth proof where the affected path owns or derives state.
- **Cost or capacity guardrail:** prove the selected cost/capacity dimensions, forecast or measured bound, owner, and cap or approval.
- **Applicable cost/capacity evidence:** include storage, egress, autoscaling, or anomaly alerts only where the actual exposure and response policy require them.
- **Cost/capacity proof limits:** state residual limits.
- **Incident or production diagnosis closure:** prove timeline, verified cause, false hypotheses ruled out, bounded command output, redaction rule, corrective action, and watch signal.

## Evidence Rules
- Every accepted evidence item names command or validator, report/dashboard/log artifact, exit code when runnable, freshness, and the exact reliability claim it proves.
- Every evidence item also states what it does not prove: peak traffic, rare dependency behavior, live rollback success, long-tail cost, or recovery under incident pressure.
- Prefer existing load/profile/query tools, dashboards, alert queries, runbooks, and incident reports before adding new instrumentation or support code.
- Do not accept a dashboard screenshot alone unless the dashboard itself is the reviewed artifact; pair it with the query, alert rule, report export, or bounded command slice when possible.
