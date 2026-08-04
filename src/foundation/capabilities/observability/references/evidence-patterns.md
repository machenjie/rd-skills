# Observability Evidence Patterns

Use this reference when observability closure depends on current evidence, validation freshness, tool boundaries, or changed-signal validation.
Current evidence includes repository inspection, prior-task claims, action sequences, dashboards, and runbooks.
Keep this file as an evidence map, not a second observability tutorial.

## Changed-Signal-To-Validation Map

| Claim | Minimum evidence | What it proves | What it does not prove |
| --- | --- | --- | --- |
| SLI/SLO is measurable | User journey, metric name, formula, labels, window, owner, dashboard panel, and current query or config path. | The named journey has a measurable user-impact signal. | Historical baseline accuracy, production scale, or all client segments are proven. |
| Structured log is safe and queryable | Field list, redacted/excluded fields, correlation or trace binding, sample query, and current source/config path. | Operators can find the inspected event without exposing sensitive fields. | Every caller, debug path, log sink, or retention policy is safe unless inspected. |
| Metric labels are bounded | Label list, allowed values or cardinality estimate, rejected high-cardinality fields, and metric query. | The inspected metric is unlikely to overload the telemetry backend through obvious unbounded labels. | Production cardinality, tenant skew, or backend retention cost is proven. |
| Trace continuity is current | Ingress extraction, outbound injection, async/job propagation point, span names, and trace lookup or source proof. | The inspected path can correlate logs, metrics, and spans across the named boundary. | Sibling async flows, provider-specific propagation, or sampling behavior is complete. |
| Alert and dashboard are actionable | Alert query, threshold, severity, owner, runbook action, dashboard path, and synthetic/sample event when feasible. | The inspected operator workflow can detect and start remediation for the named symptom. | On-call behavior, alert fatigue, or incident response effectiveness is proven. |
| Validation is fresh | Command or query, working directory or environment, exit code/outcome, report/artifact path, and final-edit freshness. | Evidence was produced after the final material change for the mapped signal. | Later source/config/dashboard/generated/report edits are covered. |

## Current Evidence And Freshness

- Treat prior repository, task, dashboard, incident, generated-doc, validation, and action-sequence evidence as discovery input.
- Confirm discovery input with current source, configuration, or query evidence.
- Accept a prior dashboard, alert, trace, or runbook-owner claim only when current definitions and changed paths still match.
- Reject or downgrade memory that lacks date, owner, environment, query/config path, changed-signal scope, command outcome, or residual-risk owner.
- Mark evidence stale after edits to log fields, metric names, labels, spans, trace propagation, alerts, dashboards, or runbooks.
- Also mark it stale after edits to generated docs, reports, build outputs, or validation mappings.
- Map each final observability claim for the changed signal scope to current evidence.
- Use a command, telemetry query, trace lookup, alert check, dashboard, synthetic event, owner approval, or explicit residual risk.

- For synthetic events, fixtures, dashboard exports, or generated docs, record the source-of-truth input and output owner.
- Also record redaction, diff review, and rollback for those generated artifacts.
- For live queries, connector exports, consoles, deploys, migrations, rollbacks, or production alert changes, require available permission or sandbox proof.
- Redact tenant, user, and secret-bearing values from that evidence.
- State its retention limits.
