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

- Test the brief as four connected dimensions: problem and acceptance; ownership and invariants; placement, contract, and failure design; acceptance-to-validation mapping.
- Require decisions only when they change downstream work, risk, rollback, or user-visible behavior.
- Confirm the First Executable Slice remains safe, verifiable, and reversible.
- Reject dependency cycles, conflicting writes, unowned shared contracts, and rollback claims without an executable path.

## High-Value Gotchas

- More artifacts do not improve accuracy when they repeat the same facts.
- A complete-looking brief can still name the wrong owner or omit version skew and failure behavior.
- Review breadth must remain proportional to the concrete risk.

## Execution Checklist

1. Verify source evidence and acceptance.
2. Check owner, invariants, reuse, and rejected placements.
3. Check public contract, data, failure, compatibility, and rollback effects.
4. Check dependencies, workspace requirements, integration, review, and validation boundaries.

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
