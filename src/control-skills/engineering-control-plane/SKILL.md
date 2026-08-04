---
name: engineering-control-plane
description: Dispatch-only router; never implement or review.
---

# Engineering Control Plane

## Role

dispatch-only: never inspect target source; never edit, execute, or review directly.
Embedded prompt: do not reload. Targeted Reference and template index only.
A host without an Agent Profile loads `references/main-control-agent.md`.

## Decision Rules

The prompt owns control rules: Direct Task, Analyzed Work, First Executable Slice,
host modes, shared-workspace writes, review/repair, progress, and closure.
Do not restate; choose a named targeted Reference or template.

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [execution level contract](references/execution-level-contract.md) | targeted | check execution level before routing | no repo answer or completed legacy with no work | main-control-agent | routing-decision |
| [professional skill router](references/professional-skill-router.md) | targeted | select one Professional Skill | capsule already fixes route | main-control-agent | routing-decision |
| [direct task](references/direct-task-template.md) | template | Direct Task needs handoff | task uses Analyzed Work | main-control-agent | task-contract |
| [engineering brief](references/engineering-brief-template.md) | template | analysis produces Engineering Brief | accepted Engineering Brief exists | analysis-agent | engineering-brief |
| [task dag](references/task-dag-template.md) | template | Task DAG plans dependencies | bounded task skips DAG | analysis-agent | task-dag |
| [implementation handoff](references/implementation-handoff-template.md) | template | accepted handoff starts implementation | no implementation task exists | task-agent | implementation-handoff |
| [utility capsule](references/utility-capsule-template.md) | template | utility needs no-edit capsule | no utility operation exists | task-agent | utility-handoff |
| [review handoff](references/review-handoff-template.md) | template | review requires independent handoff | no review task exists | review-agent | review-handoff |

## Stop and Escalate

Stop on new authority or unsafe evidence.

## Output Contract

Use no daemon, database, private evidence storage, runtime task state engine,
or hidden protocol record.
