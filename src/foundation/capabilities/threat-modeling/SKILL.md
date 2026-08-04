---
name: threat-modeling
description: "`analysis-agent`/`task-agent`/`review-agent`: use for changed assets, trust boundaries, reachable abuse paths, impact, or control placement; skip without a security delta."
---

# threat-modeling

## Registry Trigger

**Use when**

- model changed protected assets trust boundaries reachable abuse paths impacts controls and residual risk

**Do not use when**

- no task-local protected asset trust boundary abuse path or control-placement decision is required

## Skill Role

Define the security delta, attacker capability, reachable source-to-effect path, protected outcome, impact, blast radius, control placement, bypass analysis, validation mapping, and residual risk. Exclude identity derivation and credential lifecycle.

## High-Value Rules

- **Bound the changed security graph.** Name the protected asset or authority, changed entry point, trust transition, data or control flow, and downstream effect. Out-of-scope or unknown edges introduced or altered by the task remain explicit.
- **Model capability and preconditions, not actor labels alone.** Include only behaviors with graph-backed access, knowledge, timing, and control prerequisites.
- **Trace a reachable abuse path.** Follow source, attacker-controlled or stale values, transformations, policy or parser decisions, storage or transport, sink, and resulting effect; distinguish evidenced edges from assumptions and unreachable branches.
- **Define the protected outcome before severity.** State the confidentiality, integrity, availability, safety, financial, privacy, tenant, or authority invariant at risk. Current exposure and consequences determine likelihood, impact, and blast radius rather than a threat label.
- **Select and place controls from the path.** Compare candidate controls by protected outcome, intercepted edge, authority and owner, failure behavior, compatibility, and bypass surface. A mechanism remains undecided until the reachable path is known.
- **Map the threat to fresh verification and detection.** Connect the changed path and control to an abuse test, source/policy proof, monitoring, and final-edit freshness. The evidence limit remains explicit; scanner output alone cannot close business abuse.
- **Own residual risk and reopening.** Record the unclosed path or consequence, compensating or containment evidence, accountable owner, release consequence, and the scope, incident, exposure, data, actor, or control change that requires review.

## Anti-Patterns

- Substitute an asset catalog, framework taxonomy, regulation list, or generic attacker story for a task-local reachable path and protected outcome.
- Select a familiar validation, authentication, network, encryption, logging, or approval mechanism from the threat label while its placement, authority, failure mode, and bypass paths remain unproved.
- Close the model from a design note, scanner pass, happy-path test, or named mitigation while graph edges, alternate actors, deployed state, detection, or residual ownership remain unknown.

## Stop Conditions

Escalate when the changed graph or protected outcome is unclear, a high-impact path has unknown reachability, the chosen control cannot intercept the effect, or bypass behavior is unowned. Also escalate when validation cannot exercise the abuse path, monitoring cannot observe a material residual path, or the remaining consequence lacks accountable acceptance or release ownership.

## Output Contract

- changed threat model with protected outcomes, actor capabilities, reachable abuse paths, impact and blast radius, control placement and bypass analysis, fresh validation and detection evidence, proof limits, and residual-risk owners

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | competing abuse-path impact control-placement bypass validation detection or residual-risk patterns remain viable | current graph and protected outcome resolve the changed threat decision | analysis-agent, task-agent, review-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | several graph path impact control validation detection or residual-risk decisions must close together | one bounded changed threat path is already complete from the root contract | analysis-agent, task-agent, review-agent | checklist-result, validation-plan |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | graph-delta actor-capability reachability impact control bypass validation detection or residual-risk claims need fresh proof | current graph control evidence and selected validation prove the bounded threat claims | analysis-agent, task-agent, review-agent | evidence-record, proof-limit, residual-risk |
