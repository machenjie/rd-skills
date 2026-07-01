---
name: engineering-stage-professionalism
description: Stage launcher capability for stage-by-stage execution of a code or product change. Use when deciding the current engineering stage, product surface, language surface, and risk surface, which minimum professional capabilities to launch versus skip, the context budget, and the next-stage handoff. Not for loading every capability at once.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "104"
changeforge_version: 0.1.0
---

# Mission

Launch professional capability by engineering stage. Decide which stage a change is in, which product surface and language surface it touches, and which risks apply, then launch only the minimum sufficient capabilities for that stage. Explicitly skip heavy out-of-stage capabilities, declare a context budget, and name the next-stage handoff. This capability is a launcher, not a checklist owner: the stage model registry is canonical, this body carries routing and gates, and [references/stage-launch-matrix.md](references/stage-launch-matrix.md) carries deeper launch/evidence detail.

# When To Use

Use for any non-trivial change that involves design, implementation planning, coding, debugging, bug-fix, code review, refactoring, testing, release, documentation handoff, or skill authoring, when the request does not already declare which stage is active and which capabilities should launch. Use before doing the work, and again when the active stage changes.

# Do Not Use When

- Do not use for a single trivial edit whose stage and capability are already obvious.
- Do not use as a replacement for `change-forge-router`; the router selects the path, this capability sequences professional launch within it.
- Do not use to launch every relevant capability; that defeats the stage budget.
- Do not use to copy the stage, product, or language matrices into other skills.

# Non-Negotiable Rules

1. **Stage first.** Decide the current engineering stage before launching any capability.
2. **Mapped launch.** Every launched capability maps to the current stage, product surface, language surface, or a named risk trigger.
3. **Explicit skip.** Every heavy capability not launched this stage is recorded with a skip reason.
4. **Stage-by-stage execution.** A cross-stage task is split; it does not load all stages' capabilities at once.
5. **Requirement intake precedes engineering action.** For target-project engineering prompts, requirement-intake runs before implementation-planning or coding unless the prompt already provides current behavior, desired behavior, non-goals, constraints, and testable acceptance.
6. **Read before implementation planning.** Implementation-planning cannot start until relevant target-project code, tests, configs, docs, existing implementation, conventions, and likely call chain have been inspected or the plan is explicitly non-executing with not-inspected risk.
7. **TDD signal before coding.** Coding cannot start until inspected boundaries and a failing/new/updated test, eval, validation command, acceptance check, or not-verified residual risk are named.
8. **Independent review by stage.** Code-review and action review must be performed by a review skill or capability different from the action owner.
9. **Repair/re-review closes review.** Review findings route back to the owner skill or a specialist for repair, then return to review before the stage can advance.
10. **No default coding deep review.** The coding stage does not launch architecture deep review by default.
11. **No default release gate at review.** The code-review stage does not launch the release gate by default.
12. **No default refactor at debugging.** The debugging-diagnosis stage launches refactoring only when the verified root cause requires structural change.
13. **No default language deep checks at release.** The release-delivery stage does not launch language deep checks unless code still changes.
14. **No default coding at documentation.** The documentation-handoff stage launches coding capabilities only when docs contain API or code examples.
15. **Skill-authoring uses its owner.** The skill-authoring stage always launches `skill-authoring-expert`.
16. **Senior judgment is conditional and evidence-bound.** Launch `senior-programming-judgment-core` when non-trivial engineering work affects behavior, object relationships, state/rule/invariant constraints, boundaries, failure contract, side effects, validation map, observability, or residual risk; skip it only with an explicit trivial/no-semantic/no-engineering rationale.

# Stage Fit

Use this capability to launch the current stage only. If the request spans multiple stages, record the current stage, required evidence, and next-stage handoff rather than loading every stage at once.

- Start only capabilities needed by the active stage, product surface, language surface, or explicit risk trigger.
- Do not cross into heavy out-of-stage capabilities unless current evidence shows their trigger; record the skipped capability and reason.
- Name transition evidence, next gate, stage conflict, graph/memory freshness limit, and skip rationale before handoff.

# Industry Benchmarks

Anchor against phase-gate engineering review, trunk-based delivery, context engineering, risk-based testing, definition-of-ready/done, workflow state machines, validation freshness, and decision-record handoff boundaries. Keep this body focused on selection and closure; load [references/stage-launch-matrix.md](references/stage-launch-matrix.md) for detailed launch/evidence/transition matrices and [references/checklist.md](references/checklist.md) for a compact operator checklist.

# Selection Rules

Map the stage to its launch set using the stage model registry as source of truth. Launch only the matching current-stage, product-surface, language-surface, and risk-trigger capabilities; defer out-of-stage architecture, coding, testing, release, and documentation gates with explicit reasons.

Compact current-stage default launch summary:

| Stage | Default capabilities |
| --- | --- |
| requirement-intake | `requirement-clarification`, `requirement-structuring`, `non-goal-boundary-definition`, `acceptance-standard-definition`, `scenario-decomposition` |
| architecture-design | `architecture-style-selection`, `module-boundary-design`, `layered-architecture-design`, `architecture-tradeoff-analysis`, `extensibility-design`, `solution-optimality-evaluation` |
| implementation-planning | `repository-context-map`, `implementation-structure-design`, `module-boundary-design`, `code-clarity-maintainability`, `language-idiom-enforcement` |
| coding | `language-idiom-enforcement`, `input-validation`, `logging-error-handling` |
| debugging-diagnosis | `failure-diagnosis`, `agent-execution-discipline`, `observability` |
| bug-fix | `agent-execution-discipline`, `regression-testing`, `code-review` |
| code-review | `code-review`, `plan-execution-consistency`, `implementation-structure-design`, `code-clarity-maintainability`, `language-idiom-enforcement` |
| refactoring | `refactoring`, `implementation-structure-design`, `code-clarity-maintainability`, `code-review`, `regression-testing` |
| testing | `test-strategy`, `plan-execution-consistency`, `language-testing-strategy`, `test-data-management` |
| release-delivery | `ci-cd`, `release-rollback`, `containerization`, `kubernetes-gateway`, `observability`, `backup-recovery` |
| documentation-handoff | `agent-workflow-state-machine`, `plan-execution-consistency`, `documentation-generation`, `agent-execution-discipline` |
| skill-authoring | `repository-context-map`, `skill-authoring-expert`, `skill-efficacy-benchmark`, `documentation-generation`, `agent-execution-discipline`, `plan-execution-consistency` |

Use [references/stage-launch-matrix.md](references/stage-launch-matrix.md) for the human-readable launch matrix, including conditional senior judgment launch rules for requirement-intake, architecture-design, debugging-diagnosis, implementation-planning, coding, and skill-authoring. Pair with `change-forge-router` for the overall path, `agent-workflow-state-machine` for legal transitions, and `agent-execution-discipline` for evidence and handoff discipline.

# Professional Evidence By Stage

Each stage has a minimum handoff obligation: requirement clarity, inspected boundaries, owner/reviewer split, selected/skipped capability rationale, validation signal, evidence freshness, behavior preservation, residual risk, and next gate. Load [references/stage-launch-matrix.md](references/stage-launch-matrix.md) for the stage-by-stage evidence table.

# Stage Transition Rules

Stage transitions require the entry evidence for the next stage and the exit evidence for the current one. Move forward only after blocking requirement questions, source inspection, reuse/placement, TDD or validation signal, owner/reviewer split, repair/re-review, proof limits, and residual risk are explicit. If graph, memory, or validation freshness is stale, route back to read, repair, validation, or review instead of advancing.

# Risk Escalation Rules

- Escalate to `security-privacy-gate` when the stage touches auth, secrets, input trust boundary, or data exposure.
- Escalate to `reliability-observability-gate` when the stage touches production behavior, performance, or cost.
- Escalate to `delivery-release-gate` when code or config reaches a rollout path.
- Escalate to `architecture-impact-reviewer` when an implementation or refactor stage shifts module boundaries or dependency direction.
- Escalate to `failure-diagnosis` when a third same-path retry is attempted; force a stage and route change.
- Escalate to `senior-programming-judgment-core` when a stage needs explicit purpose, source-backed facts, objects, states, behaviors, rules, invariants, boundaries, failure contract, side effects, reuse/placement, minimality, validation, observability, and residual-risk evidence.

# Proactive Professional Triggers

- **Signal:** Route or plan starts coding, testing, release, or documentation without exactly one current stage.
  **Hidden risk:** Out-of-stage capabilities hide missing entry evidence and skipped gates.
  **Required professional action:** Require a stage launch plan before implementation or closure.
  **Route to:** `agent-workflow-state-machine`, `agent-execution-discipline`.
  **Evidence required:** current stage, selected/skipped capability map, context budget, transition condition, stage manifest.
- **Signal:** Implementation-planning or coding begins before source, tests, configs, docs, callers, or generated artifacts are inspected.
  **Hidden risk:** Prompt-only planning creates wrong placement, duplicate helpers, or stale validation assumptions.
  **Required professional action:** Inspect current source and verify reuse, placement, and validation before advancing.
  **Route to:** `repository-context-map`, `repository-graph-analysis`, `implementation-structure-design`.
  **Evidence required:** inspected paths, search scope, reuse ladder, rejected locations, validator map.
- **Signal:** Project memory, repository graph, compaction summary, or prior validation is used as current proof.
  **Hidden risk:** Stale context selects the wrong stage or marks stale evidence ready.
  **Required professional action:** Downgrade to selector-only, compare with current source, and rerun stale validators.
  **Route to:** `project-memory-governance`, `execution-trajectory-analysis`, `validation-broker`.
  **Evidence required:** accepted/rejected memory or graph claim, freshness comparison, command/report path, residual owner.
- **Signal:** A non-trivial stage proceeds with code shape, prose intent, or local validation but no senior judgment evidence.
  **Hidden risk:** The stage can advance while source-backed facts, object relationships, state/rule invariants, side effects, failure behavior, validation proof, observability, or residual risk remain unexamined.
  **Required professional action:** Launch `senior-programming-judgment-core` or record an allowed trivial/no-semantic/no-engineering skip reason.
  **Route to:** `senior-programming-judgment-core`, `implementation-structure-design`, `quality-test-gate`.
  **Evidence required:** `senior_programming_judgment` summary or explicit skip reason, selected specialist handoffs, validation map, proof limits, residual risk.

# Critical Details

- A stage is identified by the action being performed, not by the artifact type alone: editing a file during a bug-fix is the bug-fix stage, not the coding stage.
- The launch set is additive per active stage only; previously launched stages are not kept loaded once their evidence is produced and handed off.
- Skip rationale is part of the output, not a silent omission. "Skipped: release gate (no rollout in this change)" is valid; dropping the gate silently is not.
- The context budget decision is explicit: `minimal` for L1, `single-stage` for L2, `staged-plan` for L3+ where planning spans stages but execution stays staged.
- The canonical machine-readable launch matrix lives in the stage model registry. This body keeps only runtime routing rules, and validators reject drift between them. Per-language deep checklists stay in the language professional usage capability bodies.
- `code-element-professionalism` launches conditionally when evidence mentions variable, expression, statement, default, cleanup, fallthrough, boolean trap, side-effect getter, or event-order hazards.
- Mode Matrix sections in professional skills refine the active stage: for example, backend `bug-fix` selects bug-fix stage evidence, while backend `performance/reliability fix` stays in coding, debugging, or release depending on whether the work is implementation, diagnosis, or rollout.
- Anti-pattern examples that must be rejected: loading architecture, coding, testing, and release gates for one local patch; running release-delivery during review because a deployment might happen later; loading all language capabilities for a config-only release; keeping debugging references loaded after root cause has been handed to bug-fix.

# Stage-Specific Hidden Risks

Hidden risks include missing reuse/placement evidence, local success hiding contract or release-skew risk, symptom patching without cause, sibling same-pattern defects, review drifting into implementation, habitual tests missing the real risk, and rollback invalidated by migration/config state. Use [references/stage-launch-matrix.md](references/stage-launch-matrix.md) for stage-specific risk detail.

# Failure Modes

- Loading every relevant capability at once, bloating context and hiding the next action.
- Skipping a heavy capability without recording a reason, so a needed gate is silently lost.
- Treating a cross-stage task as one step and launching design, coding, testing, and release capabilities together.
- Launching architecture deep review during coding, or the release gate during code review.
- Launching refactoring during debugging before a verified root cause exists.
- Copying the stage, product, or language matrix into multiple skill bodies, creating drift.
- Failing to re-run when the active stage changes, so the launch set no longer matches the work.

# Reference Loading Policy

The `SKILL.md` body carries L1/L2 stage selection, launch, output, and closure rules. Load [references/checklist.md](references/checklist.md) for quick stage-launch review. Load [references/stage-launch-matrix.md](references/stage-launch-matrix.md) when the launch set, evidence obligation, transition, skipped-heavy rationale, graph/memory/execution coupling, or stage-specific risk needs detail. Do not load deep references for trivial single-stage edits where the stage, launch set, and validation signal are already explicit.

# Output Contract

Return a **Stage Professional Launch Plan**:

- Current engineering stage:
- Next engineering stage:
- Product surface:
- Language surface:
- Selected professional skills:
- Selected foundation capabilities:
- Selected domain extensions:
- Explicitly skipped capabilities:
- Skip rationale:
- Context budget decision:
- Senior programming judgment:
- Required evidence:
- Required quality gates:
- Stage transition condition:
- Stage selection evidence:
- Stage conflicts ruled out:
- Graph/memory/execution freshness:
- Validation evidence and proof limits:
- Residual risk and rollback note:
- Handoff target:

Each selected capability must cite its stage, product surface, language surface, or risk trigger. Each skipped heavy capability must cite a skip rationale. The context budget decision must be one of `minimal`, `single-stage`, or `staged-plan`. The plan must include active-stage evidence, graph/memory/execution freshness, validation proof limits, residual risk, and the transition condition for the next stage.

# Evidence Contract

Close a stage launch only when the plan states:

- `current_stage` and the stage evidence that selected it.
- Selected capabilities and the stage, product, language, or risk trigger for each.
- Skipped heavy capabilities with a concrete reason.
- Boundaries inspected: product surface, language surface, risk surface, source files, callers, docs, configs, validators, and generated artifacts relevant to this stage.
- Reuse and placement rationale: why the selected stage owner and capabilities are the minimum sufficient launch set and why skipped stages are deferred.
- Senior programming judgment: complete `senior_programming_judgment` record or an allowed skip reason for trivial/no-semantic/no-engineering work.
- Behavior preservation: old runtime profile, routing, skill, registry, docs, and source/dist behavior preserved or intentionally changed.
- Repository context dependency: inspected files, callers, docs, configs, validators, generated artifacts, graph/memory claims, or accepted not-inspected risk.
- Validation freshness: commands or review artifacts, exit code when available, whether files changed after evidence, and what the evidence proves/does not prove.
- Next-stage handoff: next gate, owner, and transition condition.

# Quality Gate

1. The current engineering stage is named before any capability is launched.
2. Every selected capability maps to the stage, product surface, language surface, or a risk trigger.
3. Every skipped heavy capability has a recorded skip rationale.
4. The context budget decision is present and consistent with the change level.
5. Required evidence and required quality gates are listed for the active stage.
6. The handoff target names the next stage or a blocking owner.
7. No stage, product, or language matrix is copied into this plan; it is referenced.
8. Stage transition conditions are explicit; no cross-stage bundle is used as a substitute for handoff.
9. Senior programming judgment is launched or explicitly skipped with rationale when non-trivial engineering behavior is present.

# Used By

Route-level capability. It may be selected whenever a `changeforge_stage_route`
manifest is emitted, even if the stage owner is not one of the selected
professional skills.

- change-forge-router

# Handoff

Hand off to `change-forge-router` when the active stage changes; `implementation-structure-design` for placement/reuse; `failure-diagnosis` for verified cause; `quality-test-gate` for test evidence; `delivery-release-gate` for rollout/rollback; `change-documentation-gate` for docs boundary; and `skill-authoring-expert` for skill, capability, reference, registry, and routing changes.

# Completion Criteria

This capability is complete when an agent can name the current engineering stage, launch only the minimum sufficient capabilities for that stage, record skipped heavy capabilities and reasons, declare a context budget, list required evidence and quality gates, reconcile graph/memory/execution freshness, and name the next-stage handoff without loading every capability at once or copying stage matrices.
