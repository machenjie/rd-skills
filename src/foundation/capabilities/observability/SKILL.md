---
name: observability
description: "`analysis-agent`/`task-agent`/`review-agent`: primary-Skill-selected for logs, metrics, traces, alerts, SLI/SLO, or diagnostics; never task owner; skip without signal impact."
---

# observability

## Registry Trigger

**Use when**

- design logs metrics traces dashboards alerts SLI and diagnostic context

**Do not use when**

- no task-local observability decision is required

## Skill Role

Select privacy-safe, correlated signals that prove material impact and guide an accountable operator action.

## High-Value Rules

- Start from material user, system, invariant, security, compliance, or audit impact, then choose only signals that guide an operator decision.
- Permit telemetry only with secret-free values, bounded labels, and approved protection for investigation identifiers.
- Create root correlation or trace context at operation entry when absent, then propagate it across triggered boundaries needed to join the evidence.
- Give alerts a condition, owner, severity, and response.
- Define or adjust an SLI/SLO only for an existing objective or triggered risk, and prove its semantics.

## Anti-Patterns

- Unbounded labels can exhaust the metrics backend and destabilize alerts.
- Correlation without privacy controls creates a cross-system data leak.
- A signal that cannot change an operator action is noise, not release evidence.

## Execution Checklist

1. Name the material impact or invariant, failure mode, operator question, and signal gap.
2. Select bounded fields, correlation, retention/access, and actionable signals.
3. Verify signal emission, joins, label bounds, privacy, alert action, and SLI semantics.

## Stop Conditions

Escalate inaccurate SLI semantics, sensitive-data exposure, an unobservable critical flow, or an alert or dead-man signal with no owner and response.

## Output Contract

- observability plan with signals dashboards alerts and investigation paths, evidence, and proof limits

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | signal alert SLI trace or runbook choices remain unresolved | operator decision and existing objective determine required signals | analysis-agent, task-agent, review-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | change affects user impact correlation metrics traces alerts or ownership | no operational signal or response behavior changes | analysis-agent, task-agent, review-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | dashboard alert propagation or runbook claims need fresh proof | current queries configs and synthetic checks prove each claim | analysis-agent, task-agent, review-agent | evidence-record, proof-limit, residual-risk |
