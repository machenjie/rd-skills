---
name: execution-trajectory-analysis
description: Reconstructs and analyzes agent execution trajectories for lifecycle transitions, repair and re-review ledgers, validation freshness timelines, and behavior fixture candidates.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "127"
changeforge_version: 0.1.0
---

# Mission
Build a bounded review view of the agent execution path so illegal transitions, edit-before-read behavior, stale validation, repair without re-review, repeated same-path failure, and missing closure risk are visible before handoff. Trajectory evidence is an ordering and freshness control: it can trigger source reread, graph refresh, memory governance, validation broker repair, reviewer re-entry, or blocked closure without retaining raw prompts or full command output.

# When To Use
- When a task mentions trajectory, lifecycle path, edit before read, repair without re-review, repeated attempt, skipped engineering stage, stop without residual risk, or pressure/behavior candidate generation.
- Before reviewing AI-assisted work with multiple read, plan, edit, test, repair, review, build, install, release, compaction, or handoff steps.
- When validation freshness depends on whether commands ran before or after final material edits.
- When project memory, repository graph, prior context, or report evidence may be stale because later actions changed the target boundary.
- When runtime evidence should propose pressure or behavior eval candidates for human-reviewed promotion.

# Do Not Use When
- The task is a simple read-only answer and no action trajectory affects scope, validation, or closure.
- The user asks for raw logs, prompts, environment values, secrets, personal data, or full command output.
- Stage state is trivial, current source was read, no files changed, and no validation/review claim will be made.
- The primary need is source discovery, graph extraction, validation command selection, or memory projection without an execution-order question.

# Stage Fit
Use during planning, review, repair, validation, release, compaction, and final handoff whenever order changes the evidence obligation. Re-run after a repair edit, a second same-path failure, a graph or memory refresh, a generated artifact build, a new validation command, or any material edit after a previously passing check.

# Non-Negotiable Rules
- Build the trajectory from bounded lifecycle facts, not raw prompts, secrets, personal data, environment variables, credentials, or full command output.
- Use ordered lifecycle events for read, plan, edit, review, repair, validation, build, release, compaction, stop, and handoff.
- Check event order against the stage model, route manifest, plan, review scope, validation broker result, and changed files.
- Edits before current target-boundary read are defects unless an explicit source-of-truth exception and direct-source fallback are recorded.
- Repair after review requires a repair ledger entry and targeted re-review before approval can support closure.
- Validation is current only when it ran after final material edits and covers the changed paths or risk surface.
- Pressure or behavior fixtures are candidate evidence only until privacy review and explicit eval authoring promote them.

# Industry Benchmarks
Anchor against workflow audit trails, finite-state transition validation, review repair ledgers, CI freshness control, incident timeline reconstruction, evidence-retention minimization, and human-reviewed eval mining. Keep the capability focused on order, freshness, and closure; load the reference only when event schema, lifecycle state, validation coupling, or fixture promotion details are needed.

# Mode Matrix
| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities |
| --- | --- | --- | --- | --- |
| Lifecycle reconstruction | Multi-step read/plan/edit/test/review/handoff path. | Build ordered bounded events and stage transitions. | Event ids, stage, paths, action class, owner/reviewer, order. | `agent-workflow-state-machine` |
| Edit-before-read gate | Target files changed before source/context read. | Detect skipped context and require direct-source repair. | Edited path, first read event, source-of-truth status, repair route. | `repository-context-map`, `repository-graph-analysis` |
| Repair re-review gate | Review finding followed by edits. | Ensure repaired diff is inspected by reviewer/gate. | Finding id, changed files, repair evidence, re-review result. | `ai-code-review-refactor`, `quality-test-gate` |
| Validation freshness gate | Command pass predates later edit or has unclear scope. | Mark current, stale, partial, failed, or not verified. | Command, outcome, covered paths, later edits, freshness verdict. | `validation-broker` |
| Repeated failure gate | Same command, patch path, or diagnosis repeats twice. | Stop loop and require new route or blocked handoff. | Attempt ledger, failure class, changed hypothesis, next owner. | `project-memory-governance`, `failure-diagnosis` |
| Fixture candidate review | Trajectory reveals pressure or behavior pattern. | Propose candidate without treating it as measured evidence. | Bounded facts, privacy status, reviewer, promotion decision. | `skill-efficacy-benchmark`, `skill-authoring-expert` |

# Selection Rules
- Select this capability with `agent-workflow-state-machine` when stage transitions or lifecycle state need order evidence.
- Select it with `validation-broker` when command freshness, affected-path coverage, or negative evidence gates closure.
- Select it with `repository-graph-analysis` when graph/context evidence predates edits, reports, generated artifacts, or compaction.
- Select it with `project-memory-governance` when repeated failures, fragile files, stale context, or prior review findings change execution risk.
- Select it with `ai-code-review-refactor` when the final diff is insufficient because repair order, skipped review, or stale validation can hide risk.

# Technical Selection Criteria
Evaluate trajectory use by event boundedness, ordering confidence, stage legality, source-read freshness, review/repair coupling, validation freshness, graph/memory interaction, privacy boundary, fixture-promotion authority, and closure consequence. A trajectory claim is usable only as accepted current evidence, rejected, stale, partial, candidate, or not verified.

# Proactive Professional Triggers
- **Signal:** A file is edited before the target boundary is read.
  **Hidden risk:** stale source assumptions and wrong source-of-truth constraints drive the implementation.
  **Required professional action:** inspect current source, document edit-before-read status, scan same-pattern paths, and revalidate the repair.
  **Route to:** `repository-context-map`, `agent-execution-discipline`.
  **Evidence required:** edited path, first read event, current source evidence, same-pattern scan, repair validation command.
- **Signal:** A review finding is repaired but no re-review event follows.
  **Hidden risk:** wrong approved diff ships because review evidence predates the repaired files.
  **Required professional action:** require targeted re-review, verify repaired file scope, or downgrade closure.
  **Route to:** `ai-code-review-refactor`, `quality-test-gate`.
  **Evidence required:** finding id, repaired files, reviewer/gate, re-review result, uncovered diff map.
- **Signal:** Validation passed before later source, registry, hook runtime, generated artifact, report, or install-output edits.
  **Hidden risk:** stale validation evidence silently overclaims final patch coverage.
  **Required professional action:** compare command order, route changed paths to validators, rerun stale checks, or disclose partial status.
  **Route to:** `validation-broker`, `plan-execution-consistency`.
  **Evidence required:** command order report, covered-path map, later-edit list, freshness verdict, selected validator.
- **Signal:** The same diagnosis, command, or patch route fails twice.
  **Hidden risk:** repeated retry hides missing cause and creates a third wrong same-path attempt.
  **Required professional action:** record the attempt ledger, classify the failure, change route, and block another retry without a new hypothesis.
  **Route to:** `project-memory-governance`, `failure-diagnosis`.
  **Evidence required:** attempt ledger, failure class, changed hypothesis, next owner, blocked reason if no safe path remains.
- **Signal:** Prior memory, graph, or compaction summary is used as proof after later edits.
  **Hidden risk:** stale context or memory substitutes for current repository evidence.
  **Required professional action:** downgrade prior evidence to selector-only, inspect current source, and reconcile validation before closure.
  **Route to:** `repository-graph-analysis`, `project-memory-governance`.
  **Evidence required:** freshness comparison report, accepted/rejected claims, direct-source fallback, residual risk owner.
- **Signal:** Runtime trajectory suggests a behavior fixture.
  **Hidden risk:** private execution facts leak into durable policy or measured evidence without review.
  **Required professional action:** label the fixture as candidate, classify privacy, exclude sensitive material, and require maintainer/eval authoring promotion.
  **Route to:** `skill-efficacy-benchmark`, `skill-authoring-expert`.
  **Evidence required:** bounded fact set, excluded sensitive material, privacy review status, promotion decision, rollback note.

# Risk Escalation Rules
- Escalate when edits occur before read/context evidence for the target boundary.
- Escalate when implementation skips required planning, testing, review, documentation, release, or handoff stages.
- Escalate when repair changes files after review without re-review.
- Escalate when validation passed before later material edits or does not cover changed paths.
- Escalate when the same path, command, or diagnosis is retried a third time without new evidence.
- Escalate when closure omits residual risk for not-run, stale, partial, unsupported, privacy-sensitive, or unknown-owner evidence.
- Escalate to `security-privacy-gate` if capture would include raw prompts, secrets, personal data, environment variables, credentials, or full command output.

# Critical Details
- A trajectory event records id, stage, bounded path/artifact family, action class, owner skill, reviewer skill, command class, outcome summary, privacy class, and timestamp/order.
- The analyzer compares event order to stage model, route manifest, plan, review scope, changed files, graph freshness, memory signals, and validation broker results.
- Illegal transition findings name expected previous state, observed state, affected boundary, consequence, and required repair route.
- Repair/re-review ledger names finding id, files changed, repair evidence, reviewer/gate, re-review status, and uncovered diff areas.
- Validation freshness timeline names command, scope, outcome, covered paths, later edits, stale/current/partial verdict, and next validator.
- Candidate fixture generation proposes structural examples only; it does not silently add evals, write policy, or claim live behavior evidence.
- Load [references/trajectory-validation-coupling.md](references/trajectory-validation-coupling.md) for event schema, lifecycle transition rules, freshness matrix, graph/memory coupling, and output template.
- Load [references/trajectory-privacy-fixture-boundary.md](references/trajectory-privacy-fixture-boundary.md) when privacy classification, sensitive-field exclusion, fixture candidate retention, or promotion authority needs exact fields.
- Load [references/trajectory-handoff-closure-map.md](references/trajectory-handoff-closure-map.md) when mapping trajectory findings to validation, re-review, rollback, blocked handoff, or residual risk.

# Failure Modes
- **Final-diff tunnel vision:** Review ignores that code was edited before current context was read.
- **Skipped review:** A repair changes the final diff after approval.
- **Stale pass:** A validation command passed before the final registry, hook, source, generated, report, or install-output edit.
- **Repeated retry loop:** A third same-path attempt proceeds with no new cause, route, validator, or blocked handoff.
- **Sensitive trace:** Raw prompts, secrets, personal data, environment values, or full command output are retained instead of bounded facts.
- **Fixture overclaim:** A candidate trajectory fixture is reported as measured behavior evidence or promoted without privacy review.
- **Degraded adapter overclaim:** unsupported lifecycle or validation events are treated as full trajectory proof.
- **Closure downgrade skipped:** stale, partial, not-run, or privacy-sensitive evidence is named but not mapped to blocked handoff or residual risk.

# Reference Loading Policy
The `SKILL.md` body carries selection, gates, output, and closure rules.
- Load [references/trajectory-validation-coupling.md](references/trajectory-validation-coupling.md) when drafting a concrete trajectory record, reconciling validation freshness with final edits, deciding repair/re-review status, coupling graph or memory evidence, or proposing fixture candidates.
- Load [references/trajectory-privacy-fixture-boundary.md](references/trajectory-privacy-fixture-boundary.md) when trajectory capture, fixture candidates, privacy classification, retention, redaction, or human promotion authority needs exact fields.
- Load [references/trajectory-handoff-closure-map.md](references/trajectory-handoff-closure-map.md) when findings must map to source reread, validator rerun, targeted re-review, blocked closure, rollback, or next owner.

# Output Contract
Return an `execution_trajectory_analysis` record with:
- `mode_selected` (lifecycle reconstruction, edit-before-read gate, repair re-review gate, validation freshness gate, repeated failure gate, or fixture candidate review).
- `boundaries_inspected` (source files, registry/config/docs, reports, generated artifacts, tests/evals, validation output, graph slice, memory signals, review findings, and skipped boundaries with reason).
- `trajectory_events` (ordered bounded facts for read, plan, edit, review, repair, validation, build, release, compaction, stop, and handoff events).
- `findings_and_repair_ledger` (illegal transitions, skipped stages, repeated failures, closure gaps, repairs, reviewer/gate, re-review status, and uncovered diff areas).
- `validation_freshness_timeline` (command outcomes, covered paths, later edits, current/stale/partial/not-run status, and next validator).
- `graph_memory_validation_coupling` (accepted/rejected/stale graph or memory claims, validation broker adequacy, and closure consequence).
- `changed_trajectory_to_validation_map` (each changed path, repair, generated artifact, report, or fixture candidate mapped to validator, review, owner response, or residual risk).
- `privacy_and_retention_boundary` (bounded fields retained, sensitive fields excluded, fixture candidate status, promotion authority, and retention limit).
- `closure_advice` (ready, needs source reread, needs repair, needs re-review, needs validation, needs fixture review, or blocked).
- `evidence_limits` and `residual_risk` (what the trajectory proves, what it does not prove, rollback note, and next owner).
- `handoff` (closure decision, owner/reviewer route, validation limits, rollback note, and next gate).

# Evidence Contract
Close trajectory analysis only when these answers are concrete:
- **Basis:** route/stage signal, changed boundary, and why execution order changes risk.
- **Current evidence:** source, registry/config/docs, reports, generated outputs, graph, memory, review findings, validation output, and event order inspected.
- **Privacy boundary:** bounded fields retained, sensitive fields excluded, and fixture candidate status if any.
- **Freshness and repair:** edit-before-read status, repair/re-review status, validation freshness, repeated-failure status, and direct-source fallback.
- **Coupling and closure:** graph/memory/validation judgment, changed-trajectory-to-validation map, rollback note, residual risk, and next owner.

# Benchmark Coverage
This capability covers workflow audit trails, finite-state transition checks, edit-before-read prevention, repair re-review discipline, validation freshness timelines, repeated-failure loop control, graph-memory-validation reconciliation, privacy-minimized execution records, fixture candidate governance, and evidence-limited handoff.

# Routing Coverage
Routes from `change-forge-router`, `quality-test-gate`, `ai-code-review-refactor`, `change-documentation-gate`, `agent-execution-discipline`, and `skill-authoring-expert` should arrive here when execution order changes read, review, validation, repair, memory, graph, fixture, or closure obligations. Route away when the primary need is raw source graphing, validation command brokering, memory projection, failure diagnosis, or code review without an ordering signal.

# Quality Gate
1. Trajectory is bounded and excludes raw prompts, secrets, personal data, environment variables, credentials, and full command output.
2. Stage transitions are checked against allowed workflow movement and route/stage requirements.
3. Edit-before-read, skipped-stage, repair-without-re-review, repeated-failure, and stale-validation signals are evaluated when present.
4. Validation freshness timeline covers final material source, registry, hook runtime, generated artifact, report, benchmark, package, or install-output edits.
5. Candidate fixtures are labeled structural/candidate until privacy review and explicit eval authoring promote them.
6. Coupling verdict reconciles graph/context freshness, memory signals, validation broker results, review findings, and final handoff claims.
7. Every trajectory finding maps to repair, re-review, validation, owner response, blocked handoff, or residual risk.
8. Handoff states inspected evidence, unknowns, validation limits, rollback note, and next owner.

# Used By
`change-forge-router`, `quality-test-gate`, `ai-code-review-refactor`, `change-documentation-gate`, `agent-execution-discipline`, `skill-authoring-expert`.

# Handoff
Hand off trajectory findings to the reviewer, validator, stage owner, or maintainer with source evidence requirements and explicit limits. Hand off fixture candidates through project memory governance or explicit eval authoring review; do not promote them automatically.

# Completion Criteria
The capability is complete when execution events are bounded and ordered, illegal transitions are named, edit-before-read and repeated-failure gates are handled, repair/re-review status is current, validation freshness covers final material edits, graph/memory/validation coupling is reconciled, candidate fixtures are privacy-reviewed or deferred, and residual risk is explicit.
