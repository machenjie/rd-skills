---
name: agent-execution-discipline
description: Enforces execution discipline for AI and agent-assisted code changes through evidence-based completion, verified-cause diagnosis, route repair after repeated failure, mandatory same-pattern scans before any local fix, reuse-and-placement rationale before adding structure, and proactive closure with explicit risk, boundary, and validation results at every handoff.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "102"
changeforge_version: 0.1.0
---

# Mission

Constrain agent-assisted change execution so that every claim is backed by evidence, every diagnosis is backed by verified cause, every retry is backed by a new approach after two failures, every local fix is backed by a same-pattern scan, every new function/class/file/directory is backed by reuse and placement rationale, and every handoff is backed by an explicit risk, boundary, and validation result statement. Provide a small, repeatable execution kernel that any professional skill or reviewer can apply without adding entertainment rhetoric, corporate narration, user-shaming, or runtime PUA-style state.

# When To Use

Use this capability whenever an AI or agent is producing, modifying, diagnosing, validating, deploying, or handing off any code change, including:

- AI or agent code generation, refactor, or patch authoring.
- Bug investigation and root-cause analysis performed by an agent.
- Deployment, release, rollback, or migration steps proposed by an agent.
- Test failure triage and remediation by an agent.
- Multi-step task execution where the agent reports completion, claims a fix, or hands off to another skill or human.

# Do Not Use When

Do not use for trivial L1 changes such as text copy edits, README typo fixes, log message text, single-string label changes, or comment-only changes that have no code path, dependency, or behavior impact.

Do not use to add narrative storytelling, persona styling, emoji-laden status lines, or persistent runtime state for "agent mood" or "agent score". This capability is a behavior constraint, not a runtime feature.

# Stage Fit

Launched across stages as the execution kernel, with emphasis in debugging-diagnosis, bug-fix, and documentation-handoff. Per-stage focus:

- **debugging-diagnosis**: verified cause before fix; no same-path retry after two failures.
- **bug-fix**: same-pattern scan, minimal diff, reuse and placement rationale.
- **documentation-handoff**: evidence inventory, residual risk, and validation results before closure.

# Non-Negotiable Rules

- **Evidence-based completion.** A change is not complete until concrete evidence (test output, validator output, fixture diff, screenshot, log excerpt, or measured result) is attached to the completion claim.
- **No engineering action before requirement clarification.** For target-project engineering prompts, the agent must first record current behavior, desired behavior, non-goals, constraints, acceptance/TDD signal, blocking questions, assumptions, and proceed/block status. If blocking questions remain, the agent stops and asks them instead of reading, planning, or editing around the gap.
- **No plan before target-project inspection.** A plan is invalid until the agent has inspected relevant target-project code, tests, configs, docs, existing implementation, conventions, and likely call chain, or has explicitly limited the work to non-executing advice with not-inspected risk.
- **Repository context before plan or action.** Before planning or editing, record the owning surface, related files, caller/callee flow, local conventions, tests, configs/docs, generated artifacts, rejected locations, and not-inspected boundaries. A generic plan without repository context is not a plan.
- **Workflow state before and after phase transitions.** Record current phase, allowed next phase, owner skill, reviewer skill, validation freshness, open findings, repair/re-review state, and closure readiness before moving from read to plan, plan to edit, edit to test, test to review, repair to re-review, or review to handoff.
- **Tool permission/sandbox before risky action.** Before shell commands, connector/MCP actions, destructive filesystem operations, migrations, deploys, network writes, secret-bearing calls, or untrusted tool output handling, record tool/action class, permission state, sandbox boundary, dry-run/revert path, and redaction rule.
- **No implementation before TDD or validation signal.** Before editing behavior, the agent names the failing, new, or updated test, eval, validation command, acceptance check, or explicit not-verified residual risk that will prove the change.
- **No action closure without independent review.** Each action must name an owner skill or capability and a different review skill or capability. The action owner may not substitute self-review for an independent review gate.
- **No review closure while findings remain.** When review finds issues, route repair to the owner skill or appropriate specialist, then re-run the independent review. Handoff is blocked until findings are repaired and re-reviewed, or explicitly carried as not-verified residual risk with an owner.
- **No completion claim without fresh verification evidence.** Success-implying language ("done", "fixed", "should pass", "looks good", and similar phrases catalogued in the completion-evidence reference) is forbidden unless a fresh command output, validator result, or artifact from the current change backs it. Evidence from before the current change, from a different file, or from a superseded run is stale and must be re-run. The phrase is not the evidence; the captured outcome is.
- **Broker freshness is evidence, not decoration.** When Validation Broker output exists, closure must state command level, outcome, coverage alignment, and whether the validation completed after the latest material edit. Stale, failed, not-run, no-outcome, or coverage-mismatch broker results cannot back completion language.
- **Honest not-verified disclosure.** When verification cannot be run, the agent must state "Not verified", state why it was not run, state the residual risk, and give the exact command the user or next agent should run. It may say "changes prepared, not yet verified"; it may not say the change is complete.
- **Partial verification is reported as partial.** A passing linter is not a passing build, a passing unit test is not a passing integration suite, and one green test is not full coverage. Generalizing a partial run to "all checks pass" is an overclaim.
- **Verified-cause diagnosis.** No bug or failure may be declared "diagnosed" without a verified cause traced to a specific symbol, configuration, dependency version, environment value, or input. Speculation about the environment, user, or unknown background process is not a diagnosis.
- **Route repair after repeated failure.** After two failures of the same approach (same command, same patch shape, same hypothesis) the agent must change the route. Allowed route changes: reread the failing output, inspect the call site, reduce the change scope, or escalate. Repeating the same path a third time is forbidden.
- **Same-pattern scan before local fix.** Before applying a local fix to a bug, defect, or wrong call, the agent must scan for the same pattern in the rest of the codebase. If the pattern exists elsewhere, the fix must either cover all instances or explicitly justify why it is local-only.
- **Reuse and placement rationale before new structure.** No new function, class, file, directory, component, hook, service, repository, adapter, utility, or abstraction may be added without an explicit reuse search, placement decision, and shared/common/utils audit. This rule delegates to `implementation-structure-design` for the placement schema.
- **Proactive closure with risk, boundary, and validation result.** Every handoff or task closure must include: the change boundary, the validation results that were actually run, the residual risks, and the next-skill or human handoff target. When the change was routed, the closure also restates the `changeforge_route` manifest (and `changeforge_stage_route` for non-trivial work) instead of dropping it after the first turn. Silent handoff is rejected.
- **Plan-execution consistency before final review or handoff.** Compare accepted plan, actual changed files, validation commands, skipped work, stale evidence, unplanned behavior changes, and residual risk. Any mismatch routes back to planning or review.
- **Local convention scan before naming.**
  Before adding or renaming any file, function, method, class, directory, component, hook, service, repository, adapter, helper, or utility, the agent must inspect same-file, same-directory, parent-module, sibling-module, and test naming conventions.
- **Reuse ladder before new code.**
  Before adding new code, the agent must walk the reuse ladder and record why direct reuse, extension reuse, composition, adapter/wrapper, and extraction are insufficient.
- **Extension safety before modifying existing logic.**
  When extending an existing function, method, class, service, repository, adapter, component, or hook, the agent must prove old behavior is preserved and new behavior is covered by tests.
- **Comment quality evidence.**
  Any agent-assisted code addition or refactor must record whether exported declarations, complex internal logic, and non-trivial tests require comments. Missing required comments are not acceptable completion.

# Industry Benchmarks

- **Google Site Reliability Engineering**: blameless postmortems and verified-cause analysis — no incident is "resolved" without a documented root cause and corrective action.
- **NASA software engineering "ten rules"** and Toyota production-system "five whys": stop the line on failure, do not retry without changing the input.
- **OWASP ASVS / SAMM verification controls**: every security claim must be backed by an evidence artifact (test, scan, review note).
- **DevOps DORA metrics — change failure rate and MTTR**: silent fixes without same-pattern scans inflate change failure rate and lengthen MTTR.
- **DDD / Clean Architecture placement rules**: reuse and placement rationale prevents shared-utility pollution and dependency-direction drift.
- **Toyota Andon principle**: route repair after repeated failure mirrors "stop the line" — do not push through with the same failing approach.

# Selection Rules

Select this capability when:

- A professional skill is being invoked by an AI or agent and the task has any non-trivial diagnosis, code-mutation, deployment, or handoff component.
- `ai-code-review-refactor` is evaluating AI-generated output.
- `quality-test-gate` is asked to accept a "fix" without test evidence.
- `delivery-release-gate` is asked to roll out a change after a failed pipeline.
- `reliability-observability-gate` is asked to close an incident.
- `change-impact-analyzer` is producing a final impact statement that will be acted on by another agent.
- `failure-diagnosis` is producing a diagnosis that will be acted on by another agent.

Prefer companion capabilities for the substantive content: `implementation-structure-design` for placement detail, `failure-diagnosis` for root-cause workflow, `solution-optimality-evaluation` for algorithmic-choice review.

# With-Skill Vs Without-Skill Behavior

This capability changes agent behavior from plausible completion to evidenced execution: engineering prompts start with requirement clarification, plans follow target-project inspection, implementation follows a TDD or validation signal, actions have owner and independent review skills, review findings trigger repair and re-review, completion must name boundary, fresh command output, residual risk, and handoff; diagnosis must name symptom, tested hypothesis, method, verified cause, and counter-evidence; local fixes require same-pattern scan; new helpers/classes/files require reuse and placement rationale; two same-path failures force route repair; validation states what it proves and does not prove.

# Risk Escalation Rules

- Escalate when the agent has produced two failed attempts at the same approach — the next step must be a route change or human escalation, not a third retry.
- Escalate when a "fix" is proposed without a verified cause — route to `failure-diagnosis`.
- Escalate when a same-pattern scan reveals the bug exists in multiple modules — route to `change-impact-analyzer` and the relevant `*-change-builder`.
- Escalate when reuse-and-placement rationale cannot be produced — route to `implementation-structure-design` and, if module boundaries are affected, `architecture-impact-reviewer`.
- Escalate when completion evidence cannot be produced because tests, fixtures, or validators are missing — route to `quality-test-gate`.

# Critical Details

## Evidence Inventory

Every completion claim must list the evidence in a structured inventory: **command run** (literal command line, working directory), **output captured** (exit code, head/tail, or fixture), **artifact produced** (file path, diff, screenshot, log excerpt), and **outcome** (pass/fail/inconclusive, what it proves, what it does not prove).

Speculative evidence — "this should work", "based on the docs", "the linter probably passes" — is not evidence.

## Completion Claim Gate

When verification could not run, the closure replaces the completion claim with a not-verified disclosure: **status** (changes prepared, not yet verified), **why not run**, **residual risk**, and the **exact command** to verify. Dressing an unverified change as complete is a discipline violation. The success-language catalog, partial-verification traps, and worked disclosures live in [references/completion-evidence.md](references/completion-evidence.md).

## Verified-Cause Statement

A diagnosis is structured as:

- **Symptom**: literal observable failure (message, stack frame, status code, metric drop).
- **Hypothesis tested**: what was checked.
- **Method**: how it was checked (file inspected, command run, value printed).
- **Verified cause**: the specific symbol, file, line, configuration key, dependency version, environment value, or input that produced the symptom.
- **Counter-evidence**: any signal that contradicts the cause (must be addressed, not ignored).

Forbidden patterns: "must be environment", "probably the user's setup", "some background process", "intermittent flakiness" without a reproduction script.

## Route Repair Ledger

When two attempts of the same approach fail, log attempt 1, attempt 2, shared failure signature, route change chosen (re-read failing output / inspect call site / shrink scope / escalate), and the new hypothesis.

A third attempt of the same approach without a route change is a discipline violation.

## Same-Pattern Scan Record

Before any local code fix, record pattern signature, scope scanned, other occurrences found, and decision: cover all / cover subset with rationale / local-only with rationale.

## Reuse and Placement Rationale (delegated)

Delegate the schema to `implementation-structure-design`; this capability requires its output be present before code is accepted, not redefine it.

## Proactive Closure Package

Every handoff must include boundary, validation results with exit codes, residual risk, and handoff target with the specific question or action required. When the change was routed, the package restates the `changeforge_route` manifest (and `changeforge_stage_route` when the work was non-trivial) so the closure carries the selected skills, capabilities, required references, and quality gates as machine-checkable evidence rather than dropping them after the first turn.

## Runtime Prompt Flow Ledger

For target-project engineering work, attach a ledger with: requirement clarification and proceed/block decision; files, code paths, configs, tests, docs, conventions, and call-chain boundaries inspected before plan; TDD or validation signal named before implementation; action owner/review skill map with different owner and review skills; review findings, repair owner, repair evidence, re-review result, and remaining risk. Pure explanation, translation, or no-action Q&A may record "no engineering action" and skip the full ledger.

## Evidence Contract Answer Set

The five questions every professional skill's own Evidence Contract must answer; the skill names the concrete artifact for each answer, this capability enforces that none is skipped:

1. **Basis** — what authority backs the change: the requirement, contract, standard, prior art, or repository convention it rests on.
2. **Files and boundaries inspected** — which files, modules, call sites, configs, and trust or ownership boundaries were actually read, and what was found.
3. **Placement rationale** — why each new or changed element lives where it does: reuse-vs-new decision, owner, and dependency direction (schema from `implementation-structure-design`).
4. **Validation commands** — the literal commands or checks run to prove the change works, with outcomes (schema from the Evidence Inventory above).
5. **Residual risk** — what remains untested, unmigrated, unmonitored, or assumed, and who owns the follow-up.

## AI Generated Code Discipline Failures

Treat these as execution defects until corrected with evidence: local fix without same-pattern scan; invented helper without reuse search; completion claim without command output; diagnosis without verified cause; retrying the same failed approach; business logic in common/utils; scope expansion without boundary statement; validation overclaim such as presenting lint, typecheck, one unit test, or manual inspection as full build, full regression, or production readiness.

# Reference Loading Policy

The body carries the decision-critical execution rules and is the part compiled into professional-skill references for the recommended and full profiles. Deep material loads only when authoring or auditing discipline behavior:

- [references/completion-evidence.md](references/completion-evidence.md) — success-language catalog, partial-verification traps, worked not-verified disclosures, and completion-claim pressure scenarios.

# Failure Modes

- Agent declares "done" with no command output, diff, or validator result attached.
- Agent reports a lint-only or single-test pass as "all tests pass", "build is green", or "everything works".
- Agent claims completion when verification could not run, instead of disclosing not-verified status, residual risk, and the exact command to run.
- Agent diagnoses a bug as "probably the environment" without inspecting code, configuration, or logs.
- Agent retries the same failing command three or more times with the same arguments, hoping for a different result.
- Agent fixes one occurrence of a defect and ships, leaving the same defect present in five other modules.
- Agent adds a new helper in `utils/` or `common/` without inspecting existing utilities or justifying placement.
- Agent hands off with "ready for review" but lists no risks, no boundary, and no validation results.
- Agent adds narrative storytelling, mock dialogue, persona styling, or persistent "agent state" instead of execution evidence.
- Agent claims a security or migration step is complete without a verified artifact (no scan log, no migration plan, no rollback note).

# Output Contract

Return an Execution Discipline Report alongside any non-trivial agent-assisted change:

- **Evidence inventory**: list of commands run, outputs captured, artifacts produced, outcomes.
- **Runtime prompt flow ledger**: requirement clarification, inspected boundaries before plan, TDD/validation signal, action owner/review map, and repair/re-review record.
- **Completion claim status**: verified (with the backing command and outcome), partially verified (with the gap named), or not verified (with the not-verified disclosure: status, why not run, residual risk, exact command).
- **Validation broker result**: selected command level, outcome, evidence strength, coverage alignment, freshness after final material edit, and next route when evidence is weak or negative.
- **Repository context map**: owning surface, related files, caller/callee flow, conventions, tests/config/docs, generated artifacts, rejected locations, and not-inspected boundaries.
- **Workflow state summary**: current phase, allowed transition, owner/reviewer split, validation freshness, open findings, repair/re-review status, and closure readiness.
- **Tool permission/sandbox record**: risky tool/action class, permission state, sandbox boundary, dry-run/revert path, and redaction rule.
- **Verified cause statement** (when a diagnosis is part of the change): symptom, hypothesis, method, verified cause, counter-evidence.
- **Route repair ledger** (when applicable): attempt 1, attempt 2, failure signature, route change, new hypothesis.
- **Same-pattern scan record** (when a local fix is applied): pattern signature, scope, other occurrences, decision.
- **Proactive closure package**: boundary, validation results, residual risk, handoff target.
- **Plan-execution consistency record**: accepted plan, actual changed files, validation commands, skipped work, stale evidence, unplanned behavior changes, and residual-risk reconciliation.
- **Professional evidence contract answer set**: basis; files and boundaries inspected; reuse/placement rationale; behavior preservation when applicable; validation commands; residual risk; next gate.
- **Discipline violations**: any rule violation that was accepted with justification, or "none".
- **Local convention scan record**: same file, same directory, parent module, sibling module, tests, selected convention.
- **Reuse ladder record**: direct reuse, extension reuse, composition, adapter/wrapper, extraction, new code decision.
- **Extension safety record**: old behavior preserved, compatibility risk, tests covering old and new behavior.
- **Comment quality record**: exported/public comments, complex internal comments, test scenario/regression comments, redundant comments removed, and intentional omissions.

# Quality Gate

1. Completion claim has an evidence inventory with at least one concrete command-output, artifact, or validator result.
2. Engineering work did not start before requirement clarification, unless the output explicitly states no engineering action is being taken.
3. Planning did not start before relevant target-project code, tests, configs, docs, conventions, and call-chain boundaries were inspected, or not-inspected risk was explicitly accepted for non-executing advice.
4. Implementation did not start before a TDD or validation signal was named.
5. Every action names an owner skill/capability and a different review skill/capability.
6. Every review finding has a repair owner and re-review result before closure, or a not-verified residual risk disclosure with owner.
7. Any diagnosis attached to the change carries a verified-cause statement.
8. If the agent attempted the same approach twice and failed, a route repair ledger is attached and no third same-path retry occurred.
9. Any local code fix carries a same-pattern scan record covering the rest of the codebase.
10. Any new function, class, file, directory, component, hook, service, repository, adapter, utility, or abstraction carries reuse and placement rationale.
11. The closure package lists boundary, validation results, residual risks, and the next handoff target.
12. No entertainment rhetoric, persona narration, emoji status lines, or runtime PUA state are introduced by the change.
13. Any new or renamed structure has local naming convention evidence.
14. Any new code has a Reuse Ladder Record.
15. Any extension of existing logic has an Extension Safety Record.
16. Any exported/public declaration has a doc comment in the language-standard format.
17. Any complex internal logic and non-trivial test has required comments or an explicit omission rationale.
18. When a professional skill emits an Evidence Contract, all five canonical answers — basis, files and boundaries inspected, placement rationale, validation commands, residual risk — are present and non-empty.
19. Any completion claim names a fresh verification (command, validator, or test) that ran against the current change; success-implying language without backing evidence is absent.
20. Partial verification is reported as partial, never generalized to a full pass; "all tests pass" is not claimed from a lint-only or single-test run.
21. When verification could not run, a not-verified disclosure — status, why not run, residual risk, exact command — replaces any completion claim.
22. When the change is a review, spec compliance (requirement, acceptance criteria, non-goals, plan, compatibility, old-behavior preservation) is confirmed before code-quality judgement, and implementer self-review does not replace independent review.
23. AI-generated code is rejected or repaired when it shows local-only fixing, invented helpers, missing reuse search, wrong shared/common placement, hidden scope expansion, or validation overclaim.
24. Every professional skill closure answers the full evidence contract set: inspected boundaries, judgment, reuse/placement rationale, behavior preservation, validation evidence, residual risk, and next gate.
25. Repository context is present before planning or action for target-project engineering and skill-authoring work.
26. Workflow state is explicit before phase transitions and at handoff.
27. Risky shell, connector/MCP, destructive, deploy, migration, network-write, secret-bearing, or untrusted-output actions carry tool permission/sandbox evidence.
28. Final review and handoff include plan-execution consistency and disclose stale validation or unplanned changes.

# Used By

- change-forge-router
- change-intake-compiler
- change-impact-analyzer
- acceptance-criteria-builder
- task-dag-planner
- experience-impact-modeler
- domain-impact-modeler
- architecture-impact-reviewer
- data-api-contract-changer
- frontend-change-builder
- backend-change-builder
- data-middleware-change-builder
- integration-change-builder
- quality-test-gate
- security-privacy-gate
- reliability-observability-gate
- delivery-release-gate
- ai-code-review-refactor
- change-documentation-gate

# Handoff

- `failure-diagnosis` — when the verified-cause statement cannot be produced.
- `implementation-structure-design` — when reuse and placement rationale cannot be produced.
- `change-impact-analyzer` — when the same-pattern scan reveals broader blast radius.
- `quality-test-gate` — when evidence cannot be produced because tests or fixtures are missing.
- `delivery-release-gate` — when a release is being closed without a route repair ledger after a failed pipeline.
- `reliability-observability-gate` — when an incident is being closed without a verified cause.

# Completion Criteria

The capability is complete for a given change when the Execution Discipline Report is attached, the evidence inventory is non-empty, repository context exists before planning, workflow state is current, risky tools have permission/sandbox evidence, every completion claim names a fresh verification that ran against the current change (or a not-verified disclosure replaces it), any diagnosis carries a verified cause, any repeated failure carries a route repair ledger, any local fix carries a same-pattern scan, any new structure carries reuse and placement rationale, plan-execution consistency reconciles the final work, and the closure package documents boundary, validation results, residual risks, and handoff target.
