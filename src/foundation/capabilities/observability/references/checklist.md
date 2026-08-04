# Observability Checklist

- Identify user impact, operational owner, investigation path, and the named operator or risk question.
- Select the signal families that answer that question and record why omitted log, metric, trace, profile, event/audit, dashboard, or alert families are not needed.
- For each selected family, define producer, schema or context, privacy/cardinality/sampling/retention limits, expected observation, and owner action.
- Preserve correlation or trace context across selected signals when the investigation requires a cross-boundary join.
- Define dashboards and actionable alerts when the named question requires persistent views or notification, with thresholds and owners.
- Verify selected signals and recorded omissions in test, staging, or post-release checks.
