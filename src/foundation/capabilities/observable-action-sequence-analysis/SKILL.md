---
name: observable-action-sequence-analysis
description: "`analysis-agent`/`task-agent`/`review-agent`: use offline to find validation, review, repair, or closure gaps; skip without sequence evidence; never infer live performance."
---

# observable-action-sequence-analysis

## Registry Trigger

**Use when**

- offline analysis of observable dispatch read edit validation review repair re-review and closure actions
- measure preparation loops duplicate reads stale validation missing review coverage or repair without re-review

**Do not use when**

- no task-local observable action sequence analysis decision is required

## Skill Role

Measure observable engineering actions offline without executable interception, hidden state, or runtime control.

## High-Value Rules

- Analyze only observable dispatch, read, edit, command, validation, review, repair, re-review, progress, and closure actions.
- Measure first productive action, first edit, control turns, duplicate reads, subagent count, loaded Skills, context size, and repair loops.
- Detect repeated preparation, stale validation, unreviewed changed files, and repair without re-review.
- Separate deterministic fixtures from live-agent evidence and label uncollected metrics.

## Anti-Patterns

- Deterministic fixtures prove evaluator behavior, not live-agent quality.
- Missing timestamps or outputs must be reported as uncollected.
- A shorter observable action sequence is not better when accuracy or risk coverage falls.

## Stop Conditions

- Stop comparisons unless baseline and treatment share the same task, acceptance, environment, and measurement definition.
- Escalate any claimed improvement without accuracy and defect-escape evidence.

## Output Contract

- ordered action-sequence record with first productive action, first edit, control turns, duplicate reads, subagent count, loaded Skills, context size, and repair loops
- per-metric value or explicit uncollected/not-applicable status and evidence basis, plus validation freshness, review/repair findings, caveats, and residual risk

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [action sequence](references/action-sequence-checklist.md) | decision-checklist | an agent action trace needs mutability ordering failure and evidence classification | the task contains no observable agent action sequence | analysis-agent, task-agent, review-agent | checklist-result, residual-risk |
