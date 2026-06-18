---
name: plan-execution-consistency
description: Reconciles planned actions with actual changed files, commands, validation, review scope, extra work, stale evidence, and residual risk before final handoff.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "122"
changeforge_version: 0.1.0
---

# Plan Execution Consistency

## Mission
Compare the planned work against actual repository changes, commands, validation results, reviews, and handoff claims. The capability prevents silent scope drift, extra-file changes, stale validation, unreviewed repairs, and claims that no longer match the final patch.

## When To Use
- Before final handoff after any non-trivial plan, edit, test, review, repair, or release action.
- When files changed differ from planned files.
- When validation ran before final edits or only covered part of the final scope.
- When repair changed code after review and targeted re-review is required.
- When a plan, task DAG, route manifest, or stage manifest must match final evidence.

## Do Not Use When
- The task is read-only and no plan-to-execution comparison exists.
- A trivial single-file edit has an inline plan, matching diff, fresh validation, and no extra files.
- The work is intentionally abandoned and the handoff is a blocked/not-done status rather than completion.

## Non-Negotiable Rules
- Compare planned files, actual changed files, and final handoff file list.
- Explain every extra, missing, renamed, generated, or deleted file relative to the plan.
- Re-run validation after final material edits or disclose that validation is stale/not run.
- Match every changed behavior or public contract to acceptance criteria or explicit non-goal.
- Do not report partial validation as full validation.
- Repair after review requires targeted re-review before closure.
- Final handoff must disclose plan deviations, residual risk, and next gate.

## Industry Benchmarks
- **Change control variance analysis**: Compare approved plan to executed change before closure.
- **Code review scope control**: Review approval applies only to inspected files and behavior.
- **Test freshness discipline**: Test results are valid only for the code they ran against.
- **Release readiness review**: Deployment closure reconciles planned rollout, actual commands, and rollback evidence.
- **Audit evidence integrity**: Final claims must match artifacts, commands, and approvals.

## Selection Rules
- Select this capability for L2 or higher engineering work at final handoff.
- Select it when a plan or task DAG exists and files changed.
- Select it when validation, review, or release evidence could be stale.
- Select it with `quality-test-gate` when changed-code-to-test mapping is required.
- Select it with `ai-code-review-refactor` when an AI-generated patch may have drifted from the requested scope.

## Risk Escalation Rules
- Escalate when actual changed files include unplanned source, registry, hook, release, migration, generated, or security-sensitive artifacts.
- Escalate when validation is stale because files changed after the run.
- Escalate when review approval does not cover the final diff.
- Escalate when a plan deviation changes user behavior, API/data contract, security posture, release behavior, or docs obligations.
- Escalate when the handoff claims no residual risk while unverified deviations remain.

## Critical Details
- Planned files are not a hard prison; changes may legitimately expand, but every expansion needs a reason and review scope.
- Generated files must be labeled as generated or source-of-truth; validation should match repository policy.
- Validation freshness is relative to the final material diff, not to the start of the turn.
- A successful lint, build, or single test can be reported only as the specific evidence it provides.
- The final answer is part of the change artifact and must not overstate what was done or verified.

## Failure Modes
- **Extra file drift**: The agent changes an unplanned helper and does not mention it in handoff.
- **Stale test pass**: Tests ran before the registry update, but the final answer says all validation passed.
- **Partial validation inflation**: One targeted test is reported as full-suite success.
- **Unreviewed repair**: A review finding is fixed after approval and never re-reviewed.
- **Spec drift**: The implementation satisfies an invented plan but misses the original requested behavior.

## Output Contract
Return a `plan_execution_consistency_report` with:
- **Plan summary**: planned actions, files, owner skill, reviewer skill, acceptance signal, and validation command.
- **Actual diff summary**: changed, added, deleted, generated, and docs files.
- **Variance table**: planned vs actual with status `matched`, `extra`, `missing`, `renamed`, `generated`, or `deferred`.
- **Behavior mapping**: requirement or acceptance criterion to changed files and tests.
- **Validation freshness**: commands run, outcomes, whether files changed after each run, and what each command proves or does not prove.
- **Review scope**: reviewer, files reviewed, findings, repairs, and re-review status.
- **Documentation and registry consistency**: docs, registries, build outputs, or installation references affected and validated.
- **Residual risk**: unverified deviations, stale evidence, skipped checks, and next owner.
- **Closure decision**: ready, blocked, not verified, or needs re-review.

## Quality Gate
1. Planned files and actual changed files are reconciled.
2. Extra or missing files have rationale and review status.
3. Validation results are fresh for the final material diff or disclosed as stale/not run.
4. Changed behavior maps to acceptance criteria or non-goals.
5. Review scope covers the final diff or targeted re-review is required.
6. Partial validation is not reported as full validation.
7. Residual risk and next gate are explicit.

## Used By
- `change-forge-router`
- `task-dag-planner`
- `quality-test-gate`
- `ai-code-review-refactor`
- `delivery-release-gate`
- `reliability-observability-gate`
- `change-documentation-gate`
- `skill-authoring-expert`
- `agent-execution-discipline`

## Handoff
Hand off the consistency report with final implementation, review, release, or documentation closure. If deviations or stale evidence remain, hand off to the owner skill for repair or to the reviewer skill for targeted re-review.

## Completion Criteria
The capability is complete when the final handoff accurately reconciles plan, actual diff, validation, review, repairs, docs, residual risk, and next gate without overstating completion or hiding scope drift.
