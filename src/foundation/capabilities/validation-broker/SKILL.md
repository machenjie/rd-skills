---
name: validation-broker
description: Selects and evaluates validation commands from changed paths, validator scope, freshness, parsed outcomes, negative evidence, and stop-closure needs.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "126"
changeforge_version: 0.1.0
---

# Validation Broker

## Mission
Broker validation from changed paths to narrow, module, or full checks, parse outcomes conservatively, reject stale or negative evidence, and feed stop closure without inflating partial validation into completion.

## When To Use
- When a task mentions validation command selection, stale validation, validation without outcome, affected tests, or changed path validation.
- Before final closure after code, registry, hook runtime, docs, generated, benchmark, or installation changes.
- When a validator result must be parsed into pass, fail, not-run, not-verified, stale, or partial.
- When stop closure needs fresh validation evidence and residual risk.

## Do Not Use When
- The task is read-only and no validation claim will be made.
- A maintainer explicitly supplies the exact command and only wants raw execution, though freshness still belongs in handoff.
- There is no changed path, no command, and no validation decision to broker.

## Non-Negotiable Rules
- Map changed paths to validation commands before claiming verification.
- Select narrow, module, or full validators based on blast radius, source-of-truth, generated artifacts, and risk.
- Parse validation result text into structured outcome, command, timestamp, scope, and evidence.
- Reject validation freshness when material files changed after the command ran.
- Record negative validation evidence; failures, skipped checks, warnings, and stale results are not hidden.
- Stop closure must include broker outcome or disclose not-run/not-verified residual risk.
- Do not report a targeted validator as full-suite evidence.

## Industry Benchmarks
- **Affected-test selection**: Changed paths select relevant checks before full suites are considered.
- **CI evidence discipline**: Command, outcome, time, scope, and artifacts are explicit.
- **Freshness control**: Test results are valid only for the final material diff.
- **Negative evidence accounting**: Failures and skipped checks are first-class evidence.
- **Release gate closure**: Stop decisions consume structured validation, not prose optimism.

## Selection Rules
- Select this capability with `quality-test-gate` for changed-code-to-test mapping.
- Select it with `repository-graph-analysis` when graph edges identify affected tests or generated artifacts.
- Select it with `plan-execution-consistency` when final diff and validation order must reconcile.
- Select it with `agent-workflow-state-machine` when validation gates stage transitions or closure.

## Risk Escalation Rules
- Escalate to full validation when changed paths cross module, registry, hook runtime, packaging, installation, or generated artifact boundaries.
- Escalate when validation output is missing, unparseable, stale, partial, or contradictory.
- Escalate when negative validation evidence appears after a previous pass.
- Escalate when stop closure is requested with no fresh evidence for the final diff.
- Escalate to `delivery-release-gate` when validation affects release, migration, install, or deployment readiness.

## Critical Details
- Changed-path-to-validation mapping must include source files, registries, docs, evals, hook runtime, generated artifacts, and tests.
- Narrow validators check one affected surface; module validators check a subsystem; full validators check release profile or repository-wide gates.
- Validation freshness compares command time and final material diff, including generated files and report outputs.
- Negative validation evidence includes non-zero exit, failing assertion, stale report, missing expected output, skipped command, or warnings that block closure.
- Stop closure integration should produce `passed`, `failed`, `not-run`, `not-verified`, `stale`, or `partial`.

## Failure Modes
- **Wrong validator**: A docs-only check is used after hook runtime code changed.
- **Stale pass**: A pass before final edits is reported as current validation.
- **Outcome missing**: The handoff names a command but not the result.
- **Partial inflation**: A single targeted check is described as complete regression coverage.
- **Negative evidence hidden**: A failed command is omitted because a later unrelated check passed.

## Output Contract
Return a `validation_broker_result` with:
- **Changed-path mapping**: changed files, owning surface, validator candidates, and selected scope.
- **Selection rationale**: narrow, module, or full validator choice with risk reason.
- **Command ledger**: command, start time, outcome, parsed evidence, and relevant output summary.
- **Freshness**: whether material files changed after each command and current/stale decision.
- **Negative evidence**: failures, skipped checks, stale reports, warnings, or unverified areas.
- **Stop closure input**: closure outcome, residual risk, and next validator or owner.

## Quality Gate
1. Every material changed path has a validator decision or explicit no-validator rationale.
2. Selected validation depth matches blast radius and risk.
3. Results include command, outcome, scope, and timestamp or equivalent ordering evidence.
4. Stale or partial validation is not reported as full pass.
5. Negative validation evidence is disclosed.
6. Stop closure consumes broker status and residual risk.

## Used By
- `change-forge-router`
- `quality-test-gate`
- `delivery-release-gate`
- `ai-code-review-refactor`
- `change-documentation-gate`
- `agent-execution-discipline`

## Handoff
Hand off the broker result to final handoff, release, review, or documentation owners. If validation is stale, failed, or partial, hand off the next required command and residual risk.

## Completion Criteria
The capability is complete when changed paths map to appropriate validators, outcomes are parsed, freshness is current or disclosed, negative evidence is recorded, and stop closure cannot overclaim verification.
