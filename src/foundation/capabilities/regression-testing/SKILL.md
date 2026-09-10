---
name: regression-testing
description: "`analysis-agent`/`task-agent`/`review-agent`: use for recurrence guards on known defects, incidents, or escaped failures; skip speculative risk without a prior failure mechanism."
---

# regression-testing

## Registry Trigger

**Use when**

- protect a named prior failure mechanism and materially reachable same-pattern variants from recurrence

**Do not use when**

- no accepted defect, incident, review finding, or equivalent recurrence mechanism exists

## Skill Role

Protect an accepted prior failure at the narrowest boundary that preserves its
causal trigger and observable result. Exclude speculative guards and release verdicts.

## High-Value Rules

- Preserve the causal trigger, fixture, observable failure, and real boundary.
- Prove counterfactual value or state its limit.
- Scan same-pattern paths, classify their task relation, and assert allowed plus forbidden effects with deterministic or bounded observation.
- Broad retry, stale evidence, or a green adjacent behavior is not recurrence proof.

## Anti-Patterns

- Local success substituted for evidence of the regression testing contract.

## Stop Conditions

- Stop when reproduction is unsafe, requires irreversible/shared effects, or leaves material same-pattern exposure without accepted detection and ownership.

## Output Contract

- recurrence map with failure mechanism, guard boundary, counterfactual evidence, fixture fidelity, same-pattern coverage, freshness, and residual risk

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | Failure mechanism leaves guard boundary counterfactual fixture or same-pattern strategy unresolved | One narrow fresh guard preserves the mechanism and covers material recurrence paths | analysis-agent, task-agent, review-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | A known failure needs counterfactual fixture same-pattern concurrency eventual-consistency or flake decisions closed together | No accepted prior failure mechanism is being protected | analysis-agent, task-agent, review-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | Failure-mechanism counterfactual fixture same-pattern concurrency freshness or flake claims need proof | Fresh scoped evidence closes the known mechanism and material variants | analysis-agent, task-agent, review-agent | evidence-record, proof-limit, residual-risk |
