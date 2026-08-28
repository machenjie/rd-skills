---
name: integration-change-builder
description: "Use `analysis-agent` for integration decisions or `task-agent` for cross-system/external changes involving contracts, retries, idempotency, authentication, or reconciliation. Skip isolated work with no integration edge."
---

# integration-change-builder

## Role

- **Analysis mode (`analysis-agent`):** Decide contract, authority, and failure behavior.
- **Task mode (`task-agent`):** Apply the boundary and reconciliation.

## When To Use

- cross worker merge
- external integration change
- shared contract alignment

## Do Not Use

- isolated change with no integration edge
- unrelated source inspection

## Required Inputs

- component handoffs
- contract summary
- **Analysis mode (`analysis-agent`):** producer, consumer, credential, failure, and reconciliation evidence.
- **Task mode (`task-agent`):** accepted boundary decision with provider, duplicate, and recovery checks.

## Professional Decision Rules

- Keep integration decisions within declared owners, inputs, stops, and outputs.
- Align producer, consumer, provider, version, credential, and exact signed-representation contracts before changing the adapter or resolving implementation conflicts.
- Define timeout, retry, idempotency, ordering, verification, replay, unknown-outcome, partial-failure, compensation, and reconciliation behavior at the owning boundary.
- Validate the integrated diff, credential containment, mapping compatibility, and recovery behavior across affected consumers; isolated component success is insufficient.

## High-Value Gotchas

- A successful request can still leave a duplicate or unknown external effect.
- Provider sandbox behavior does not prove production credentials, quotas, ordering, or recovery.
- Signature, serialization, or adapter drift can invalidate an otherwise correct contract.

## Execution Checklist

- **Analysis mode:** Map producer, consumer, provider, credential, contract, and reconciliation authority.
- **Task mode:** Apply the accepted adapter boundary with idempotency and failure handling.
- Verify timeout, retry, duplicate, malformed, denied, and unknown-outcome behavior.
- Record provider assumptions and untested recovery paths as residual risk.
- Minimal validation: run contract and failure tests at the real adapter or calibrated sandbox.

## Stop / Escalation Conditions

Block unknown provider/environment/credential/reconciliation authority or unproved signed bytes/order, duplicates/failures, sensitive data, or adapter mappings; escalate material production/provider/combined-impact/weak-recovery risk.

## Output Contract

- **Analysis mode (`analysis-agent`):** integration design; authority and failure decisions; reconciliation model.
- **Task mode (`task-agent`):** integrated boundary changes; conflict and credential decisions; unresolved provider risk.

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [checklist](references/checklist.md) | decision-checklist | Closing or reviewing an external integration change needs provider-contract, timeout, retry/backoff, circuit-breaker, idempotency, webhook/replay, credential, reconciliation, test, and monitoring checks | The inline Skill quality gate is sufficient for an L1 read or a deeper capability reference already covers the same checklist with task-specific detail | analysis-agent, task-agent | checklist-result, validation-plan |
| [index](references/index.md) | index | competing integration change builder references require dependency, conflict, or output-fragment selection | the integration change builder root or a task-named reference already resolves selection | analysis-agent, task-agent | reference-selection |
| [solution optimality](references/solution-optimality.md) | targeted | An outbound call, webhook, provider migration, retry, concurrency, delivery, or reconciliation design has a material failure, latency, cost, or state-consistency tradeoff | The provider contract and accepted task already determine a bounded adapter change with no material delivery or failure-mode choice | analysis-agent, task-agent | failure-decision, residual-risk |
