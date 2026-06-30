---
name: validation-broker
description: Selects and evaluates validation commands from changed paths, validator scope, freshness, parsed outcomes, negative evidence, and stop-closure needs.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "126"
changeforge_version: 0.1.0
---

# Mission
Broker validation from changed paths, risk surfaces, source-of-truth boundaries, generated artifacts, and final material edits to proportional narrow, module, or full checks. Parse outcomes conservatively, preserve negative evidence, reject stale or mismatched validation, and feed stop closure without inflating partial proof into completion.

# When To Use
- When a task mentions validation command selection, stale validation, validation without outcome, affected tests, changed path validation, changed-path-to-validation mapping, or stop closure evidence.
- Before final closure after code, registry, hook runtime, docs, generated artifacts, reports, benchmark fixtures, packages, installation outputs, or release-support artifacts change.
- When a validator result must be parsed into passed, failed, stale, partial, not-run, or not-verified with evidence limits.
- When repository graph, project memory, or execution trajectory evidence changes validator depth, freshness, or negative-evidence handling.
- When a handoff needs the exact next validator, owner, residual risk, or no-validator rationale.

# Do Not Use When
- The task is read-only and no validation claim, closure claim, or test-evidence decision will be made.
- A maintainer explicitly supplies the exact command and asks only to run it, though freshness and evidence limits still belong in handoff.
- There is no changed path, risk surface, command, generated artifact, report, or validation decision to broker.
- The primary need is designing tests rather than selecting/parsing validation evidence; use `quality-test-gate` first.

# Stage Fit
Use during planning, coding, debugging, code-review, refactoring, testing, validation, repair, release readiness, and final handoff whenever evidence must prove the final material state. Re-run after any material source, registry, hook runtime, generated artifact, report, benchmark, package, install-output, fixture, or validation-input edit that occurs after a previous check.

# Non-Negotiable Rules
- Map every material changed path or risk surface to a validator decision before claiming verification.
- Select narrow, module, or full validation based on blast radius, source-of-truth, generated artifacts, install/release impact, and risk.
- Parse command output into structured outcome, scope, evidence limit, and freshness status; do not accept a command name without result.
- Reject freshness when material files, generated outputs, reports, fixtures, lockfiles, or validation inputs changed after the command ran.
- Preserve negative evidence: failures, skipped checks, stale reports, warnings, missing outputs, unparseable output, and unsupported evidence channels.
- Stop closure must consume broker status or disclose not-run, not-verified, stale, partial, or failed residual risk.
- A targeted validator is never full-suite evidence; a green lint/type/build is not behavior proof unless that is the mapped obligation.

# Industry Benchmarks
Anchor against affected-test selection, CI evidence discipline, build graph validation, generated artifact provenance, negative evidence accounting, validation freshness control, release gate evidence, and audit-ready stop decisions. Keep the body focused on routing and closure decisions; load the reference only for concrete validator matrices, parsing fields, and stop-closure templates.

# Mode Matrix
| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities |
| --- | --- | --- | --- | --- |
| Changed-path mapping | Changed source, docs, registry, hook runtime, report, fixture, generated artifact, or package. | Map path to validator, owner, and scope. | Changed path, source-of-truth, validator candidates, no-validator rationale. | `repository-graph-analysis` |
| Validator depth selection | Narrow/module/full choice is unclear. | Match depth to blast radius and risk. | Risk surface, affected graph, generated/install impact, selected command. | `quality-test-gate` |
| Outcome parsing | Command output exists but pass/fail/scope is ambiguous. | Parse outcome and evidence limit. | Command, exit status/output summary, covered paths, artifacts. | `agent-execution-discipline` |
| Freshness repair | Validation predates later material edits. | Mark stale/partial and require rerun or disclosure. | Command order, later edits, covered scope, freshness verdict. | `execution-trajectory-analysis` |
| Negative evidence ledger | Failure, skipped check, warning, missing output, or unsupported channel exists. | Preserve blocking evidence and route repair. | Failure class, affected path, next validator, owner. | `failure-diagnosis`, `project-memory-governance` |
| Stop closure package | Handoff claims ready/done/verified. | Prevent overclaim and feed residual risk. | Broker result, changed-path map, stale/not-run scope, evidence limits. | `plan-execution-consistency` |

# Selection Rules
- Select this capability with `quality-test-gate` for changed-code-to-test mapping, validator depth, test evidence limits, or stop closure.
- Select it with `repository-graph-analysis` when graph edges identify affected tests, generated artifacts, source-of-truth, owners, or missing test edges.
- Select it with `execution-trajectory-analysis` when command order, later edits, repair/re-review, or repeated failures affect freshness.
- Select it with `project-memory-governance` when prior validation gaps, fragile files, previous failures, or stale context change validator depth.
- Select it with `delivery-release-gate` when build, install, package, release profile, migration, or deployment readiness evidence is required.

# Technical Selection Criteria
Evaluate validation by changed-path materiality, source-vs-generated status, validator ownership, risk surface, test graph coverage, command scope, parsed outcome confidence, command order, generated/report freshness, negative evidence, no-validator rationale, stop-closure consequence, and residual risk. A validation claim is usable only as passed-current, failed, stale, partial, not-run, not-verified, or unsupported.

# Proactive Professional Triggers
- **Signal:** Changed paths cross source, registry, hook runtime, generated artifact, report, benchmark, package, or install output boundaries. **Hidden risk:** narrow command misses build/install or route-level breakage. **Required professional action:** escalate to module/full validation or name omitted scope. **Route to:** `quality-test-gate`, `delivery-release-gate`. **Evidence required:** changed-path map, selected full/module commands, skipped-scope rationale.
- **Signal:** Command output is summarized as "passed" without exit status, scope, or relevant output. **Hidden risk:** closure relies on an unverifiable claim. **Required professional action:** parse outcome and evidence limit or mark not-verified. **Route to:** `agent-execution-discipline`. **Evidence required:** command, outcome, covered paths, proof limit.
- **Signal:** Validation ran before later material edits. **Hidden risk:** stale evidence supports a final diff it never exercised. **Required professional action:** rerun mapped validators or downgrade closure. **Route to:** `execution-trajectory-analysis`. **Evidence required:** command order, later edits, freshness verdict, next validator.
- **Signal:** A failed command is followed by an unrelated pass. **Hidden risk:** negative evidence is hidden. **Required professional action:** preserve failure and route repair or prove irrelevance. **Route to:** `failure-diagnosis`, `quality-test-gate`. **Evidence required:** failure class, affected path, relation to later pass, repair status.
- **Signal:** Graph shows no direct test edge and validation is guessed. **Hidden risk:** untested changed behavior is reported as covered. **Required professional action:** record missing test-edge residual risk or choose broader validator. **Route to:** `repository-graph-analysis`, `quality-test-gate`. **Evidence required:** searched graph scope, missing edge, selected fallback command.
- **Signal:** Generated artifacts or reports changed without source generator/build proof. **Hidden risk:** generated-only drift or stale report appears validated. **Required professional action:** map generated artifact to source and generator command. **Route to:** `repository-graph-analysis`, `delivery-release-gate`. **Evidence required:** source file, generator/build command, generated freshness.
- **Signal:** Memory says a path is fragile or trajectory says validation order is stale, but the selected command ignores graph edges. **Hidden risk:** prior experience, current graph, and execution order split into inconsistent proof. **Required professional action:** reconcile graph, memory, and trajectory before selecting scope. **Route to:** `project-memory-governance`, `repository-graph-analysis`, `execution-trajectory-analysis`. **Evidence required:** accepted/rejected memory, graph test edge, command order, selected validator, closure consequence.

# Risk Escalation Rules
- Escalate to full validation when changed paths cross module, registry, hook runtime, package, installation, generated artifact, release, migration, security, or adapter boundaries.
- Escalate when validation output is missing, unparseable, stale, partial, contradictory, or unsupported by the adapter.
- Escalate when negative validation evidence appears after a previous pass or after repair.
- Escalate when stop closure is requested with no fresh evidence for the final material diff.
- Escalate when a no-validator rationale is used for behavior, auth, data, integration, release, or generated-artifact changes.
- Escalate to `agent-execution-discipline` when an agent repeats the same failing command twice without route repair.

# Critical Details
- Changed-path mapping covers source, registries, docs, evals, benchmarks, hook runtime, reports, fixtures, lockfiles, generated artifacts, packages, tests, and install/build outputs.
- Validator depth is `narrow`, `module`, or `full`; selection must match blast radius, source-of-truth, generated artifact provenance, install/release risk, and security/privacy risk.
- Outcome parsing records command, order, exit status or equivalent outcome, relevant output summary, artifacts, covered paths, uncovered paths, and evidence limit.
- Freshness compares command order against final material edits, generated outputs, reports, fixtures, package/build products, and validation inputs.
- Negative evidence includes failed command, stale report, missing expected artifact, skipped command, unparseable output, warning that blocks closure, unsupported evidence channel, and contradicted prior pass.
- Stop closure status is `passed`, `failed`, `not-run`, `not-verified`, `stale`, `partial`, or `unsupported`. Load [references/validation-freshness-matrix.md](references/validation-freshness-matrix.md) for validator matrices and the output template.

# Failure Modes
- **Wrong validator:** A docs-only check is used after hook runtime or registry behavior changed.
- **Stale pass:** A pass before final edits is reported as current validation.
- **Outcome missing:** The handoff names a command but not result, scope, or evidence limit.
- **Partial inflation:** A single targeted check is described as complete regression coverage.
- **Negative evidence hidden:** A failed command is omitted because a later unrelated check passed.
- **Generated-only proof:** A generated artifact is validated without proving source generator freshness.
- **No-validator overclaim:** A no-op or docs-only rationale is used for behavior, release, or security-sensitive changes.
- **Coupling split brain:** graph, memory, and trajectory each suggest different validation depth, but closure reports only the cheapest command.

# Reference Loading Policy
The `SKILL.md` body carries selection, gates, output, and closure rules. Load only the reference needed for the active validation decision:
- Load [references/validation-freshness-matrix.md](references/validation-freshness-matrix.md) when comparing validator depth, parsing outcome/freshness, mapping generated artifacts, or drafting a concrete broker result.
- Load [references/graph-memory-trajectory-validator-map.md](references/graph-memory-trajectory-validator-map.md) when repository graph, project memory, execution trajectory, source/generated edges, or missing test edges change validation scope.
- Load [references/validation-stop-closure-ledger.md](references/validation-stop-closure-ledger.md) when negative evidence, stale/not-run status, rollback, residual risk, or final handoff needs a closure ledger.

# Output Contract
Return a `validation_broker_result` with:
- `mode_selected` (changed-path mapping, validator depth selection, outcome parsing, freshness repair, negative evidence ledger, or stop closure package).
- `boundaries_inspected` (source, registry/config/docs, tests/fixtures/evals, reports, generated artifacts, packages/install outputs, graph, memory, trajectory, and skipped boundaries with reason).
- `changed_path_map` (changed path or artifact, materiality, owner surface, source-vs-generated status, risk surface, validator candidates, and no-validator rationale).
- `validator_selection` (narrow/module/full decision, command list, selection reason, skipped validators, and escalation trigger).
- `validation_ledger` (command, order, outcome, parsed evidence, covered paths, uncovered paths, artifacts, freshness, and evidence limit).
- `negative_evidence` (failures, skipped checks, stale reports, warnings, missing output, unsupported channels, and repair/owner status).
- `graph_memory_trajectory_coupling` (graph test edges, memory validation gaps, trajectory order/freshness, accepted/rejected claims, and closure consequence).
- `business_semantic_validation` when BSP is selected: `validate-business-semantic-pack`, business semantic routing/review evals, rule/workflow golden cases, and residual semantic risk.
- `stop_closure_input` (passed, failed, not-run, not-verified, stale, partial, or unsupported; residual risk; next validator or owner).
- `evidence_limits` and `residual_risk` (what validation proves, what it does not prove, rollback note, and next gate).
- `handoff_package` (route/stage manifest linkage, validators run or skipped, rollback note, owner, reviewer, and residual risk).

# Evidence Contract
Close validation brokerage only when these answers are concrete:
- **Basis:** changed path, risk surface, command, and why validation depth changes closure.
- **Current evidence:** source, registry/config/docs, reports, generated outputs, tests, graph, memory, trajectory, and command output inspected.
- **Selection rationale:** why the chosen validator depth is sufficient and why skipped validators are not required or remain residual risk.
- **Freshness and parsing:** command outcome, covered paths, later edits, stale/partial/not-run/not-verified status, and negative evidence.
- **Closure and handoff:** changed-path-to-validation map, stop closure status, evidence limits, rollback note, residual risk, and next owner.

# Benchmark Coverage
This capability covers affected-test selection, validator depth calibration, CI outcome parsing, freshness rejection, negative evidence accounting, generated artifact provenance, build/install validation, graph-memory-trajectory reconciliation, stop-closure inputs, and evidence-limited handoff.

# Routing Coverage
Routes from `change-forge-router`, `quality-test-gate`, `delivery-release-gate`, `ai-code-review-refactor`, `change-documentation-gate`, and `agent-execution-discipline` should arrive here when validation selection, outcome parsing, freshness, negative evidence, changed-path mapping, generated artifact proof, or stop closure is at issue. Route away when the primary need is designing new tests, extracting graph edges, reconstructing execution order, or diagnosing a failure cause without a validation-selection decision.

# Quality Gate
1. Every material changed path, generated artifact, report, benchmark, package, or install output has a validator decision or explicit no-validator rationale.
2. Selected validation depth matches blast radius, source-of-truth, generated artifact provenance, and risk.
3. Results include command, outcome, scope, order, relevant output summary, artifacts, and evidence limit.
4. Stale, partial, not-run, not-verified, unsupported, or failed validation is not reported as a full pass.
5. Negative validation evidence is disclosed and reconciled with later passes.
6. Generated artifacts map to source and build/generator command before closure.
7. BSP changes run or explicitly defer the business semantic pack, routing, and review validators with evidence limits.
7. Graph, memory, and trajectory evidence are reconciled before stop closure.
8. Stop closure consumes broker status and names residual risk, rollback note, and next owner.

# Used By
`change-forge-router`, `quality-test-gate`, `delivery-release-gate`, `ai-code-review-refactor`, `change-documentation-gate`, `agent-execution-discipline`.

# Handoff
Hand off the broker result to final handoff, release, review, documentation, or repair owners. If validation is stale, failed, partial, not-run, not-verified, unsupported, or mismatched to changed paths, hand off the next required command, owner, and residual risk.

# Completion Criteria
The capability is complete when changed paths and risk surfaces map to appropriate validators, outcomes are parsed, freshness covers final material edits, negative evidence is preserved, generated artifacts have source/build proof, stop closure cannot overclaim verification, and residual risk is explicit.
