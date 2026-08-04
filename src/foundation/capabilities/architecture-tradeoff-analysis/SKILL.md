---
name: architecture-tradeoff-analysis
description: "`analysis-agent`: use when architecture options, constraints, material consequences, and exit costs need an evidence-backed comparison; skip when no task-local tradeoff exists."
---

# architecture-tradeoff-analysis

## Registry Trigger

**Use when**

- compare architecture options constraints forces risks and long term cost

**Do not use when**

- no task-local architecture tradeoff analysis decision is required

## Skill Role

Compare feasible architecture options against hard constraints, material consequences, reversibility, exit cost, decisive evidence, and assumption-change triggers. Do not design or implement the selected architecture.

## High-Value Rules

- **Bound the decision before comparing options.** Name the decision owner, affected boundary, in-scope outcome, excluded decisions, and sourced contractual, policy, ownership, compatibility, safety, capacity, or delivery constraints.
- **Exclude infeasible and unresolved options from preference comparison.** Screen candidates against hard constraints, classifying evidence-backed failures as disqualified and unresolved feasibility as pending.
- **Separate disqualifiers from preferences.** A hard constraint determines feasibility; a preference differentiates feasible choices. Do not let weighting, popularity, familiarity, or sunk cost average away a disqualifier.
- **Record only material consequences.** Include only consequences that can change selection, ownership, public behavior, boundaries, operations, cost, delivery, validation, or future change.
- **Make reversibility and exit concrete.** Identify what must be migrated, restored, unwound, or retained; name data/contract portability, authority, dependency, validation, and residual obligations on exit.
- **Make decisive evidence falsifiable.** Map claims that determine feasibility or selection to current source, contract, policy, prototype, measurement, or owner evidence plus a check capable of rejecting the claim; otherwise state the proof limit.
- **Review when an assumption changes.** Name the constraint, workload, ownership, vendor, regulatory, cost, incident, or capability signal that reopens the choice, its owned source, and the decision consequence.

## Anti-Patterns

- Score an infeasible option beside feasible choices or use a preferred criterion to hide a failed hard constraint.
- Produce a broad pros-and-cons inventory, pre-filled consequence sections, or numeric precision that does not change the choice or lacks comparable evidence.
- Treat the selected option as permanent while exit obligations, decisive assumptions, and owned review signals remain unstated.

## Stop Conditions

Escalate when the decision boundary or owner is unclear, candidate feasibility is unproved, a hard constraint lacks authority, or decisive evidence is inaccessible. Also escalate when exit would strand data, contracts, or ownership, or the choice changes a public contract, trust boundary, compliance scope, availability objective, vendor dependency, or irreversible operating commitment.

## Output Contract

- architecture decision comparison with bounded scope, hard constraints, feasible options, material consequences, reversibility and exit path, falsifiable decisive evidence, and owned assumption-change review trigger

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [checklist](references/checklist.md) | decision-checklist | Several feasibility consequence exit evidence or review-trigger decisions remain open together | The root record already closes boundary feasibility disqualifiers material consequences exit evidence and review triggers | analysis-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | Graph edges boundary claims decisive evidence or decision-to-validation freshness need proof | No source-backed boundary graph feasibility exit or review-trigger claim awaits closure | analysis-agent | evidence-record, proof-limit, residual-risk |
| [tradeoff benchmarks](references/tradeoff-benchmarks.md) | benchmark-pattern | Feasible options need a qualitative or evidence-supported numeric comparison method | Hard constraints leave one feasible path or current qualitative evidence resolves the choice | analysis-agent | option-comparison, selected-approach |
