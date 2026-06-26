---
name: microservice-splitting
description: Evaluates whether a service split is justified by ownership, deployment, scaling, fault isolation, contracts, data consistency, and operational cost.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "21"
changeforge_version: 0.1.0
---

# Mission

Approve, reject, or defer a microservice split by testing whether the proposed runtime boundary has real business ownership, data ownership, contract stability, failure isolation, independent deployability, observability, rollback, and operating capacity. A split is valuable only when it removes coupling faster than it adds distributed-system cost.

# When To Use

Use this capability when a change proposes extracting a bounded context into an independently deployable service, splitting or merging existing services, replacing in-process calls with HTTP/gRPC/event calls, changing service ownership, or adding a greenfield service beside an existing system. Use it whenever the proposed change draws or removes a runtime deployment boundary.

# Do Not Use When

Do not use this capability to split because a folder is large, a team wants a different framework, or "eventual microservices" sounds cleaner. Use `module-boundary-design` when an in-process module boundary, public facade, or import rule can solve the problem. Use `architecture-style-selection` when the macro style itself is still undecided.

# Stage Fit

Use during architecture planning when a concrete service boundary is proposed, during code review when a change introduces a network call or deployable unit, during testing when contract/rollback/observability evidence is missing, during release planning when split rollout affects multiple services, and during handoff when the decision must state approve/defer/reject with evidence limits.

# Non-Negotiable Rules

- Shared databases, shared schemas, cross-service foreign keys, or direct table reads block independent deployability until data ownership is separated or mediated through contracts/events.
- API, gRPC, or event contracts must be versioned before extraction; never expose ORM/domain internals as the service contract.
- Service owner, on-call path, deployment owner, SLO, runbook, and incident escalation must be named before production.
- Transaction boundaries must be redesigned explicitly with Saga, transactional outbox/inbox, compensation, reconciliation, or a documented decision to keep the boundary in-process.
- Every new synchronous call needs timeout, retry, circuit breaker, bulkhead where relevant, degraded-mode behavior, and observability.
- Consumer-driven contract tests or equivalent compatibility checks must protect old/new mixed-version windows before lockstep releases are removed.
- A split must reject at least one simpler in-process alternative with concrete evidence, not preference.

# Industry Benchmarks

Anchor against Domain-Driven Design bounded contexts, Sam Newman service extraction and strangler patterns, Fowler's microservice trade-offs and monolith-first heuristic, Team Topologies ownership, Pact/consumer-driven contract testing, transactional outbox and Saga patterns, CAP/PACELC tradeoffs, SRE SLO/runbook discipline, and DORA deployment independence. Keep detailed scoring and decision aids in [references/checklist.md](references/checklist.md).

# Mode Matrix

| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities / gates | Skip guidance |
| --- | --- | --- | --- | --- | --- |
| Split justification | New service, service extraction, or in-process call becomes network call. | Prove business, ownership, scaling, deploy, or fault-isolation force beats distribution cost. | Force scorecard, rejected modular alternative, owner, operational cost. | `architecture-impact-reviewer`, `architecture-style-selection` | Skip split approval when module boundary repair can satisfy the need. |
| Boundary readiness | Bounded context, data owner, API/event contract, or team ownership unclear. | Prevent distributed monolith and split-brain data ownership. | Boundary map, entities moved, current consumers, contract version, data owner. | `module-boundary-design`, `data-model-design`, `api-contract-design` | Skip runtime split until public contract and data ownership exist. |
| Consistency and failure | Cross-service transaction, synchronous call, event flow, retry, or compensation appears. | Preserve correctness under timeout, duplicate, partial failure, and replay. | Saga/outbox/reconciliation plan, timeout/retry/circuit/degradation, failure tests. | `transaction-consistency`, `event-driven-architecture`, `degradation-circuit-breaking` | Skip big-bang extraction when compensation is not designed. |
| Deployment migration | Strangler, branch-by-abstraction, dual-read/write, parallel run, or cutover needed. | Make extraction incremental and rollback-aware. | Migration phases, feature flag/route control, rollback/forward-fix, contract tests. | `delivery-release-gate`, `release-rollback`, `version-compatibility` | Skip lockstep release claims without mixed-version evidence. |
| Operability review | New service reaches production or changes ownership/on-call. | Ensure the team can run the service independently. | SLO, alerts, traces, dashboard, logs, runbook, capacity/cost, on-call owner. | `reliability-observability-gate`, `observability`, `performance-budgeting` | Skip production readiness when work is architecture-only and clearly not approved for go-live. |

# Selection Rules

Select this capability when the primary question is whether a concrete runtime deployment boundary should exist, move, split, merge, or be removed. Route elsewhere when:

- `module-boundary-design` is sufficient because the boundary can stay in-process.
- `architecture-style-selection` is primary because the macro style is still undecided.
- `api-contract-design` is primary because the split is already approved and endpoint/event details remain.
- `event-driven-architecture` is primary because the services already exist and the async flow is the main design problem.
- `delivery-release-gate` is primary because the split design is done and rollout evidence is the blocker.

# Technical Selection Criteria

Evaluate split proposals by business capability cohesion, team ownership, deploy cadence divergence, scaling divergence, fault-isolation value, regulated-data boundary, data ownership, contract stability, consumer count, transaction boundary, latency budget, failure mode, migration path, rollback path, observability, cost, on-call capacity, and simpler modular alternative. A valid decision is `approved`, `deferred`, `rejected`, or `merge recommended`, with evidence for every blocker.

# Proactive Professional Triggers

- **Signal:** A split is justified by code size, folder count, framework preference, or "future microservices" language. **Hidden risk:** distribution tax is added without a force that justifies it. **Required professional action:** challenge the split and test an in-process module boundary first. **Route to:** `architecture-impact-reviewer`, `module-boundary-design`. **Evidence required:** force scorecard, rejected modular alternative, current coupling graph, owner.
- **Signal:** Proposed services share tables, schemas, foreign keys, ORM models, read replicas, or direct database access. **Hidden risk:** services remain lockstep and data ownership becomes split-brain. **Required professional action:** block or defer until data ownership and mediated contracts are explicit. **Route to:** `data-model-design`, `api-contract-design`, `transaction-consistency`. **Evidence required:** entity owner map, shared-data decision, contract/event boundary, migration risk.
- **Signal:** An in-process transaction becomes cross-service behavior. **Hidden risk:** partial failure, duplicate side effects, or missing compensation leaves inconsistent business state. **Required professional action:** design Saga/outbox/reconciliation and prove compensation/idempotency paths. **Route to:** `transaction-consistency`, `idempotency-retry-design`, `event-driven-architecture`. **Evidence required:** step map, compensation, idempotency key, failure-mode test or not-verified disclosure.
- **Signal:** A hot-path synchronous call is introduced between services. **Hidden risk:** p99 latency and availability chain degrade or cascade failure spreads. **Required professional action:** require timeout, retry, circuit breaker, degraded mode, SLO math, and traces before approval. **Route to:** `reliability-observability-gate`, `degradation-circuit-breaking`, `performance-budgeting`. **Evidence required:** latency budget, timeout/circuit values, degraded behavior, dashboard/alert path.
- **Signal:** Extraction plan relies on lockstep release, big-bang cutover, or no old/new compatibility window. **Hidden risk:** rollback cannot recover the old path and teams keep coordinating releases after the split. **Required professional action:** require strangler/parallel-run/branch-by-abstraction, contract tests, and rollback/forward-fix plan. **Route to:** `delivery-release-gate`, `release-rollback`, `version-compatibility`. **Evidence required:** phase plan, traffic switch, contract test, rollback trigger, exit criteria.
- **Signal:** New service lacks owner, SLO, runbook, alert, dashboard, capacity plan, secrets/config owner, or on-call coverage. **Hidden risk:** production ownership gap creates orphan service and slow incident response. **Required professional action:** block production approval or record explicit residual risk and owner. **Route to:** `reliability-observability-gate`, `observability`, `delivery-release-gate`. **Evidence required:** owner/on-call, SLO, runbook, alert/dashboard, capacity and cost estimate.

# Risk Escalation Rules

Escalate when a split crosses financial, entitlement, inventory, identity, or regulated-data boundaries; introduces synchronous calls on critical paths; requires data migration or dual writes; changes public consumer contracts; lacks rollback; or creates a service without an owner and on-call. Escalate from architecture review to release/reliability/security/data gates when the split is intended for production.

# Critical Details

- Strangler fig and parallel run reduce split risk because traffic can move gradually and rollback can return to the in-process path.
- API DTOs and event schemas are contracts; ORM/domain models are not external service contracts.
- A Saga compensation is a business action, not a database undo. Design refund, release, cancel, or reconcile semantics explicitly.
- Operational cost is part of architecture: each service adds pipeline, alerts, dashboards, runbooks, secrets/config, capacity, security policy, and on-call load.
- A service merge can be the correct outcome when independent deployment never materialized or operational cost exceeds isolation value.

# Failure Modes

- **Shared database split:** one service migration breaks another service at runtime; coordinated deployment remains mandatory.
- **Contract leakage:** extracted service exposes internal persistence fields and breaks consumers on a later schema refactor.
- **Cascading timeout:** upstream hot path waits on a slow downstream service until thread pools and connection pools exhaust.
- **Partial business state:** payment succeeds, inventory reservation fails, and no compensation or reconciliation exists.
- **Ownerless service:** production incident has no on-call owner, runbook, SLO, or escalation path.
- **Lockstep release:** both services still deploy together because contract tests and mixed-version compatibility are absent.
- **Legacy-plus-new drift:** strangler starts but no retirement trigger exists, so both paths run indefinitely.
- **Service split hides module debt:** network boundary is added while imports, public APIs, and ownership remain tangled.

# Reference Loading Policy

The `SKILL.md` body carries routing, gates, and closure rules. Load [references/checklist.md](references/checklist.md) when drafting a concrete service split assessment, scoring readiness, comparing split vs module boundary, reviewing data/contract/transaction readiness, or planning migration/rollback. Use [examples/example-output.md](examples/example-output.md) only when output shape is unclear. Do not load references for pure routing or wording-only edits.

# Output Contract

Return a `service_split_assessment` with:
- `mode_selected` and trigger signal.
- `decision`: approved, approved-with-conditions, deferred, rejected, or merge recommended.
- `boundaries_inspected`: source modules, deploy units, data stores, contracts, consumers, transactions, failure paths, observability, release path, ownership docs, and skipped boundaries with reason.
- `proposed_boundary`: capability, responsibilities moved, responsibilities retained, current callers/consumers, and owner.
- `split_force_scorecard`: deploy cadence, scaling, ownership, fault isolation, compliance, latency, cost, and rejected simpler option.
- `readiness_matrix`: data ownership, API/event contract, transaction/consistency, failure handling, deployment independence, observability, contract tests, team/on-call.
- `contract_and_data_plan`: OpenAPI/proto/event schema, versioning, consumer compatibility, entity owner, migration, and no-shared-table decision.
- `migration_and_release_plan`: strangler/parallel-run/branch-by-abstraction phases, mixed-version window, rollback trigger, and retirement exit criteria.
- `validation_evidence`: command, validator/test, output, exit code, artifact/report path, covered decision, and freshness.
- `evidence_limits`, `residual_risk`, and next gate or handoff owner.

# Evidence Contract

Close a split decision only when these answers are concrete:
- **Boundaries inspected:** modules, services, deploy units, databases, contracts, consumers, transactions, queues/events, observability, ownership, release path, and skipped scope.
- **Validation evidence:** exact command, validator/test, output summary, exit code, artifact/report path, graph/contract/check result, and freshness relative to the final decision.
- **What evidence proves:** boundary cohesion, data ownership decision, contract readiness, migration safety, deployment independence, failure-handling readiness, or operability readiness.
- **What evidence does not prove:** production traffic behavior, unknown consumers, real incident response, future team ownership, provider behavior, or data migration reversibility unless separately verified.
- **Reuse / placement rationale:** why the decision belongs in service extraction, module boundary repair, event flow, API contract work, or release planning.
- **Residual risk:** unverified consumers, unresolved data coupling, incomplete compensation, lockstep release, missing observability, owner gap, or deferred rollback evidence.
- **Next gate:** `architecture-impact-reviewer`, `module-boundary-design`, `data-api-contract-changer`, `reliability-observability-gate`, `delivery-release-gate`, or `quality-test-gate`.

# Benchmark Coverage

This capability covers split-vs-module challenge, bounded-context cohesion, data ownership, contract versioning, consumer compatibility, transaction redesign, failure isolation, latency/availability impact, migration strategy, rollback, contract testing, observability, ownership/on-call, operational cost, service merge/defer decisions, graph/memory/current-source evidence, and validation freshness.

# Routing Coverage

Routes from `architecture-impact-reviewer`, `delivery-release-gate`, `architecture-style-selection`, `module-boundary-design`, `domain-impact-modeler`, `data-api-contract-changer`, `event-driven-architecture`, and `release-rollback` should arrive here when a concrete service boundary is being approved, rejected, deferred, merged, or extracted. Route away when the task only defines in-process imports, chooses macro style, shapes endpoint fields after approval, or designs async topology for existing services.

# Quality Gate

1. All readiness dimensions are scored; blockers are resolved or explicitly deferred with conditions.
2. API contract (OpenAPI/proto/event schema) is versioned and documented before extraction begins.
3. Data ownership is confirmed: no shared tables, schemas, or cross-service foreign keys post-split.
4. Distributed transaction strategy is designed with compensation, idempotency, reconciliation, or an explicit in-process deferral.
5. Failure handling defined: timeout + retry + circuit breaker + degradation for every synchronous cross-service call.
6. Consumer-driven contract tests or equivalent compatibility checks are planned before first production deployment.
7. Named team owner and on-call rotation assigned before production deployment.
8. Deployment independence verified: each service has its own pipeline and can deploy on its own schedule.
9. Observability plan covers logs, metrics, traces, alerts, dashboards, runbook, and SLO.
10. Operational cost assessed and justified against business benefit.
11. Simpler in-process module boundary is considered and rejected with evidence, or the split is rejected/deferred.
12. Migration and rollback path names phases, traffic switch, mixed-version compatibility, and retirement exit criteria.
13. Validation evidence is fresh, scoped, and does not overclaim production readiness.

# Used By

- architecture-impact-reviewer
- delivery-release-gate

# Handoff

Hand off to `module-boundary-design` if the split is rejected or deferred in favor of in-process repair; `api-contract-design` for endpoint/event contract detail; `event-driven-architecture` and `transaction-consistency` for async/Saga/outbox work; `observability` and `reliability-observability-gate` for runtime readiness; `delivery-release-gate` and `release-rollback` for extraction rollout.

# Completion Criteria

The capability is complete when the split decision is documented with boundary evidence, rejected simpler alternative, readiness score, stable contract, data ownership plan, consistency strategy, failure handling, owner/on-call, deployment independence, migration/rollback plan, operational cost, validation evidence, and evidence limits; or the split is rejected/deferred with the next in-process boundary or readiness step.
