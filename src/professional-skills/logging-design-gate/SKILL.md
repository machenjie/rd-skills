---
name: logging-design-gate
description: "Use `task-agent` for bounded logging changes or `review-agent` to independently assess placement, schema, severity, redaction, correlation, and signal tradeoffs. Skip work with no logging impact and self-review requests."
---

# logging-design-gate

## Role

Support `task-agent` and `review-agent` for bounded logging decisions.

- **Task mode (`task-agent`):** Apply the accepted logging purpose, placement, and schema.
- **Review mode (`review-agent`):** Judge logging against purpose, safety, and signal criteria.

## When To Use

- logging schema or redaction change
- diagnostic gap

## Do Not Use

- no logging impact
- self review request

## Required Inputs

- acceptance
- logging decision
- **Task mode (`task-agent`):** event boundary, logger policy, sensitive-field classification, and signal checks.
- **Review mode (`review-agent`):** changed event paths with safe-logging evidence.

## Professional Decision Rules

- Log only for a named diagnostic, audit, security, or operational question; prefer another signal or no new signal when it answers better.
- Place one event at the boundary owning the outcome; do not duplicate intermediate retries, wrappers, and terminal failures.
- Select level and stable schema from current logger policy, event meaning, and reachable failure states.
- Allow only purpose-required fields; omit or transform secrets, credentials, sensitive payloads, and unnecessary personal data under current policy.
- Preserve only the correlation needed across affected request, trace, message, or job boundaries without exposing raw identity.
- Bound material rate, value-space, retention, access, sink, cost, cardinality, and audit risk with measured/platform evidence and an owner.

## High-Value Gotchas

- Raw payload logging creates a durable privacy incident.
- Intermediate retry errors can create false incidents before the terminal outcome is known.
- High-cardinality fields, hot-path events, or an error without useful context can make the signal unusable.

## Execution Checklist

1. Trace the named operational question to one owning event boundary and consumer action.
2. Choose level, schema, fields, redaction, correlation, and sink from current policy.
3. Verify failure visibility, duplicate emission, cardinality, rate, retention, and sensitive-data behavior.
4. **Task mode:** apply the logging decision at the owning event boundary.
5. **Review mode:** judge every changed event path against safe-logging criteria.
6. Stop when event purpose, owner, or data classification is unproven.

## Stop / Escalation Conditions

- Stop without a named question, event owner, and placement; operational logs need an action, while audit evidence needs a consumer and protected meaning.
- Stop when fields, correlation, retention, access, or sinks can expose classified data without policy-consistent transformation and negative proof.
- Stop volume/cardinality risk without bounded rate or value-space evidence and an owned control or no-log outcome.
- Stop sensitive evidence actions without permission, sandbox, redaction, bounded scope, and rollback or cleanup.

## Output Contract

- **Task mode (`task-agent`):** logging changes; placement and redaction evidence; signal risk.
- **Review mode (`review-agent`):** logging verdict; unsafe event findings; unproven signal behavior.

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [checklist](references/checklist.md) | decision-checklist | A bounded L2 mode needs compact checks for its triggered purpose, placement, fields, redaction, level, signal split, or validation risk | The root contract is enough or targeted proof fields are required | task-agent, review-agent | checklist-result, validation-plan |
| [index](references/index.md) | index | competing logging design gate references require dependency, conflict, or output-fragment selection | the logging design gate root or a task-named reference already resolves selection | task-agent, review-agent | reference-selection |
| [logging output and gates](references/logging-output-and-gates.md) | targeted | L3-L5 implementation or review needs mode-specific closure and targeted gates for selected purpose, placement, schema safety, correlation, volume, sink, or failure-visibility risk | The root result is sufficient and no selected risk needs the extended proof contract | task-agent, review-agent | gate-decision, residual-risk |
| [logging selection criteria](references/logging-selection-criteria.md) | targeted | A concrete purpose, level, field, redaction, correlation, placement, or signal choice needs more detail than the root contract | The root contract determines the no-log or bounded logging decision | task-agent, review-agent | selected-approach, residual-risk |
