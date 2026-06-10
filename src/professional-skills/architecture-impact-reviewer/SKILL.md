---
name: architecture-impact-reviewer
description: Reviews architectural impact across boundaries, layering, dependency direction, service ownership, scalability, extensibility, operability, tradeoffs, and simpler alternatives before endorsing additional complexity.
license: MIT
changeforge_kind: professional-skill
changeforge_version: 0.1.0
---

# Architecture Impact Reviewer

## Mission
Keep the architecture coherent, observable, and evolutionarily sound by rigorously reviewing every change that touches module boundaries, dependency direction, service topology, shared abstractions, data ownership, or scalability assumptions — while consistently defaulting to the simplest design that satisfies current requirements and credible near-term constraints.

## When To Use
- A change introduces a new module, service, shared library, or cross-team dependency.
- A monorepo, workspace, package graph, affected-test strategy, generated-file policy, or incremental-build system changes module boundaries.
- New abstractions, interfaces, generic handlers, or extension points are proposed.
- Data ownership moves across service or team boundaries.
- An async workflow, event-driven pattern, or message queue is added or modified.
- A synchronous dependency is introduced between services that have separate availability targets.
- The change affects API or contract boundaries that external consumers depend on.
- A migration, protocol change, or topology change is involved.
- The team is unsure whether to build, buy, or reuse an existing capability.

## Do Not Use When
- The change is a local implementation detail that fits cleanly within existing architecture and carries no boundary, coupling, or scaling risk.
- The change is a bug fix confined to a single module with no interface change.
- Documentation or configuration updates with no impact on system topology or service contracts.

## Non-Negotiable Rules
- Default to the simplest sufficient design — **complexity requires justification, simplicity does not**.
- Respect existing ownership and dependency direction: dependencies must flow toward stable, lower-volatility layers, never the other direction.
- All tradeoffs between chosen design and alternatives must be made explicit in writing — no implicit decisions.
- Do not add abstractions for anticipated future use cases that do not currently exist and have no concrete roadmap commitment.
- Every service or module boundary creates a failure mode — new boundaries require explicit availability, consistency, and failure handling analysis.
- Avoid synchronous dependencies on services with lower availability targets than the calling service.
- Shared abstractions must have a clear owner — unowned shared code accumulates as unmaintainable technical debt.
- Every architectural decision that is reversible should be noted as such; irreversible decisions require explicit acknowledgment and approval.
- Data ownership must be singular: each entity or aggregate has one authoritative owner; reads from non-owners go through contracts, not direct database access.
- New external service dependencies require a circuit breaker, fallback, timeout, and operational runbook.
- Monorepo module boundaries are architectural boundaries: workspace layout, dependency graph, generated-code ownership, and affected-test selection must reflect real ownership, not folder convenience.

## Industry Benchmarks
- **Architecture Decision Records (ADRs)**: Every significant architectural choice should produce a written ADR with context, decision, rationale, alternatives rejected, and consequences.
- **Clean Architecture (Uncle Bob / Robert Martin)**: Dependency rule — source code dependencies point inward only, toward higher-level policy. UI and infrastructure are plugins, not core.
- **Domain-Driven Design (DDD)**: Bounded contexts, aggregate ownership, anti-corruption layers, published languages for cross-context communication.
- **Modular Monolith / Evolutionary Architecture**: Don't distribute before you must — premature service extraction creates coordination and failure complexity that scales with team maturity.
- **The Twelve-Factor App**: Factor III (Config), Factor IV (Backing services), Factor V (Build/release/run) — architectural decisions affecting deployability and environment parity.
- **CAP / PACELC Theorem**: Partition-tolerant systems cannot simultaneously guarantee consistency and availability — every distributed data ownership decision must declare its consistency model.
- **Service Mesh / API Gateway patterns**: Cross-cutting concerns (auth, rate limiting, tracing) belong at the infrastructure layer, not embedded in every service.
- **CQRS and Event Sourcing**: Apply when write and read models are under significantly different load profiles, not as a default pattern — operational complexity cost is high.

### Complexity Justification Matrix

| Proposed Addition | Justification Required | Simpler Alternative |
|---|---|---|
| New microservice | >2 teams own distinct scaling/deployment lifecycles | Modular monolith with clear bounded module |
| Shared library | ≥3 consumers with identical need; single owner declared | Copy-paste with protocol for future consolidation |
| Event-driven async | Decoupling required; eventual consistency acceptable | Direct synchronous call with timeout |
| CQRS read model | Write model cannot serve read load patterns | Index or view on the existing model |
| Generic handler / plugin system | ≥3 extension cases exist today | Explicit if/switch with planned refactor trigger |
| New external service dependency | No internal capability meets need | Extend existing service or use standard library |

## Technical Selection Criteria
Evaluate architecture proposals against:
- **Boundary clarity**: Can each module's responsibilities be stated in one sentence without exception lists?
- **Dependency direction**: Do all dependencies flow from volatile layers to stable layers? Are no cycles introduced?
- **Coupling measurement**: How many callers would break if this component changed its interface? Is that acceptable?
- **Data ownership**: Is there a single authoritative owner for each entity? Is cross-owner data access mediated by contracts?
- **Scalability model**: What are the throughput and latency assumptions? At what scale does this design break?
- **Failure blast radius**: If this component fails, what is the operational impact? Is that bounded?
- **Deployability**: Can this component be deployed independently? What is the rollout and rollback sequence?
- **Observability gap**: What tracing, metrics, and alerts would operators need to diagnose failures in this design?
- **Migration path**: If this design turns out to be wrong, what is the escape hatch? Can it be reversed?
- **Team ownership**: Who owns each boundary, shared contract, and service for ongoing maintenance?
- **Monorepo module graph**: Which packages/modules exist, who owns them, which dependencies are allowed, which generated files cross boundaries, and which affected tests prove the boundary?

## Mode Matrix
Select the architecture review mode before approving a design.

| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities | Skip by default |
|---|---|---|---|---|---|
| Boundary review | New module, directory, shared package, public API, generated client, or ownership boundary. | Keep responsibilities, public surface, dependency direction, and owner explicit. | Module graph, owner, allowed imports, public/private surface, affected tests. | `module-boundary-design`, `implementation-structure-design` | Service split unless module boundary cannot serve the need. |
| Complexity challenge | New abstraction, plugin system, generic handler, framework, queue, or service is proposed. | Compare over-engineering vs under-design and choose simplest sufficient option. | Alternatives, concrete constraints, rejected simpler option, reversibility. | `architecture-tradeoff-analysis`, `solution-optimality-evaluation` | Future-proofing without current use cases. |
| Service/data ownership | New service, direct DB access, cross-service write, event stream, or system-of-record move. | Preserve one data owner, consistency model, failure handling, and migration path. | Owner map, contract/event boundary, rollback/migration, consistency tradeoff. | `domain-impact-modeler`, `data-api-contract-changer` | Direct database sharing as shortcut. |
| Reliability/operability review | New synchronous dependency, external vendor, SLO path, or topology change. | Bound failure blast radius, availability chain, timeout, fallback, observability, and runbook. | Availability math, timeout/circuit/fallback, metrics/traces/alerts, runbook owner. | `reliability-observability-gate`, `integration-change-builder` | Release gate unless deployment topology changes. |
| Refactor/monorepo governance | Package graph, affected tests, build cache, generated files, or shared utility pollution. | Prevent hidden coupling and test selection gaps during structural change. | Dependency graph, transitive dependents, cache key inputs, generated source owner. | `ci-cd`, `quality-test-gate`, `refactoring` | New architecture decision when behavior-preserving local refactor suffices. |

## Proactive Professional Triggers
These triggers are hidden-risk escalators, not ordinary checklist items.

- **Signal:** A helper, common package, shared module, plugin point, or generic interface is proposed for one consumer. **Hidden risk:** speculative abstraction becomes unowned boundary debt. **Required professional action:** challenge reuse threshold and local placement first. **Route to:** `implementation-structure-design`, `architecture-tradeoff-analysis`. **Evidence required:** current consumers, owner, rejected local alternative, reversibility.
- **Signal:** A new service or direct cross-service data access is proposed without data owner and contract. **Hidden risk:** split-brain ownership or distributed monolith. **Required professional action:** assign authoritative owner and mediated contract before approval. **Route to:** `domain-impact-modeler`, `data-api-contract-changer`. **Evidence required:** owner map, data flow, contract/event path, rollback/migration risk.
- **Signal:** Synchronous dependency is added on a lower-SLO or unknown-SLO service. **Hidden risk:** caller availability is silently reduced and p99 latency compounds. **Required professional action:** require timeout, fallback, circuit, availability math, and observability. **Route to:** `reliability-observability-gate`, `integration-change-builder`. **Evidence required:** SLO comparison, timeout budget, fallback behavior, alert/runbook.
- **Signal:** Monorepo or generated-code change updates one package but not affected-test selection or source-of-truth policy. **Hidden risk:** transitive consumers and generated clients drift unnoticed. **Required professional action:** inspect graph and generated-file ownership before merge. **Route to:** `ci-cd`, `quality-test-gate`. **Evidence required:** dependency graph, generated source, affected tests, cache key inputs.
- **Signal:** Design says "we can refactor later" for irreversible data, API, service, or public abstraction choice. **Hidden risk:** reversibility is assumed but no escape hatch exists. **Required professional action:** record ADR/rollback path or reduce scope to reversible step. **Route to:** `release-rollback`, `change-documentation-gate`. **Evidence required:** reversibility classification, ADR need, rollback/migration path, residual owner.

### Monorepo Architecture Review

For monorepo or workspace changes, require:

- Module graph with packages/modules, owners, public interfaces, and forbidden dependency directions.
- Affected test selection that includes direct dependents, transitive dependents, contract tests, generated clients, and shared tooling.
- Incremental build strategy with Bazel, Pants, Nx, Turborepo, or equivalent only when the module graph justifies it.
- Build cache correctness: cache key inputs include lockfiles, toolchain versions, generated inputs, configuration, and test fixtures.
- Generated file policy: committed vs ignored outputs, source of truth, drift check, and review owner.
- DevEx boundary: onboarding time, devcontainer or reproducible local environment, pre-commit scope, and full-suite fallback cadence.

### Decision Tree: Approve or Request Design Revision

```
Does the change introduce a new service or module boundary?
├── Yes → Require ownership declaration and failure handling analysis
│   └── No clear owner → Block until ownership assigned
Does the change create a new inter-service synchronous dependency?
├── Yes → Check availability targets (caller vs. callee)
│   └── Callee is lower availability → Require async or graceful degradation
Does the change introduce a shared abstraction?
├── Yes → Require ≥2 current consumers and named owner
│   └── Single consumer → Use local implementation
Does the change move data ownership across a boundary?
├── Yes → Require explicit data contract and migration path
│   └── No contract → Block
All checks pass → Review tradeoffs, document in ADR, approve
```

## Solution Optimality Self-Check
Apply when evaluating architectural options — every choice must survive explicit challenge before endorsement. Answer the **Three-Challenge Rule**: (1) why this design (state the concrete constraint simpler options fail), (2) is it the simplest sufficient architecture (a modular monolith before microservices until evidence justifies the cost), (3) what is the strongest simpler alternative and the specific operational cost that rejects it. Quantify the architecture performance dimensions — hops/latency, availability arithmetic, throughput ceiling, Amdahl's sequential fraction — and record the result as an ADR that names the rejected alternative.

Load [references/solution-optimality.md](references/solution-optimality.md) for the full architecture performance-dimension matrix and additional considerations (operational cost, availability chaining, data-ownership invariant) when endorsing added complexity. Method compiled from `solution-optimality-evaluation`.

## Risk Escalation Rules
- Escalate when the change alters the ownership boundary of a shared service used by multiple teams.
- Escalate when persistence ownership moves between services — this affects consistency, migration, and disaster recovery.
- Escalate when a new synchronous dependency reduces overall system availability (Amdahl's Law of service chaining).
- Escalate when the proposed design relies on eventual consistency for money movement, authorization decisions, or audit records.
- Escalate when a change cannot be rolled back without manual data migration or customer-visible downtime.
- Escalate when the design adds a new external vendor dependency that creates a single point of failure.
- Escalate when the change affects publicly documented API contracts with SLA obligations.
- Escalate when monorepo affected-test selection can skip transitive dependents, generated-code consumers, or shared contract tests.
- Escalate when build cache keys omit lockfiles, generated inputs, toolchain versions, or environment-affecting configuration.

## Critical Details
- The hardest architectural problems are not technical — they are ownership and coordination problems. Name the owner before approving the design.
- Architecture drift accumulates via individually approved changes — always check the cumulative direction, not just the isolated change.
- "We can refactor later" is an escalation signal, not a resolution — future refactors rarely happen unless the pain is immediate.
- Distributed transactions (2PC, SAGA) add significant complexity; require explicit documentation of the failure recovery and compensating transaction model.
- Every new queue, topic, or event stream requires: schema ownership, versioning strategy, consumer documentation, and dead-letter handling.
- GraphQL federated schemas, service meshes, and API gateways each solve specific problems — they also introduce operational complexity that must be owned by an operator.
- Security boundaries are architectural boundaries: if services share a database directly, they share a security perimeter — document this explicitly.
- Circuit breakers and bulkheads must be configured with realistic thresholds — default "open" thresholds from libraries are rarely appropriate for production.
- A module graph is a product of architecture, not tooling. Bazel, Pants, Nx, or Turborepo can enforce a graph, but they cannot decide ownership, API stability, or dependency direction. Those are architecture decisions.
- Generated code creates hidden dependencies. OpenAPI clients, protobufs, ORM types, GraphQL artifacts, and SDKs must be represented in the module graph so affected tests run when source schemas change.

### Anti-Examples

| Proposed Architecture | Problem | Preferred Alternative |
|---|---|---|
| "We'll add a plugin system for future extensibility" | Speculative complexity, no concrete extensions yet | Explicit case handling, revisit when third extension exists |
| Service A reads directly from Service B's database | Cross-ownership data access, hidden coupling | Publish API or event from Service B |
| Generic `EventBus.publish("anything")` | No schema, no owner, no versioning | Explicit typed events with schema and consumer documentation |
| New service for a feature owned by one team | No independent deployment need | Bounded module within existing service |
| Auth decision made in-process per service | No consistent enforcement, easy to bypass | Centralized auth middleware / API gateway |

## Failure Modes
- **Premature abstraction**: Generic handlers and plugin systems created for anticipated use cases that never materialize — complexity persists, benefit never arrives.
- **Boundary leak**: Module A imports types from Module C's internal layer — the boundary dissolves over time and refactoring becomes impossible.
- **Hidden synchronous dependency**: Service A calls Service B synchronously during checkout — Service B's 200 ms latency spike degrades Service A's p99 from 100 ms to 300 ms.
- **Unowned shared library**: A shared utility package has no declared owner — bug fixes require a team coordination meeting with no clear accountability.
- **Data ownership ambiguity**: Two services each update the `user.email` field — consistency depends on write order, which is non-deterministic.
- **Rollback-impossible schema migration**: A new service owns a table that the old service still reads — rolling back the new service requires schema migration coordination.
- **No ADR for irreversible decision**: The team chose Event Sourcing without documenting why — six months later no one remembers the reasoning and the pattern is cargo-culted.
- **Availability chain degradation**: A new synchronous dependency on a 99.5% available service reduces the calling service's effective availability to ≤99.5%.
- **Decentralized auth logic**: Each service implements its own role check — the checks diverge over time, creating inconsistent authorization behavior.

## Reference Loading Policy
Do not load every reference by default. Treat references as targeted support selected by the router and the task risk.

- L1 changes: do not read references unless the task touches security, data, auth, external integration, performance, release, or irreversible behavior.
- L2 changes: read `references/capabilities/index.md` and only capability files explicitly selected by `change-forge-router`.
- L3 changes: read all selected capability references and `references/checklist.md` when present.
- L4/L5 changes: read all selected capability references, `references/checklist.md` when present, and domain extension references when selected.
- Selected capability reference path format: `references/capabilities/<capability-id>-<capability-name>.md`.

Examples:
- `42 idempotency-retry-design` -> `references/capabilities/42-idempotency-retry-design.md`
- `82 solution-optimality-evaluation` -> `references/capabilities/82-solution-optimality-evaluation.md`

## Output Contract
Return a structured architecture review with:
- **Mode selected**: Architecture mode and trigger signal that selected it.
- **Decision**: Approved / Approved with conditions / Returned for redesign.
- **Alternatives considered**: At least one simpler alternative with explicit reason for rejection.
- **Boundary impact**: New or changed module and service boundaries with ownership declarations.
- **Module graph**: Monorepo package/module graph, owners, public interfaces, allowed dependency directions, and generated-file ownership when applicable.
- **Dependency impact**: New dependencies with direction, coupling level, and availability analysis.
- **Data ownership impact**: Any changes to authoritative data ownership with contract requirements.
- **Tradeoff analysis**: Explicit tradeoffs accepted (performance vs. consistency, simplicity vs. extensibility, etc.).
- **Failure blast radius**: Operational impact if the new component fails.
- **Observability requirements**: Metrics, traces, and alerts required for the new component.
- **Build and test impact**: Affected tests, incremental build approach, build cache key inputs, generated file policy, and full-suite fallback when applicable.
- **ADR requirement**: Yes/No — whether a written ADR is required before implementation.
- **Open risks**: Unresolved design risks with proposed owners and review dates.
- **Boundaries inspected**: modules, packages, services, public APIs, data owners, generated files, dependency edges, release topology, and tests inspected.
- **Professional judgment**: over-engineering vs under-design decision, reversibility, hidden coupling ruled out, and owner accountability.
- **Reuse and placement rationale**: existing module/service/API/contract reused or new boundary justified, with public/private decision.
- **Behavior preservation statement**: existing contract, dependency direction, ownership, rollout, and operational behavior preserved or intentionally changed.
- **Validation evidence**: dependency-graph, affected-test, build-cache, ADR, or not-verified disclosure with outcome.
- **Evidence limits**: what architecture evidence proves and does not prove about scale, org ownership, production traffic, and future requirements.
- **Residual risk and next gate**: accepted tradeoff, deferred ADR, rollout/reliability/docs handoff, and owner.

## Evidence Contract
Close an architecture review only when all five canonical answers are concrete (answer schema: `agent-execution-discipline`):
- **Basis**: the existing module boundaries, dependency directions, and parent-directory conventions the review starts from — structure-first, before any new boundary is proposed.
- **Files and boundaries inspected**: the existing modules, public interfaces, shared functions, and dependency edges read, and where the change would alter them.
- **Placement rationale**: why any new directory, class, interface, or service is justified over reusing existing structure, with at least one simpler alternative and the explicit reason it is rejected.
- **Validation commands**: the dependency-graph, affected-test, or build-cache checks run to confirm no cycle or boundary violation, each with its outcome.
- **Architecture judgment and evidence limits**: mode selected, behavior preservation, reversibility, what evidence proves, what it does not prove, residual risk, and next gate.
- **Residual risk**: the accepted tradeoff, failure blast radius, or deferred ADR that remains, with the named owner and review date.

## Quality Gate
1. The chosen design is demonstrably simpler than at least one alternative that was explicitly considered.
2. Every new boundary has a named owner and a failure handling strategy.
3. Dependency direction is correct — no dependencies point from stable to volatile layers.
4. Data ownership is unambiguous — no entity has two authoritative owners.
5. All tradeoffs are explicitly documented, not assumed.
6. No speculative extensibility abstractions without existing concrete use cases.
7. Availability implications of new synchronous dependencies are quantified.
8. Irreversible decisions are explicitly acknowledged and approved.
9. Rollback path exists or the absence is explicitly documented and accepted.
10. Observability requirements for the new component are stated.
11. Monorepo changes include module graph, affected tests, cache key inputs, generated-file policy, and ownership boundaries.

## Handoff
- **data-api-contract-changer** — when new or changed data models, schemas, or API contracts require design.
- **backend-change-builder** — when implementation direction is confirmed and coding can begin.
- **integration-change-builder** — when new external service dependencies are introduced.
- **reliability-observability-gate** — when new components require SLI/SLO definition and observability design.
- **delivery-release-gate** — when architectural changes affect deployment topology, migration sequencing, or rollback safety.
- **change-documentation-gate** — when an ADR, runbook, or developer guide update is required.
- **ci-cd** — when module graph decisions must be enforced through affected tests, incremental builds, or cache policy.
- **package-dependency-management** — when workspace dependencies, lockfiles, generated packages, or hoisting affect architecture boundaries.

## Completion Criteria
The change has an architecture direction with justified complexity, documented tradeoffs, declared ownership for all boundaries, an explicit failure handling strategy, a quantified availability impact, monorepo/module graph governance when applicable, and either an approved ADR or a documented rationale for why one is not required.
