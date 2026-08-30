---
name: ai-code-review-refactor
description: "Use `review-agent` on implementation or repair diffs for hallucinated APIs, unsupported assumptions, unsafe abstractions, and dependency or regression risks. Skip work without a diff or after reviewer edits."
---

# ai-code-review-refactor

## Role

Support `review-agent` in independently reviewing the actual implementation or
repair diff. Review is non-mutating and does not change its assigned scope.

## When To Use

- implementation diff ready
- repair diff ready for re-review

## Do Not Use

- no actual diff
- reviewer implemented changed scope

## Required Inputs

- fixed Goal/Acceptance/Non-goals, boundary, invariants, actual diff and changed paths, and fresh evidence

## Professional Decision Rules

- Inspect the actual diff within fixed acceptance and boundary.
- When a finding is proposed, reject it unless current source evidence establishes a reachable failure path.
- Classify adjacent risk separately.
- Record reviewed/unreviewed scope, severity, repair boundary, freshness, proof limits, and residual risk.
- Preserve the non-mutating assigned review boundary.

## High-Value Gotchas

- Pattern similarity without a reachable mechanism is calibration evidence, not a finding.
- A no-finding verdict is bounded by the files, behaviors, consumers, and validation actually reviewed.
- Re-review closes against the latest repair diff and fresh evidence, not the superseded implementation.

## Execution Checklist

- **Review mode:** Bind the actual diff to fixed acceptance, boundary, invariants, changed paths, and current evidence.
- Inspect changed and reachable source, tests, contracts, and validation.
- Reject a candidate without a concrete failure mechanism.
- Record findings or non-findings, reviewed and unreviewed scope, severity, repair boundary, freshness, proof limits, and residual risk.

## Stop / Escalation Conditions

- Block on inaccessible diff, stale evidence, or unbounded scope; record out-of-boundary risk as unreviewed without expanding authority.

## Output Contract

- reviewed/unreviewed scope, evidence-backed findings or non-findings, relation/severity, repair boundary, freshness, proof limits, and residual risk

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [ai review pattern catalog](references/ai-review-pattern-catalog.md) | benchmark-pattern | Findings need pattern-calibrated examples for recurring AI failure modes | The issue is already concrete and no calibration examples are needed | review-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | A bounded review needs a compact checklist before approval | Pattern examples or exhaustive gates are required | review-agent | checklist-result, residual-risk |
| [index](references/index.md) | index | competing ai code review refactor references require dependency, conflict, or output-fragment selection | the ai code review refactor root or a task-named reference already resolves selection | review-agent | reference-selection |
| [review output and gates](references/review-output-and-gates.md) | targeted | L5 review needs exhaustive schema, quality gates, handoff routing, or repair/re-review semantics | A compact severity finding list is sufficient | review-agent | gate-decision, residual-risk |
| [solution optimality](references/solution-optimality.md) | targeted | An AI-generated diff introduces a material algorithm, data-structure, concurrency, cache, abstraction, or measurable resource-use choice | The issue is already a concrete finding or no material implementation choice changed | review-agent | selected-approach, residual-risk |
