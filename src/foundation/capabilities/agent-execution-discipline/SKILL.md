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
- **Verified-cause diagnosis.** No bug or failure may be declared "diagnosed" without a verified cause traced to a specific symbol, configuration, dependency version, environment value, or input. Speculation about the environment, user, or unknown background process is not a diagnosis.
- **Route repair after repeated failure.** After two failures of the same approach (same command, same patch shape, same hypothesis) the agent must change the route. Allowed route changes: reread the failing output, inspect the call site, reduce the change scope, or escalate. Repeating the same path a third time is forbidden.
- **Same-pattern scan before local fix.** Before applying a local fix to a bug, defect, or wrong call, the agent must scan for the same pattern in the rest of the codebase. If the pattern exists elsewhere, the fix must either cover all instances or explicitly justify why it is local-only.
- **Reuse and placement rationale before new structure.** No new function, class, file, directory, component, hook, service, repository, adapter, utility, or abstraction may be added without an explicit reuse search, placement decision, and shared/common/utils audit. This rule delegates to `implementation-structure-design` for the placement schema.
- **Proactive closure with risk, boundary, and validation result.** Every handoff or task closure must include: the change boundary, the validation results that were actually run, the residual risks, and the next-skill or human handoff target. Silent handoff is rejected.
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

# Risk Escalation Rules

- Escalate when the agent has produced two failed attempts at the same approach — the next step must be a route change or human escalation, not a third retry.
- Escalate when a "fix" is proposed without a verified cause — route to `failure-diagnosis`.
- Escalate when a same-pattern scan reveals the bug exists in multiple modules — route to `change-impact-analyzer` and the relevant `*-change-builder`.
- Escalate when reuse-and-placement rationale cannot be produced — route to `implementation-structure-design` and, if module boundaries are affected, `architecture-impact-reviewer`.
- Escalate when completion evidence cannot be produced because tests, fixtures, or validators are missing — route to `quality-test-gate`.

# Critical Details

## Evidence Inventory

Every completion claim must list the evidence in a structured inventory:

- **Command run** (literal command line, working directory).
- **Output captured** (exit code, head/tail of stdout/stderr, or attached fixture).
- **Artifact produced** (file path, diff, screenshot, log excerpt).
- **Outcome** (pass/fail/inconclusive) and what it proves.

Speculative evidence — "this should work", "based on the docs", "the linter probably passes" — is not evidence.

## Verified-Cause Statement

A diagnosis is structured as:

- **Symptom**: literal observable failure (message, stack frame, status code, metric drop).
- **Hypothesis tested**: what was checked.
- **Method**: how it was checked (file inspected, command run, value printed).
- **Verified cause**: the specific symbol, file, line, configuration key, dependency version, environment value, or input that produced the symptom.
- **Counter-evidence**: any signal that contradicts the cause (must be addressed, not ignored).

Forbidden patterns: "must be environment", "probably the user's setup", "some background process", "intermittent flakiness" without a reproduction script.

## Route Repair Ledger

When two attempts of the same approach fail, log:

- **Attempt 1**: hypothesis, change, result.
- **Attempt 2**: hypothesis, change, result.
- **Failure signature** shared by both attempts.
- **Route change** chosen: re-read failing output / inspect call site / shrink scope / escalate.
- **New hypothesis** that the route change produces.

A third attempt of the same approach without a route change is a discipline violation.

## Same-Pattern Scan Record

Before any local code fix:

- **Pattern signature**: regex, symbol, or call-shape that captures the defect.
- **Scope scanned**: directories, languages, file globs.
- **Other occurrences found**: list with file:line, or "none found".
- **Decision**: cover all / cover subset with explicit rationale / local-only with explicit rationale.

## Reuse and Placement Rationale (delegated)

Delegate the schema to `implementation-structure-design`. The execution-discipline contribution is to require that the schema output be present before code is accepted, not to redefine it.

## Proactive Closure Package

Every handoff must include:

- **Boundary**: what changed and what did not.
- **Validation results**: which validators or tests actually ran, with exit codes.
- **Residual risk**: what remains untested, unmigrated, unrolled-back, or unmonitored.
- **Handoff target**: next skill or human, with the specific question or action required.

# Failure Modes

- Agent declares "done" with no command output, diff, or validator result attached.
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
- **Verified cause statement** (when a diagnosis is part of the change): symptom, hypothesis, method, verified cause, counter-evidence.
- **Route repair ledger** (when applicable): attempt 1, attempt 2, failure signature, route change, new hypothesis.
- **Same-pattern scan record** (when a local fix is applied): pattern signature, scope, other occurrences, decision.
- **Reuse and placement rationale**: presence confirmed (schema from `implementation-structure-design`).
- **Proactive closure package**: boundary, validation results, residual risk, handoff target.
- **Discipline violations**: any rule violation that was accepted with justification, or "none".
- **Local convention scan record**:
  same file, same directory, parent module, sibling module, tests, selected convention.
- **Reuse ladder record**:
  direct reuse, extension reuse, composition, adapter/wrapper, extraction, new code decision.
- **Extension safety record**:
  old behavior preserved, compatibility risk, tests covering old and new behavior.
- **Comment quality record**:
  exported/public comments added;
  complex internal logic comments added;
  test scenario/regression comments added;
  redundant comments removed;
  comments intentionally omitted with reason.

# Quality Gate

1. Completion claim has an evidence inventory with at least one concrete command-output, artifact, or validator result.
2. Any diagnosis attached to the change carries a verified-cause statement.
3. If the agent attempted the same approach twice and failed, a route repair ledger is attached and no third same-path retry occurred.
4. Any local code fix carries a same-pattern scan record covering the rest of the codebase.
5. Any new function, class, file, directory, component, hook, service, repository, adapter, utility, or abstraction carries reuse and placement rationale.
6. The closure package lists boundary, validation results, residual risks, and the next handoff target.
7. No entertainment rhetoric, persona narration, emoji status lines, or runtime PUA state are introduced by the change.
8. Any new or renamed structure has local naming convention evidence.
9. Any new code has a Reuse Ladder Record.
10. Any extension of existing logic has an Extension Safety Record.
11. Any exported/public declaration has a doc comment in the language-standard format.
12. Any complex internal logic and non-trivial test has required comments or an explicit omission rationale.

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

The capability is complete for a given change when the Execution Discipline Report is attached, the evidence inventory is non-empty, any diagnosis carries a verified cause, any repeated failure carries a route repair ledger, any local fix carries a same-pattern scan, any new structure carries reuse and placement rationale, and the closure package documents boundary, validation results, residual risks, and handoff target.
