---
name: frontend-api-integration
description: "`task-agent`: use when frontend API loading, cancellation, retries, auth expiry, pagination, stale data, errors, or optimistic updates change; skip when no integration changes."
---

# frontend-api-integration

## Registry Trigger

**Use when**

- integrate frontend with API loading caching errors retries and optimistic updates

**Do not use when**

- no task-local frontend api integration decision is required

## Skill Role

Implement request identity, API contract use, cancellation, stale-response handling, cache and pagination semantics, authentication-expiry coordination, optimistic reconciliation, user-visible failures, and integration evidence. Exclude API and authorization design.

## High-Value Rules

- **Bind requests to current user intent.** Define input identity, tenant or account context, cache key, supersession, cancellation, and late-response ordering so stale work cannot overwrite newer state.
- **Consume the declared API contract.** Map request and response fields, errors, pagination, empty values, compatibility, and partial outcomes without inferring behavior from one successful sample.
- **Coordinate authentication expiry centrally.** Follow the current session and replay contract, prevent refresh amplification, preserve safe navigation intent, and avoid replaying consequential requests whose commit status is unknown.
- **Model cache freshness and invalidation.** Identify authoritative source, key dimensions, ownership, stale allowance, mutation effects, pagination interaction, account switching, and recovery after invalidation failure.
- **Treat pagination and streaming as changing datasets.** Define cursor or offset stability, duplicate and missing item behavior, ordering, filter changes, cancellation, completion, and reconciliation with concurrent updates.
- **Reconcile optimistic and unknown outcomes.** Preserve prior state, operation identity, server authority, rejection, timeout, duplicate submission, rollback or forward reconciliation, and user-visible uncertainty.
- **Prove negative integration paths.** Exercise malformed and partial responses, denial, expiry, timeout, cancellation, stale arrival, retry exhaustion, pagination drift, and cache divergence relevant to the task.

## Anti-Patterns

- Couple request execution directly to rendering so navigation, cancellation, or account change leaves stale mutation behind.
- Retry or replay writes after timeout without idempotency or authoritative outcome reconciliation.
- Treat transport success as domain completion, or collapse denial, absence, validation, and dependency failure into one generic message.

## Stop Conditions

Escalate when API/session semantics are unknown, replay can duplicate consequential effects, cache identity crosses users or tenants, or stale responses cannot be ordered. Also escalate when optimistic rollback can lose state, or affected contract and negative paths cannot be exercised.

## Output Contract

- frontend integration decision with request identity, API mapping, session-expiry behavior, cancellation, cache and pagination semantics, optimistic reconciliation, negative-path evidence, and residual owners

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | Cancellation, retry, caching, or response-mapping strategies remain open | No remote request lifecycle behavior changes | task-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | UI operations span auth expiry, conflicts, pagination, or optimistic rollback | The change performs only synchronous local computation | task-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | Integration claims require fresh clients, schemas, mocks, and race tests | No operation-lifecycle or contract claim needs proof | task-agent | evidence-record, proof-limit, residual-risk |
