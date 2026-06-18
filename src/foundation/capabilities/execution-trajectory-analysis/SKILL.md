---
name: execution-trajectory-analysis
description: Reconstructs and analyzes agent execution trajectories for lifecycle transitions, repair and re-review ledgers, validation freshness timelines, and behavior fixture candidates.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "127"
changeforge_version: 0.1.0
---

# Execution Trajectory Analysis

## Mission
Build a bounded review view of the agent's execution path so illegal transitions, edit-before-read behavior, stale validation, repair without re-review, and missing closure risk are visible before handoff.

## When To Use
- When a task mentions trajectory, edit before read, repair without re-review, stop without residual risk, skipped engineering stage, or pressure/behavior candidate generation.
- Before reviewing AI-assisted work that has multiple read, edit, test, repair, review, or handoff steps.
- When validation freshness depends on the order of edits and commands.
- When runtime evidence should generate pressure or behavior eval candidates.

## Do Not Use When
- The task is a simple read-only answer and no action trajectory exists.
- The user asks for raw logs, prompts, or full command output; trajectory analysis stores bounded facts only.
- Stage state is already trivial and current validation/review evidence is fresh.

## Non-Negotiable Rules
- Build the trajectory from bounded lifecycle facts, not raw prompts or sensitive content.
- Use a trajectory builder to order read, plan, edit, review, repair, test, release, compaction, stop, and handoff events.
- Use a trajectory analyzer to detect illegal transition, skipped stage, stale validation, repeated failure, and missing closure evidence.
- Record repair/re-review ledger entries when a review finding changes files.
- Maintain a validation freshness timeline that ties command outcomes to later material edits.
- Generate pressure/behavior candidate fixtures only from bounded facts and reviewed failure patterns.

## Industry Benchmarks
- **Workflow audit trail**: Reviewable lifecycle facts support closure and post-review learning.
- **State-machine validation**: Transitions are checked against allowed stage movement.
- **Review repair discipline**: Repair after review needs targeted re-review evidence.
- **Test freshness timeline**: Validation is ordered against final changes.
- **Evaluation mining**: Recurrent failures become candidate fixtures after privacy review.

## Selection Rules
- Select this capability with `agent-workflow-state-machine` when stage transitions need evidence.
- Select it with `validation-broker` when command freshness depends on event order.
- Select it with `ai-code-review-refactor` when review should inspect more than the final diff.
- Select it with `project-memory-governance` when repeated trajectory failures should become governed memory or fixtures.

## Risk Escalation Rules
- Escalate when edits occur before read/context evidence for the target boundary.
- Escalate when implementation skips required planning, testing, review, or documentation stages.
- Escalate when repair changes files after review without re-review.
- Escalate when validation passed before later material edits.
- Escalate when stop closure omits residual risk for not-run, stale, partial, or unsupported evidence.
- Escalate to `security-privacy-gate` if trajectory capture would include secrets, prompts, personal data, or full command output.

## Critical Details
- Trajectory builder records event id, stage, bounded path, action type, owner skill, reviewer skill, command class, and timestamp/order.
- Trajectory analyzer compares event order to stage model, route manifest, plan, review scope, and validation broker results.
- Illegal transition detection should name expected previous state, observed state, and required repair route.
- Repair/re-review ledger must name finding id, files changed, repair evidence, reviewer, and re-review result.
- Validation freshness timeline must show command outcome, covered paths, later edits, and current status.
- Candidate generation proposes pressure or behavior fixtures; it does not silently add them as measured evidence.

## Failure Modes
- **Final-diff tunnel vision**: Review ignores that code was edited before context was read.
- **Skipped review**: A repair changes the final diff after approval.
- **Stale validation**: A pass predates the final registry, hook, or source edit.
- **Sensitive trace**: Raw prompts or command output are preserved instead of bounded facts.
- **Fixture overclaim**: A candidate trajectory fixture is reported as live behavior evidence.

## Output Contract
Return an `execution_trajectory_analysis` record with:
- **Trajectory builder output**: ordered lifecycle events, stages, bounded paths, commands, owners, and reviewers.
- **Trajectory analyzer findings**: illegal transitions, skipped stages, repeated failures, and closure gaps.
- **Repair/re-review ledger**: findings, repairs, re-review status, and uncovered diff areas.
- **Validation freshness timeline**: command outcomes, covered paths, later edits, and stale/current status.
- **Candidate fixtures**: pressure or behavior fixture candidates with privacy review status.
- **Closure advice**: ready, needs repair, needs re-review, needs validation, or blocked with residual risk.

## Quality Gate
1. Trajectory is bounded and excludes raw prompts, secrets, personal data, and full command output.
2. Stage transitions are checked against allowed workflow movement.
3. Edit-before-read, repair-without-re-review, and skipped-stage signals are evaluated.
4. Validation freshness timeline covers final material edits.
5. Candidate fixtures are labeled structural/candidate until reviewed.
6. Closure advice includes residual risk and next owner when evidence is missing.

## Used By
- `change-forge-router`
- `quality-test-gate`
- `ai-code-review-refactor`
- `change-documentation-gate`
- `agent-execution-discipline`
- `skill-authoring-expert`

## Handoff
Hand off trajectory findings to the reviewer, validator, or stage owner. Hand off fixture candidates through project memory governance or explicit eval authoring review.

## Completion Criteria
The capability is complete when the execution path, illegal transitions, repair/re-review status, validation freshness, fixture candidates, privacy boundary, and closure advice are explicit and bounded.
