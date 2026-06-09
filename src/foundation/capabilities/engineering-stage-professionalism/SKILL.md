---
name: engineering-stage-professionalism
description: Stage launcher capability that decides the current engineering stage, product surface, language surface, and risk surface, then launches only the minimum professional capabilities that stage needs, explicitly skips heavy out-of-stage capabilities, sets a context budget, and names the next-stage handoff. Use to plan stage-by-stage execution of a code or product change, not to load every capability at once.
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
5. **No default coding deep review.** The coding stage does not launch architecture deep review by default.
6. **No default release gate at review.** The code-review stage does not launch the release gate by default.
7. **No default refactor at debugging.** The debugging-diagnosis stage launches refactoring only when the verified root cause requires structural change.
8. **No default language deep checks at release.** The release-delivery stage does not launch language deep checks unless code still changes.
9. **No default coding at documentation.** The documentation-handoff stage launches coding capabilities only when docs contain API or code examples.
10. **Skill-authoring uses its owner.** The skill-authoring stage always launches `skill-authoring-expert`.

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
| requirement-intake | `requirement-clarification`, `acceptance-standard-definition`, `non-goal-boundary-definition` | coding, language, testing |
| architecture-design | `architecture-style-selection`, `module-boundary-design`, `solution-optimality-evaluation` | language idiom, coding |
| implementation-planning | `implementation-structure-design`, `module-boundary-design`, `code-clarity-maintainability` | full architecture review, release |
| coding | language professional usage, `language-idiom-enforcement`, `input-validation` | architecture deep review, release |
| debugging-diagnosis | `failure-diagnosis`, `agent-execution-discipline`, `observability` | refactoring, new design |
| bug-fix | `agent-execution-discipline`, `regression-testing`, `code-review` | architecture redesign |
| code-review | `code-review`, `implementation-structure-design`, `code-clarity-maintainability`, `ai-code-review-refactor` | release, deployment |
| refactoring | `refactoring`, `implementation-structure-design`, `code-clarity-maintainability`, `regression-testing` | feature design, release |
| testing | `test-strategy`, `language-testing-strategy`, matching test capability | new feature coding |
| release-delivery | `ci-cd`, `release-rollback`, `observability` | language deep checks |
| documentation-handoff | `documentation-generation`, `agent-execution-discipline` | coding capabilities |
| skill-authoring | `skill-authoring-expert` | product coding, release |

Select the product surface and language surface for the change, and launch only the
matching professional skill and capabilities. Pair with `change-forge-router` for the overall
path and `agent-execution-discipline` for evidence and handoff discipline.

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
- This capability keeps a compact launch matrix in its own body; it does not copy or depend on an external matrix file. Per-language deep checklists stay in the language professional usage capability bodies.

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
- Handoff target:

Each selected capability must cite its stage, product surface, language surface, or risk
trigger. Each skipped heavy capability must cite a skip rationale. The context budget decision
must be one of `minimal`, `single-stage`, or `staged-plan`.

# Quality Gate

1. The current engineering stage is named before any capability is launched.
2. Every selected capability maps to the stage, product surface, language surface, or a risk trigger.
3. Every skipped heavy capability has a recorded skip rationale.
4. The context budget decision is present and consistent with the change level.
5. Required evidence and required quality gates are listed for the active stage.
6. The handoff target names the next stage or a blocking owner.
7. No stage, product, or language matrix is copied into this plan; it is referenced.

# Used By

- change-forge-router
- backend-change-builder
- frontend-change-builder
- data-api-contract-changer
- architecture-impact-reviewer
- ai-code-review-refactor
- quality-test-gate
- delivery-release-gate

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
