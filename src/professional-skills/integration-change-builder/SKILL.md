---
name: integration-change-builder
description: "Use `analysis-agent` for integration decisions or `task-agent` for cross-system/external changes involving contracts, retries, idempotency, authentication, or reconciliation. Skip isolated work with no integration edge."
---

# integration-change-builder

## Role

Support `analysis-agent` and `task-agent` for bounded cross-component and external-integration changes.

- **Analysis mode (`analysis-agent`):** Decide cross-boundary contract, authority, and failure behavior.
- **Task mode (`task-agent`):** Apply the accepted boundary and reconciliation behavior.

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

- Align affected producer and consumer contracts before resolving implementation conflicts.
- Define triggered timeout, retry, idempotency, ordering, authentication, version-skew, and partial-failure behavior at the boundary.
- Derive the exact signed representation and permitted transformation or canonicalization from the current provider contract.
- Preserve raw bytes only when the current provider contract defines raw bytes as the signed representation.
- Complete verification, freshness, and replay checks before an operation changes the signed representation or causes effects.
- Keep integration ownership explicit; do not hide a shared contract inside a local adapter.
- Validate the integrated diff and changed cross-boundary behavior, not only isolated components.

## High-Value Gotchas

- Passing component tests does not prove the integrated contract.
- Retries across a non-idempotent boundary amplify failures.
- Conflict resolution can silently choose one owner’s incompatible assumption.

## Execution Checklist

1. Trace producer, consumer, authority, timeout, duplicate, and partial-failure behavior across the boundary.
2. Choose retry, idempotency, reconciliation, and version-skew controls from provider semantics.
3. Derive the exact signed representation and permitted transformation or canonicalization from the current provider contract.
4. Prove verification, freshness, and replay checks precede representation-changing operations and effects.
5. Verify credential containment, recovery, and integrated consumer behavior.
6. **Analysis mode:** select timeout, duplicate, and reconciliation behavior from provider evidence.
7. **Task mode:** apply the accepted boundary across producer and consumer paths.
8. Stop when provider authority or reconciliation ownership remains unknown.

## Stop / Escalation Conditions

Block when:
- affected provider, credential, sandbox/production, or reconciliation authority is unknown and changes acceptance, security, data, or release;
- the current provider contract does not establish the exact signed representation or permitted transformation or canonicalization;
- raw-byte preservation is assumed without provider evidence that raw bytes are the signed representation;
- evidence cannot prove verification, freshness, and replay checks precede representation-changing operations and effects;
- a retried external write lacks idempotency scope, duplicate-result behavior, aggregate retry budget, or compensation or reconciliation;
- payload, signature, token, cookie, authorization, secret, or credential data could enter logs, source, images, configuration, or generated artifacts;
- provider or generated models escape the adapter without version, null, and default mapping.

Escalate consequential, no-sandbox, no-reconciliation, provider-contract, production-release, combined high-impact, or unclear-rollback risk.

## Output Contract

- **Analysis mode (`analysis-agent`):** integration design; authority and failure decisions; reconciliation model.
- **Task mode (`task-agent`):** integrated boundary changes; conflict and credential decisions; unresolved provider risk.

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [checklist](references/checklist.md) | decision-checklist | Closing or reviewing an external integration change needs provider-contract, timeout, retry/backoff, circuit-breaker, idempotency, webhook/replay, credential, reconciliation, test, and monitoring checks | The inline Skill quality gate is sufficient for an L1 read or a deeper capability reference already covers the same checklist with task-specific detail | analysis-agent, task-agent | checklist-result, validation-plan |
| [index](references/index.md) | index | competing integration change builder references require dependency, conflict, or output-fragment selection | the integration change builder root or a task-named reference already resolves selection | analysis-agent, task-agent | reference-selection |
| [solution optimality](references/solution-optimality.md) | targeted | An outbound call, webhook, provider migration, retry, concurrency, delivery, or reconciliation design has a material failure, latency, cost, or state-consistency tradeoff | The provider contract and accepted task already determine a bounded adapter change with no material delivery or failure-mode choice | analysis-agent, task-agent | failure-decision, residual-risk |
