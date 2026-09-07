# Observability Checklist

- Identify user impact, operational owner, investigation path, and the named operator or risk question.
- Select the signal families that answer that question and record why omitted log, metric, trace, profile, event/audit, dashboard, or alert families are not needed.
- For each selected family, define producer, schema or context, privacy/cardinality/sampling/retention limits, expected observation, and owner action.
- Preserve correlation or trace context across selected signals when the investigation requires a cross-boundary join.
- Define dashboards and actionable alerts when the named question requires persistent views or notification, with thresholds and owners.
- Verify selected signals and recorded omissions in test, staging, or post-release checks.

## Anti-Patterns

- Unbounded labels can exhaust the metrics backend and destabilize alerts.
- Correlation without privacy controls creates a cross-system data leak.
- A signal that cannot change an operator action is noise, not release evidence.

## Execution Checklist

1. Name the material impact or invariant, failure mode, operator question, and signal gap.
2. Select bounded fields, correlation, retention/access, and actionable signals.
3. Verify signal emission, joins, label bounds, privacy, alert action, and SLI semantics.
