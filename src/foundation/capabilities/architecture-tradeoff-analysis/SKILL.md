---
name: architecture-tradeoff-analysis
description: Produces ADR-ready architecture decisions by comparing alternatives, rejected options, decision forces, risks, mitigations, consequences, and reassessment triggers before durable architecture choices are accepted.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "23"
changeforge_version: 0.1.0
---

# Mission

Make important architecture decisions **reviewable, auditable, and reversibly-traceable** by documenting decision context, options considered, decision forces with weights, rejected alternatives with disqualifying constraints, risks with mitigations and residual risk, consequences across delivery / testing / operations / security / cost, and an explicit reassessment trigger.

# When To Use

Use this capability when a change selects: a structural approach, a foundational dependency (database, broker, runtime, framework), a boundary (service, module, tenant, region), a data ownership model, an integration style (sync/async, push/pull), a deployment topology, a long-lived abstraction (DSL, plugin model, schema-evolution policy), an encryption/identity model, a build/deploy toolchain, or any decision whose blast radius extends beyond one feature.

# Do Not Use When

Do not use this capability for minor implementation choices that are easily reversible, locally scoped, and already covered by existing project convention (e.g., picking a logger, picking a date utility). Do not use it as a substitute for `architecture-style-selection` (style is one option of many decisions) or `extensibility-design` (variation modeling).

# Stage Fit

- **Discovery / intake** - frame the decision question, hard constraints, owner, affected boundaries, and existing ADR/project-memory context before implementation starts.
- **Design / architecture** - compare viable options using current repository graph, operational evidence, force weights, rejected alternatives, and reversibility class.
- **Implementation / review** - verify the chosen option maps to tests, fitness functions, rollout assumptions, and specialist handoffs before code commits to the decision.
- **Release / evolution** - record reassessment triggers, expiry conditions, monitoring evidence, and supersession rules so decisions do not silently rot.

# Non-Negotiable Rules

- Include **at least one rejected alternative** with the constraint that disqualified it. "No reasonable alternative" requires a documented mandatory constraint (regulatory, contractual, platform).
- State decision forces explicitly and **rank them by weight** — equal weighting is rarely true and hides the real driver.
- Identify risks → mitigations → residual risks → review owner. Risks without mitigations are unfinished work.
- Include **consequences** for delivery, testing, operations, security, privacy, compliance, cost, and future change. Each section is required; "none" is an answer that must be defended.
- Produce output that can be copied into, or condensed into, an ADR. Format matters less than content; consistency within the team matters.
- Classify **reversibility** (Type 1 irreversible / Type 2 reversible — Bezos) and apply scrutiny proportionally.
- Define a **reassessment trigger** — the concrete signal (metric, time, event) that requires re-deciding. "Periodically" is not a trigger.
- Name the **decision owner** (single accountable individual) and the **review owner** (separate person who challenged it).
- Record the decision **before** implementation begins. Retroactive ADRs are documentation, not decisions.
- Ground the decision in **current graph, memory, and execution evidence**. Prior ADRs, old benchmarks, generated summaries, or team memory are leads only until current source, validation, telemetry, or command evidence confirms them.

# Industry Benchmarks

Use benchmark names only to calibrate tradeoff evidence, reversibility, blast radius, operational cost, and rejected alternatives. Load [references/tradeoff-benchmarks.md](references/tradeoff-benchmarks.md) only for architecture review, ADR preparation, or L4/L5 changes.

# Selection Rules

Select this capability when the decision needs **evidence and future accountability**. Adjacent routing:

- Prefer `architecture-style-selection` when the main choice is the overall architecture style.
- Prefer `microservice-splitting` when the specific question is service boundary placement.
- Prefer `extensibility-design` when the question is variation/plugin design.
- Prefer `delivery-release-gate` when the remaining question is rollout mechanics.
- Prefer `version-compatibility` when the remaining question is rollout across clients.
- Prefer `change-impact-analyzer` when the work is impact assessment of a decided change.
- Use **with** `change-documentation-gate` to publish the ADR into the official record.

# Proactive Professional Triggers

Use this capability proactively, even when the request does not ask for a tradeoff analysis:

- **Signal:** a change introduces a durable dependency, vendor, framework, runtime, storage engine, broker, identity model, topology, or public contract. **Hidden risk:** a long-lived choice becomes default architecture without rejected alternatives or exit cost. **Required professional action:** require an ADR-ready decision with force weights, reversibility class, rejected options, and reassessment trigger. **Route to:** `architecture-tradeoff-analysis`, `technology-stack-selection`, `language-runtime-selection`, and `change-documentation-gate`. **Evidence required:** decision question, options matrix, current constraints, exit cost, and owner/reviewer.
- **Signal:** repository graph shows a boundary move across modules, services, tenants, regions, deploy units, data owners, or generated contracts. **Hidden risk:** the selected architecture can create hidden coupling, ownership gaps, or test/release blast radius. **Required professional action:** map affected graph edges and compare boundary alternatives before accepting the change. **Route to:** `repository-graph-analysis`, `module-boundary-design`, `architecture-impact-reviewer`, and this capability. **Evidence required:** caller/callee or dependency graph, affected tests, rejected boundary placements, and residual risk.
- **Signal:** project memory, old ADRs, benchmark posts, prior incidents, or generated summaries are used to justify a decision. **Hidden risk:** stale context can preserve a decision after constraints, scale, ownership, or vendor risk changed. **Required professional action:** compare memory against current source, telemetry, validation, and owner reality before reusing it. **Route to:** `project-memory-governance`, `execution-trajectory-analysis`, `validation-broker`, and this capability. **Evidence required:** source date, accepted/rejected assumptions, current validation evidence, and expiry condition.
- **Signal:** the winning option is defended with "best practice", "industry standard", "faster", "simpler", "future-proof", or senior preference. **Hidden risk:** authority or preference replaces weighted forces and hides the true decision driver. **Required professional action:** restate the decision question, rank forces before scoring, and reality-test the strongest objection to the winner. **Route to:** `solution-optimality-evaluation`, `architecture-style-selection`, and this capability. **Evidence required:** ranked forces, hostile-review objection, selected/rejected rationale, and not-chosen constraints.
- **Signal:** a decision has high residual risk, unclear rollback, time pressure, regulated scope, cost threshold, or multi-year maintenance obligation. **Hidden risk:** an effectively irreversible decision ships without owner, monitoring, or supersession path. **Required professional action:** escalate rigor, name accountable owners, define fitness functions, and require release/documentation handoff. **Route to:** `delivery-release-gate`, `reliability-observability-gate`, `security-privacy-gate`, and this capability. **Evidence required:** residual-risk owner, fitness function, rollback/exit plan, approval record, and next review trigger.

# Reference Loading Policy

- **L1:** Use only this `SKILL.md` for routing or rejecting a local reversible choice that does not need an ADR.
- **L2:** Load `references/checklist.md` when drafting or reviewing any real tradeoff analysis, ADR-ready decision, rejected-alternative record, or reassessment trigger.
- **L3:** Load `examples/example-output.md` when the expected output shape is unclear or a concise user-facing decision record is needed.
- **L4:** Load `references/tradeoff-benchmarks.md` for architecture review, ADR preparation, L4/L5 decisions, irreversible choices, force-weight calibration, or complex option matrices.
- **L5:** Pair with `repository-graph-analysis`, `project-memory-governance`, `execution-trajectory-analysis`, and `validation-broker` when the decision depends on current graph reachability, prior ADRs, command output, telemetry, tests, or validation freshness.

# Risk Escalation Rules

Escalate when a decision is **difficult to reverse** (data model, partition key, public contract, identity model, multi-region topology), changes public contracts, moves data ownership, introduces new infrastructure or vendor dependency, affects compliance scope, changes availability targets, creates a multi-year maintenance obligation, requires hiring/restructuring, or commits to spend above an organizational threshold. Specifically escalate when: the disqualifying constraint of the winning option is "we lack the skill", when the residual risk is rated high, when there is no plausible exit plan, or when the decision is being made under time pressure that prevents alternative analysis.

# Critical Details

Tradeoffs are not pros-and-cons pasted beside a preferred answer. The output must show **why the winning option is acceptable under the strongest constraints, and why each rejected option was not chosen**. Apply these refinements:

- **State the decision question precisely.** "Should we use X?" is rarely the right framing. "Given constraints A, B, C, which option best satisfies them with acceptable residual risk?" is.
- **Set force weights before scoring.** Otherwise scoring becomes rationalization.
- **Widen options before narrowing.** WRAP rule: if you have only 2 options, you do not have a decision, you have a dilemma. Aim for 3+ before eliminating.
- **Reality-test.** For each top option, identify the **strongest argument against it** from an outside perspective. Decisions that pass hostile review survive longer.
- **Distinguish reversible from irreversible.** Type-2 decisions can be made fast and recorded lightly. Type-1 decisions require Type-1 review: senior approval, prototype evidence, documented exit cost.
- **Quantify where possible.** Cost in $, latency in ms, throughput in RPS, migration in person-weeks. Adjectives ("expensive", "slow") hide disagreement.
- **Residual risk must remain visible.** Mitigations rarely eliminate risk; they reduce it. Record what remains and who owns watching it.
- **Define the reassessment trigger as a measurable signal** — e.g., "revisit when monthly cost > $50k", "revisit when team count > 8", "revisit when p95 > 400 ms", "revisit on 18-month anniversary". Without a trigger, decisions silently expire.
- **Capture the decision context's expiry.** What constraint, if it changed, would invalidate the decision? "If we acquire Company X this changes."
- **Avoid strawmen.** Each considered option must have been viable at the moment of consideration. Otherwise the rejected list is theater.
- **Avoid analysis paralysis.** Set a decision deadline. If the deadline approaches with no data, make the decision based on reversibility (favor Type-2) and document the gap.
- **Avoid HiPPO** (Highest Paid Person's Opinion). Senior input is welcome; senior overrule without engaging the matrix is decision-debt.
- **Record the decision body publicly.** Private ADRs do not constrain future drift.

### Anti-examples

| Anti-pattern | Why it fails | Fix |
| --- | --- | --- |
| "Pros and cons" list ending with the author's preferred answer | No force weighting; no rejected alternative discipline; rationalized | Use weighted matrix; preset weights |
| "We considered building it ourselves but chose vendor X" | No detail of build cost, vendor cost, or exit plan | Add cost ranges and exit cost |
| "Industry standard, so we picked it" | Authority-by-popularity; ignores context | Map standard to local constraints |
| "We will revisit periodically" | Never revisited; decision rots | Define numeric/event trigger |
| "Low risk" with no mitigation | Risk theater | List risk → mitigation → residual |
| ADR added 6 months after the fact | Decision was uncontested at the time; serves only documentation | Author ADR before merge |
| One option (the chosen one) listed | Not a decision | Require ≥ 1 rejected alternative |

# Failure Modes

- The document records only the chosen solution; rejected alternatives are absent or strawmen.
- Risks are generic ("could fail"); mitigations are missing or unowned; residual risk is invisible.
- The decision hides operational cost, support burden, or cost-at-scale.
- Force weights are added after scoring to justify the preferred answer.
- No reassessment signal is defined → outdated decisions persist past their context.
- Decision is recorded after implementation → ADR is documentation, not decision.
- Reviewer is the same person as the author → no challenge.
- Decision conflates several questions (style + vendor + topology + identity) → cannot be revisited atomically.
- Senior override bypasses the matrix → decision-debt that future teams cannot unwind.
- "Best practice" cited without local force mapping → cargo-culting.
- The decision is private to one team → other teams diverge and cannot align.

# Output Contract

Return an ADR-ready decision with:

- `id` (stable, sequential)
- `title` (action-oriented)
- `status` (proposed | accepted | superseded by ADR-N | deprecated)
- `date`, `decision_owner`, `reviewers`
- `context` (problem, constraints, what changed that requires a decision)
- `decision_question` (precise question being answered)
- `boundaries_inspected` (current source paths, graph edges, existing ADRs, owners, tests, configs, deployment/runtime surfaces, and skipped boundaries)
- `graph_memory_execution_validation` (repository graph, project memory, telemetry, command output, and validation evidence accepted or rejected with freshness limits)
- `forces` (ranked list with weights and probe data)
- `options_considered` (≥ 3 where credible; each with description and cost-class)
- `options_matrix` (weighted scoring table)
- `decision` (selected option)
- `rationale` (why this option satisfies the heaviest forces)
- `rejected_alternatives` (each with disqualifying constraint and conditions under which it would have won)
- `consequences` (delivery, testing, operations, security, privacy, cost, future flexibility)
- `risks` (list of `{risk, likelihood, impact, mitigation, residual_risk, owner}`)
- `reversibility_class` (Type 1 / Type 2 + exit cost estimate)
- `verification_plan` (how we will know the decision was right or wrong — fitness functions, metrics, review checkpoint)
- `decision_to_validation_map` (each force, risk, and consequence mapped to test, metric, prototype, rollout guard, or specialist gate)
- `reassessment_trigger` (concrete signal, not "periodically")
- `expiry_conditions` (what would invalidate this decision)
- `related_decisions` (links to ADRs that depend on or supersede this)
- `evidence_limits` (unverified assumptions, stale memory, missing metrics, not-inspected boundaries, and residual risk owner)

# Quality Gate

The analysis passes only when:

1. A reviewer who was not in the room can understand why the chosen option won under the named constraints.
2. ≥ 1 rejected alternative exists with a non-strawman disqualifying constraint.
3. Force weights were set before scoring and are documented.
4. Each risk has mitigation, residual risk, and a named owner.
5. Reversibility class is named and the rigor of analysis matches it.
6. Reassessment trigger is a measurable signal.
7. Consequences cover delivery, testing, operations, security, privacy, cost, future flexibility — even when "none".
8. The decision was recorded before implementation OR the ADR is explicitly marked "post-hoc" and a forward-looking ADR replaces it.
9. Repository graph, project memory, and execution evidence were inspected or explicitly marked unavailable with next proof step.
10. Decision-to-validation map links forces, risks, consequences, and reassessment trigger to tests, metrics, prototypes, rollout guards, or specialist gates.
11. Evidence limits state what the analysis proves, what it does not prove, and which boundaries remain unverified.
12. Required adjacent capabilities and skipped gates are recorded with rationale.

# Evidence Contract

The decision must cite `boundaries_inspected`, validation commands or artifacts, what evidence proves, what evidence does not prove, residual risk, and next handoff gate. Tradeoff evidence proves only the constraints, graph, metrics, and assumptions inspected at decision time; it does not prove future scale, downstream adoption, production reliability, or consumer compatibility unless those gates were selected and verified. Missing current graph, memory freshness, telemetry, or validation evidence blocks acceptance or downgrades the decision to proposed.

# Benchmark Coverage

Benchmark frameworks and ADR templates are calibration aids, not proof. Approval requires local decision forces, current repository graph, owner reality, reversible/irreversible classification, and a validation or fitness-function plan tied to the selected option.

# Routing Coverage

When selected by a router, report which adjacent capabilities were loaded or intentionally skipped: `architecture-style-selection`, `module-boundary-design`, `microservice-splitting`, `event-driven-architecture`, `data-model-design`, `solution-optimality-evaluation`, `repository-graph-analysis`, `project-memory-governance`, `execution-trajectory-analysis`, `validation-broker`, `change-documentation-gate`, `delivery-release-gate`, `security-privacy-gate`, and `reliability-observability-gate`.

# Used By

- architecture-impact-reviewer
- change-impact-analyzer

# Handoff

Hand off to `change-documentation-gate` when the decision must enter the official ADR record; the relevant architecture capability (`architecture-style-selection`, `module-boundary-design`, `microservice-splitting`, `event-driven-architecture`, `data-model-design`) when a specific unresolved boundary needs deeper design; `delivery-release-gate` when the decision implies rollout sequencing; `security-privacy-gate` when residual security/privacy risk requires specialist review; `reliability-observability-gate` when fitness functions / operational obligations need owning.

# Completion Criteria

The capability is complete when the decision has: a precisely framed question, ≥ 1 credible rejected alternative with disqualifying constraint, weighted forces set before scoring, risks with mitigations and residual ownership, consequences across all required dimensions, a reversibility classification matched by analysis depth, current graph/memory/execution evidence with limits, a decision-to-validation map, and a measurable reassessment trigger — and is recorded publicly in an ADR-ready form before implementation begins.
