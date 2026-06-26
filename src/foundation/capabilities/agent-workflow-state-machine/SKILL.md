---
name: agent-workflow-state-machine
description: Enforces explicit agent stage state, legal transitions, owner and reviewer separation, repair loops, validation freshness, and closure evidence for multi-step engineering work.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "119"
changeforge_version: 0.1.0
---

# Mission
Keep agent-assisted engineering work in an explicit state machine from clarification through repository inspection, planning, implementation, testing, review, repair, re-review, release, and handoff. The capability prevents illegal jumps, stale evidence, self-approval, repeated same-path loops, and completion claims that do not match the actual workflow state.

# When To Use
- For L3 or higher work, multi-turn work, broad edits, or any task that crosses read, plan, edit, test, review, repair, release, or handoff stages.
- When route, current stage, next stage, owner, reviewer, validation freshness, stop condition, or closure status is ambiguous.
- When repair/re-review, stale validation, trajectory order, tool permission, release, hook runtime, or compaction work needs a documented legal transition.
- When project memory, repository graph, executor adapter, validation broker, or trajectory evidence changes what the next stage may legally be.
- When an agent claims done, fixed, validated, reviewed, or blocked after material work.

# Do Not Use When
- The task is a single read-only answer and no engineering action, validation claim, review claim, or handoff state is needed.
- A trivial edit already supplied current source evidence, fresh validation, residual risk, and final handoff evidence.
- The user asks only for brainstorming and no implementation, validation, review, or closure decision will occur.
- The primary need is raw source graphing, validation command selection, memory projection, or trajectory reconstruction without a stage-transition question.

# Stage Fit
Use before planning, before editing, before closure, after any repair edit, after validation, after review, after compaction, and after any material source, registry, hook runtime, generated artifact, report, benchmark, package, or install-output edit that changes the proof obligation. Re-enter the state gate whenever evidence order changes the legal next stage.

# Non-Negotiable Rules
- Name exactly one current stage and one next stage or closed state for each non-trivial handoff.
- Do not move from request to implementation without clarification status, repository context, and a TDD, eval, validation, or not-verified fallback signal.
- Do not move from review to closure while findings remain unrepaired, unre-reviewed, or outside the stated approval scope.
- The action owner and independent reviewer must be different skills or capabilities; implementer self-approval is not closure evidence.
- Validation is current only when it ran after final material edits and covers the changed paths or risk surface.
- Validation broker, executor adapter, repository graph, project memory, and trajectory evidence are inputs to state; unsupported, stale, partial, or low-confidence evidence degrades closure rather than proving it.
- Repair requires a targeted re-review of the repaired area and original finding before approval can support closure.
- A third same-path command, diagnosis, or patch attempt is blocked unless new evidence, route repair, or an explicit blocked handoff is recorded.

# Industry Benchmarks
Anchor against Kanban workflow policies, finite-state transition checks, incident-command handoff, code review governance, TDD entry criteria, CI freshness discipline, change-advisory closure, and audit-ready release gates. Keep the body focused on route-time state decisions; load the reference only when a concrete transition ledger or handoff template is needed.

# Mode Matrix
| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities |
| --- | --- | --- | --- | --- |
| Initial stage declaration | Non-trivial request, route manifest, compaction resume, or stage ambiguity. | Name current stage, entry evidence, next stage, and owner. | Requirement status, route/stage manifest, source boundary, validation signal. | `change-forge-router`, `agent-execution-discipline` |
| Read-before-plan gate | Planning starts with unclear source, graph, owner, or source-of-truth boundary. | Prevent plan from outrunning repository context. | Inspected files, same-pattern scan, graph freshness, skipped boundaries. | `repository-context-map`, `repository-graph-analysis` |
| Plan-to-edit gate | Implementation begins after a plan, DAG, or stage route. | Confirm legal transition and TDD or validation signal. | Accepted plan, owning surface, validation intent, permission/sandbox status. | `task-dag-planner`, `agent-tool-permission-sandbox` |
| Test/review gate | Validation or review evidence is used for closure. | Separate test, review, and closure states. | Command outcome, review scope, changed paths, evidence limits. | `validation-broker`, `quality-test-gate` |
| Repair re-review gate | Findings are fixed or final diff changes after review. | Require targeted re-review and fresh validation. | Finding id, repair owner, changed files, re-review result. | `ai-code-review-refactor`, `execution-trajectory-analysis` |
| Stop/handoff closure | Work is claimed done, blocked, released, installed, or handed off. | Reconcile state, validation, residual risk, and next owner. | Route/stage manifests, plan consistency, broker result, rollback note. | `plan-execution-consistency`, `delivery-release-gate` |

# Selection Rules
- Select this capability for L3 or higher work, multi-turn work, and all work with review/repair loops.
- Select it when an agent claims completion after edits, tests, release work, installation, diagnosis, documentation, or validation.
- Select it when stage routing, active skill context, owner/reviewer, validation freshness, stop condition, or next handoff is ambiguous.
- Select it with `agent-execution-discipline` when evidence, retry, repair, self-approval, skipped stage, or closure risk exists.
- Select it with `change-forge-router` when routed work needs a `changeforge_stage_route` manifest or route/stage consistency.
- Select it with `executor-adapter-protocol` when lifecycle state is derived from runtime adapter events or adapter capability limits.
- Select it with `execution-trajectory-analysis` when event order, edit-before-read, skipped stage, repair/re-review integrity, or validation freshness must be reconstructed.

# Technical Selection Criteria
Evaluate workflow state by stage clarity, legal transition, entry evidence, exit criteria, source-read freshness, owner/reviewer separation, plan-to-diff consistency, validation freshness, repair/re-review status, repeated-failure count, adapter support, graph/memory/trajectory coupling, release/install impact, and closure consequence. A workflow state is usable only as legal, blocked, stale, partial, needs repair, needs re-review, needs validation, or not verified.

# Proactive Professional Triggers
- **Signal:** Planning or editing starts before the target repository boundary is read.
  **Hidden risk:** the plan follows stale assumptions or missing source-of-truth constraints.
  **Required professional action:** block the edit transition, inspect current source, scan same-pattern paths, and name validation intent.
  **Route to:** `repository-context-map`, `repository-graph-analysis`.
  **Evidence required:** inspected paths map, omitted paths, source-of-truth decision, validator command candidates.
- **Signal:** Project memory, repository graph, or compaction summary is used as current proof.
  **Hidden risk:** stale context authorizes the wrong stage.
  **Required professional action:** classify it as selector-only until current source and validation freshness are reconciled.
  **Route to:** `project-memory-governance`, `execution-trajectory-analysis`.
  **Evidence required:** accepted/rejected claims report, freshness comparison matrix, direct-source fallback.
- **Signal:** Validation passed before later source, registry, hook runtime, generated artifact, report, package, or install-output edits.
  **Hidden risk:** final handoff reports stale proof as current validation.
  **Required professional action:** compare command order, rerun mapped validators, or mark closure stale, partial, or not-run.
  **Route to:** `validation-broker`, `quality-test-gate`.
  **Evidence required:** command, outcome, covered paths map, later edits, freshness verdict.
- **Signal:** A repair changes files after review or the reviewer scope is unclear.
  **Hidden risk:** the approved diff becomes unverified after the repair.
  **Required professional action:** record repair ledger and require targeted re-review before closure.
  **Route to:** `ai-code-review-refactor`, `plan-execution-consistency`.
  **Evidence required:** finding id, repair diff, reviewer report, re-review result.
- **Signal:** The same command, diagnosis, or patch route fails twice.
  **Hidden risk:** execution repeats the wrong path without a verified cause.
  **Required professional action:** block same-path retry and require route repair, new hypothesis, or blocked handoff.
  **Route to:** `failure-diagnosis`, `project-memory-governance`.
  **Evidence required:** attempt ledger report, failure class, changed route map, next owner.
- **Signal:** Adapter lifecycle output omits or does not support a state needed for closure.
  **Hidden risk:** missing runtime event is treated as approval.
  **Required professional action:** degrade evidence, use manual state summary, and disclose unsupported event limits.
  **Route to:** `executor-adapter-protocol`, `agent-tool-permission-sandbox`.
  **Evidence required:** supported fields report, missing fields map, fallback state, closure consequence.

# Risk Escalation Rules
- Escalate to `failure-diagnosis` after two same-path failures without verified cause, changed hypothesis, or route repair.
- Escalate to `quality-test-gate` and `validation-broker` when validation freshness, changed-code-to-test mapping, or test result scope is uncertain.
- Escalate to `ai-code-review-refactor` when AI-generated implementation needs spec-first review, repair re-review, or approval-scope correction.
- Escalate to `repository-graph-analysis` when source-of-truth, affected tests, owners, generated artifacts, or downstream callers are unclear.
- Escalate to `project-memory-governance` when prior context, fragile files, repeated failures, or stale memory affect the current stage.
- Escalate to `delivery-release-gate` when release, build, install, package, rollback, or artifact state participates in closure.
- Escalate to `security-privacy-gate` when tool permissions, secrets, auth, user data, raw prompts, environment variables, credentials, or full command output affect evidence capture.

# Critical Details
- A stage is not a prose label; it controls the evidence required before the next action.
- Planning, implementation, validation, review, repair, release, and closure are separate states; a plan without inspected boundaries is invalid.
- Review approval must state scope; approval of one file, finding, or behavior does not approve unreviewed extra files.
- Validation freshness compares command order against final material edits and changed risk surface, not against user confidence.
- Graph, memory, adapter, and trajectory evidence can widen scope, downgrade proof, or route repair; they cannot replace current source inspection, independent review, or mapped validation.
- Load [references/workflow-transition-ledger.md](references/workflow-transition-ledger.md) for allowed transitions, entry/exit fields, repair ledger rules, and the output template.

# Failure Modes
- **Illegal implementation jump:** Code changes start before repository context, same-pattern scan, and validation signal exist.
- **Lost repair loop:** Findings are fixed without targeted re-review, so the final diff is unapproved.
- **Self-approval:** The same skill or capability implements and declares review complete.
- **Stale validation:** A test, eval, build, install, or audit run before the final edit is reported as current proof.
- **Memory or graph overclaim:** Old context, graph, or compaction evidence is treated as source truth.
- **Adapter overclaim:** Unsupported lifecycle events are reported as completed workflow states.
- **State drift after compaction:** The resumed handoff omits current stage, owner, next gate, validation limit, or residual risk.
- **Closure package mismatch:** The route manifest, stage manifest, changed files, validators, rollback note, and residual risk describe different scopes.

# Reference Loading Policy
The `SKILL.md` body carries selection, gates, output, and closure rules. Load only the reference needed for the active state decision:
- Load [references/workflow-transition-ledger.md](references/workflow-transition-ledger.md) when drafting a concrete state summary, validating a transition, or documenting repair/re-review.
- Load [references/workflow-adapter-trajectory-coupling.md](references/workflow-adapter-trajectory-coupling.md) when adapter support, trajectory order, graph, memory, or validation broker evidence changes the legal next stage.
- Load [references/workflow-closure-state-package.md](references/workflow-closure-state-package.md) when final handoff must reconcile route/stage manifests, changed files, validators, rollback, residual risk, and next owner.

# Output Contract
Return a `workflow_state_summary` with:
- `mode_selected` (initial stage declaration, read-before-plan gate, plan-to-edit gate, test/review gate, repair re-review gate, or stop/handoff closure).
- `boundaries_inspected` (requirements, source files, registries/config/docs, tests/evals, reports, generated artifacts, install/build outputs, graph, memory, trajectory, adapter output, and skipped boundaries with reason).
- `workflow_state` (current stage, entry evidence, exit criteria, prior stage, next stage or closed state, legal transition verdict, and stop condition).
- `transition_decision` (allowed, blocked, stale, partial, needs read, needs repair, needs re-review, needs validation, needs release gate, or not verified).
- `owner_review_map` (action owner, reviewer skill/capability, independence check, review scope, approval limits, and next owner).
- `validation_freshness` (command, outcome, scope, covered paths, later edits, broker result, current/stale/partial/not-run/not-verified status).
- `repair_rereview_ledger` (finding id, repair owner, changed files, repair evidence, re-review result, unresolved findings, and uncovered diff areas).
- `tool_permission_adapter_limits` (permission/sandbox state, adapter lifecycle source, unsupported events, degradation note, and closure consequence).
- `trajectory_validation_coupling` (ordered event facts, edit-before-read status, graph/memory freshness, validation order, and accepted/rejected claims).
- `closure_decision` (ready, needs source reread, needs plan repair, needs re-review, needs validation, needs release/install check, or blocked).
- `evidence_limits` and `residual_risk` (what the state proves, what it does not prove, rollback note, and next gate).

# Evidence Contract
Close workflow-state review only when these answers are concrete:
- **Basis:** route/stage signal, requested change, affected boundary, and why state order changes risk.
- **Current evidence:** requirements, source, registry/config/docs, tests, reports, generated artifacts, graph, memory, trajectory, adapter output, validation, and review findings inspected.
- **Legal transition:** current stage, entry evidence, exit criteria, next stage, and blocked or allowed rationale.
- **Ownership and review:** action owner, independent reviewer, repair owner, approval scope, and re-review result.
- **Freshness and closure:** validation broker status, later edits, stale/partial/not-run limits, plan consistency, rollback note, residual risk, and next owner.

# Benchmark Coverage
This capability covers explicit workflow policies, finite-state transition checks, owner/reviewer separation, TDD and validation entry criteria, repair re-review governance, CI freshness rejection, repeated-failure stop rules, adapter capability degradation, graph-memory-trajectory reconciliation, and audit-ready handoff.

# Routing Coverage
Routes from `change-forge-router`, `task-dag-planner`, `quality-test-gate`, `ai-code-review-refactor`, `delivery-release-gate`, `reliability-observability-gate`, `change-documentation-gate`, `skill-authoring-expert`, and `agent-execution-discipline` should arrive here when workflow state, legal transition, owner/reviewer split, repair, validation freshness, stop condition, adapter state, or closure evidence is at issue. Route away when the primary need is raw graph extraction, validation command brokerage, memory governance, failure cause diagnosis, or code review without a state-transition question.

# Quality Gate
1. Exactly one current stage is named with entry evidence and exit criteria.
2. Next transition is legal, blocked, or not verified with a concrete reason.
3. Repository context and source-of-truth boundaries are inspected before planning or editing.
4. Owner and reviewer are different, and approval scope is stated.
5. Repair has targeted re-review before closure.
6. Validation freshness covers final material source, registry, hook runtime, generated artifact, report, benchmark, package, or install-output edits.
7. Stale, partial, not-run, unsupported, low-confidence, or failed evidence is not reported as closure proof.
8. Repeated same-path attempts stop after two failures unless new evidence and route repair are recorded.
9. Graph, memory, adapter, trajectory, validation broker, route manifest, and stage manifest evidence are reconciled when available.
10. Final handoff states inspected evidence, unknowns, validation limits, rollback note, residual risk, and next owner.

# Used By
`change-forge-router`, `task-dag-planner`, `quality-test-gate`, `ai-code-review-refactor`, `delivery-release-gate`, `reliability-observability-gate`, `change-documentation-gate`, `skill-authoring-expert`, `agent-execution-discipline`.

# Handoff
Hand off the current state summary with every implementation, review, repair, test, release, documentation, compaction, or closure transition. If the next stage is blocked, hand off only to the skill, gate, reviewer, validator, or owner that can remove the block.

# Completion Criteria
The capability is complete when the work has a coherent current stage, legal next transition, owner/reviewer split, fresh validation status, repair/re-review ledger, adapter and trajectory limits, graph/memory freshness judgment, stop condition, and closure evidence matching the repository state.
