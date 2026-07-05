# Microservice Splitting Benchmarks And Patterns

Use this reference when `microservice-splitting` needs deeper split-force calibration, extraction patterns, distributed-consistency choices, operability readiness, or anti-pattern review. Keep `SKILL.md` focused on selection, evidence, output, and gates.

## Benchmark Anchors

- **Domain-Driven Design:** deployable service boundaries should align with bounded contexts, ubiquitous language, and aggregate ownership.
- **Monolith-first heuristic:** prefer modular monolith repair unless independent deployment, scaling, ownership, failure isolation, or compliance is a hard force.
- **Team Topologies:** service ownership must fit team cognitive load, stream ownership, and platform support.
- **Strangler fig and branch by abstraction:** extraction should be phased behind routing seams or internal abstractions before traffic moves.
- **Consumer-driven contract testing:** mixed-version service windows need compatibility checks before independent release.
- **Transactional outbox/inbox and Saga patterns:** cross-service workflows need durable events, idempotency, compensation, and reconciliation.
- **SRE operational readiness:** every new runtime unit needs SLO, alerts, dashboards, runbook, capacity, cost, and on-call owner.
- **DORA deployment independence:** a split is not real if services still require coordinated deployment for normal changes.

## Split Force Calibration

| Force | Strong split evidence | Reject or defer when |
| --- | --- | --- |
| Business capability | Separate bounded context, policy owner, and lifecycle language | Same business rules, same owner, or unclear domain vocabulary |
| Team ownership | Different team owns code, incidents, deploys, and roadmap | Same team owns both sides or platform/on-call is missing |
| Deploy cadence | One side is blocked by another team's release or freeze window | Releases remain coordinated after extraction |
| Scaling or cost | Measured CPU/memory/IO/traffic divergence or cost isolation need | Scale claim lacks profile, capacity, or cost evidence |
| Fault isolation | Failure of one side must degrade rather than cascade | Synchronous hot path still requires both sides to be healthy |
| Compliance or data perimeter | Regulated scope, residency, tenant, or audit boundary shrinks | Same data classification and controls remain shared |
| Contract stability | Public API/event schema is stable and versioned | Contract exposes persistence/domain internals or unknown consumers |
| Operational capacity | Platform, observability, on-call, and runbook capacity exists | Another service would exceed team support capacity |

## Extraction Patterns

| Pattern | Fit | Required evidence |
| --- | --- | --- |
| In-process module boundary first | Split force is weak or data/contract readiness is low | Import rule, public facade, ownership map, and reassessment trigger |
| Strangler routing | Legacy capability can be routed by tenant, endpoint, feature, or workflow | Routing seam, parity checks, traffic switch, rollback trigger, retirement criteria |
| Branch by abstraction | Internal code must decouple before runtime split | Adapter seam, feature flag, old/new behavior parity, cleanup owner |
| Parallel run or shadow traffic | New service can compare outputs safely before serving users | Divergence metric, sample scope, cost owner, privacy boundary, stop condition |
| Expand-contract migration | Schema/API compatibility is required during split | Old/new schema support, backfill, dual-read/write decision, cleanup plan |
| Merge or recombine | Independence never materialized or cost exceeds isolation value | Deployment coupling evidence, owner agreement, migration/rollback plan |

## Distributed Consistency Patterns

- Keep a workflow in-process when atomic correctness is mandatory and no compensation exists.
- Use Saga orchestration when one owner needs visible command over long-running steps.
- Use Saga choreography when event ownership is mature and replay/ordering are observable.
- Use transactional outbox and inbox/dedup for durable event publication and idempotent consumption.
- Use reconciliation when eventual consistency is accepted; name cadence, owner, alert, and repair path.
- Avoid two-phase commit as the default service-split answer unless the platform and failure model explicitly support it.

## Operability Readiness Pattern

Before production approval, require:

- service owner, release owner, on-call rotation, escalation path, and runbook;
- SLI/SLO, alert thresholds, dashboard, trace propagation, dependency metrics, and log correlation;
- secrets/config ownership, service identity, network policy, TLS/cert ownership, and deploy rollback;
- capacity model, 12-month cost estimate, platform support, and incident rehearsal or not-verified risk;
- retirement plan for legacy path and dashboard signal proving old traffic is gone.

## Anti-Patterns To Reject

| Anti-pattern | Why it fails |
| --- | --- |
| Splitting because a folder is large | Size is not deploy, scale, ownership, fault-isolation, or compliance evidence |
| Shared database after extraction | Keeps release and data coupling while adding network and operational cost |
| New service with no runbook or on-call | Moves failure into production without an owner |
| Synchronous chain on a hot path with no fallback | Multiplies p99 latency and availability risk |
| Big-bang cutover | Removes rollback and hides mixed-version incompatibility until release |
| Contract exposes ORM models | Future persistence refactors become breaking API changes |
| Strangler with no retirement trigger | Legacy and new service run forever |
| Project memory copied into an ADR without source confirmation | Stale assumptions can approve a split whose forces disappeared |
