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

# Stage Fit

Use during architecture planning when the style, deployable unit, runtime topology, team boundary, compliance perimeter, or migration path is still being chosen. Use during review when a proposal adds services, events, serverless functions, cells, regions, or edge/runtime boundaries and claims the complexity is justified. Treat repository graph, project memory, and execution trajectory as discovery inputs only: current source, tests, deploy topology, ownership files, ADRs, runbooks, and validation output must confirm or reject that evidence before it influences the decision. Hand off when the style is chosen and the remaining work is internal module design, concrete service extraction, event-flow design, ADR wording, release sequencing, or production readiness.

# Non-Negotiable Rules

- Default to the **simplest architecture** that satisfies measurable constraints. Complexity is paid by operations, not by authors.
- Prefer a **modular monolith** before microservices unless **independent deployability, independent scaling, independent failure isolation, regulatory boundary, or independent team ownership** justifies service separation. Codebase size, language preference, or hiring narrative are not justifications.
- State the decision forces explicitly: coupling, deployability, data ownership, latency budget, availability target, compliance boundary, team Cognitive Load (Team Topologies), operating cost, talent availability, on-call maturity.
- Include the **migration path** from the current structure to the chosen style — strangler fig steps, dual-running window, rollback condition, freeze points.
- Do not add distributed boundaries to compensate for unclear module boundaries. Network calls do not enforce design; they amplify failure.
- Require **at least one rejected alternative** with the constraint that disqualified it.
- Decisions must be recorded as an ADR (`architecture-tradeoff-analysis` output).
- Operational readiness must be proved, not assumed: each new runtime component requires owner, SLO, alert, runbook, deploy pipeline, observability before go-live.

# Mode Matrix

Select the architecture-style mode before recommending topology or migration.

| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities | Skip by default |
| --- | --- | --- | --- | --- | --- |
| Baseline style selection | New product area, unclear topology, greenfield module/service choice, or no current ADR. | Choose least-complex style from current constraints and credible 12-24 month forces. | Current architecture, force ranking, rejected simpler option, owner/review path. | `architecture-impact-reviewer`, `architecture-tradeoff-analysis` | Distributed boundaries before constraints are measured. |
| Complexity escalation review | Microservice, event-driven, serverless, cell, edge, or multi-region boundary is proposed. | Prove deploy/scale/fault/compliance/team force exceeds operational premium. | Simpler-style disqualification, operational readiness gap list, cost/reliability impact. | `reliability-observability-gate`, `delivery-release-gate` | "Codebase is large" as justification. |
| Style migration | Current style is moving to modular monolith, services, events, cells, or hybrid. | Make migration reversible where possible and prevent legacy-plus-new forever. | Migration pattern, phases, freeze points, rollback/containment, dual-run owner. | `module-boundary-design`, `data-migration-design`, `release-rollback` | Rewrite-then-cutover without proving rollback. |
| Org/compliance boundary | Team topology, data residency, PCI/HIPAA/GDPR scope, or ownership changes. | Align style to owners and regulated data boundaries without over-fragmenting. | Team map, data classification, compliance perimeter, approval owner. | `domain-impact-modeler`, `security-privacy-gate`, `permission-boundary-modeling` | Org chart as sole architecture proof. |
| Drift reassessment | Repository graph, project memory, incidents, cost, release contention, or execution trajectory shows style no longer fits. | Reassess current style using current-source and operational evidence. | Drift signal, source confirmation, DORA/SLO/cost evidence, keep/change decision. | `repository-graph-analysis`, `project-memory-governance`, `execution-trajectory-analysis` | Treating stale ADRs as current truth. |

# Industry Benchmarks

Anchor against ADRs, C4 diagrams, modular monolith practice, Domain-Driven Design bounded contexts, Team Topologies, evolutionary architecture and fitness functions, DORA/Accelerate metrics, cell-based architecture, 12-Factor and CNCF operability, Conway's Law, SRE operational readiness review, and the microservices premium / monolith-first heuristic. Keep this body focused on mode selection, routing, evidence, and quality gates; load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) for style comparison, force scoring, decision trees, migration and reversibility patterns, operational readiness, graph/memory/trajectory coupling, and anti-pattern detail.

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

# Proactive Professional Triggers

- **Signal:** A microservice, serverless, event-driven, edge, cell, or multi-region style is proposed before current deployability, scaling, ownership, latency, compliance, and reliability constraints are measured. **Hidden risk:** architecture adds operational premium without solving a real force. **Required professional action:** score the forces and disqualify the simpler option with evidence. **Route to:** `architecture-impact-reviewer`, `reliability-observability-gate`. **Evidence required:** force scorecard, rejected simpler option, operating model and cost impact.
- **Signal:** Repository graph or project memory suggests the system is "already modular", "already service-oriented", or "ready to split" but current source, ownership, tests, CI, deploy topology, or runbooks were not inspected. **Hidden risk:** stale architecture memory turns into unverified service boundaries. **Required professional action:** confirm graph/memory/trajectory against current source and generated artifacts before decision. **Route to:** `repository-context-map`, `repository-graph-analysis`, `project-memory-governance`, `execution-trajectory-analysis`. **Evidence required:** inspected paths, accepted/rejected memory, freshness limit, unknown boundary list.
- **Signal:** A distributed boundary is introduced while module boundaries, public contracts, data ownership, or transaction ownership are unclear. **Hidden risk:** a network boundary hides a modularity defect and creates a distributed monolith. **Required professional action:** repair or explicitly defer module/data boundary design before style approval. **Route to:** `module-boundary-design`, `data-model-design`, `transaction-consistency`. **Evidence required:** boundary map, public contracts, data owner, shared-database decision, residual risk.
- **Signal:** Style migration has no phased migration, rollback, dual-run, freeze point, or old-system retirement trigger. **Hidden risk:** legacy and new architectures run indefinitely with doubled cost and unclear ownership. **Required professional action:** define migration pattern and reversibility class. **Route to:** `release-rollback`, `delivery-release-gate`, `architecture-tradeoff-analysis`. **Evidence required:** phases, rollback/containment, dual-run owner, retirement trigger.
- **Signal:** Architecture choice changes compliance perimeter, sensitive data flow, tenant isolation, public exposure, or AI/agent tool execution boundary. **Hidden risk:** style change silently expands privacy, security, or prompt/tool attack surface. **Required professional action:** run security/privacy and domain-extension review before approval. **Route to:** `security-privacy-gate`, `threat-modeling`, `ai-product-extension` when model/tool behavior is in scope. **Evidence required:** data classification, trust boundary, allowed actors/tools, redaction and permission evidence.
- **Signal:** New runtime components, queues, regions, cells, functions, or services lack SLOs, alerts, traces, dashboards, runbooks, capacity plan, or on-call ownership. **Hidden risk:** architecture looks clean on paper but is not operable. **Required professional action:** block readiness or mark explicit residual risk until operations evidence exists. **Route to:** `reliability-observability-gate`, `performance-budgeting`, `concurrency-control`. **Evidence required:** SLI/SLO, telemetry, runbook, capacity/cost guardrail, owner.

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

# Reference Loading Policy

The `SKILL.md` body carries L1/L2 architecture-style selection, boundary, and evidence rules. Load [references/checklist.md](references/checklist.md) when drafting or reviewing a concrete style decision, when constraints or migration coverage are uncertain, or before implementation planning depends on the style. Load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) when style comparison, force scoring, migration/reversibility, operational readiness, graph/memory/trajectory reuse, or anti-pattern depth is needed. Use [examples/example-output.md](examples/example-output.md) only when output shape is unclear. Do not load references for pure routing or trivial wording work where the output contract and quality gate are sufficient.

# Output Contract

Return an architecture style decision document containing:

- `mode_selected` (baseline style selection, complexity escalation review, style migration, org/compliance boundary, or drift reassessment)
- `current_architecture_evidence` (source paths, deploy artifacts, ownership docs, ADRs, tests, runbooks, dashboards, and docs inspected; or explicit not-yet-existing state)
- `graph_memory_trajectory_judgment` (repository graph, project memory, and execution trajectory evidence accepted, rejected, or not verified, with freshness limits)
- `selected_style` (with sub-style: e.g., modular monolith with hexagonal layering)
- `constraints` (forces ranked by weight: deployability, scalability, latency, availability, compliance, team topology, cost, talent)
- `style_force_scorecard` (each candidate style scored against hard constraints and credible near-term forces)
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
- `changed_decision_to_validation_map` (each style, boundary, migration, reliability, security, cost, and fitness-function decision mapped to evidence or residual risk)
- `handoff_boundaries` (what moves to module boundary, microservice split, event-driven design, domain impact, security/privacy, reliability, delivery, or ADR formalization)
- `evidence_limits` (what was not verified: production load, unknown consumers, runtime topology, current dashboards, incident history, cost model, or organizational commitment)
- `review_owner` (named individual + escalation chain)
- ADR-ready prose (context, decision, status, consequences)

# Evidence Contract

Close an architecture-style decision only when the output names the selected mode, current architecture evidence, force ranking, simpler option rejected by measured constraint, graph/memory/execution freshness judgment, data ownership impact, deployment impact, operational obligations, migration and rollback path, reversibility class, validation map, handoff boundaries, residual risk, and evidence limits. A style label or "use microservices/modular monolith" statement is not sufficient evidence.

# Benchmark Coverage

Improved style decisions should reject the common weak patterns: distributed boundaries for vague complexity, service splits before module/data ownership, serverless without latency/cost proof, event-driven style without consistency/replay/readiness evidence, cell or active-active topology before blast-radius or sovereignty needs, and stale ADR/project-memory reuse without current-source confirmation. Detailed comparisons and decision aids belong in references so this body stays efficient.

# Routing Coverage

Route here when the primary work is choosing or reassessing architecture style, deployable unit count, runtime topology, topology migration, or whether distributed complexity is justified. Hand off when the style is already chosen and the remaining decision is module internals (`module-boundary-design` or `layered-architecture-design`), concrete service boundaries (`microservice-splitting`), async topology (`event-driven-architecture`), ADR formalization (`architecture-tradeoff-analysis`), production readiness (`reliability-observability-gate`), or rollout sequencing (`delivery-release-gate`).

# Quality Gate

The decision passes only when:

1. The chosen style is the **least complex option** that satisfies explicit constraints, and the simpler rejected option has a documented disqualifying constraint.
2. Migration is a credible engineering plan, not aspiration.
3. Operational obligations are owned by named teams **before** go-live.
4. Fitness functions are encoded in CI to detect drift.
5. The reassessment trigger is specific (number/event), not "periodically".
6. Compliance, data residency, and PII/PHI scope are explicitly addressed.
7. The decision survives a hostile review by an architect outside the proposing team.
8. Current architecture evidence and graph/memory/execution trajectory inputs are confirmed against current source or marked not verified.
9. Every selected style and rejected alternative maps to a measured force, not preference or stale precedent.
10. Data ownership, transaction boundary, and shared-database impact are explicit before any service or event boundary is approved.
11. Reliability, security/privacy, compliance, cost, and on-call obligations are routed to the right gates or recorded as residual risk.
12. Each style/migration/fitness-function decision maps to validation evidence or a named residual risk owner.
13. Handoff boundaries and evidence limits are explicit so style selection is not over-claimed as service split design, event topology proof, production readiness, or ADR approval.

# Used By

- architecture-impact-reviewer

# Handoff

Hand off to `architecture-tradeoff-analysis` for ADR formalization; `module-boundary-design` for internal boundary design; `microservice-splitting` for concrete service separation; `event-driven-architecture` for asynchronous flow design; `domain-impact-modeler` to validate bounded-context alignment; `delivery-release-gate` for migration rollout sequencing; `reliability-observability-gate` for operational readiness review.

# Completion Criteria

The capability is complete when the architecture style is justified by **concrete, measurable constraints**; simpler alternatives were tested and disqualified by named forces; operational consequences are visible and owned; migration is planned with rollback; and drift detection (fitness functions, reassessment trigger) is in place so the decision can be honestly revisited.
