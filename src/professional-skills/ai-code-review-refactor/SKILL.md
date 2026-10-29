---
name: ai-code-review-refactor
description: "Use `review-agent` for diff-review or a bounded snapshot-audit. Find reachable defects and unsupported assumptions. Skip module explanation, unbounded scope, and code implemented by the reviewer."
---

# ai-code-review-refactor

## Role

Support `review-agent` in independently reviewing a current diff or bounded code snapshot. Remain read-only and preserve the assigned scope.

## When To Use

- implementation diff ready
- repair diff ready for re-review
- snapshot-audit with a fixed commit or snapshot, paths, questions, and depth

## Do Not Use

- no bounded diff or code snapshot
- module explanation without an audit question
- reviewer implemented changed scope

## Required Inputs

- Mode, fixed commit or snapshot identity, paths, questions, depth, and available validation.
- Diff and changed paths for diff-review; inspected module scope for snapshot-audit.

## Professional Decision Rules

- Inspect the selected diff or snapshot within fixed acceptance and boundary.
- When a finding is proposed, reject it unless current source evidence establishes a reachable failure path.
- Classify adjacent risk separately.
- Record reviewed/unreviewed scope, severity, repair boundary, freshness, proof limits, and residual risk.
- Preserve the non-mutating assigned review boundary.

## High-Value Gotchas

- Pattern similarity without a reachable mechanism is calibration evidence, not a finding.
- A no-finding verdict is bounded by the files, behaviors, consumers, and validation actually reviewed.
- Re-review closes against the latest repair diff and fresh evidence, not the superseded implementation.

## Execution Checklist

- Bind the selected mode to its commit, scope, questions, and current evidence.
- Inspect scoped source, reachable consumers, tests, contracts, and validation.
- Reject a candidate without a concrete failure mechanism.
- Record findings or non-findings, reviewed and unreviewed scope, severity, repair boundary, freshness, proof limits, and residual risk.

## Stop / Escalation Conditions

- Report inaccessible source, stale evidence, or unbounded scope before issuing a verdict.
- Leave uninspected paths explicit; send repairs to the implementation owner.

## Output Contract

- reviewed/unreviewed scope, evidence-backed findings or non-findings, relation/severity, repair boundary, freshness, proof limits, and residual risk

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [ai review pattern catalog](references/ai-review-pattern-catalog.md) | benchmark-pattern | Findings need pattern-calibrated examples for recurring AI failure modes | The issue is already concrete and no calibration examples are needed | review-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | A bounded review needs a compact checklist before approval | Pattern examples or exhaustive gates are required | review-agent | checklist-result, residual-risk |
| [index](references/index.md) | index | competing ai code review refactor references require dependency, conflict, or output-fragment selection | the ai code review refactor root or a task-named reference already resolves selection | review-agent | reference-selection |
| [review output and gates](references/review-output-and-gates.md) | targeted | review needs exhaustive schema, quality gates, handoff routing, or repair/re-review semantics | A compact severity finding list is sufficient | review-agent | gate-decision, residual-risk |
| [solution optimality](references/solution-optimality.md) | targeted | An AI-generated diff introduces a material algorithm, data-structure, concurrency, cache, abstraction, or measurable resource-use choice | The issue is already a concrete finding or no material implementation choice changed | review-agent | selected-approach, residual-risk |
| [snapshot audit](references/snapshot-audit.md) | targeted | Review examines bounded current code without requiring a diff | The request is a diff review or module explanation | review-agent | decision-record, proof-limit, residual-risk |
