# Architecture Style Selection Benchmarks And Patterns

Use this reference when `architecture-style-selection` needs more than routing-level guidance. Keep the main `SKILL.md` focused on mode selection, evidence, output, and gates; use this file for style comparison, force scoring, migration and reversibility, operational readiness, graph/memory/trajectory coupling, and anti-pattern review.

## Benchmark Anchors

- **ADRs and C4 model:** record the style decision and show context/container/component consequences.
- **Modular monolith practice:** enforce internal boundaries before paying distributed-system costs.
- **Domain-Driven Design:** align deployable or module boundaries with bounded contexts and data ownership.
- **Team Topologies and Conway's Law:** architecture must fit ownership, cognitive load, and communication paths.
- **Evolutionary Architecture:** define fitness functions that keep chosen constraints from decaying.
- **DORA/Accelerate:** use deployment frequency, lead time, change failure rate, and MTTR as evidence for delivery forces.
- **Google SRE ORR:** every new runtime unit needs SLO, alerting, runbook, capacity, and owner readiness.
- **Cell-based and multi-region architecture:** use for explicit blast-radius, sovereignty, or regional latency needs.
- **12-Factor and CNCF maturity:** require deployability, config, logs, process model, and platform support before service proliferation.
- **Microservices premium / monolith-first heuristic:** split only when independent deployability, scaling, failure isolation, compliance, or ownership outweighs operational cost.

## Style Comparison Matrix

| Style | Deploy unit | Strongest force | Cost driver | Failure mode if mis-selected |
| --- | --- | --- | --- | --- |
| Monolith | One process. | Speed of change at small scale. | Internal structure can tangle. | Cross-cutting edits and release contention. |
| Modular monolith | One process with enforced modules. | Clear boundaries with low ops cost. | Boundary discipline and architecture checks. | Modules drift without fitness tests. |
| Layered / hexagonal | Usually one process. | Testability and domain isolation. | Indirection and adapter overhead. | Anemic domain or leaky adapters. |
| SOA | Several coarse services. | Enterprise reuse or coarse ownership. | Governance and shared platform overhead. | Smart pipes and tightly governed endpoints. |
| Microservices | Many independently deployed services. | Independent deploy, scale, own, or isolate. | Platform, observability, on-call, and data consistency. | Distributed monolith. |
| Event-driven choreography | Producers and consumers. | Decoupling, fan-out, audit, latency decoupling. | Replay, ordering, and observability complexity. | Lost events, replay storms, stale projections. |
| Event-driven orchestration | Workflow engine plus participants. | Visible long-running flow. | Engine governance and operational ownership. | Workflow bloat or engine coupling. |
| Serverless / FaaS | Function. | Spiky traffic and low baseline operations. | Cold starts, vendor lock-in, and cost at scale. | Hidden distributed monolith over shared data. |
| Cell-based | Replicated cell. | Blast-radius isolation at scale. | Routing, placement, and multi-cell ops. | Premature operational overhead. |
| Edge / active-active | Per region or edge runtime. | Latency, sovereignty, or locality. | Conflict resolution and deployment consistency. | Split-brain on mutable shared data. |

## Force Scorecard

Score each candidate style against the current and credible 12-24 month forces. Hard constraints disqualify options; soft forces only rank surviving options.

| Force | Evidence to inspect | Disqualifies simpler option when |
| --- | --- | --- |
| Independent deployment | Release cadence, freeze windows, deploy ownership, rollback evidence. | One deploy unit blocks a team, regulation boundary, or critical release cadence. |
| Independent scaling | Traffic shape, CPU/memory/IO profiles, autoscaling limits, cost model. | One component differs by orders of magnitude and cannot be isolated inside one deploy. |
| Failure isolation | Incident history, blast-radius requirement, SLO and error budget. | Shared runtime failure violates user, tenant, or regulatory isolation. |
| Data ownership | Schema ownership, transaction boundaries, shared DB coupling, migration path. | Data owner or regulated scope must change independently. |
| Latency | p50/p95/p99 budget, network hop count, region/edge needs. | Local call cannot satisfy locality or latency, or network split would violate budget. |
| Team topology | CODEOWNERS, team map, cognitive load, coordination cost. | One team cannot safely own the whole deployable boundary. |
| Compliance | PCI/HIPAA/GDPR/data residency classification. | Regulated data must be isolated to reduce scope or residency exposure. |
| Operational maturity | CI/CD, observability, SLOs, on-call, runbooks, incident process. | The organization can run the added topology before go-live. |
| Cost | 12-month infra, tracing, platform, on-call, opportunity, migration cost. | Added topology has approved budget and cheaper style cannot satisfy hard forces. |

## Decision Tree

```text
1. Does one team own the code and runtime today?
   - Yes: prefer monolith or modular monolith unless a hard force disqualifies it.
   - No: evaluate ownership-aligned boundaries, then validate platform and on-call maturity.

2. Is independent deployment required by release cadence, regulatory freeze, or blast radius?
   - No: keep one deploy unit and strengthen module boundaries.
   - Yes: evaluate service split or cell boundary.

3. Is independent runtime scaling required by measured CPU, memory, I/O, latency, or cost profile?
   - No: avoid service split for scale claims.
   - Yes: confirm the team can operate the new runtime unit.

4. Is the dominant interaction synchronous or eventful?
   - Synchronous: minimize hops and co-locate data with the owner.
   - Eventful: require eventual-consistency product decision, replay safety, and event observability.

5. Is per-tenant, per-region, or regulated blast-radius isolation required?
   - Yes: evaluate cell, region, or bounded service perimeter.
   - No: do not add cell or active-active topology early.

6. Can the migration be phased and reversed or contained?
   - No: classify as Type 1 and raise review bar.
   - Yes: define phases, rollback triggers, and retirement criteria.
```

## Migration And Reversibility

| Pattern | Fit | Required evidence |
| --- | --- | --- |
| Strangler fig | Gradual replacement of a legacy capability. | Routing seam, old/new parity checks, cutover window, old path retirement trigger. |
| Branch by abstraction | Internal structure changes before runtime split. | Stable public contract, feature flag or adapter seam, rollback behavior. |
| Expand-contract | Data/API compatibility during migration. | Old/new schema support, backfill, dual-read/write decision, cleanup owner. |
| Parallel run / shadow traffic | Compare new style without serving users. | Comparison metrics, divergence threshold, cost owner, rollback trigger. |
| Cell introduction | Introduce bounded blast radius by tenant/region. | Cell routing key, placement rules, failover behavior, data ownership, operational owner. |

Reversibility classes:

- **Type 2:** reversible with config, routing, or deploy rollback. Evidence can be lighter but still current.
- **Type 1:** hard to reverse because it affects data ownership, public contracts, partition keys, compliance scope, or team ownership. Requires ADR, migration plan, rollback/containment, and leadership/architecture review.

## Operational Readiness Questions

Before approving new runtime units, answer:

- Who owns the service/function/cell/region during business hours and on-call?
- What SLI/SLO detects user-visible failure?
- Which dashboard shows rate, errors, duration, saturation, queue lag, or regional health?
- What alert pages or tickets, and what runbook action follows?
- How is config/secrets/deploy/rollback handled independently?
- What is the capacity model and 12-month cost projection?
- What trace context crosses boundaries?
- What failure mode is intentionally degraded rather than hard failed?

## Graph, Memory, And Trajectory Coupling

Treat repository graph, project memory, and execution trajectory as leads, not proof.

- Repository graph can suggest current modules, services, imports, deployment artifacts, generated clients, tests, and owners. Confirm with current files.
- Project memory can explain why a style was chosen or why a prior migration failed. Confirm that the constraints still exist.
- Execution trajectory can reveal edit-before-read, repeated failed service splits, skipped validation, or stale ADR assumptions. Use it to raise review depth, not to skip evidence.
- If current source contradicts graph or memory, current source wins and the discrepancy becomes a residual-risk note or follow-up.

## Validation Evidence Patterns

A strong architecture-style handoff includes:

- current architecture and deploy topology inspected;
- candidate style list and force scorecard;
- least-complex selected style with rejected simpler alternative;
- data ownership and transaction-boundary impact;
- operational readiness gap list for every added runtime unit;
- migration pattern, phases, rollback, dual-run, and retirement trigger;
- fitness functions such as import rules, deploy independence checks, latency budget checks, or SLO/alert existence checks;
- security/privacy/compliance review when style changes data perimeter or trust boundary;
- reliability review when style changes runtime components, latency, queueing, capacity, or on-call;
- evidence limits and next gate.

## Anti-Patterns To Reject

| Anti-pattern | Why it fails |
| --- | --- |
| Microservices because the codebase feels large. | Size is not a deploy, scale, ownership, or failure-isolation force. |
| Service split with shared database and coordinated releases. | Keeps coupling while adding network, deploy, and observability cost. |
| Event-driven style to hide unclear transaction ownership. | Moves the ambiguity into replay, ordering, and debugging failures. |
| Serverless for sustained high-throughput low-latency path without cost/latency proof. | Cold starts and per-invocation cost can violate both budget and SLO. |
| Cell architecture before tenant/region blast-radius need. | Adds routing and data-placement overhead with no resilience return. |
| Active-active mutable data without conflict strategy. | Creates split-brain and silent data divergence. |
| ADR copied from project memory without source confirmation. | Stale context can preserve an obsolete decision. |
| Strangler migration without retirement trigger. | Legacy and replacement run forever. |
| No fitness functions. | Architecture decays silently after the decision. |
| Operational readiness deferred until after go-live. | New topology fails before it can be diagnosed or rolled back. |
