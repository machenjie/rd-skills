---
name: agent-execution-discipline
description: Use when an AI or agent changes, diagnoses, validates, reviews, deploys, or hands off code or skill work; enforces evidence-based completion, verified cause, route repair, same-pattern scans, reuse/placement rationale, and residual-risk closure.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "102"
changeforge_version: 0.1.0
---

# Mission

Constrain agent-assisted execution so that every completion claim has fresh evidence, every diagnosis has a verified cause, every repeated failure changes route, every local fix has a same-pattern scan, every new structure has reuse and placement rationale, and every handoff states boundary, validation result, residual risk, and next owner. Couple skill selection, project memory, repository graph, validation broker output, and execution trajectory without adding personal corpus mapping, entertainment rhetoric, user-shaming, or runtime PUA-style state.

# When To Use

Use when an AI or agent is producing, modifying, diagnosing, validating, reviewing, releasing, or handing off non-trivial work, especially:

- Code generation, refactor, patch authoring, or skill-authoring changes.
- Bug investigation, failure triage, root-cause analysis, or repair after failed validation.
- Release, migration, rollback, connector, or destructive filesystem actions.
- Multi-step execution where the agent says done, fixed, ready, verified, blocked, or hands work to another skill or human.

# Do Not Use When

Do not launch for trivial L1 changes such as README typos, copy-only label edits, comment-only cleanup, or single literal text changes with no behavior, dependency, test, registry, or release impact.

Do not use this capability to add narrative status, persona styling, emoji progress lines, persistent mood/score state, personal archive ingestion, private archive mappings, or user-specific runtime content. It is a behavior constraint and report kernel.

# Stage Fit

- **read / intake:** requirement clarification, repository context, memory and graph signal, proceed/block decision.
- **plan / edit:** TDD or validation signal before implementation, owner/reviewer split, reuse and placement rationale.
- **debugging / bug-fix:** verified cause, same-pattern scan, route repair after two same-path failures.
- **test / review / release:** validation broker freshness, evidence limits, repair/re-review, rollback or release boundary.
- **handoff:** boundary, residual risk, route manifest, next gate, unsupported adapter limits.

# Mode Matrix

| Stage mode | Trigger signals | Professional focus | Required evidence | Companion capabilities / gates | Skip guidance |
| --- | --- | --- | --- | --- | --- |
| Read/intake | Target-project engineering request has code, skill, registry, hook, or release impact | Clarify requirement, non-goals, assumptions, repository graph, and project memory before plan | Requirement ledger, inspected paths, caller/callee or registry map, proceed/block decision | `change-intake-compiler`, `repository-context-map`, `project-memory-governance` | Skip only for no-action explanation or typo-only work with no behavior impact |
| Plan/edit | Agent will mutate code, skill content, generated artifacts, configs, tests, or docs | Name validation signal, owner skill, review skill, reuse ladder, placement decision, and behavior preservation | Planned command, accepted boundary, reuse/placement rationale, old/new behavior coverage | `implementation-structure-design`, `quality-test-gate`, `ai-code-review-refactor` | Defer edit until target files and conventions were inspected |
| Debug/repair | Failure, bug, flaky claim, or repeated failed command appears | Verify cause, compare counter-evidence, change route after two same-path failures | Symptom trace, tested hypothesis, exact cause, route repair ledger, new hypothesis | `failure-diagnosis`, `execution-trajectory-analysis` | Do not diagnose from speculation or retry the same path a third time |
| Local fix | One occurrence of a query, permission, cache, schema, or state defect is patched | Scan repository graph and decide all/subset/local-only coverage | Pattern signature, search scope, other occurrences, rationale, regression output | `change-impact-analyzer`, `regression-testing` | Skip closure until scan result is recorded |
| Validation/handoff | Agent claims done, fixed, green, ready, complete, or transfers ownership | Prove freshness, scope alignment, evidence limits, independent review, residual risk, and route manifest | Command, exit code, report/artifact, what evidence proves and does not prove, next owner | `validation-broker`, `plan-execution-consistency`, `quality-test-gate` | Treat stale, partial, failed, or no-outcome validation as partial or not verified |

# Non-Negotiable Rules

- **Evidence-based completion:** no done/fixed/ready claim without fresh command output, validator result, artifact, screenshot, fixture diff, or measured result from the current change.
- **Requirement and repository context first:** before target-project engineering action, record current behavior, desired behavior, non-goals, constraints, acceptance/TDD signal, assumptions, proceed/block status, inspected source, tests, configs, docs, call chain, conventions, generated artifacts, memory, and graph boundaries.
- **Workflow state across transitions:** before read-to-plan, plan-to-edit, edit-to-test, test-to-review, repair-to-re-review, and review-to-handoff, record current phase, allowed next phase, owner skill, reviewer skill, validation freshness, open findings, and closure readiness.
- **Tool and sandbox record:** risky shell, connector, MCP, migration, deploy, network write, destructive filesystem, secret-bearing, or untrusted-output action records permission state, sandbox boundary, dry-run or revert path, and redaction rule.
- **Validation signal before edit:** behavior changes name the failing, new, or updated test, eval, validator, acceptance check, or explicit not-verified residual risk before implementation.
- **Independent review and repair:** each non-trivial action names different owner/reviewer skills; findings route back to owner or specialist, then re-run review or become explicit residual risk.
- **Broker freshness and partial verification:** Validation Broker output counts only with command level, outcome, coverage alignment, and post-edit freshness; lint is not build, one unit test is not integration, manual inspection is not regression, and stale evidence is not current evidence.
- **Verified-cause diagnosis:** diagnoses name symptom, tested hypothesis, method, concrete cause, and counter-evidence; environment or flakiness guesses are not diagnosis.
- **Route repair:** after two failures of the same command, patch shape, or hypothesis, stop and choose a new route: reread output, inspect call site, shrink scope, or escalate.
- **Same-pattern scan:** local bug fixes record pattern signature, scan scope, other occurrences, and all/subset/local-only decision.
- **Reuse, placement, behavior, and comments:** new or changed structure requires convention scan, reuse ladder, owner, dependency direction, placement decision, old behavior preservation, new behavior coverage, and necessary comments.
- **Proactive closure:** handoff states change boundary, validation results, residual risks, next owner, and `changeforge_route` / `changeforge_stage_route` when routed.

# Industry Benchmarks

Google SRE, NASA ten rules, Toyota five whys, OWASP ASVS/SAMM, DORA, DDD, and Clean Architecture all point to the same execution bar: verified cause, changed input after failure, explicit evidence artifacts, same-pattern control, ownership, public/private API boundaries, and internal dependency direction.

# Selection Rules

Select this capability when:

- A professional skill performs non-trivial diagnosis, code mutation, generated artifact changes, deployment, release, validation, review, or handoff.
- `ai-code-review-refactor` evaluates AI-generated output or hallucinated APIs.
- `quality-test-gate` is asked to accept a fix without evidence.
- `delivery-release-gate` closes rollout, rollback, or migration work after a failed pipeline.
- `reliability-observability-gate` closes an incident or degraded service.
- `change-impact-analyzer` produces an impact statement another agent will act on.

Prefer companion capabilities for domain work: `implementation-structure-design` for placement schema, `failure-diagnosis` for root-cause workflow, `validation-broker` for validation result normalization, and `plan-execution-consistency` for final reconciliation.

# With-Skill Vs Without-Skill Behavior

Without this capability, an agent can sound plausible while skipping cause, scope, validation, and residual risk. With it, execution is coupled to memory, graph, selected skills, validation broker output, and trajectory: every plan follows inspection, every edit follows a validation signal, every failure has a repair route, every local fix scans the same pattern, and every closure reports what is proven, what is not proven, and who owns the next gate.

# Proactive Professional Triggers

- **Signal:** Final response says done, fixed, green, ready, or complete after changing `src/` or generated reports, but no current command, working directory, exit code, or artifact is attached.
  **Hidden risk:** unverified completion claim hides stale validation, wrong file boundary, or missing generated output.
  **Required professional action:** block completion language, require fresh validation broker evidence, and state what the evidence proves and does not prove.
  **Route to:** `validation-broker`, `quality-test-gate`, `plan-execution-consistency`.
  **Evidence required:** command output with exit code, post-edit timestamp or freshness statement, artifact path, and residual risk.
- **Signal:** Diagnosis labels a failure as flaky, environment, dependency, or user setup before inspecting stack trace, configuration, symbol, version, input, or logs.
  **Hidden risk:** wrong verified cause leads to repeated wrong patch, hidden regression, or unresolved incident.
  **Required professional action:** route to root-cause workflow, compare counter-evidence, and withhold diagnosis until the concrete cause is traced.
  **Route to:** `failure-diagnosis`, `execution-trajectory-analysis`.
  **Evidence required:** symptom trace, tested hypothesis, method used, verified cause, and counter-evidence record.
- **Signal:** The same command, patch shape, prompt, or hypothesis has failed twice in one execution trajectory.
  **Hidden risk:** a third same-path retry wastes context and may overwrite useful failure evidence.
  **Required professional action:** stop same-route retry, reread failing output, inspect call site or graph edge, shrink scope, or escalate.
  **Route to:** `execution-trajectory-analysis`, `failure-diagnosis`, `task-dag-planner`.
  **Evidence required:** attempt ledger, shared failure signature, selected route change, and new hypothesis.
- **Signal:** A local fix changes one query, permission check, API caller, cache invalidation, state transition, or validation rule.
  **Hidden risk:** same defect remains in sibling repository, service, controller, schema, or test fixture.
  **Required professional action:** scan the repository graph for the same pattern and decide all-instance, subset, or local-only treatment.
  **Route to:** `change-impact-analyzer`, `regression-testing`, `backend-change-builder`.
  **Evidence required:** pattern signature, search command output, other occurrences found, decision rationale, and regression validation.
- **Signal:** Final diff, project memory, route manifest, generated report, or validation broker output disagrees with the stated plan or handoff.
  **Hidden risk:** stale memory, dropped capability, unplanned behavior change, or residual risk hidden from the next owner.
  **Required professional action:** reconcile accepted plan, actual paths, skipped work, validation coverage, and route/stage manifests before handoff.
  **Route to:** `plan-execution-consistency`, `project-memory-governance`, `repository-graph-analysis`.
  **Evidence required:** plan-vs-diff report, memory/graph note, validation coverage matrix, and explicit next gate.

# Risk Escalation Rules

- Escalate a fix without verified cause to `failure-diagnosis`.
- Escalate two same-path failures to route repair or human owner; never attempt the same path a third time.
- Escalate multi-occurrence same-pattern findings to `change-impact-analyzer` and the relevant `*-change-builder`.
- Escalate missing reuse or placement rationale to `implementation-structure-design`, and cross-module boundary changes to `architecture-impact-reviewer`.
- Escalate missing tests, fixtures, validators, or no-run verification to `quality-test-gate`.

# Critical Details

- **Evidence inventory:** command, working directory, exit code, output or report, artifact path, outcome, what evidence proves, and what evidence does not prove.
- **Completion claim gate:** success language is allowed only after fresh evidence from the current change; otherwise say "Not verified", why not run, residual risk, and exact verification command.
- **Verified-cause statement:** symptom, hypothesis tested, method, cause traced to symbol/config/version/input, and counter-evidence.
- **Route repair ledger:** attempt 1, attempt 2, shared failure signature, route change, and new hypothesis.
- **Same-pattern scan record:** pattern signature, scope scanned, other occurrences, and all/subset/local-only rationale.
- **Memory / graph / execution coupling:** compare project memory, repository graph, selected skills, validation broker output, accepted plan, actual diff, and execution trajectory before final review or handoff.

# Evidence Contract

Close only when these answers are concrete and current:

- **Basis:** requirement, contract, standard, issue, prior art, or repository convention supporting the action.
- **Boundaries inspected:** source paths, tests, configs, docs, generated artifacts, caller/callee graph, trust boundary, owner, permission, and not-inspected boundary.
- **Reuse / placement rationale:** convention scan, reuse-vs-new decision, owner, public/private API, dependency direction, and rejected locations.
- **Behavior preservation:** old behavior protected, new behavior covered, compatibility and rollback effects named.
- **Validation evidence:** literal command, working directory, exit code, output/report, artifact, fixture, screenshot, or validation broker result after the latest material edit.
- **What evidence proves:** the exact behavior, contract, build target, regression, routing, installation, or report freshness supported by the evidence.
- **What evidence does not prove:** skipped suites, partial coverage, unsupported adapter events, untested migration/release paths, or stale external conditions.
- **Residual risk:** remaining assumption, untested path, degraded evidence channel, release risk, or human decision with owner.
- **Next gate:** required reviewer, specialist capability, validation command, rollout check, or human question before broader closure.

# Reference Loading Policy

The body carries the execution rules compiled into professional-skill references. Load deep material only when authoring, auditing, or repairing discipline behavior:

- [references/completion-evidence.md](references/completion-evidence.md) - success-language catalog, partial-verification traps, not-verified disclosures, and pressure scenarios.
- [references/execution-report-and-gates.md](references/execution-report-and-gates.md) - full Execution Discipline Report fields and exhaustive Quality Gate.
- [references/checklist.md](references/checklist.md) - compact operator checklist for quick review.
- [examples/example-output.md](examples/example-output.md) - example report shape when sample output is needed.

# Failure Modes

- Agent declares done with no command output, diff, artifact, report, or validator result.
- Agent presents lint, one unit test, manual inspection, or stale output as full build or full regression.
- Agent cannot run verification but writes completion language instead of not-verified disclosure.
- Agent diagnoses environment, flakiness, user setup, or dependency behavior without verified cause.
- Agent repeats the same failed command, patch shape, or hypothesis three times.
- Agent fixes one permission, query, schema, cache, or state defect while same pattern remains elsewhere.
- **Structure drift:** Agent adds `utils/`, `common/`, helper bags, tiny helper files, or adapters without reuse and placement rationale.
- **Extension drift:** Agent extends existing logic without behavior preservation evidence or new behavior coverage.
- **Silent handoff:** Agent hands off without risk, boundary, validation result, route manifest, or next owner.
- **Narrative drift:** Agent introduces story, persona, emoji status, or runtime mood/score state instead of evidence.

# Output Contract

Return an Execution Discipline Report with:

- **Mode selected:** read/intake, plan/edit, debug/repair, local fix, validation/review, handoff/release, or not-applicable with reason.
- **Decision:** approved, blocked, partial, not verified, route repair required, or handoff required.
- **Boundaries inspected:** requirement, source paths, tests, configs/docs, generated artifacts, memory, graph, permissions, owner, and not-inspected areas.
- **Execution flow:** workflow state, accepted plan, actual changed files, owner skill, reviewer skill, and plan-execution consistency result.
- **Evidence inventory:** command, working directory, exit code, output/report, artifact, freshness, validation broker result, and evidence limits.
- **Cause or route:** verified-cause statement, counter-evidence, route repair ledger, or reason diagnosis was not attempted.
- **Same-pattern scan:** pattern signature, scope, hits, all/subset/local-only decision, and regression evidence.
- **Structure controls:** naming convention scan, reuse ladder, reuse/placement rationale, behavior preservation, and comment quality decision.
- **Tool controls:** permission state, sandbox boundary, dry-run/revert path, redaction rule, adapter capabilities, and unsupported events.
- **Residual risk:** what remains untested, unmigrated, unmonitored, stale, assumed, or human-owned.
- **Handoff:** next gate, owner, exact command or question, and routed `changeforge_route` / `changeforge_stage_route` manifests when applicable.

For the full report field list and exhaustive Quality Gate, load [references/execution-report-and-gates.md](references/execution-report-and-gates.md).

# Quality Gate

1. Completion language has fresh evidence inventory; missing or partial verification is labeled not verified or partial with exact follow-up command.
2. Requirement clarification, repository context, memory/graph check, workflow state, validation signal, and owner/reviewer split precede action closure.
3. Diagnoses have verified-cause statements; two same-path failures have route repair ledger.
4. Local fixes have same-pattern scan; new or renamed structure has convention scan, reuse ladder, placement rationale, and behavior preservation evidence.
5. Validation broker results are post-edit, scoped to changed paths, and state what they prove and do not prove.
6. Risky tools have permission/sandbox evidence, revert path, and redaction rule; unsupported adapter channels degrade the claim.
7. Closure answers basis, boundaries inspected, reuse / placement rationale, validation evidence, behavior preservation, residual risk, and next gate.
8. Final handoff reconciles plan, actual diff, generated artifacts, skipped work, stale evidence, residual risks, route manifest, and handoff boundary.

# Used By

`change-forge-router`, `change-intake-compiler`, `change-impact-analyzer`, `task-dag-planner`, `frontend-change-builder`, `backend-change-builder`, `data-middleware-change-builder`, `integration-change-builder`, `quality-test-gate`, `security-privacy-gate`, `reliability-observability-gate`, `delivery-release-gate`, `ai-code-review-refactor`, `change-documentation-gate`, `skill-authoring-expert`.

# Handoff

- `failure-diagnosis` - verified cause is missing or contradicted.
- `implementation-structure-design` - reuse, naming, owner, or placement rationale is missing.
- `change-impact-analyzer` - same-pattern scan shows broader blast radius.
- `quality-test-gate` - evidence cannot be produced, is partial, stale, or mismatched.
- `delivery-release-gate` - rollout, migration, rollback, or pipeline closure lacks evidence.
- `reliability-observability-gate` - incident closure lacks verified cause, metric evidence, or residual owner.

# Completion Criteria

This capability is complete for a change when the Execution Discipline Report is attached, evidence inventory is non-empty and fresh, repository context and memory/graph checks exist before planning, risky tools have sandbox evidence, completion language is bounded by validation, diagnoses have verified cause, repeated failures changed route, local fixes scanned same pattern, new structure has reuse and placement rationale, plan-execution consistency reconciles the final diff, and handoff states boundary, validation result, residual risk, route manifest, and next owner.
