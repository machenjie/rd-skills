---
name: data-side-effect-flow-tracing
description: Use when validation, mapping, policy, persistence, cache, events, external IO, file IO, time/random/env, logging, metrics, idempotency, or compensation can hide or misorder side effects across owned boundaries.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "113"
changeforge_version: 0.1.0
---

# Mission

Make data flow and side effects visible, ordered, testable, owned, and fresh against the repository graph so writes, cache changes, events, logging, metrics, file IO, clock/random/env reads, and external calls do not hide in mappers, getters, policies, or domain objects.

# When To Use

Use when a change validates, maps, mutates, persists, publishes events, invalidates cache, calls external APIs, writes files, reads time/random/env, logs, emits metrics, opens transactions, uses an outbox, or needs idempotency or compensation.

Use when a mapper, getter, policy, domain method, decorator, proxy, helper, or repository hides side effects.

Use when test confidence depends on the order of validation, mapping, authorization, mutation, persistence, event publication, cache invalidation, external IO, file IO, observability, retry, or compensation.

# Do Not Use When

Do not use for pure local transformations with no mutation, IO, time/random/env read, or observable side effect.

Do not use to forbid local conventions where a framework visibly owns side effects and tests can prove the boundary.

Do not use as a replacement for `transaction-consistency`, `cache-design`, `message-queue-design`, `idempotency-retry-design`, `failure-contract-design`, or `observability` when the side effect is already visible and the deeper design problem belongs to that capability.

# Stage Fit

Use during planning, coding, bug-fix, debugging, code-review, refactoring, testing, release readiness, validation mapping, repair, and final handoff when a code path crosses from pure decisions into mutation or IO. Re-run after material edits that add, remove, move, or reorder a side effect, because earlier flow evidence becomes stale when the call path, transaction boundary, cache key, event publisher, adapter, retry wrapper, or test target changes.

# Non-Negotiable Rules

- Pure decision logic and side effects are separated unless local convention proves otherwise.
- Every side effect has an owner boundary, execution order, failure behavior, retry or no-retry stance, and validation evidence.
- Side effects must be visible in service, adapter, repository, job, handler, or explicitly documented framework boundary.
- Trace the path from input to terminal state: response, durable write, queued work, emitted event, skipped operation, compensation, or operator-visible failure.
- Events must not publish before durable commit unless an explicit pre-commit contract proves consumers cannot observe rolled-back or uncommitted state.
- Cache mutation must name source of truth, key scope, invalidation or write-through policy, stale tolerance, and failure behavior.
- Mappers, getters, serializers, schema converters, validators, policy checks, and domain objects must not mutate external state unless the local framework contract makes that effect explicit and tested.
- Logging, tracing, and metrics must not alter business outcome, swallow material errors, or create hidden durable side effects.
- External IO and file IO need timeout, cancellation, retry bounds, cleanup, idempotency or duplicate-safety stance, and observable failure.
- Repository graph and project memory are leads, not proof: verify current code paths and tests before claiming the flow is covered.

# Industry Benchmarks

Anchor against command-query separation, transactional outbox, publish-after-commit, unit-of-work patterns, idempotent side-effect design, source-of-truth cache discipline, OpenTelemetry observability, saga compensation for multi-step effects, durable retry queues, consumer idempotency, and audit-ready failure ledgers.

# Mode Matrix

| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities |
| --- | --- | --- | --- | --- |
| Hidden side effect scan | Mapper, getter, validator, policy, serializer, decorator, proxy, helper, or domain method may write, publish, cache, call IO, read env/time/random, log with callbacks, or emit metrics with behavior impact. | Separate pure decisions from effects and expose the owning boundary. | Callers, callees, side-effect inventory, convention exception, tests or review evidence. | `model-boundary-mapping`, `implementation-structure-design` |
| Transaction and event ordering | Event, outbox, queue publish, cache invalidation, external notification, or file write occurs around commit. | Prevent consumers from seeing rolled-back state and name durable ordering. | Transaction boundary, publish point, outbox decision, rollback behavior, consumer visibility. | `transaction-consistency`, `message-queue-design` |
| Cache and source-of-truth flow | Cache is read, populated, invalidated, or updated near persistence. | Preserve source of truth, key scope, and stale tolerance. | Source of truth, key dimensions, invalidation order, failure handling, freshness tests. | `cache-design`, `repository-persistence` |
| External or file IO effect | HTTP/RPC/provider/file/storage call occurs in a service, job, adapter, transaction, retry, or compensation path. | Bound latency, failure, cleanup, idempotency, and duplicate behavior. | Timeout, cancellation, retry policy, idempotency key, cleanup, operator visibility. | `integration-change-builder`, `file-storage-processing` |
| Nondeterministic input | Clock, random, environment, process state, or feature flag changes behavior. | Make nondeterminism injectable, named, and testable. | Source, read boundary, default, test override, replay or audit implication. | `configuration-runtime-policy`, `testability-seam-design` |
| Multi-step compensation | Multiple durable effects can partially succeed. | Define forward recovery, compensation, reconciliation, and residual irreversible effects. | Step order, success marker, compensation action, non-reversible effect, reconciliation test. | `idempotency-retry-design`, `failure-contract-design` |

# Selection Rules

Select this capability when the primary risk is hidden, misplaced, stale, unowned, or misordered side effects. Use it before deeper design capabilities when the first question is "what changes state, where, and in what order?"

Use `transaction-consistency` for atomicity and isolation decisions after the effect path is visible. Use `cache-design` for cache correctness after source of truth and key scope are known. Use `message-queue-design`, `domain-event-modeling`, or `event-driven-architecture` for event and queue contracts after publish timing is known. Use `idempotency-retry-design` for duplicate safety after every side effect and replay point is inventoried. Use `failure-contract-design` for surfaced error semantics after failure points are named.

Pair with `repository-graph-analysis` when owners, callers, generated wrappers, consumers, cache users, or affected tests are unclear. Pair with `project-memory-governance` when prior incidents, stale assumptions, or previous validation gaps may indicate hidden effects, but confirm against current source before acting.

# Technical Selection Criteria

Evaluate the flow by input source, trust boundary, validation boundary, mapping boundary, policy decision, mutation command, transaction scope, persistence write, event or queue publish, cache action, external IO, file IO, nondeterministic read, observability effect, retry wrapper, compensation path, consumer visibility, test edge, and residual risk. A side effect is professionally handled only when its owner, order, failure mode, duplicate behavior, observability, and validation status are concrete.

# Proactive Professional Triggers

- **Signal:** A mapper, getter, schema converter, serializer, validator, policy, or domain method calls a repository, cache, queue, HTTP client, file API, logger callback, metric callback, clock, random source, environment, or feature flag. **Hidden risk:** pure-looking code changes state, leaks data, becomes nondeterministic, or becomes untestable. **Required professional action:** classify the effect, move or document the owning boundary, and prove tests cover the visible path. **Route to:** `model-boundary-mapping`, `testability-seam-design`. **Evidence required:** same-pattern scan, owner boundary, exception rationale, test or review evidence.
- **Signal:** Event, queue publish, webhook, notification, cache invalidation, search indexing, file write, or external call happens before or inside a transaction commit. **Hidden risk:** consumers observe rolled-back state, duplicate work, or partial effects. **Required professional action:** define publish-after-commit, outbox, compensation, or explicit safe pre-commit contract. **Route to:** `transaction-consistency`, `message-queue-design`. **Evidence required:** transaction boundary, commit point, consumer visibility, rollback behavior.
- **Signal:** Cache write or invalidation sits near persistence without source-of-truth and stale-tolerance language. **Hidden risk:** failed writes, reordered invalidation, or broad keys serve stale or unauthorized data. **Required professional action:** name source of truth, key scope, invalidation order, and failure behavior. **Route to:** `cache-design`, `permission-boundary-modeling` when access scope is material. **Evidence required:** key dimensions, source path, stale policy, tests or reviewer proof.
- **Signal:** External IO, file IO, storage write, provider call, or webhook occurs without timeout, cancellation, retry bounds, cleanup, or idempotency. **Hidden risk:** latency, duplicate side effects, leaked resources, and unreconciled partial completion. **Required professional action:** bound the call, define duplicate behavior, and expose failure to recovery or operators. **Route to:** `integration-change-builder`, `idempotency-retry-design`, `failure-contract-design`. **Evidence required:** adapter boundary, timeout, retry/no-retry decision, idempotency key or compensation.
- **Signal:** Clock, random, env, process state, or feature flag is read from business logic, mapping, validation, or policy code. **Hidden risk:** non-replayable behavior, test flake, hidden config dependency, or audit mismatch. **Required professional action:** inject or centralize the nondeterministic source and name default/test behavior. **Route to:** `configuration-runtime-policy`, `testability-seam-design`. **Evidence required:** source boundary, test override, replay/audit impact.
- **Signal:** Logging, tracing, or metrics path invokes callbacks, lazy fields, redaction hooks, async exporters, or error swallowing. **Hidden risk:** observability changes behavior, persists sensitive data, or hides material failure. **Required professional action:** keep observability side effects non-authoritative and privacy-safe. **Route to:** `observability`, `logging-error-handling`, `security-privacy-gate`. **Evidence required:** emitted fields, redaction stance, error handling, no-business-outcome proof.
- **Signal:** Tests validate only the happy response while durable writes, cache, events, external calls, retries, and compensation are unasserted. **Hidden risk:** the visible API passes while side-effect order is broken. **Required professional action:** map side-effect assertions or disclose missing coverage and choose broader validation. **Route to:** `quality-test-gate`, `validation-broker`. **Evidence required:** affected tests, missing test edge, selected validator, residual risk.

# Risk Escalation Rules

Escalate to `data-middleware-change-builder` when persistence, cache, queue, search, storage, or indexing owns the side effect. Escalate to `integration-change-builder` for external API effects, webhooks, provider calls, or reconciliation. Escalate to `reliability-observability-gate` when side-effect ordering affects production recovery, retry storms, duplicate work, resource cleanup, or SLOs. Escalate to `security-privacy-gate` when side effects can leak, persist, publish, cache, log, or mutate sensitive data. Escalate to `quality-test-gate` and `validation-broker` when the flow cannot be verified with existing tests.

# Reference Loading Policy

Current mode is inline-only: this capability has no deep reference files today, so this `SKILL.md` contains the active data and side-effect flow rules.

If deep references are added later, load them only for L3+ work, cross-boundary transactions, mapper/getter side effects, event-before-commit risk, cache source-of-truth ambiguity, external IO, idempotency, or compensation.

Do not load deep references for L1/L2 local flow edits where the inline output contract for input-to-response map, ordering decision, and side-effect visibility is enough.

# Critical Details

- Trace input to validation, mapping, policy, mutation, transaction, persistence, event, cache, external IO, response.
- Include skipped and terminal states: rejected validation, denied permission, no-op update, queued work, compensation, reconciliation, and operator-visible failure.
- Classify side effects: persistence write, cache mutation, event publish, queue enqueue, search indexing, external API, webhook, logging, metrics, tracing, file IO, storage IO, clock/random/env read, timer, subscription, network call, lock, and process signal.
- Transaction boundary must state what is inside and outside commit.
- Outbox is preferred when event publish must follow durable state change.
- Publish-after-commit prevents consumers from seeing uncommitted or rolled-back state.
- Cache mutation names source of truth, key scope, invalidation order, and stale tolerance.
- Idempotency names duplicate key, side-effect replay behavior, and response replay behavior.
- Compensation names what is undone, what cannot be undone, and how operators observe it.
- Observability should record side-effect start/end/failure without changing outcome.
- Same-pattern scans cover sibling mappers, validators, policies, repositories, adapters, jobs, decorators, and generated wrappers that could hide the same effect.
- Repository graph evidence covers current callers, callees, consumers, transaction owners, cache users, adapter implementations, and affected tests; project memory can raise suspicion but cannot replace current-source inspection.
- Validation evidence must be fresh for the final material path; if code changes after the map, rerun or downgrade the claim.

# Execution Coupling

- **Repository graph:** inspect the owning method, upstream callers, downstream adapters, transaction owner, cache key users, event consumers, queue consumers, generated wrappers, and directly affected tests before claiming a side effect is visible.
- **Project memory:** use prior incidents, fragile files, known hidden side-effect patterns, and stale validation notes only as search leads; reject memory that conflicts with current source.
- **Execution path:** connect planned edits and validation commands to the flow map, so implementation does not move a side effect without updating tests and handoff.
- **Freshness:** mark the map stale when later edits alter call order, transaction scope, adapter boundary, cache key, event topic, retry wrapper, or test target.
- **Plan consistency:** after repair or review findings, re-check the side-effect inventory and owner table before final closure.

# Failure Modes

- **Hidden mapper effect:** Mapper writes DB, updates cache, emits event, or calls HTTP.
- **Nondeterministic getter:** Getter reads environment or clock and changes behavior unpredictably.
- **Ghost event:** Event publishes before transaction commit and consumers observe rolled-back data.
- **Cache drift:** Cache invalidation happens before failed persistence or with unclear source of truth.
- **Behavioral logging:** Logging callback mutates state or swallows errors.
- **Unbounded IO:** External IO lacks timeout, cancellation, retry bounds, or cleanup.
- **Partial saga:** Multi-step side effects are not idempotent and have no compensation.
- **Unsafe retry:** Retry wrapper repeats a non-idempotent write, publish, or provider call.
- **Orphaned file:** File or storage write succeeds while database state rolls back and no cleanup or reconciliation exists.
- **Sensitive telemetry:** Metrics, tracing, or logging persists sensitive fields or changes error behavior.
- **Hidden framework hook:** Framework hook, decorator, ORM lifecycle callback, or generated client hides a durable side effect outside tests.
- **Stale memory:** Project memory says a path is safe but current code has drifted.

# Output Contract

Return a Data and Side-Effect Flow Map:

- `mode_selected` (hidden side effect scan, transaction and event ordering, cache and source-of-truth flow, external or file IO effect, nondeterministic input, or multi-step compensation).
- `boundaries_inspected` (input, validation, mapping, policy, mutation, transaction, persistence, cache, event/queue, external IO, file/storage IO, nondeterministic reads, observability, tests, graph, memory, and skipped boundaries with reason).
- `input_to_terminal_path` (source, trust boundary, validation result, policy decision, mutation command, terminal response or async state, and no-op/denial/compensation paths).
- `side_effect_inventory` (effect type, owner boundary, caller, callee, order, durable or transient status, duplicate behavior, failure behavior, and validation status).
- `ordering_decision` (what must happen before commit, after commit, after response, in a job, in a consumer, or never in the same transaction).
- `transaction_event_cache_policy` (transaction scope, outbox or publish-after-commit decision, cache source of truth, key scope, invalidation or write-through order, and stale tolerance).
- `external_io_file_io_policy` (adapter boundary, timeout, cancellation, retry/no-retry decision, cleanup, reconciliation, idempotency key, and operator visibility).
- `nondeterminism_and_observability` (time/random/env/flag reads, injection or centralization stance, logging/metric/trace fields, redaction, and no-business-outcome proof).
- `tests_and_validation` (same-pattern scan, affected tests, missing test edges, selected validators, freshness, and not-verified limits).
- `residual_side_effect_risk` (remaining hidden-effect, ordering, idempotency, compensation, privacy, reliability, or validation risk and next owner).

# Evidence Contract

Close the map only when these answers are concrete:

- **Basis:** changed path, flow entry point, side-effect trigger, and why hidden or ordered effects matter for the current change.
- **Current evidence:** source files, callers/callees, repositories, adapters, events/queues, cache keys, transaction owner, tests, graph leads, memory leads, and validation commands inspected.
- **Inventory:** each side effect has type, owner, order, durable/transient status, failure behavior, duplicate behavior, and observable proof.
- **Boundary decision:** pure logic, mapping, validation, policy, domain, service, repository, adapter, job, framework hook, and generated wrapper boundaries are separated or exception-tested.
- **Ordering proof:** transaction, event, queue, cache, external IO, file IO, retry, compensation, and observability order is tested, reviewed, or explicitly not verified.
- **Boundaries inspected:** entry points, callers, callees, transaction owner, repository, adapter, cache key, event/queue topic, file/storage writer, logger/metric emitter, and affected tests are named or explicitly skipped.
- **Validation evidence:** validator commands, test names, review artifacts, report paths, or not-run reasons are attached to the side-effect inventory.
- **What evidence proves:** the final visible flow, owner boundary, ordering decision, and duplicate/failure behavior that the inspected tests or reviews actually cover.
- **What evidence does not prove:** skipped consumers, untested retries, uninspected framework hooks, stale project memory, external provider behavior, or missing rollback/cleanup proof.
- **Handoff:** unresolved proof gaps name the next owner, next gate, rollback or cleanup note, and residual risk.
- **Freshness and limits:** evidence reflects the final material path; stale, partial, missing, or not-run validation is disclosed with residual risk and next owner.

# Benchmark Coverage

This capability covers command-query separation, hidden side-effect detection, publish-after-commit, transactional outbox selection, unit-of-work boundary mapping, source-of-truth cache discipline, idempotent side-effect replay, retry and compensation ordering, nondeterministic source control, observability-no-behavior-change checks, repository graph coupling, and validation freshness for side-effect maps.

# Routing Coverage

Routes from `backend-change-builder`, `data-middleware-change-builder`, `integration-change-builder`, `reliability-observability-gate`, `ai-code-review-refactor`, `quality-test-gate`, and `architecture-impact-reviewer` should arrive here when mutation or IO ownership, visibility, order, or proof is unclear. Route away when the effect is already visible and the primary question is atomicity, cache policy, event schema, retry math, failure contract, observability field design, or release readiness.

# Quality Gate

1. Pure decisions and side effects are separated or the convention exception is documented.
2. Side effects are visible at service, adapter, repository, or job boundaries.
3. Events publish after commit or the pre-commit publish is explicitly safe.
4. Cache mutation names source of truth and invalidation strategy.
5. Mappers and getters do not mutate external state.
6. Logging and metrics do not alter behavior.
7. External IO has timeout, cancellation, retry, and cleanup.
8. Tests cover ordering, failure, and idempotency where material.
9. Same-pattern scan covers sibling mappers, validators, policies, repositories, adapters, jobs, decorators, and generated wrappers likely to hide the same effect.
10. Transaction, event, queue, cache, external IO, file IO, nondeterministic input, observability, retry, and compensation order is named or explicitly out of scope.
11. Repository graph, project memory, and execution trajectory are reconciled, with memory treated as a lead rather than proof.
12. Validation evidence is fresh for the final material path; stale, partial, missing, or not-verified coverage is disclosed.
13. Sensitive data is not newly persisted, cached, published, logged, or emitted without security/privacy review.
14. Residual side-effect risk names next owner, rollback or cleanup note, and next validation gate.

# Used By

- backend-change-builder
- data-middleware-change-builder
- integration-change-builder
- reliability-observability-gate
- ai-code-review-refactor
- quality-test-gate
- architecture-impact-reviewer

# Handoff

Hand off to `transaction-consistency`, `cache-design`, `message-queue-design`, `domain-event-modeling`, `event-driven-architecture`, `idempotency-retry-design`, `failure-contract-design`, `observability`, `security-privacy-gate`, `quality-test-gate`, or `validation-broker` for deeper side-effect-specific design, proof, or closure.

# Completion Criteria

The capability is complete when the data path and every side effect have an owner, boundary, order, transaction/cache/event policy, external/file IO stance, nondeterminism stance, idempotency or compensation stance, observability, same-pattern scan, fresh validation evidence, and residual risk statement.
