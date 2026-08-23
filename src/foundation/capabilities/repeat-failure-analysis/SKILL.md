---
name: repeat-failure-analysis
description: "`analysis-agent`/`task-agent`/`review-agent`: use when repeated failure needs a new hypothesis or proof path; skip an initial failure with verified cause and a different action."
---

# repeat-failure-analysis

## Registry Trigger

**Use when**

- the same path, cause, patch shape, or validator has failed twice
- a repair repeats an approach already contradicted by current evidence

**Do not use when**

- the first failure has a verified cause and a materially different next action
- prior attempts are unavailable and the current repository must be inspected first

## Skill Role

Analyze repeated failure from observable source, commands, diffs, findings, and current-task evidence. Do not create a persistent memory subsystem.

## Inputs

- attempted hypotheses and their observable results
- current diff, failing output, changed paths, and acceptance
- known owner, adjacent patterns, and validation entry points

## High-Value Rules

- Classify observed facts, rejected hypotheses, and untested hypotheses separately.
- After two failures, do not repeat the same path without new evidence.
- Search the same pattern and affected consumers before applying a local repair.
- Change at least one material dimension: hypothesis, owner, patch location,
  instrumentation, reproduction, or validation method.
- Select the smallest feasible reproducer that can falsify the next hypothesis without losing the suspected mechanism.

## Anti-Patterns

- Local success substituted for evidence of the repeat failure analysis contract.

## Stop Conditions

- Stop when no new hypothesis or evidence distinguishes another attempt.
- Escalate when the next probe is destructive, privileged, production-facing,
  or outside the allowed scope.

## Output Contract

- observed facts, rejected hypotheses, same-pattern impact, next hypothesis,
  changed execution path, validation method, proof limits, and blocker if any

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [repeat failure](references/repeat-failure-checklist.md) | decision-checklist | the same path cause patch or validator has failed twice | this is the first verified failure or the next path is materially different | analysis-agent, task-agent, review-agent | checklist-result, residual-risk |
