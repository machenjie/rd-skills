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

- Define the changed protected outcome.
- Trace its capability-backed reachable source-to-effect path.
- Select and place an owned control at an intercepting edge.
- Select the named decision or evidence Reference for impact, bypass, validation, detection, and residual-risk detail.
- When the selected threat-model decision remains active, load only its named Reference.

## Anti-Patterns

- Do not substitute a catalog, threat label, scanner pass, or named mitigation for a reachable task-local path, control placement, bypass analysis, and residual owner.

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
