---
name: plan-execution-consistency
description: "`analysis-agent`/`task-agent`/`review-agent`: use when diff, behavior, validation, review, or re-review may drift from an accepted plan; skip without a closure consistency need."
---

# plan-execution-consistency

## Registry Trigger

**Use when**

- plan execution consistency planned files actual changed files extra file stale validation unplanned behavior review scope repair re-review final handoff
- plan drift actual diff differs validation before final edit partial validation reported as full extra generated file missing planned file

**Do not use when**

- no task-local plan execution consistency decision is required

## Skill Role

Reconcile the visible plan with actual changed files, behavior, commands, validation, review coverage, and unresolved discrepancies.

## High-Value Rules

- Audit actual changes and evidence against the accepted plan or capsule.
- Record and explain any unplanned path, omitted path, or changed assumption that affects acceptance or evidence.
- Require fresh validation of affected behavior after the final material edit.
- Require explicit validation coverage for every changed file in scope.
- After repair, reconcile the latest diff and fresh affected validation. Re-review only for a new material question needing independent judgment or an unresolved required review.

## Anti-Patterns

- An extra generated file can indicate editing the wrong source.
- A review of the prior diff does not prove the repair. Use fresh evidence for the changed behavior without assuming another review is required.
- Planned scope does not excuse an actual change missing type-appropriate inspection, validation, or required independent judgment.

## Stop Conditions

- Block closure when changed paths are unexplained, evidence for affected behavior predates its final material edit, a changed path lacks type-appropriate inspection or validation, or required independent judgment remains unresolved.
- Escalate intentional behavior or scope changes not covered by acceptance.

## Output Contract

- Return a plan-to-actual diff: state changed-file variance, behavior mapping, post-edit validation, review coverage, unverified scope, and residual risk

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [consistency](references/consistency-checklist.md) | decision-checklist | the actual diff or validation may diverge from the approved plan and acceptance | there is no execution plan or no repository change to reconcile | analysis-agent, task-agent, review-agent | checklist-result, validation-plan |
