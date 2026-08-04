---
name: task-handoff-context
description: "Select evidence-bearing context for a downstream consumer after work when claims, artifacts, validation, unresolved decisions, or omissions must cross a boundary."
---

# task-handoff-context

## Registry Trigger

**Use when**

- completed work has decision-changing claims or evidence to transfer to a named downstream consumer for a stated purpose
- candidate transfer may be lossy, stale, contradictory, overinclusive, or missing material context

**Do not use when**

- context is being selected before or during the current decision
- the request is to define a control-owned transfer schema, format, or process

## Skill Role

Decide what context must cross a downstream boundary after work.
`task-context-selection` owns working context before or during a decision. This
Skill does not define field names, format, phases, routing, or closure.

## Inputs

- downstream consumer, purpose, and the decision or next action they own
- candidate decision-changing claims, exact artifacts, latest diff, and validation
- unresolved decisions, constraints, findings, owners, exclusions, and known conflicts

## High-Value Rules

- Select decision-changing claims only after naming their downstream consumer and purpose.
- Bind each included claim to exact artifacts, source identity, the latest diff when code changed, and fresh supporting validation with coverage and proof limits.
- Preserve unresolved decisions, constraints, findings, owner, and next action without resolving them by summary.
- Select exclusions and omissions explicitly, stating why each is safe or how it may affect the downstream decision.
- Define staleness and reload triggers from material changes to artifacts, diff, validation, constraints, or findings.
- Keep contradictory evidence visible and state what fact would reconcile it.
- Detect lossy transfer when compression drops an artifact identity, qualification, unresolved decision, or proof limit.
- Report residual uncertainty that the selected transfer cannot close.

## Anti-Patterns

- A result summary without exact artifacts cannot establish what was inspected or changed.
- A newer narrative does not replace the latest diff or fresh validation.
- Passing evidence for one claim does not cover omitted constraints or findings.
- Silent contradiction removal makes the transfer smaller but less trustworthy.

## Execution Checklist

1. Name the downstream consumer, purpose, and owned next decision or action.
2. Bind included claims to exact artifacts, the latest diff, and fresh validation.
3. Preserve unresolved decisions, constraints, findings, owners, and proof limits.
4. Select exclusions and omissions with downstream impact.
5. Record staleness, reload triggers, contradictions, and lossy-transfer risks.
6. Return residual uncertainty.

## Stop Conditions

- Return `insufficient` when the downstream consumer or purpose is unknown.
- Return `contradictory` when supplied evidence conflicts and the transfer cannot preserve both sides with a reconciliation need.

## Output Contract

- downstream-context transfer decision with consumer, purpose, included claims, exact artifacts and latest diff, fresh validation, unresolved decisions, constraints, owner, next action, findings, proof limits, exclusions, omissions, staleness and reload triggers, contradictions, lossy-transfer risks, and residual uncertainty

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [task context](references/task-context-checklist.md) | decision-checklist | candidate transfer needs claim artifact freshness omission contradiction or loss comparison | consumer purpose included evidence exclusions and reload triggers are already explicit | analysis-agent, review-agent | checklist-result, residual-risk |
