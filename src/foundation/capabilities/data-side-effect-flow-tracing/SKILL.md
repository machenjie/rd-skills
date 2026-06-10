---
name: data-side-effect-flow-tracing
description: Traces input, validation, mapping, policy, mutation, transaction, persistence, cache, events, external IO, observability, idempotency, and compensation so side effects stay visible at owned boundaries.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "113"
changeforge_version: 0.1.0
---

# Mission

Make data flow and side effects visible, ordered, testable, and owned so writes, cache changes, events, logging, metrics, file IO, clock/random/env reads, and external calls do not hide in mappers, getters, policies, or domain objects.

# When To Use

Use when a change validates, maps, mutates, persists, publishes events, invalidates cache, calls external APIs, writes files, reads time/random/env, logs, emits metrics, opens transactions, uses an outbox, or needs idempotency or compensation.

Use when a mapper, getter, policy, domain method, decorator, proxy, helper, or repository hides side effects.

# Do Not Use When

Do not use for pure local transformations with no mutation, IO, time/random/env read, or observable side effect.

Do not use to forbid local conventions where a framework visibly owns side effects and tests can prove the boundary.

# Non-Negotiable Rules

- Pure decision logic and side effects are separated unless local convention proves otherwise.
- Side effects must be visible in service, adapter, repository, or job boundary.
- Events must not publish before commit unless explicitly safe.
- Cache mutation must name source of truth and invalidation.
- Mappers and getters must not mutate external state.
- Logging and metrics must not alter behavior.
- External IO has timeout, cancellation, retry, and cleanup.

# Industry Benchmarks

Anchor against command-query separation, transactional outbox, publish-after-commit, unit-of-work patterns, idempotent side-effect design, source-of-truth cache discipline, OpenTelemetry observability, and saga compensation for multi-step effects.

# Selection Rules

Select this capability when the primary risk is hidden or misordered side effects. Use `transaction-consistency` for atomicity, `cache-design` for cache correctness, `domain-event-modeling` or `event-driven-architecture` for event contracts, `idempotency-retry-design` for duplicate safety, and `failure-contract-design` for failure semantics.

# Risk Escalation Rules

Escalate to `data-middleware-change-builder` when persistence, cache, queue, search, or storage owns the side effect. Escalate to `integration-change-builder` for external API effects. Escalate to `reliability-observability-gate` when side-effect ordering affects production recovery or SLOs. Escalate to `security-privacy-gate` when side effects can leak or mutate sensitive data.

# Critical Details

- Trace input to validation, mapping, policy, mutation, transaction, persistence, event, cache, external IO, response.
- Classify side effects: persistence write, cache mutation, event publish, external API, logging, metrics, file IO, clock/random/env read, timer, subscription, network call.
- Transaction boundary must state what is inside and outside commit.
- Outbox is preferred when event publish must follow durable state change.
- Publish-after-commit prevents consumers from seeing uncommitted or rolled-back state.
- Cache mutation names source of truth, key scope, invalidation order, and stale tolerance.
- Idempotency names duplicate key, side-effect replay behavior, and response replay behavior.
- Compensation names what is undone, what cannot be undone, and how operators observe it.
- Observability should record side-effect start/end/failure without changing outcome.

# Failure Modes

- Mapper writes DB, updates cache, emits event, or calls HTTP.
- Getter reads environment or clock and changes behavior unpredictably.
- Event publishes before transaction commit and consumers observe rolled-back data.
- Cache invalidation happens before failed persistence or with unclear source of truth.
- Logging callback mutates state or swallows errors.
- External IO lacks timeout, cancellation, retry bounds, or cleanup.
- Multi-step side effects are not idempotent and have no compensation.

# Output Contract

Return a Data and Side-Effect Flow Map:

- Input source.
- Validation boundary.
- Mapping boundary.
- Policy decision.
- Mutation boundary.
- Transaction boundary.
- Persistence, cache, event, external IO, file IO, clock/random/env, logging, and metrics.
- Ordering.
- Outbox or publish-after-commit decision.
- Idempotency and compensation.
- Observability.
- Tests.
- Residual side-effect risk.

# Evidence Contract

Close the map only when changed side effects are enumerated, their owners and order are named, transaction/cache/event/external IO behavior is tested or reviewed, hidden-side-effect locations are scanned, validation evidence is recorded, and residual ordering/idempotency risk is explicit.

# Quality Gate

1. Pure decisions and side effects are separated or the convention exception is documented.
2. Side effects are visible at service, adapter, repository, or job boundaries.
3. Events publish after commit or the pre-commit publish is explicitly safe.
4. Cache mutation names source of truth and invalidation strategy.
5. Mappers and getters do not mutate external state.
6. Logging and metrics do not alter behavior.
7. External IO has timeout, cancellation, retry, and cleanup.
8. Tests cover ordering, failure, and idempotency where material.

# Used By

- backend-change-builder
- data-middleware-change-builder
- integration-change-builder
- reliability-observability-gate
- ai-code-review-refactor
- quality-test-gate
- architecture-impact-reviewer

# Handoff

Hand off to `transaction-consistency`, `cache-design`, `message-queue-design`, `domain-event-modeling`, `idempotency-retry-design`, `failure-contract-design`, or `observability` for deeper side-effect-specific design.

# Completion Criteria

The capability is complete when the data path and every side effect have an owner, boundary, order, transaction/cache/event policy, idempotency or compensation stance, observability, tests, and residual risk statement.
