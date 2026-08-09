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

Prove non-recurrence of a known failure mechanism at the narrowest boundary that preserves its trigger and observable result. Exclude wider portfolio and release verdicts.

## High-Value Rules

- Require causal-trigger reproduction rather than adjacent correct behavior as the recurrence guard.
- Establish counterfactual value: observe the guard fail for the matching reason on unfixed behavior when safe, or challenge the assertion with a targeted mutation or fault. If neither is admissible, state the proof limit and compensating evidence.
- Choose the narrowest admissible boundary that still contains the failure mechanism. A local test is insufficient when serialization, storage, browser, provider, concurrency, or deployment behavior caused the defect.
- Preserve the triggering fixture or a minimized equivalent whose removed fields are shown irrelevant. Own redaction, schema drift, setup, and cleanup across pass, failure, and cancellation paths.
- Map sibling paths, consumers, variants, and duplicate implementations for the same mechanism.
- Classify a match `current-task` only when it affects Acceptance or a required Invariant within scope, `scope-blocker` when required work is outside scope, or `adjacent` otherwise with rationale, residual risk, and no edit.
- Assert allowed and forbidden outcomes, including absence of unauthorized or duplicate side effects. For concurrency or eventual consistency, define admissible result sets and use bounded observation instead of fixed sleeps.
- Do not use broad retry to certify a flaky guard. Isolate nondeterminism with owned clock, randomness, scheduling, and data seams; quarantine or non-automation needs an owner, release consequence, and revisit trigger.

## Anti-Patterns

- Calling a new green-only happy-path test a regression guard without showing it constrains the prior failure.
- Following a fixed test pyramid when the original mechanism lives at a real boundary.
- Shrinking fixtures until the triggering condition disappears, or reusing stale incident/CI evidence after material edits.
- Claiming recurrence is closed before all authorized `current-task` occurrences are fixed, or repairing every discovered sibling regardless of task relation.

## Stop Conditions

- Escalate when safe reproduction is infeasible, the failure requires irreversible or shared-environment effects, or material same-pattern exposure remains without compensating detection and accepted ownership.

## Output Contract

- recurrence map with failure mechanism, guard boundary, counterfactual evidence, fixture fidelity, same-pattern coverage, freshness, and residual risk

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | Failure mechanism leaves guard boundary counterfactual fixture or same-pattern strategy unresolved | One narrow fresh guard preserves the mechanism and covers material recurrence paths | analysis-agent, task-agent, review-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | A known failure needs counterfactual fixture same-pattern concurrency eventual-consistency or flake decisions closed together | No accepted prior failure mechanism is being protected | analysis-agent, task-agent, review-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | Failure-mechanism counterfactual fixture same-pattern concurrency freshness or flake claims need proof | Fresh scoped evidence closes the known mechanism and material variants | analysis-agent, task-agent, review-agent | evidence-record, proof-limit, residual-risk |
