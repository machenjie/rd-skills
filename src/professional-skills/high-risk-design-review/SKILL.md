---
name: high-risk-design-review
description: "Use `review-agent` for a high-risk Engineering Brief when a critical path, architecture boundary, material risk, or multiple downstream tasks need deeper design evidence. Skip ordinary work without those signals."
---

# High-Risk Design Review

## Role

Support `review-agent` in assessing a high-risk Engineering Brief whose
decisions affect multiple downstream tasks. Reject phase-pipeline expansion.

## When To Use

- critical path requires deeper design evidence
- major architecture boundary

## Do Not Use

- ordinary fast path
- ordinary standard path
- As a planner, implementer, or mandatory ceremony for every change.

## Required Inputs

- Source-backed Engineering Brief and observable acceptance.
- Ownership, invariants, placement, contract/data/failure impact, validation, rollback, and First Executable Slice.

## Professional Decision Rules

- Keep the selected high risk design review decision within its declared owner, inputs, stops, and output contract.
- Test the brief as connected problem/acceptance, owner/invariant, placement/contract/failure, and acceptance-to-validation decisions using current source evidence.
- Compare a plausible alternative at each critical boundary and require a decision only when it changes downstream work, material risk, recovery, or user-visible behavior.
- Reject dependency cycles, conflicting writes, unowned shared contracts, and rollback claims without an executable rollback or forward-repair path; keep the First Executable Slice safe, verifiable, and reversible.

## High-Value Gotchas

- When ownership is ambiguous, an invariant or failure path may be split across decision makers.
- Reversibility on paper does not prove an executable rollback or forward-repair path.
- Multiple downstream tasks can preserve local acceptance while breaking the shared boundary.

## Execution Checklist

- **Review mode:** Map every material decision to one owner, invariant, failure path, and proof.
- Compare the selected design with at least one plausible alternative at the critical boundary.
- Verify rollback or forward repair for each irreversible or cross-task consequence.
- Record unreviewed decisions and evidence gaps as blocking findings or residual risk.
- Minimal validation: inspect the brief's named proofs and its recovery path.

## Stop / Escalation Conditions

- Stop when source evidence, acceptance, owner, rollback, or a user-owned decision is missing.
- Escalate destructive, production, privileged, irreversible, security, privacy, or financial choices.

## Output Contract

- verdict and blocking design findings
- affected decisions and downstream impact
- First Executable Slice assessment
- validation, rollback, and residual-risk gaps

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [design review](references/design-review-checklist.md) | decision-checklist | critical-path design changes need boundary, alternative, and reversibility review | no material architecture boundary or high-risk design decision changed | review-agent | checklist-result, residual-risk |
