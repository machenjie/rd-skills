---
name: architecture-style-selection
description: Selects the simplest sufficient architecture style and requires explicit justification before service, event, or distributed complexity is added.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "18"
changeforge_version: 0.1.0
---

# Mission

Select the least complex architecture style that satisfies current constraints, credible 12–24 month growth, ownership, reliability, regulatory boundaries, and delivery cadence — and require explicit justification before service, event, or distributed complexity is added.

# When To Use

Use this capability when a change proposes, questions, or migrates between: monolith, modular monolith, layered/hexagonal/clean, service-oriented (SOA), microservices, event-driven (broker-centric or choreography), serverless/FaaS, edge-deployed, cell-based architecture, or hybrid combinations. Also use when team topology, deployment cadence, blast radius, or compliance scope changes meaningfully.

# Do Not Use When

Do not use this capability to rename an existing architecture for marketing reasons, to justify a personal preference without measured constraints, or to override a local pattern that already satisfies the change safely. Do not use it to design *within* a chosen style — that is the job of `module-boundary-design`, `microservice-splitting`, `event-driven-architecture`, or `layered-architecture-design`.

# Non-Negotiable Rules

- Default to the **simplest architecture** that satisfies measurable constraints. Complexity is paid by operations, not by authors.
- Prefer a **modular monolith** before microservices unless **independent deployability, independent scaling, independent failure isolation, regulatory boundary, or independent team ownership** justifies service separation. Codebase size, language preference, or hiring narrative are not justifications.
- State the decision forces explicitly: coupling, deployability, data ownership, latency budget, availability target, compliance boundary, team Cognitive Load (Team Topologies), operating cost, talent availability, on-call maturity.
- Include the **migration path** from the current structure to the chosen style — strangler fig steps, dual-running window, rollback condition, freeze points.
- Do not add distributed boundaries to compensate for unclear module boundaries. Network calls do not enforce design; they amplify failure.
- Require **at least one rejected alternative** with the constraint that disqualified it.
- Decisions must be recorded as an ADR (`architecture-tradeoff-analysis` output).
- Operational readiness must be proved, not assumed: each new runtime component requires owner, SLO, alert, runbook, deploy pipeline, observability before go-live.

# Industry Benchmarks

Anchor against: **ADRs (Michael Nygard)**, **C4 model (Simon Brown)** for context/container/component diagrams, **Modular Monolith** practice (Simon Brown, Kamil Grzybek), **Domain-Driven Design** (Evans) for bounded contexts, **Team Topologies** (Skelton/Pais) for stream-aligned/platform/enabling/complicated-subsystem teams, **Evolutionary Architecture** (Ford/Parsons/Kua) including fitness functions, **DORA / Accelerate** metrics (deployment frequency, lead time, change-fail rate, MTTR), **Reactive Manifesto** for responsive/resilient/elastic/message-driven, **Cell-Based Architecture** (AWS, Slack), **12-Factor App** (Heroku), **CNCF** maturity model for cloud-native operability, **Conway's Law** & inverse-Conway maneuver, **Google SRE** operational readiness review (ORR), **Microservices premium / monolith first** (Martin Fowler).

### Style Comparison Matrix

| Style | Deploy unit | Strongest force | Cost driver | Failure mode if mis-selected |
| --- | --- | --- | --- | --- |
| **Monolith** | 1 process | Speed of change at small scale | Becomes a tangle without internal modules | Cross-cutting edits, contention on release train |
| **Modular monolith** | 1 process, enforced module boundaries | Clear boundaries + low ops cost | Discipline required in code review | Modules drift without architecture fitness tests |
| **Layered / hexagonal** | Often 1 process | Testability, domain isolation | Indirection overhead | Anemic domain, leaky adapters |
| **SOA (coarse services)** | Several services | Reuse across enterprise | ESB / governance overhead | Smart pipes, dumb endpoints |
| **Microservices** | Many small services | Independent deploy/scale/own | Platform, observability, on-call cost grows superlinearly | Distributed monolith — all deploy together but with network in between |
| **Event-driven (choreography)** | Producers + consumers | Decoupling, audit, fan-out | Hard to reason end-to-end | Lost events, ordering bugs, replay storms |
| **Event-driven (orchestration)** | Workflow engine | Visible long-running flows | Engine becomes single point of authority | Workflow bloat, tight coupling to engine |
| **Serverless / FaaS** | Function | Spiky traffic, low baseline, ops offload | Cold starts, vendor lock-in, cost at scale | Hidden distributed monolith via shared DB |
| **Cell-based** | Replicated cell | Blast-radius isolation at scale | Multi-cell routing + data placement cost | Premature for sub-multi-region scale |
| **Edge / multi-region active-active** | Per-region | Low latency, sovereignty | Data conflict resolution | Split-brain on shared mutable data |

### Decision Tree

```
1. Does one team own all the code today?
   ├─ Yes → 2.
   └─ No  → Strong signal toward service split per team boundary (Conway).
              Validate with team-topology and on-call capability before proceeding.

2. Is independent deployment of any part required (release cadence, regulatory freeze, blast radius)?
   ├─ No  → Monolith or modular monolith. STOP. Add fitness tests for module boundaries.
   └─ Yes → 3.

3. Is independent runtime scaling required (CPU/memory/latency profile differs by orders of magnitude)?
   ├─ No  → Modular monolith with separate horizontal scale rarely needs split. Re-evaluate (2).
   └─ Yes → 4.

4. Is the operating organization able to support N additional services?
       (Each service ≈ pipeline + dashboards + alerts + on-call + runbook + SLO + capacity plan.)
   ├─ No  → Stop. Build the platform capability first, or stay modular monolith.
   └─ Yes → 5.

5. Is the dominant interaction synchronous request/response or eventful?
   ├─ Sync-dominant → Microservices with REST/gRPC; minimize chatty calls; co-locate data with owner.
   └─ Event-dominant → Event-driven; choose choreography vs orchestration by who owns the end-to-end view.

6. Is per-tenant or per-region blast radius isolation a stated requirement?
   ├─ Yes → Add cell-based partitioning over the chosen style.
   └─ No  → Proceed.
```

# Selection Rules

Select this capability when the primary decision is **the architecture style itself**. Adjacent routing:

- Prefer `module-boundary-design` when the style is already chosen and the question is how to draw internal boundaries.
- Prefer `microservice-splitting` when a concrete service split is proposed within an already-services architecture.
- Prefer `event-driven-architecture` when async flow design is primary (broker topology, ordering, replay).
- Prefer `architecture-tradeoff-analysis` when the question is how to record the decision, not which to choose.
- Prefer `extensibility-design` when the question is plugin/extension points, not topology.
- Use **with** `domain-impact-modeler` to align bounded contexts with style boundaries before splitting.

# Risk Escalation Rules

Escalate when the selected style changes: deployment topology, data ownership, availability/RTO/RPO targets, incident response ownership, compliance boundary (PCI/HIPAA/GDPR data residency), release cadence, the number of runtime components operators must support, the on-call rotation count, or vendor lock-in posture. Specifically escalate when moving from monolith → microservices without an existing platform team, or when moving to serverless for workloads with > 50 RPS sustained or > 100 ms latency budgets. Escalate any "rewrite vs evolve" decision to leadership with explicit cost ranges.

# Critical Details

The right style is constrained by the **team and operating model** as much as by code shape. Apply these refinements:

- **Conway's Law is not optional.** Architecture you ship will mirror your communication structure. If you cannot change the org, do not draw boundaries the org cannot maintain.
- **Modular monolith ≠ legacy monolith.** A modular monolith enforces module boundaries via package/namespace rules, architecture fitness tests (ArchUnit, dependency-cruiser, Sonargraph), and module-owned migrations. Without enforcement it decays.
- **Microservices require platform capabilities before the first split:** CI/CD per service, container/runtime platform, service discovery, centralized logging, distributed tracing (OpenTelemetry), metrics, alerting, secrets, config, identity, service mesh or library equivalent, deploy automation, on-call rotation, runbooks, SLOs. Missing platform capabilities turn microservices into a **distributed monolith** — strictly worse than the monolith.
- **Event-driven designs require:** schema registry with compatibility rules, replay semantics, dead-letter handling, idempotent consumers, ordering guarantees made explicit per topic, lag/backlog monitoring, contract tests across producers and consumers. Without these, eventual consistency becomes eventual incident.
- **Data ownership is the hardest boundary to move.** A service split that leaves shared databases is a distributed monolith. Plan database split before, with, or as the explicit non-goal of the service split — but never silently after.
- **Latency budget.** Every network hop adds p99 jitter measured in tens of ms. Budget end-to-end latency *before* deciding on hops. Mobile and global traffic make this brutal.
- **Migration is the design.** Strangler fig, branch-by-abstraction, expand-contract, dual-write/dual-read with reconciliation, parallel-run with shadow traffic — pick one explicitly. "We will rewrite then cut over" is rarely a credible plan.
- **Reversibility class.** Classify the decision (Bezos Type 1 = irreversible vs Type 2 = reversible). Irreversible decisions (data model, public contracts, partitioning key) deserve a higher bar.
- **Cost model.** Serverless and microservices shift cost from CapEx (servers) to OpEx (per-invocation, per-deploy, per-tracer). Model 12-month cost at projected scale, not at today's scale.
- **Compliance perimeter.** PCI scope shrinks when card-data services are isolated; HIPAA PHI scope shrinks when PHI lives in a single service; GDPR data residency may force per-region services. Style choice is regulated.
- **On-call sustainability.** Each new service adds rotation load. If on-call is already burning out the team, adding services compounds it.
- **Fitness functions.** Encode the constraints that justified the style as automated tests (e.g., "no module X imports module Y", "p95 ≤ 200ms in synthetic test", "service has SLO + alert"). Without fitness functions, architecture decays silently.

# Failure Modes

- Microservices selected because the codebase "feels large" or for resume-driven reasons, not because deploy/scale/own boundaries require it. Result: distributed monolith.
- Modular monolith remains unmodular; every change is cross-cutting; release contention; team morale collapses.
- Event-driven architecture used to **hide** unclear ownership or transaction boundaries → ordering bugs, replay storms, missing messages, debugging nightmares.
- The decision ignores **migration cost, production support burden, or local team maturity** — paper architecture that never ships.
- Style is chosen with no rejected alternatives → impossible to audit or revisit; locks future leaders into the same mistake.
- "Microservices" with one shared database → distributed coupling without distributed benefit; every deploy still needs coordination.
- Serverless chosen for sustained high-throughput workloads → cost explodes, cold-start latency violates SLA.
- Premature cell-based isolation at small scale → operational overhead with no resilience benefit.
- Active-active multi-region on mutable shared data without conflict resolution strategy → split-brain.
- Decision is made, never reviewed; system grows past the constraints that justified it; no reassessment trigger.
- Org reorganized but architecture not revisited → boundaries no longer match teams; ownership decays.
- "Strangler fig" begun but never finished — legacy + new run forever, doubling cost.

# Output Contract

Return an architecture style decision document containing:

- `selected_style` (with sub-style: e.g., modular monolith with hexagonal layering)
- `constraints` (forces ranked by weight: deployability, scalability, latency, availability, compliance, team topology, cost, talent)
- `rejected_alternatives` (≥ 1, each with the disqualifying constraint)
- `justification` (mapping forces → style choice)
- `boundaries` (module list for monolith; service list for services; bounded-context map)
- `data_ownership_impact` (per-data-domain owner; shared vs split databases; migration class)
- `deployment_impact` (deploy units, pipeline count, release cadence change, blue-green / canary capability required)
- `operational_obligations` (per new runtime component: SLO, alerts, runbook, on-call, dashboard, capacity plan)
- `migration_path` (named pattern: strangler fig / expand-contract / branch-by-abstraction; phases; rollback condition; freeze points; dual-run window)
- `risks` (technical, organizational, financial) with `mitigations` and `residual_risk`
- `cost_model` (12-month projection at projected scale: infra, platform, on-call, opportunity)
- `reversibility_class` (Type 1 irreversible / Type 2 reversible)
- `fitness_functions` (automated checks that detect drift from the decision)
- `reassessment_trigger` (concrete signal that requires re-deciding: traffic, team count, compliance change, cost threshold)
- `review_owner` (named individual + escalation chain)
- ADR-ready prose (context, decision, status, consequences)

# Quality Gate

The decision passes only when:

1. The chosen style is the **least complex option** that satisfies explicit constraints, and the simpler rejected option has a documented disqualifying constraint.
2. Migration is a credible engineering plan, not aspiration.
3. Operational obligations are owned by named teams **before** go-live.
4. Fitness functions are encoded in CI to detect drift.
5. The reassessment trigger is specific (number/event), not "periodically".
6. Compliance, data residency, and PII/PHI scope are explicitly addressed.
7. The decision survives a hostile review by an architect outside the proposing team.

# Used By

- architecture-impact-reviewer

# Handoff

Hand off to `architecture-tradeoff-analysis` for ADR formalization; `module-boundary-design` for internal boundary design; `microservice-splitting` for concrete service separation; `event-driven-architecture` for asynchronous flow design; `domain-impact-modeler` to validate bounded-context alignment; `delivery-release-gate` for migration rollout sequencing; `reliability-observability-gate` for operational readiness review.

# Completion Criteria

The capability is complete when the architecture style is justified by **concrete, measurable constraints**; simpler alternatives were tested and disqualified by named forces; operational consequences are visible and owned; migration is planned with rollback; and drift detection (fitness functions, reassessment trigger) is in place so the decision can be honestly revisited.
