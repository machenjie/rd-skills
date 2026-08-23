# Observability Evidence Patterns

Use this evidence map for a named signal, correlation, alert, dashboard, privacy/cardinality, freshness, or proof-limit claim; it is not a second observability tutorial.

## Changed-Signal-To-Validation Map

| Claim | Minimum current evidence | Proves / limit |
| --- | --- | --- |
| SLI/SLO measurable | Journey, formula, labels/window, owner, panel, current query/config. | Named journey; not historic baseline, scale, or every segment. |
| Log safe/queryable | Fields, exclusions/redaction, correlation, sample query, source/config. | Inspected event; not every caller, sink, or retention rule. |
| Labels bounded | Allowed values/estimate, rejected unbounded fields, metric query. | Obvious inspected risk; not production skew/cost. |
| Trace current | Ingress/outbound/async propagation, span names, lookup or source proof. | Named path; not siblings/provider sampling. |
| Alert/dashboard actionable | Query, threshold, severity, owner, runbook action, panel path, sample event when feasible. | Start of named response; not alert fatigue or incident efficacy. |
| Evidence fresh | Command/query, environment, outcome, artifact, final-edit freshness. | Post-edit scope; not later source/config/report edits. |

## Freshness Rules

- Treat prior repository, task, dashboard, incident, generated-doc, validation, and action-sequence evidence as discovery.
- Confirm discovery through current source, configuration, query, or bounded validation.
- Reopen after changes to fields, metric names, labels, spans, propagation, alerts, dashboards, runbooks, generated docs, reports, builds, or validation maps.
- Map each final changed-signal claim to current command/query/lookup/check/dashboard/event/approval evidence or an explicit residual owner.

## Tool Boundary And Handoff

- Synthetic events and generated artifacts record source input, output owner, redaction, diff review, and rollback.
- Live queries/exports/consoles/deploys/rollbacks require available permission or sandbox evidence.
- Redact tenant, user, and secret values and state retention limits.
- Handoff records changed signal, producer/schema, query/artifact, owner action, current result, freshness, proof limit, and residual risk.
