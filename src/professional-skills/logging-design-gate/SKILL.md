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

- Keep the selected logging design gate decision within its declared owner, inputs, stops, and output contract.

## High-Value Gotchas

- More events can reduce diagnostic value through volume, cardinality, or duplicate noise.
- Redaction after formatting can expose sensitive values before the sink applies policy.
- A schema change can silently break alerts, audit consumers, or correlation.

## Execution Checklist

- **Task mode:** Map the diagnostic question to its event owner, placement, schema, and sink.
- **Task mode:** Apply approved field classification, redaction, level, and correlation decisions.
- **Review mode:** Compare emitted and suppressed paths with purpose and safe-logging evidence.
- Record unmeasured volume, consumer drift, and inaccessible sink behavior as residual risk.
- Minimal validation: run emission and suppression tests at the selected sink boundary.

## Stop / Escalation Conditions

- Stop without a named question, event owner, placement, consumer meaning, current data/sink policy, and negative proof.
- Stop unbounded volume/cardinality or sensitive evidence without measured bounds, authority, redaction, scope, and recovery.

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
