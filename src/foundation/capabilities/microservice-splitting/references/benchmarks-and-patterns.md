# Microservice Splitting Benchmarks And Patterns
Use this reference when `microservice-splitting` needs deeper split-force calibration, extraction patterns, distributed-consistency choices, operability readiness, or anti-pattern review. Keep `SKILL.md` focused on selection, evidence, output, and gates.
## Benchmark Anchors
- **DDD / monolith-first:** align deployable boundaries with bounded context, language, aggregate, and a hard independence/scale/ownership/fault/compliance force; otherwise repair the modular monolith.
- **Team Topologies / DORA:** Treat independent code, deployment, and incident ownership plus reduced routine coordination as service-split evidence. Reject or revisit the split when normal delivery or recovery still requires synchronized ownership across its proposed boundary.
- **Strangler / branch by abstraction / consumer contracts:** phase behind routing or internal seams and prove mixed-version compatibility before traffic and releases move.
- **Outbox/inbox and Saga:** durable events need idempotency, compensation, and reconciliation.
- **SRE:** for an independently deployed runtime, derive ownership, service levels, alerts, dashboard/runbook, capacity, cost, and security artifacts from its actual failure modes and operating policy; omit untriggered artifacts with rationale.
## Split Force Calibration

| Force | Strong split evidence | Reject or defer when |
| --- | --- | --- |
| Business capability | Separate bounded context, policy owner, and lifecycle language | Same business rules, same owner, or unclear domain vocabulary |
| Team ownership | Different team owns code, incidents, deploys, and roadmap | Same team owns both sides or platform/on-call is missing |
| Deploy cadence | One side is blocked by another team's release or freeze window | Releases remain coordinated after extraction |
| Scaling or cost | Measured CPU/memory/IO/traffic divergence or cost isolation need | Scale claim lacks profile, capacity, or cost evidence |
| Fault isolation | When fault isolation is a split force, failure on one side has a defined contained or degraded outcome instead of uncontrolled propagation. | Synchronous hot path still requires both sides to be healthy |
| Compliance or data perimeter | Regulated scope, residency, tenant, or audit boundary shrinks | Same data classification and controls remain shared |
| Contract stability | Public API/event schema is stable and versioned | Contract exposes persistence/domain internals or unknown consumers |
| Operational capacity | Platform, observability, on-call, and runbook capacity exists | Another service would exceed team support capacity |

## Extraction Patterns

| Pattern | Fit | Required evidence |
| --- | --- | --- |
| In-process module boundary first | Split force is weak or data/contract readiness is low | Import rule, public facade, ownership map, and reassessment trigger |
| Strangler routing | Legacy capability can be routed by tenant, endpoint, feature, or workflow | Routing seam, parity checks, traffic switch, rollback trigger, retirement criteria |
| Branch by abstraction | When this pattern prepares a runtime split, decouple internal code before activating the split | Adapter seam, feature flag, old/new behavior parity, cleanup owner |
| Parallel run or shadow traffic | New service can compare outputs safely before serving users | Divergence metric, sample scope, cost owner, privacy boundary, stop condition |
| Expand-contract migration | Schema/API compatibility is required during split | Old/new schema support, backfill, dual-read/write decision, cleanup plan |
| Merge or recombine | Independence never materialized or cost exceeds isolation value | Deployment coupling evidence, owner agreement, migration/rollback plan |

## Distributed Consistency Patterns
- Keep a workflow in-process when atomic correctness is mandatory and no compensation exists.
- Choose Saga orchestration for one visible command owner, or choreography only with mature event ownership and observable replay/ordering.
- Use outbox plus inbox/dedup for durable publication/consumption; accepted eventual consistency also names reconciliation cadence, owner, alert, and repair.
- Avoid two-phase commit as the default service-split answer unless the platform and failure model explicitly support it.

## Operability Readiness Pattern

Before production approval, inventory the risks introduced by the independently deployed boundary:
- name service/release/incident owners and verify deployment, rollback, and escalation paths;
- select SLI/SLO, alerts, dashboards/tracing/log correlation, runbook, capacity, and cost evidence from the accepted availability and recovery risks;
- add secrets/config, identity, network, TLS/certificate, platform, or rehearsal artifacts when the split creates or changes those boundaries;
- when a legacy path remains, name its retirement owner, trigger, and observable traffic evidence.

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
| prior task evidence copied into an ADR without source confirmation | Stale assumptions can approve a split whose forces disappeared |
