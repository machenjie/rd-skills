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

*Compiled from foundation capability `solution-optimality-evaluation`. Apply when evaluating architectural options — every design choice must survive explicit challenge before endorsement.*

**Three-Challenge Rule** — mandatory for every architecture review:
1. **Why this design?** State the concrete constraint (team boundary, scaling requirement, deployment independence) that this design satisfies that simpler alternatives do not. "It's more scalable" is not concrete. "At current 1k RPS the monolith suffices; this design is needed at 10k RPS which is on the roadmap for Q3" is concrete.
2. **Is this the simplest sufficient architecture?** Complexity requires justification; simplicity does not. If a modular monolith satisfies the deployment, scaling, and team-ownership requirements, it is preferred over microservices until evidence justifies the complexity cost.
3. **What is the strongest simpler alternative, and why is it rejected?** Name it. Use the Complexity Justification Matrix. Reject it with a specific operational or engineering cost.

**Architecture Performance Dimension Review** — quantify (not just describe) the following:

| Dimension | Required Architectural Question | Failure Mode |
|---|---|---|
| **CPU** | What is the per-request CPU overhead of the chosen architectural pattern vs. the simpler alternative? Does a service mesh, sidecar proxy, or API gateway add meaningful CPU cost at target throughput? | Sidecar proxy adds 2ms per hop; with 6 service hops, this is 12ms added latency and equivalent CPU overhead — unacceptable if total P99 budget is 50ms |
| **Memory** | What is the memory model of the chosen architecture — stateless (scales horizontally) or stateful (partitioned, requires affinity)? Is the memory footprint per instance calculated? | Stateful in-memory session store requires sticky routing; breaks horizontal scale-out; OOM risk during traffic spikes without per-instance memory cap |
| **Network** | How many synchronous network hops does the chosen architecture add to the critical user path? What is the added latency per hop (intra-cluster: ~1ms, cross-datacenter: ~30ms, cross-region: ~80ms)? Apply Amdahl's Law to service chain depth. | Service chain of 6 synchronous hops at 5ms avg each adds 30ms baseline latency; at P99 each hop is 20ms — aggregate P99 is 120ms added latency |
| **Disk** | What is the persistence model? Is data normalized (relational, single owner) or denormalized (read replicas, event-sourced projections)? What is the write amplification factor? | Event sourcing with 10 projections multiplies every write by 10× in storage and I/O — acceptable only if the query patterns justify it |
| **Locks / Contention** | Does the architecture require distributed locking (leader election, distributed mutex)? What is the failure behavior when the lock service is unavailable? Is optimistic concurrency (ETag, version vector) sufficient? | Distributed lock service becomes a single point of failure; all write operations block when the lock service is degraded |
| **TPS / QPS** | What is the throughput ceiling of each architectural layer? Where is the first bottleneck resource (database connection pool, message broker partition count, API gateway rate limit)? Is the ceiling above the projected peak load with 2× headroom? | API gateway has a 10k RPS hard limit; projected peak is 8k RPS with no headroom for traffic spikes or DDoS |
| **Parallelism — Amdahl's Law** | What fraction of the workload is inherently sequential (single-threaded coordinator, global serialization point, distributed transaction)? Apply Amdahl: maximum throughput speedup = 1/(1−p). Is the sequential fraction documented? | SAGA orchestrator serializes all saga steps — effectively sequential; parallel execution adds coordination overhead with no throughput gain |
| **Concurrency** | Does the architecture introduce distributed concurrency problems (split-brain, write conflicts, inconsistent reads across replicas)? Is the consistency model (strong, eventual, causal) explicitly chosen and acceptable for the use case? | Two services both write to `user.email` without a coordinator — last-write-wins with non-deterministic ordering; email updates silently overwrite each other |
| **Response Latency — Service Chaining** | Apply the service-chain latency model: P99_aggregate ≈ sum of P99 per synchronous hop. For N parallel fan-out calls: probability of at least one call exceeding P99_single ≈ 1 − (1−0.01)^N. Are both chain depth and fan-out modeled? | P99 per service = 30ms; 5 synchronous service hops → aggregate P99 ≥ 150ms baseline (additive); 10 parallel fan-out calls at P99=30ms → ~10% of aggregate responses have at least one slow call |

**Additional Professional Considerations for Architecture Decisions:**
- **Operational cost is an architectural constraint**: Every new service, queue, topic, and database adds operational overhead (on-call burden, deployment pipeline, monitoring dashboard, runbook). This cost is real and recurring. Quantify it: "this adds one new service × estimated 2h/week operational overhead." Do not treat operational simplicity as a soft concern.
- **Availability chain — Amdahl applied to service SLOs**: If Service A (99.9% available) calls Service B (99.5% available) synchronously, the combined availability is at most 99.9% × 99.5% = 99.4%. Every synchronous dependency reduces combined availability. Document the availability arithmetic before endorsing a dependency.
- **Data ownership as an architectural invariant**: Each entity has exactly one authoritative owner. If two services can both write to the same entity without a coordinator, consistency is non-deterministic. Enforce this invariant at design time — it becomes exponentially harder to fix after data drift accumulates.
- **ADR as the proof of optimality challenge**: The three-challenge rule's output IS the ADR. "Context" = problem statement. "Decision" = chosen approach. "Rationale" = why this approach over the strongest alternative. "Consequences" = tradeoffs accepted. An ADR that does not name a rejected alternative is an incomplete ADR.

## Risk Escalation Rules
- Escalate when the change alters the ownership boundary of a shared service used by multiple teams.
- Escalate when persistence ownership moves between services — this affects consistency, migration, and disaster recovery.
- Escalate when a new synchronous dependency reduces overall system availability (Amdahl's Law of service chaining).
- Escalate when the proposed design relies on eventual consistency for money movement, authorization decisions, or audit records.
- Escalate when a change cannot be rolled back without manual data migration or customer-visible downtime.
- Escalate when the design adds a new external vendor dependency that creates a single point of failure.
- Escalate when the change affects publicly documented API contracts with SLA obligations.

## Critical Details
- The hardest architectural problems are not technical — they are ownership and coordination problems. Name the owner before approving the design.
- Architecture drift accumulates via individually approved changes — always check the cumulative direction, not just the isolated change.
- "We can refactor later" is an escalation signal, not a resolution — future refactors rarely happen unless the pain is immediate.
- Distributed transactions (2PC, SAGA) add significant complexity; require explicit documentation of the failure recovery and compensating transaction model.
- Every new queue, topic, or event stream requires: schema ownership, versioning strategy, consumer documentation, and dead-letter handling.
- GraphQL federated schemas, service meshes, and API gateways each solve specific problems — they also introduce operational complexity that must be owned by an operator.
- Security boundaries are architectural boundaries: if services share a database directly, they share a security perimeter — document this explicitly.
- Circuit breakers and bulkheads must be configured with realistic thresholds — default "open" thresholds from libraries are rarely appropriate for production.

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

## Output Contract
Return a structured architecture review with:
- **Decision**: Approved / Approved with conditions / Returned for redesign.
- **Alternatives considered**: At least one simpler alternative with explicit reason for rejection.
- **Boundary impact**: New or changed module and service boundaries with ownership declarations.
- **Dependency impact**: New dependencies with direction, coupling level, and availability analysis.
- **Data ownership impact**: Any changes to authoritative data ownership with contract requirements.
- **Tradeoff analysis**: Explicit tradeoffs accepted (performance vs. consistency, simplicity vs. extensibility, etc.).
- **Failure blast radius**: Operational impact if the new component fails.
- **Observability requirements**: Metrics, traces, and alerts required for the new component.
- **ADR requirement**: Yes/No — whether a written ADR is required before implementation.
- **Open risks**: Unresolved design risks with proposed owners and review dates.

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

## Handoff
- **data-api-contract-changer** — when new or changed data models, schemas, or API contracts require design.
- **backend-change-builder** — when implementation direction is confirmed and coding can begin.
- **integration-change-builder** — when new external service dependencies are introduced.
- **reliability-observability-gate** — when new components require SLI/SLO definition and observability design.
- **delivery-release-gate** — when architectural changes affect deployment topology, migration sequencing, or rollback safety.
- **change-documentation-gate** — when an ADR, runbook, or developer guide update is required.

## Completion Criteria
The change has an architecture direction with justified complexity, documented tradeoffs, declared ownership for all boundaries, an explicit failure handling strategy, a quantified availability impact, and either an approved ADR or a documented rationale for why one is not required.
