# Architecture Style Selection Benchmarks And Patterns

Load this reference when a system-wide style, runtime boundary, migration path or reversibility decision is genuinely open. Select the least-complex style that survives current product, data, ownership, failure and operational forces.

## Style Fit

| Style | Strong fit | Reject/defer when | Required proof |
| --- | --- | --- | --- |
| Plain monolith | One cohesive owner/process and rapid change matter more than internal boundary formality. | Cross-cutting edits, release contention or tangled ownership are current problems. | Change locality, owner, deploy/rollback and a trigger for modularization. |
| Modular monolith | One deploy/owner, strong local transactions and repairable module boundaries meet needs. | Independent scale/deploy/fault/compliance force is current and material. | Module contracts, dependency enforcement and future extraction seam. |
| Layered/clean/hexagonal | Dependency direction and separation of policy from delivery/infrastructure are the main force. | Extra abstractions have no enforcement or owner. | Selected layer contract, import rules and domain/use-case tests. |
| Coarse SOA | Enterprise/coarse capability ownership or shared integration governance is an actual constraint. | Central governance, shared platform/data or “smart pipes” preserve tight coupling. | Service contract/owner, deployment/data independence and governance cost. |
| Microservices | Bounded capabilities need independent ownership/deploy/scale/fault/compliance perimeters. | Shared database/releases/on-call remain coupled or platform cost is unowned. | Service/data/contract/operability and extraction plan. |
| Event-driven | Asynchronous decoupling, replay, fan-out or temporal facts are primary. | Ordering, idempotency, lag, schema and recovery ownership are absent. | Producer/consumer, delivery/ordering, replay and consistency contract. |
| CQRS/read models | Write invariants and read/query/scale shapes differ materially. | One model is sufficient or projection rebuild/staleness is unowned. | Source authority, projection update/rebuild and consumer lag behavior. |
| Serverless/managed runtime | Bounded/spiky workload benefits from platform operations. | Runtime/latency/state/concurrency/portability/unit-cost constraints fail. | Provider limits, cost/load and failure/exit evidence. |
| Multi-tenant/region isolation shape | Tenant/region perimeter is driven by residency, noisy-neighbor, blast-radius or availability requirements. | Added duplication/routing/consistency cost lacks ownership. | Placement, identity/data isolation, failover and cost model. |

## Forces, Migration, And Reversibility

- Classify deploy cadence, scale/cost divergence, failure isolation, data consistency/authority, team ownership, compliance/residency, latency, portability and operating maturity. A style name without ranked forces is not a decision.
- Synchronous calls keep simple request semantics but couple latency/availability; events trade immediate consistency for durable delivery, ordering, idempotency, replay and reconciliation obligations.
- Migration uses an owned seam such as module repair, strangler routing, branch by abstraction, contract bridge, parallel run or expand-contract. Name mixed states, traffic/data move, rollback and legacy retirement.
- Classify the change as readily reversible, conditionally reversible, or effectively irreversible from data, client, runtime, and exit cost. The evidence records the rejected simpler style and a measurable re-evaluation trigger.

## Operability And Proof Limits

| Added surface | Evidence needed |
| --- | --- |
| Runtime/deployable | Code/release/on-call owner, health/degradation/rollback, telemetry/runbook, capacity and cost. |
| Data boundary | Single writer, migration/coexistence, consistency/reconciliation, backup/restore and privacy classification. |
| Public/event contract | Consumer inventory, compatibility/versioning, schema/generated evidence and deprecation owner. |
| Network/dependency | Latency/timeout/failure budget, identity/authorization, retry/idempotency and blast-radius behavior where required. |

ADRs, diagrams, repository graphs and prior incidents are discovery evidence; they do not prove live topology, traffic, ownership, provider limits, production cost or incident readiness. Validate the forces and new runtime obligations after the final architecture edit.

Route module shape to `module-boundary-design`, extraction to `microservice-splitting`, events to `event-driven-architecture`, layer rules to `layered-architecture-design`, operability to `reliability-observability-gate`, and regulated perimeters to `security-privacy-gate`.

Reject style-by-fashion, one-team/one-file-count heuristics as gates, distributed monoliths, and shared data with multiple writers. Also reject events without consumers/replay ownership, added runtimes without operators, migration without retirement, and “cloud agnostic” abstractions without a plausible exit force.
