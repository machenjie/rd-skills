---
name: agent-workflow-state-machine
description: Enforces explicit agent stage state, legal transitions, owner and reviewer separation, repair loops, validation freshness, and closure evidence for multi-step engineering work.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "119"
changeforge_version: 0.1.0
---

# Agent Workflow State Machine

## Mission
Keep agent-assisted engineering work in a coherent state machine from clarification through repository inspection, planning, implementation, testing, review, repair, re-review, and handoff. The capability prevents illegal jumps, stale evidence, self-approval, and completion claims that do not match the actual workflow state.

## When To Use
- For non-trivial engineering work that spans more than one stage or turn.
- When route, stage, owner, reviewer, or next action must remain clear across context changes.
- When a review finding requires repair and re-review.
- When validation was run before the final edits or the closure evidence may be stale.
- When tool, permission, release, or hook runtime work needs a documented stop condition.

## Do Not Use When
- The task is a single read-only answer with no engineering action.
- A trivial one-file edit has already supplied fresh validation, residual risk, and final handoff evidence.
- The user explicitly asks only for brainstorming and no implementation or review will occur.

## Non-Negotiable Rules
- Name exactly one current stage and one next stage or closed state for each non-trivial handoff.
- Do not jump from request to implementation without clarification status, repository-context evidence, and a TDD or validation signal.
- Do not move from review to closure when findings remain unrepaired or unre-reviewed.
- The action owner and independent reviewer must be different skills or capabilities.
- Validation evidence must be fresh after the final material edit; stale validation must be disclosed as not verified.
- When Validation Broker output is available, use its event-order freshness and coverage result as closure evidence; stale, failed, not-run, no-outcome, or coverage-mismatch results route back to testing or failure diagnosis.
- When executor adapter output is available, lifecycle state transitions must respect `AdapterCapabilities`; unsupported runtime events create degraded workflow evidence rather than full closure.
- When trajectory output is available, use `execution-trajectory-analysis` as the bounded review view for lifecycle transitions, repair/re-review, and validation freshness timeline.
- Repair requires a targeted re-review of the repaired area, not a broad completion claim.
- Stop conditions must prevent a third same-path retry after two failures without new evidence and route repair.

## Industry Benchmarks
- **Kanban workflow policies**: Work moves between explicit states only when exit criteria are met.
- **Incident command handoff**: State, owner, next action, and residual risk are explicit at every shift.
- **Code review governance**: Implementer self-approval is insufficient for meaningful review.
- **Test-driven development**: Implementation starts after a test, eval, or validation signal is named.
- **Change advisory discipline**: Closure requires evidence, rollback or residual risk, and accountable next owner.

## Selection Rules
- Select this capability for L3 or higher work, multi-turn work, and all work with review/repair loops.
- Select it when an agent claims completion after edits, tests, release work, or diagnosis.
- Select it when stage routing, active skill context, owner/reviewer, or next handoff is ambiguous.
- Select it with `agent-execution-discipline` when evidence, retry, repair, or closure risk exists.
- Select it with `change-forge-router` for routed changes that need a `changeforge_stage_route` manifest.
- Select `executor-adapter-protocol` when lifecycle state is derived from runtime adapter events.
- Select `execution-trajectory-analysis` when event order, edit-before-read, skipped stage, or repair/re-review integrity needs inspection.

## Risk Escalation Rules
- Escalate to `failure-diagnosis` after two same-path failures without verified cause.
- Escalate to `quality-test-gate` when validation freshness, changed-code-to-test mapping, or test result scope is uncertain.
- Escalate to `ai-code-review-refactor` when AI-generated implementation needs spec-first review.
- Escalate to `delivery-release-gate` when a release or install state transition requires rollout, rollback, or artifact evidence.
- Escalate to `security-privacy-gate` when tool permissions, secrets, auth, or user data affect the next transition.

## Critical Details
- A stage is not a label for prose style; it controls what evidence is needed before the next action.
- Planning and implementation are separate states. A plan without inspected boundaries is an invalid state.
- Testing and validation are evidence states, not magic completion states.
- Review approval must state scope. Approval of one file or behavior does not approve unreviewed extra files.
- Re-review after repair is targeted to the changed evidence and the original finding.

## Failure Modes
- **Illegal implementation jump**: Code changes start before repository context and validation signal exist.
- **Lost repair loop**: Review findings are fixed but not re-reviewed, so a new defect escapes.
- **Self-approval**: The same agent skill implements and declares review complete.
- **Stale validation**: A test run before the final edit is reported as proving the final patch.
- **State drift after compaction**: The resumed handoff omits current stage, owner, next gate, or residual risk.

## Output Contract
Return a `workflow_state_summary` with:
- **Current stage**: one of the canonical engineering stages.
- **Entry evidence**: facts that allow this stage to start.
- **Exit criteria**: evidence required before moving to the next stage.
- **Owner and reviewer**: action owner skill/capability and different review skill/capability.
- **Transition history**: prior stage, current stage, next stage, and reason.
- **Lifecycle state source**: manual route evidence, adapter lifecycle state, trajectory view, or unavailable source with degradation note.
- **Validation freshness**: command, outcome, timestamp or turn relation, and whether edits happened after it.
- **Validation broker result**: selected command level, coverage alignment, event-order freshness, and next route when validation failed.
- **Review and repair ledger**: findings, repair owner, re-review result, and unresolved findings.
- **Stop condition**: failure count, route repair trigger, or blocked owner question.
- **Closure package status**: route manifest, stage manifest, repository context, plan consistency, validation, residual risk, and next action.
- **Trajectory evidence view**: when telemetry is available, offline trajectory inspection may summarize route/read/plan/edit/test/review/repair/stop evidence, illegal transitions, validation freshness, and repair/re-review status. It is review evidence only, not automatic skill learning.

## Quality Gate
1. Exactly one current stage is named.
2. Entry evidence exists for the current stage.
3. Next transition is legal and justified by evidence.
4. Owner and reviewer are different.
5. Repair has targeted re-review before closure.
6. Validation evidence is fresh or explicitly disclosed as stale/not run.
7. The stop condition prevents repeated same-path retries.
8. Adapter capability limits and trajectory findings are reconciled before closure when they are available.
9. Final handoff contains route, stage, validation, residual risk, and next action evidence when engineering work occurred.

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
Hand off the current state summary with every implementation, review, repair, test, release, or documentation transition. If the next stage is blocked, hand off only to the skill or owner that can remove the block.

## Completion Criteria
The capability is complete when the work has a coherent current stage, legal next transition, owner/reviewer split, fresh validation status, repair/re-review ledger, and closure evidence that matches the actual state of the repository. When a trajectory report is used, it supports this closure check as bounded runtime evidence and does not replace human review or explicit validation.
