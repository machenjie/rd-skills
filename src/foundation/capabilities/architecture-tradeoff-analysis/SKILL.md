---
name: architecture-tradeoff-analysis
description: Produces ADR-ready architecture decisions with alternatives, rejected options, risks, mitigations, and consequences.
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

# Industry Benchmarks

Anchor against: **ADRs (Michael Nygard, 2011)** and the MADR template (markdown ADR), **Lightweight RFCs** (Oxide Computer / Squarespace / Rust RFC process), **C4 model** for context/container diagrams supporting the decision, **DACI / RAPID** decision-rights frameworks, **Risk registers** (ISO 31000), **NASA Technical Risk Management Handbook**, **Cynefin framework** (Snowden) for matching decision approach to problem domain (simple/complicated/complex/chaotic), **Wardley Mapping** for evolution-aware tradeoffs, **Cost of Delay** (Reinertsen) for time-value weighting, **Bezos Type-1/Type-2** reversibility classification, **Architecture Fitness Functions** (Ford/Parsons/Kua), **Decision Records** practice (adr.github.io), **WRAP framework** (Heath/Heath: Widen options, Reality-test, Attain distance, Prepare to be wrong), **Eisenhower / RICE** prioritization where alternatives must be ranked, **DORA** outcomes as quality lens. For irreversible technology choices, apply **Lindy effect** reasoning to bet on technologies with proven longevity.

### Decision-Force Catalog

Use this canonical list, then rank by weight (1 = decisive, 5 = nice to have). Omit forces that do not apply, but state so.

| Force | Probe question |
| --- | --- |
| Delivery speed (time-to-market) | How many weeks/months does each option add or save? |
| Cognitive load | Can the existing team operate this without specialist hiring? |
| Operational cost | What does this cost at projected 12-month scale (infra + people)? |
| Reliability / availability | What SLO does each option support, with what investment? |
| Performance (latency, throughput) | Does each option meet the p95/p99 budget under projected load? |
| Security posture | Does each option reduce or expand attack surface and trust boundaries? |
| Privacy / compliance | Does each option simplify or complicate PCI/HIPAA/GDPR scope and residency? |
| Reversibility | How costly is exit? Days, weeks, years? |
| Vendor lock-in | Is the data/format/contract portable? |
| Talent availability | Can we hire for this in our market in 6 months? |
| Ecosystem health | Library age, maintainer count, release cadence, CVE backlog |
| Coupling impact | Does this widen or narrow the blast radius? |
| Migration cost | What does it cost to get from current state to target state? |
| Testability | Can each option be tested without production-only fidelity? |
| Observability | Are metrics, logs, traces, debugging tools mature? |
| Future flexibility | Does this preserve or close downstream options? |

### Options Matrix Template

| Force (weight) | Option A | Option B | Option C |
| --- | --- | --- | --- |
| Delivery speed (4) | 6 weeks | 12 weeks | 4 weeks |
| Operational cost (5) | $X/mo | $Y/mo | $Z/mo |
| Reversibility (3) | Type 2 | Type 1 | Type 2 |
| Compliance (5) | In scope simplification | Neutral | Adds scope |
| ... | ... | ... | ... |
| **Weighted score** | | | |
| **Disqualifying constraint** | — | residual auth risk | cost > budget |

Weighting must be set **before** scoring, not adjusted to make a preferred option win.

### Decision Tree: Decision Approach by Cynefin Domain

```
What is the nature of the problem?
├─ Simple (best practice exists)        → Apply best practice; lightweight ADR; reviewer = peer.
├─ Complicated (analyzable, experts)    → Full tradeoff analysis; multiple alternatives; reviewer = senior architect.
├─ Complex (emergent, requires probing) → Run experiments (spikes, prototypes) before committing; reversible design;
│                                          design fitness functions; review after first production data.
└─ Chaotic (incident, no time to model) → Act → sense → respond; record post-hoc; revisit when stable.
```

# Selection Rules

Select this capability when the decision needs **evidence and future accountability**. Adjacent routing:

- Prefer `architecture-style-selection` when the main choice is the overall architecture style.
- Prefer `microservice-splitting` when the specific question is service boundary placement.
- Prefer `extensibility-design` when the question is variation/plugin design.
- Prefer `delivery-release-gate` when the remaining question is rollout mechanics.
- Prefer `version-compatibility` when the remaining question is rollout across clients.
- Prefer `change-impact-analyzer` when the work is impact assessment of a decided change.
- Use **with** `change-documentation-gate` to publish the ADR into the official record.

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
- `reassessment_trigger` (concrete signal, not "periodically")
- `expiry_conditions` (what would invalidate this decision)
- `related_decisions` (links to ADRs that depend on or supersede this)

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

# Used By

- architecture-impact-reviewer
- change-impact-analyzer

# Handoff

Hand off to `change-documentation-gate` when the decision must enter the official ADR record; the relevant architecture capability (`architecture-style-selection`, `module-boundary-design`, `microservice-splitting`, `event-driven-architecture`, `data-model-design`) when a specific unresolved boundary needs deeper design; `delivery-release-gate` when the decision implies rollout sequencing; `security-privacy-gate` when residual security/privacy risk requires specialist review; `reliability-observability-gate` when fitness functions / operational obligations need owning.

# Completion Criteria

The capability is complete when the decision has: a precisely framed question, ≥ 1 credible rejected alternative with disqualifying constraint, weighted forces set before scoring, risks with mitigations and residual ownership, consequences across all required dimensions, a reversibility classification matched by analysis depth, and a measurable reassessment trigger — and is recorded publicly in an ADR-ready form before implementation begins.
