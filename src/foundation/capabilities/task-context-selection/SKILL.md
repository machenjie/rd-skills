---
name: task-context-selection
description: "Select facts, artifacts, Layer 3 Skills, and References when decision context is stale, redundant, uncertain, or over budget; skip transfer and sufficient current context."
---

# task-context-selection

## Registry Trigger

**Use when**

- a working decision needs a minimum set of current facts, artifacts, Layer 3 Skills, or References
- candidate context is stale, irrelevant, redundant, uncertain, or exceeds the available budget

**Do not use when**

- current non-redundant context already supports the decision with no material omission
- context must be packaged or transferred downstream

## Skill Role

Select working context before or during one decision. Do not define routing,
phases, permissions, or downstream transfer; `task-handoff-context` owns
packaging context for another agent.

## Inputs

- the exact current decision, alternatives, and failure boundary
- candidate facts and artifacts with source identity and freshness basis
- candidate Layer 3 Skills and References, plus the available context budget

## High-Value Rules

- Include only context that can distinguish an alternative, constraint, or failure boundary in the current decision.
- Record source identity, freshness basis, and decision use for every included fact or artifact.
- Select Layer 3 Skills and References only when their material supplies a non-redundant fact, method, constraint, or comparison used by the decision.
- Exclude irrelevant, stale, and redundant context. Record omissions that could change the decision.
- Refresh an included item when a material state change can invalidate its freshness basis or decision use.
- Make the context-budget tradeoff explicit: preserve authoritative evidence and compress or drop replaceable narrative.
- Report uncertainty and residual risk without filling gaps with plausible context.

## Anti-Patterns

- More context does not make an unsupported fact reliable.
- A recent timestamp alone does not establish freshness for the current state.
- Familiar material without a named decision use consumes budget without reducing uncertainty.
- Budget pressure does not justify dropping source identity or a material omission.

## Execution Checklist

1. Name the current decision and the distinctions it must resolve.
2. Compare candidate facts and artifacts by source, freshness, and decision use.
3. Select the minimum non-redundant facts, artifacts, Layer 3 Skills, and References.
4. Record excluded context, omissions, refresh triggers, and the context-budget tradeoff.
5. Return remaining uncertainty and residual risk.

## Stop Conditions

- Return `insufficient` when a material fact lacks source identity or a defensible freshness basis.
- Stop selection when the available budget cannot retain the minimum evidence needed for the decision; name the displaced evidence and tradeoff.

## Output Contract

- working-context selection with current decision, selected facts and artifacts, source, freshness, decision use, selected Layer 3 Skills and References, excluded context, refresh triggers, omissions, uncertainty, context-budget tradeoff, and residual risk

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [context selection](references/context-selection-checklist.md) | decision-checklist | candidate facts artifacts Layer 3 Skills or References need source freshness decision-use or budget comparison | the current minimum set and refresh conditions are already explicit | analysis-agent, task-agent, review-agent | checklist-result, residual-risk |
