---
name: engineering-stage-professionalism
description: Stage launcher capability for stage-by-stage execution of a code or product change. Use when deciding the current engineering stage, product surface, language surface, and risk surface, which minimum professional capabilities to launch versus skip, the context budget, and the next-stage handoff. Not for loading every capability at once.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "104"
changeforge_version: 0.1.0
---

# Mission

Launch professional capability by engineering stage. Decide which stage a change is in,
which product surface and language surface it touches, and which risks apply, then launch only
the minimum sufficient capabilities for that stage. Explicitly skip heavy out-of-stage
capabilities, declare a context budget, and name the next-stage handoff. This capability is a
launcher, not a checklist owner: the compact launch matrix below is the runtime reference, and
the deep per-stage, per-surface, and per-language detail lives in the owning professional skills
and capability bodies, not here.

# When To Use

Use for any non-trivial change that involves design, implementation planning, coding,
debugging, bug-fix, code review, refactoring, testing, release, documentation handoff, or skill
authoring, when the request does not already declare which stage is active and which
capabilities should launch. Use before doing the work, and again when the active stage changes.

# Do Not Use When

- Do not use for a single trivial edit whose stage and capability are already obvious.
- Do not use as a replacement for `change-forge-router`; the router selects the path, this
  capability sequences professional launch within it.
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

# Industry Benchmarks

- Phase-gate and stage-gate engineering review.
- Trunk-based delivery with progressive risk gates.
- Context engineering and retrieval precision (load the minimum sufficient context).
- Risk-based testing and review depth.
- Definition-of-ready and definition-of-done per stage.
- Decision-record discipline for handoff boundaries.

# Selection Rules

Map the stage to its launch set using the compact matrix below:

| Stage | Launch focus | Skip by default |
| --- | --- | --- |
| requirement-intake | `requirement-clarification`, `requirement-structuring`, `non-goal-boundary-definition`, `acceptance-standard-definition`, `scenario-decomposition` | coding, language, testing, refactoring, release |
| architecture-design | `architecture-style-selection`, `module-boundary-design`, `layered-architecture-design`, `architecture-tradeoff-analysis`, `extensibility-design`, `solution-optimality-evaluation` | language idiom, coding, test authoring |
| implementation-planning | `repository-context-map`, `implementation-structure-design`, `module-boundary-design`, `code-clarity-maintainability`, `language-idiom-enforcement` | full architecture review, release, deep performance profiling |
| coding | matching language professional usage capability, `language-idiom-enforcement`, `input-validation`, `logging-error-handling` | architecture deep review, release, full regression suite design |
| debugging-diagnosis | `failure-diagnosis`, `agent-execution-discipline`, `observability` | refactoring, new design |
| bug-fix | `agent-execution-discipline`, `regression-testing`, `code-review`; add `minimal-correct-implementation` only for minimal fix, delete/shrink, dependency, abstraction, wrapper-only delegation, shortcut, or overengineering signals | architecture redesign |
| code-review | `code-review`, `plan-execution-consistency`, `implementation-structure-design`, `code-clarity-maintainability`, `language-idiom-enforcement`; add `minimal-correct-implementation` only for complexity/delete/shrink/dependency/abstraction/wrapper/shortcut signals; add `ai-code-review-refactor` as the professional owner for generated code | release, deployment, infrastructure |
| refactoring | `refactoring`, `implementation-structure-design`, `code-clarity-maintainability`, `code-review`, `regression-testing` | feature design, release |
| testing | `test-strategy`, `plan-execution-consistency`, `language-testing-strategy`, `test-data-management`, matching test capability | architecture redesign, new feature coding |
| release-delivery | `ci-cd`, `release-rollback`, `containerization`, `kubernetes-gateway`, `observability`, `backup-recovery` | language deep checks, coding |
| documentation-handoff | `agent-workflow-state-machine`, `plan-execution-consistency`, `documentation-generation`, `agent-execution-discipline` | coding capabilities |
| skill-authoring | `repository-context-map`, `skill-authoring-expert`, `skill-efficacy-benchmark`, `documentation-generation`, `agent-execution-discipline`, `plan-execution-consistency` | product coding, language runtime, release |

Select the product surface and language surface for the change, and launch only the
matching professional skill and capabilities. Pair with `change-forge-router` for the overall
path and `agent-execution-discipline` for evidence and handoff discipline.

# Professional Evidence By Stage

Each stage has a minimum evidence obligation before handoff:

| Stage | Professional evidence required |
| --- | --- |
| requirement-intake | current behavior, desired behavior, non-goals, constraints, assumptions, open questions, and testable completion signal. |
| architecture-design | affected boundaries, dependency direction, ownership, simpler alternative, tradeoff, and rollback implication. |
| implementation-planning | inspected target-project boundaries, reuse ladder, placement rationale, touched files, validation commands, and split/sequence decision. |
| coding | inspected local convention, selected capabilities, changed boundary, TDD or validation signal, tests or validators run, and residual risk. |
| debugging-diagnosis | symptom, hypothesis tested, method, verified cause, counter-evidence, and no same-path third retry. |
| bug-fix | verified cause, same-pattern scan, regression proof, old behavior preservation, and local/broad fix rationale. |
| code-review | independent review owner, severity-classified findings, boundary inspected, missing evidence, behavior-change risk, required fix owner, and re-review result when repaired. |
| refactoring | before/after behavior preservation, affected callers, deletion path, placement decision, and regression evidence. |
| testing | risk-based test level, fixture/data owner, what the test proves, what it does not prove, and flaky-risk note. |
| release-delivery | rollout plan, rollback path, config/migration compatibility, monitoring signal, and owner acceptance. |
| documentation-handoff | affected artifacts, no-change rationales, validation/link checks, residual doc risk, and owner. |
| skill-authoring | source body/reference boundary, registry impact, validators/evals run, and no runtime architecture drift. |

# Stage Transition Rules

- Move from diagnosis to bug-fix only after a verified cause exists or the next action is a reversible instrumentation change.
- Move from requirement-intake to implementation-planning only after blocking requirement questions are resolved or the plan records explicit assumptions and residual risk.
- Move from implementation-planning to coding only after target-project evidence is inspected and reuse, placement, validation, and skipped heavy capabilities are named.
- Move from coding to testing only after the changed behavior and residual risk are explicit; tests are then selected by risk, not by habit.
- Move from coding to code-review only with a review owner different from the action owner.
- Move from code-review to refactoring or bug-fix only when findings name a repair owner; move from code-review to documentation-handoff only after repaired findings have been re-reviewed or residual risk is explicitly accepted.
- Move from testing to release-delivery only when the test result states what it proves, what it does not prove, and which release risk remains.
- Move from release-delivery to documentation-handoff when rollout, rollback, migration, config, or operational behavior changes reader obligations.

# Risk Escalation Rules

- Escalate to `security-privacy-gate` when the stage touches auth, secrets, input trust boundary, or data exposure.
- Escalate to `reliability-observability-gate` when the stage touches production behavior, performance, or cost.
- Escalate to `delivery-release-gate` when code or config reaches a rollout path.
- Escalate to `architecture-impact-reviewer` when an implementation or refactor stage shifts module boundaries or dependency direction.
- Escalate to `failure-diagnosis` when a third same-path retry is attempted; force a stage and route change.

# Critical Details

- A stage is identified by the action being performed, not by the artifact type alone: editing a file during a bug-fix is the bug-fix stage, not the coding stage.
- The launch set is additive per active stage only; previously launched stages are not kept loaded once their evidence is produced and handed off.
- Skip rationale is part of the output, not a silent omission. "Skipped: release gate (no rollout in this change)" is valid; dropping the gate silently is not.
- The context budget decision is explicit: `minimal` for L1, `single-stage` for L2, `staged-plan` for L3+ where planning spans stages but execution stays staged.
- The canonical machine-readable launch matrix lives in the stage model registry. This body keeps only a compact runtime summary, and validators reject drift between them. Per-language deep checklists stay in the language professional usage capability bodies.
- Mode Matrix sections in professional skills refine the active stage: for example, backend `bug-fix` selects bug-fix stage evidence, while backend `performance/reliability fix` stays in coding, debugging, or release depending on whether the work is implementation, diagnosis, or rollout.
- Anti-pattern examples that must be rejected: loading architecture, coding, testing, and release gates for one local patch; running release-delivery during review because a deployment might happen later; loading all language capabilities for a config-only release; keeping debugging references loaded after root cause has been handed to bug-fix.

# Stage-Specific Hidden Risks

- **Implementation-planning:** missing reuse/placement evidence creates new helpers, public exports, or directories before ownership is known.
- **Coding:** local code success can hide contract, tenant, transaction, retry, or release-skew risks selected by the active professional skill.
- **Debugging-diagnosis:** symptom patching and same-path retry can produce a plausible diff without a verified cause.
- **Bug-fix:** one local fix can leave the same defect pattern in sibling modules unless the same-pattern scan is recorded.
- **Code-review:** review can drift into implementation or release planning before severity-classified findings and evidence gaps are named.
- **Testing:** adding tests by habit can miss the risk that matters, such as contract compatibility, regression proof, fixture ownership, or negative cases.
- **Release-delivery:** deploy rollback can be invalid when migrations, feature flags, old/new versions, or config defaults changed state.

# Failure Modes

- Loading every relevant capability at once, bloating context and hiding the next action.
- Skipping a heavy capability without recording a reason, so a needed gate is silently lost.
- Treating a cross-stage task as one step and launching design, coding, testing, and release capabilities together.
- Launching architecture deep review during coding, or the release gate during code review.
- Launching refactoring during debugging before a verified root cause exists.
- Copying the stage, product, or language matrix into multiple skill bodies, creating drift.
- Failing to re-run when the active stage changes, so the launch set no longer matches the work.

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
- Required evidence:
- Required quality gates:
- Stage transition condition:
- Stage selection evidence:
- Stage conflicts ruled out:
- Handoff target:

Each selected capability must cite its stage, product surface, language surface, or risk
trigger. Each skipped heavy capability must cite a skip rationale. The context budget decision
must be one of `minimal`, `single-stage`, or `staged-plan`. The plan must include the
professional evidence required for the active stage and the transition condition for the next
stage.

# Evidence Contract

Close a stage launch only when the plan states the **mode selected** as current
engineering stage, the product/language/risk boundaries inspected, the professional judgment
behind selected versus skipped capabilities, the validation evidence required for this stage,
validation commands or review artifacts with exit code when available, what that evidence proves
and does not prove, residual risk, and the next gate or handoff.

# Quality Gate

1. The current engineering stage is named before any capability is launched.
2. Every selected capability maps to the stage, product surface, language surface, or a risk trigger.
3. Every skipped heavy capability has a recorded skip rationale.
4. The context budget decision is present and consistent with the change level.
5. Required evidence and required quality gates are listed for the active stage.
6. The handoff target names the next stage or a blocking owner.
7. No stage, product, or language matrix is copied into this plan; it is referenced.
8. Stage transition conditions are explicit; no cross-stage bundle is used as a substitute for handoff.

# Used By

Route-level capability. It may be selected whenever a `changeforge_stage_route`
manifest is emitted, even if the stage owner is not one of the selected
professional skills.

- change-forge-router

# Handoff

- `change-forge-router`: re-routing and stage re-evaluation when the active stage changes.
- `implementation-structure-design`: placement and reuse decisions during implementation-planning.
- `failure-diagnosis`: verified root cause during debugging-diagnosis.
- `quality-test-gate`: risk-based test evidence during testing.
- `delivery-release-gate`: rollout, rollback, and config compatibility during release-delivery.
- `change-documentation-gate`: change boundary and residual risk during documentation-handoff.
- `skill-authoring-expert`: skill, capability, reference, registry, and routing changes.

# Completion Criteria

This capability is complete when an agent can name the current engineering stage, launch only
the minimum sufficient professional capabilities for that stage, record the heavy capabilities
it skipped and why, declare a context budget, list required evidence and quality gates, and name
the next-stage handoff, without loading every capability at once or copying the stage matrices.
