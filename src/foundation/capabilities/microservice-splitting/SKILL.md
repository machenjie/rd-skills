---
name: microservice-splitting
description: Evaluates whether a service split is justified by ownership, deployment, scaling, fault isolation, contracts, data consistency, and operational cost.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "21"
changeforge_version: 0.1.0
---

# Mission

**Approve, reject, or defer a microservice split** by testing whether the proposed boundary has sufficient API contract stability, data ownership clarity, failure isolation, deployment independence, observability maturity, and operational readiness — ensuring that no service boundary is introduced before the team can deploy, observe, fail, recover, and evolve it independently without lockstep coordination.

# When To Use

Use this capability when a change proposes: extracting a bounded context from a monolith into an independent deployable service; splitting an existing service into two or more services; merging two services back into one; replacing in-process function calls with network calls (HTTP, gRPC, events); or creating a new greenfield microservice alongside an existing system. Use it whenever a proposed change draws a new runtime boundary.

# Do Not Use When

Do not use this capability to split services because: code is large or a folder has many files (use `module-boundary-design` instead); the team prefers a different framework; a module boundary could be clarified in-process with better folder structure; or a split is proposed for "eventual microservices" without a concrete business justification for the added operational complexity today.

# Non-Negotiable Rules

- **A shared database invalidates a split.** If two services share a database schema, table, or foreign key — they are not independently deployable. One service's schema change requires coordinated deployment of both. The split is not real until each service owns its data store (or communicates via API/events — not shared tables). This is the single most common microservice split anti-pattern.
- **A stable API or event contract must be defined before splitting.** The service contract (OpenAPI spec, gRPC proto, Avro/JSON schema for events) must be designed and agreed upon before extraction begins. Extracting first and designing the contract later produces an internal object model exposed over HTTP — a distributed monolith.
- **Service owner and on-call responsibility must be named before production.** A service with no clear owner will have no SLO, no runbook, and no on-call coverage. The split assessment must name: owning team, on-call rotation, deployment pipeline owner, incident escalation path.
- **Distributed transactions must be replaced, not left implicit.** If the operation that is being split currently executes in a single database transaction (`INSERT orders + UPDATE inventory` in one `BEGIN/COMMIT`), splitting those two into separate services creates a distributed transaction problem. The split must include an explicit consistency strategy: Saga (choreography or orchestration), Outbox + Event, eventual consistency with reconciliation, or compensating actions. "We'll figure out transactions later" is not acceptable.
- **Failure handling must be designed before the split, not after the first incident.** The split introduces a new network call. That network call can fail, timeout, or return degraded data. Before splitting: define `timeout`, `retry` policy, `circuit breaker` thresholds, and `degradation` behavior (what the calling service does when the called service is unavailable). The degradation mode must be acceptable to the business.
- **Independent deployability must be achieved, not assumed.** If deploying the new service requires coordinating with the old service's release, the operational benefit of splitting is not realized. The split is complete only when: each service can be deployed on its own schedule; contract is versioned; the calling service can handle both old and new response formats during transition (`Tolerant Reader` pattern).
- **Release coordination must not remain lockstep post-split.** Consumer-Driven Contract Testing (CDCT) via Pact (or similar) must be in place before the split goes to production. Without CDCT, integration tests are the only safety net — and they typically require both services to deploy together, recreating the lockstep coupling the split was supposed to eliminate.

# Industry Benchmarks

Anchor against: **Sam Newman "Building Microservices" 2nd ed.** (2021) — incremental extraction, strangler fig pattern, database decomposition strategies, seam identification. **Eric Evans "Domain-Driven Design"** — bounded context: a business capability with its own language, model, and ownership; the natural unit of a microservice boundary. **Martin Fowler "Microservice Trade-offs"** (martinfowler.com) — "Don't start with microservices; they're a distribution tax"; monolith-first recommended for new products. **Fowler "Strangler Fig Application"** — incremental extraction by routing traffic; avoids "big bang" extraction risk. **Pact CDCT (pact.io)** — consumer-driven contract testing; providers must not break verified consumer expectations; prevents broken contracts without integration test environments. **Sam Newman "Monolith to Microservices"** (2019) — patterns: Extract Service, Parallel Run, Branch by Abstraction. **Chris Richardson "Microservices Patterns"** (2018) — Saga pattern (choreography + orchestration); Transactional Outbox; API Gateway; BFF (Backend for Frontend). **CAP theorem / PACELC** — distributed system consistency, availability, and partition tolerance tradeoffs; a split that crosses a transaction boundary must explicitly choose: strongly consistent (sacrifices availability) or eventually consistent (sacrifices consistency). **Google SRE Book (site reliability engineering)** — SLO per service; error budget; runbook requirements before production.

### Service Split Readiness Matrix

| Dimension | Not Ready (Block) | Caution (Condition) | Ready |
| --- | --- | --- | --- |
| Data ownership | Shared DB table / FK | Read replica of other service's data | Own schema, no cross-service FK |
| API contract | No contract defined | Internal types exposed over HTTP | Stable OpenAPI / proto / event schema |
| Failure handling | No timeout/circuit defined | Timeout only; no degradation | Timeout + retry + circuit + degradation |
| Deployment | Requires coordinated deploy | Same pipeline, separate stages | Independent pipeline, separate schedule |
| Observability | No logs/metrics | Application logs only | Structured logs + metrics + traces + alerts |
| Contract testing | None | Manual integration tests | Pact/CDCT running in CI |
| Transaction strategy | Shared DB transaction | Saga designed, not implemented | Saga or Outbox implemented + tested |
| Team ownership | No named owner | Owner named, no on-call | Named owner + on-call + runbook |

### Split Decision Tree

```
Is there a business capability that:
  a) Changes at a different rate than the surrounding system?
  b) Has a distinct team or ownership domain?
  c) Has independent scaling requirements?
  d) Has failure isolation value (failure here must not cascade)?
  e) Has clear data ownership (no shared tables)?
    ALL YES → split MAY be justified; proceed to readiness matrix

Does the proposed split share a database?
  YES → BLOCK: decompose data first (separate schemas, add API boundary in-process)

Is the API contract stable and versioned?
  NO → BLOCK: define OpenAPI/proto/event schema first; split only after contract is agreed

Is the cross-service transaction strategy defined?
  NO → BLOCK: Saga / Outbox / eventual consistency must be designed before split

Is independent deployment achievable (no lockstep releases)?
  NO → CONDITION: implement consumer-driven contract tests first; split deferred

Is the team able to operate this service in production (observability + on-call)?
  NO → CONDITION: instrument first; define runbook; name on-call rotation

All conditions met → APPROVE split with strangler fig or parallel run extraction
```

# Selection Rules

Select this capability when a **new runtime deployment boundary** is the proposed change. Route elsewhere when: **module-boundary-design** is sufficient (the boundary can remain in-process within a monolith or modular monolith); **architecture-style-selection** is the question (monolith vs microservices vs serverless as an initial architectural direction); **api-contract-design** is primary (detailed endpoint shape after a split is already approved); **event-driven-architecture** is primary (event flow design across already-split services).

# Risk Escalation Rules

Escalate when: the proposed split crosses a financial transaction boundary (payments, ledger, inventory deduction) without a defined Saga or compensating transaction strategy; the service boundary is being proposed for regulated data (PII, PHI, PAN) without data ownership and compliance review; the split introduces a synchronous call on a hot path with no circuit breaker (creating a new single point of failure); the team proposing the split does not have capacity to operate a new service in production; or the split is being driven by a desire to use a different technology stack without a clear operational benefit.

# Critical Details

- **Strangler Fig pattern minimizes split risk.** Instead of extracting a service in one step ("big bang"), route a thin slice of traffic through the new service boundary while the old code continues to handle the rest. Gradually migrate behavior. The old code path is "strangled" incrementally. This allows: validation of the new service in production with limited blast radius, rollback to the in-process path without data loss, and validation of the API contract against real traffic.
- **Internal data models exposed over HTTP create a distributed monolith.** When a service exposes its ORM model directly as its API response, every internal schema change (adding a column, renaming a field) becomes a breaking change for all consumers. The service is no longer independently evolvable. API responses must be DTOs designed for consumers, not internal representations.
- **Operational cost of a microservice is non-trivial.** Each service adds: separate deployment pipeline, independent monitoring + alerting + dashboards, on-call rotation responsibility, secrets rotation, TLS certificate management, network policy, health check, capacity planning. For a small team (< 5 engineers), maintaining more than 5–8 services becomes a burden that slows feature delivery. Sam Newman: "Don't start with microservices."
- **Saga compensating transactions are harder than they appear.** A Saga is a sequence of local transactions with compensating actions for rollback. Compensating actions must be: idempotent (can be retried), commutative (safe in any order), and semantically correct (a "refund" compensating a "charge" is not the same as never having charged). Design compensating actions explicitly for every Saga step before the split is approved.

### Anti-examples

| Anti-pattern | Problem | Fix |
| --- | --- | --- |
| Two services share `orders` table | Schema change in one requires deploy of both | Separate schemas; communicate via API or events |
| New service exposes JPA entity as API response | Internal column rename breaks all consumers | Design DTO for API; map from internal model |
| Split deployed without circuit breaker | Downstream outage cascades to upstream | Add circuit breaker with defined degradation before first production deploy |
| "We'll define the contract after extraction" | Contract designed from internal implementation details | Define OpenAPI/proto before extraction; use Pact from day 1 |
| Saga designed but compensating actions untested | Compensation fails silently on rollback | Test all Saga paths including compensation in integration test suite |
| Service split to use different language/framework | Operational cost unjustified by benefit | Use module boundary instead; keep in-process |

# Failure Modes

- Two services share a PostgreSQL schema — one team's migration adds a NOT NULL column without a default value; the other service's deployed version breaks on read; coordinated deployment required; services are not independently deployable.
- No API contract defined before split — the extracted service's response shape mirrors its internal ORM model; six months later, a DB optimization renames a column; three consumers break simultaneously.
- No circuit breaker on cross-service call — payment service calls inventory service synchronously; inventory service is slow; payment service threads block; connection pool exhausted; payment service unavailable; full outage from a partial dependency failure.
- Saga designed without compensating transactions — order confirmed, payment deducted, inventory reservation fails — there is no compensating action to refund the payment; partial failure leaves customer charged with no order.
- No named owner for new service — service goes to production without an on-call rotation; first incident at 2am has no responder; 4-hour outage.
- Lockstep deployment remains after split — each release requires deploying both services simultaneously; no actual deployment independence gained; operational cost added with no benefit.

# Output Contract

Return a service split assessment with:

- `proposed_boundary` (business capability name; description of responsibility; what moves out of existing service)
- `justification` (independent scaling need / fault isolation need / team ownership alignment / technology boundary — must state at least one concrete reason)
- `readiness_matrix` (scored on all 8 dimensions: data ownership, API contract, failure handling, deployment, observability, contract testing, transaction strategy, team ownership)
- `api_contract` (OpenAPI spec reference or proto file; event schema; versioning strategy)
- `data_ownership` (which entities move; schema separation plan; migration strategy; no shared tables after split)
- `consistency_strategy` (Saga steps with compensating actions, or Outbox pattern design, or eventual consistency with reconciliation — explicit, not "TBD")
- `failure_handling` (timeout values, retry policy, circuit breaker thresholds, degradation behavior for each cross-service call)
- `deployment_plan` (extraction strategy: strangler fig / parallel run / big bang; rollback plan; feature flag for traffic routing)
- `observability_plan` (structured logs, metrics, distributed tracing, health check, consumer lag if event-driven)
- `contract_testing` (Pact consumer-driven contract tests; CI pipeline integration)
- `operational_cost` (new pipelines, on-call, secrets, TLS, capacity planning — quantified)
- `rejected_alternatives` (in-process module boundary; shared library; other split boundary options considered)
- `decision` (APPROVED / DEFERRED / REJECTED with rationale)

# Quality Gate

The split assessment is complete only when:

1. All 8 readiness matrix dimensions are scored; all blocking items resolved or explicitly deferred with conditions.
2. API contract (OpenAPI/proto/event schema) is versioned and documented before extraction begins.
3. Data ownership is confirmed: no shared tables, schemas, or cross-service foreign keys post-split.
4. Distributed transaction strategy (Saga/Outbox/eventually consistent) is designed with compensating actions for every Saga step.
5. Failure handling defined: timeout + retry + circuit breaker + degradation for every synchronous cross-service call.
6. Consumer-driven contract tests (Pact) planned and in CI pipeline before first production deployment.
7. Named team owner and on-call rotation assigned before production deployment.
8. Deployment independence verified: each service has its own pipeline and can deploy on its own schedule.
9. Observability in place: distributed tracing propagates across service boundary; consumer lag monitored for event-driven paths.
10. Operational cost assessed and justified against business benefit.

# Used By

- architecture-impact-reviewer
- domain-impact-modeler

# Handoff

Hand off to `api-contract-design` for detailed endpoint shape after split is approved; `event-driven-architecture` for cross-service event routing; `transaction-consistency` for Saga or Outbox implementation; `module-boundary-design` if split is deferred in favor of in-process boundary; `observability` for distributed tracing and SLO design.

# Completion Criteria

The capability is complete when **the service split decision (approve/reject/defer) is documented with a scored readiness matrix, a stable API contract, an explicit data ownership plan, a distributed transaction strategy, a named owner, and a deployment independence verification — or the split is rejected with documented rationale and an alternative in-process boundary recommended**.

# Used By

- architecture-impact-reviewer
- delivery-release-gate

# Handoff

Hand off to api-contract-design for contract details, event-driven-architecture for asynchronous coordination, data-migration-design for data separation, or delivery-release-gate for rollout planning.

# Completion Criteria

The capability is complete when the split decision includes contract, data, failure, ownership, deployment, and cost evidence.
