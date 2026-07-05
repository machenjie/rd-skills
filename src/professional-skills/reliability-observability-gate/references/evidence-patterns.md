# Reliability Observability Evidence Patterns

Use this reference when reliability closure depends on runtime evidence, operational reports, or incident artifacts. Load only the rows matching the changed reliability surface.

## Evidence Map
- **SLI/SLO or alert change:** capture metric query, burn-rate math, dashboard/report artifact, alert route, owner, test or validator command, exit code, and stale-window risk.
- **Latency, throughput, or capacity change:** prove baseline, target budget, profile/load/query output, resource headroom, dataset or traffic assumption, and peak-load limit.
- **Retry, timeout, breaker, fallback, or degradation change:** prove failure contract, idempotency, fallback user semantics, metric/log/trace fields, negative test, and rollback trigger.
- **Queue, pool, cache, or dependency lifecycle change:** prove bounded depth/pool/client lifecycle, saturation signals, DLQ or fallback behavior, shutdown cleanup, and source-of-truth behavior.
- **Cost or capacity guardrail:** prove unit cost, storage/egress/autoscaling forecast, anomaly alert, owner, cap or approval, and residual spend risk.
- **Incident or production diagnosis closure:** prove timeline, verified cause, false hypotheses ruled out, bounded command output, redaction rule, corrective action, and watch signal.

## Evidence Rules
- Every accepted evidence item names command or validator, report/dashboard/log artifact, exit code when runnable, freshness, and the exact reliability claim it proves.
- Every evidence item also states what it does not prove: peak traffic, rare dependency behavior, live rollback success, long-tail cost, or recovery under incident pressure.
- Prefer existing load/profile/query tools, dashboards, alert queries, runbooks, and incident reports before adding new instrumentation or support code.
- Do not accept a dashboard screenshot alone unless the dashboard itself is the reviewed artifact; pair it with the query, alert rule, report export, or bounded command slice when possible.
