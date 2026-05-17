---
name: technology-stack-selection
description: Use when selecting or reviewing a technology stack, framework family, runtime platform, major infrastructure component, or product technical baseline against constraints, maintainability, cost, security, maturity, performance, and reversibility.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "83"
changeforge_version: 0.1.0
---

# Mission

Select or review technology stack, framework family, runtime platform, major infrastructure component, or product-level technical baseline against explicit constraints: product requirements, team maturity, hiring market, operational cost, ecosystem maturity, security posture, performance budget, support horizon, and reversibility. Reject "fashion-driven" or "resume-driven" technology decisions; require evidence that the choice is the simplest sufficient option whose total cost of ownership over the product's expected lifetime is the lowest viable.

# When To Use

Use when a change proposes a new stack, replaces a major framework, chooses a platform baseline, creates a new service foundation, evaluates whether a managed service should replace a self-managed component, or asks which technology family best fits a product and delivery context. Use when the decision will be expensive to reverse (≥ 1 engineer-quarter to switch, or ≥ 1 customer-visible migration window).

# Do Not Use When

Do not use for syntax lessons, framework setup walkthroughs, abstract trend comparison without project constraints, or technology choices already mandated by a binding architecture decision (ADR) that has not been reopened. Do not use for like-for-like upgrades within the same stack family (use `package-dependency-management` instead).

# Non-Negotiable Rules

- **Boring technology bias is the default.** New stack additions in an existing system require proof that no existing approved stack can serve the requirement at acceptable cost. Fashion, novelty, and resume value are not justifications.
- **Reversibility class must be stated.** Reversible (config/feature flag), Conditionally reversible (data migration possible within months), Irreversible (cross-system rewrite > 1 engineer-year). Irreversible decisions require ADR + named accountable owner + sunset plan.
- **TCO horizon of 3-5 years is the planning window.** Hiring market for the skill, vendor support roadmap, expected breaking-change cadence, observability tooling, and operational on-call burden must be projected over this horizon, not just the first launch.
- **Operational ownership must be named before the decision is locked.** "We'll figure out who runs it later" is a rejection signal. The team that will get the 2 AM page must accept the technology before the choice is approved.
- **Maturity floor**: prefer technology with ≥ 3 years stable production track record at organizations of comparable scale, ≥ 2 active maintainers (or vendor SLA), security CVE disclosure process, and observable upgrade cadence. Single-maintainer / pre-1.0 / abandoned-issue-tracker technology is a supply-chain risk.
- **Exit cost must be estimated before entry.** State migration cost in engineer-quarters if the choice fails. If exit cost is unknown, the decision is not ready.
- **Local development experience does not extrapolate to production scale.** Prototype success at 10 RPS and 10 GB is not evidence at 1,000 RPS and 1 TB. Production-shape evidence (load, data volume, failure modes, deployment topology) is required for production-critical choices.

# Industry Benchmarks

- **ThoughtWorks Technology Radar** — Adopt / Trial / Assess / Hold maturity classification. New stack additions should be in Adopt or Trial for the relevant problem domain.
- **DORA "Accelerate"** — loosely coupled architecture and trunk-based development as system properties of elite performers. Stack choice must not regress deployment frequency, lead time, change-failure rate, or MTTR.
- **Google SRE Workbook — Production Readiness Review (PRR)** — observability, scalability, dependability, capacity planning, and emergency response must be answered before launch.
- **NIST SSDF (SP 800-218)** and **OWASP SAMM** — secure development lifecycle posture of the candidate technology and its supply chain.
- **SLSA framework** — supply chain integrity level required for production dependencies.
- **OpenSSF Scorecard** — measurable open-source project health (maintenance, code-review, branch-protection, dangerous-workflow, vulnerabilities). Scorecard < 5/10 is a yellow flag; < 3/10 is a red flag.
- **Fowler — "ChoosingTechnology"** and the principle of "boring technology" (Dan McKinley): you have a finite budget of innovation tokens; spend them where they create competitive advantage, not on commodity infrastructure.
- **Architecture Decision Records (ADR)** — every non-trivial stack decision is recorded with context, options considered, decision, consequences (Michael Nygard format or MADR).

# Selection Rules

Select this capability when the request involves: choosing or replacing a primary framework (web, RPC, ORM, UI), datastore family (relational vs. document vs. KV vs. wide-column vs. time-series vs. graph), messaging/streaming platform, container orchestrator, observability stack, cloud provider or managed-vs-self-managed boundary, or a new "category" of infrastructure not yet present. Pair with `language-runtime-selection` when language choice is also open; `architecture-style-selection` when the choice forces a topology change; `package-dependency-management` for in-stack dependency choices.

### Decision Rubric (apply in order, stop at first decisive rejection)

```
1. Constraint fit — Does the candidate satisfy hard product/regulatory constraints?
   (latency SLO, data residency, compliance, deployment target, offline support)
   No → reject with named constraint.

2. Existing-stack sufficiency — Can an approved in-house technology meet the
   requirement at ≤ 1.5× the cost of the candidate?
   Yes → use existing. The cost of one additional technology in production is
   typically 1-2 engineer-FTE-years over its lifetime (on-call, upgrades,
   tooling, knowledge transfer).

3. Maturity floor — ≥ 3 years stable in production at comparable scale;
   ≥ 2 active maintainers or vendor SLA; CVE disclosure process; observable
   release cadence; OpenSSF Scorecard ≥ 5/10 (for OSS).
   No → reject or escalate.

4. Operational ownership — Named team accepts on-call. Hiring market viable
   (≥ 100 candidates in addressable market, or in-house upskilling plan).
   No → reject.

5. Reversibility — Reversibility class stated. If Irreversible, ADR + sunset
   plan + named owner + 2× cost-of-entry budgeted for exit risk.

6. Comparative scoring — Score top 2-3 candidates across: constraint fit,
   TCO, hiring market, ecosystem maturity, security posture, observability,
   deployment shape, exit cost. Use weighted matrix with explicit weights
   derived from product priorities, not equal weights.

7. Tradeoff analysis — Hand off to architecture-tradeoff-analysis for ADR
   when material tradeoffs remain after scoring.
```

# Risk Escalation Rules

- Escalate to `architecture-impact-reviewer` when the choice changes service boundaries, deployment topology, or dependency direction.
- Escalate to `architecture-tradeoff-analysis` when ≥ 2 candidates remain after the rubric and require formal ADR with named tradeoffs.
- Escalate to `delivery-release-gate` when rollout requires migration or coexistence of old + new stacks.
- Escalate to `security-privacy-gate` for supply-chain risk (OpenSSF Scorecard < 5, single-maintainer, install-script side effects, license incompatibility), data classification changes, or trust-boundary changes.
- Escalate to `language-runtime-selection` when the stack forces a language change.
- Escalate to `solution-optimality-evaluation` when measured performance, cost, or reliability claims have not been validated under production-shape load.

# Critical Details

- **The cost of one additional production technology** typically runs 1-2 engineer-FTE-years over its operational lifetime when fully loaded (on-call rotation, security patching, version upgrades, observability tooling, internal docs, knowledge transfer when staff turns over, integration testing across the rest of the stack). Decisions that ignore this hidden tax under-count the true cost of stack additions by 3-5×.
- **Prototype success ≠ production readiness.** A prototype validates feasibility at a specific scale. A production decision requires evidence at production scale or a credible plan to validate before commitment. Common failure: choosing a datastore based on 1 GB / 100 RPS prototype that fails at 1 TB / 10k RPS for reasons (write amplification, hot partitions, GC pressure, replication lag) not visible at prototype scale.
- **Vendor lock-in vs. abstraction cost tradeoff.** Wrapping every vendor API in an abstraction layer "to enable switching" usually costs more than the switch would ever cost — and the abstraction calcifies around the first vendor's mental model. Better discipline: use vendor primitives directly, but isolate the surface area (a single module/package owns vendor calls) so the eventual rewrite is localized.
- **Managed-vs-self-managed is an operational decision, not a cost decision.** Managed services trade money for engineer time. Calculate: hours/week × loaded engineer cost vs. managed-service monthly bill. At < $500/mo of managed cost, almost always cheaper to use managed. At > $50k/mo, self-managed may be defensible if the team has expertise. The crossover is product-specific and must be calculated, not assumed.
- **Hiring market signal**: search the candidate technology in job-market data (LinkedIn / StackOverflow Developer Survey / Hired.com). If qualified candidates in your geography are < 100, the technology is a hiring liability regardless of technical merit.
- **Innovation tokens are finite.** Use them where the technology choice creates competitive product advantage (the differentiated 20%), not where commodity infrastructure suffices (the boring 80%). A product whose innovation tokens are spent on its own database engine has none left for its core differentiator.

# Failure Modes

- **Fashion-driven adoption** — Symptom: technology chosen primarily because senior engineers want it on their resume. Cause: no decision rubric applied, no operational owner committed before the decision. Impact: 6 months later, the original advocate has left and no one remains to operate it.
- **Existing-stack sufficiency check skipped** — Symptom: a second framework/datastore added when an approved one would have served at +30-50% cost. Cause: rubric step 2 bypassed. Impact: doubled operational tax (two upgrade paths, two on-call playbooks, two observability stacks) for negligible engineering benefit.
- **Maturity floor ignored** — Symptom: pre-1.0 / single-maintainer dependency adopted because "the API is clean." Cause: OpenSSF Scorecard not checked; maintainer count not verified; CVE process not validated. Impact: maintainer disappears, unpatched CVE, forced emergency replacement under incident pressure.
- **Reversibility unstated** — Symptom: irreversible choice (e.g., proprietary cloud-only datastore with no export) accepted without exit plan. Cause: reversibility class not declared; ADR not written. Impact: vendor pricing changes / acquisition / EOL becomes existential risk to product.
- **Operational ownership deferred** — Symptom: "platform team will run it" without platform team agreement. Cause: ownership treated as a downstream problem. Impact: ownership void at first production incident.
- **Local-dev experience extrapolated to production** — Symptom: ORM/framework chosen based on local benchmark; collapses under real concurrency. Cause: no production-shape validation. Impact: post-launch rewrite under pressure.
- **Vendor abstraction over-engineering** — Symptom: 6 months building a "cloud-agnostic" wrapper for primitives used in exactly one cloud. Cause: speculative reversibility without evidence of need. Impact: real abstraction cost exceeds hypothetical switch cost.
- **Managed-vs-self misjudged** — Symptom: self-managed Kafka/Postgres/Elasticsearch consuming 1 FTE; managed cost would have been $15k/mo. Cause: TCO not calculated with loaded engineer cost. Impact: opportunity cost on product work.

# Output Contract

Return a **Stack Decision Record** (ADR-formatted) containing:
- **Context** — product constraints, requirement summary, decision driver
- **Options considered** — minimum 2, ideally 3 candidates with key attributes
- **Constraint fit per candidate** — table mapping each hard constraint (latency, residency, compliance, etc.) to satisfied / not-satisfied / requires-mitigation
- **Decision rubric trace** — explicit answer for each of the 7 rubric steps
- **Selected option** — with weighted matrix scoring (weights and rationale stated)
- **Rejected alternatives** — each with the specific cost or constraint that disqualified it (not "it's worse")
- **Reversibility class** — Reversible / Conditionally reversible / Irreversible, with exit cost estimate in engineer-quarters
- **Operational model** — named owning team, on-call coverage, upgrade cadence, observability tooling
- **Security posture** — OpenSSF Scorecard (if OSS), CVE process, threat model delta, supply-chain risk
- **Ecosystem maturity** — production track record (years × organization scale), maintainer count, hiring market size
- **TCO projection** — 3-year cost (license/managed cost + engineer-FTE-equivalent operational tax)
- **Migration path** — rollout sequence, coexistence plan, validation criteria, rollback trigger
- **Open risks** — explicitly accepted unknowns with named owners and re-evaluation date

# Quality Gate

1. **Rubric trace** — every one of the 7 rubric steps has an explicit, evidence-backed answer.
2. **Minimum 2 alternatives** scored with a weighted matrix; weights derived from product priorities.
3. **At least one alternative rejected** with a concrete, specific cost (not "it's worse" or "we prefer X").
4. **Operational ownership** named and accepted in writing.
5. **Reversibility class stated**; if Irreversible, ADR + sunset plan + 2× cost-of-entry exit budget present.
6. **Maturity floor passed**: ≥ 3 years production at comparable scale, ≥ 2 maintainers or vendor SLA, OpenSSF Scorecard ≥ 5 (for OSS).
7. **TCO** projected over 3 years with loaded engineer cost; managed-vs-self-managed calculation included where applicable.
8. **Production-shape evidence** for performance and reliability claims, not prototype-shape.

# Used By

architecture-impact-reviewer, delivery-release-gate, ai-code-review-refactor, change-impact-analyzer, change-forge-router

# Handoff

- **architecture-impact-reviewer** — for unresolved architectural consequences (boundary changes, deployment topology, dependency direction).
- **architecture-tradeoff-analysis** — when material tradeoffs remain after scoring and a formal ADR is required.
- **delivery-release-gate** — for rollout sequencing, coexistence, rollback triggers.
- **package-dependency-management** — for in-stack dependency risk (lockfile, transitive risk, license).
- **language-runtime-selection** — when the stack choice forces a language change.
- **security-privacy-gate** — for supply-chain risk, data-classification changes, trust-boundary changes.

# Completion Criteria

The decision is complete when: the rubric trace is filled in with evidence; weighted scoring is documented; at least one alternative is rejected with a specific cost; operational ownership is named and accepted; reversibility class is stated with exit cost estimate; maturity floor is verified; TCO is projected over 3 years; and any open risks have named owners and re-evaluation dates. A decision without rubric trace or weighted scoring is not approved — it is deferred.
