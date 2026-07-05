---
name: development-process-orchestrator
description: "Use this skill when implementing, reviewing, planning, or validating product or code changes that need compact PDD, DDD, SDD, and TDD traceability across problem definition, domain ownership, system design, logging decisions, and validation evidence."
license: MIT
changeforge_kind: professional-skill
changeforge_version: 0.1.0
metadata:
  changeforge.profile: recommended
  changeforge.skill_type: professional
---

# Development Process Orchestrator

## Mission
Keep code changes traceable from problem definition to domain ownership, system design, and validation evidence. This skill does not demand long documents. It requires a compact PDD, DDD, SDD, and TDD trace that proves the agent understood the problem, placed behavior in the right owner, designed failure and logging behavior, and validated the result.

## Stage Ownership

`development-process-orchestrator` owns or reviews only the stage slices where its declared surface changes the next engineering decision. It hands off adjacent API, security/privacy, data middleware, reliability, release, documentation, or domain-extension work to the selected owner or gate instead of acting as a catch-all.

## When To Use
- A code change spans multiple modules, ownership boundaries, or risk surfaces.
- A benchmark, review, or release gate needs evidence that PDD, DDD, SDD, and TDD were actually performed.
- Acceptance criteria, domain invariants, public API, failure modes, or logging decisions are unclear.
- An agent claims completion without mapping requirements to tests or validation commands.
- Work touches security, reliability, data, integration, backend, architecture, or public contracts.

## Do Not Use When
- A task is a pure documentation edit with no behavior, interface, validation, or operational evidence impact.
- The target project already contains an accepted and current process trace that maps acceptance, invariants, public API, failure modes, logging, and tests for the exact change.

## Adjacent Skill Conflict Resolution

For `development-process-orchestrator`, keep this skill primary only when PDD, DDD, SDD, TDD, stage discipline, phase traceability, or process-review evidence decides the next action. Hand API/schema compatibility to `data-api-contract-changer`, storage/query/migration concerns to `data-middleware-change-builder`, security/privacy decisions to `security-privacy-gate`, reliability/observability decisions to `reliability-observability-gate`, release/rollback readiness to `delivery-release-gate`, and documentation contract updates to `change-documentation-gate`. Domain extensions add risk-specific addenda after the primary owner is selected; record skipped plausible owners when the routing choice affects handoff or validation.

## Required Context / Missing Information Policy

Before `development-process-orchestrator` plans or closes work, collect current behavior, desired behavior, non-goals, affected surface, owner module, validation signal, existing conventions, and material data/API/security/release boundaries. Ask or block only when the missing fact can change public contract, data model, authorization, tenant behavior, migration/rollback, irreversible operation, or domain semantics; otherwise proceed with explicit reversible assumptions.

## Critical Gotchas

- `development-process-orchestrator` must inspect the owning source, tests, configs, docs, and generated-artifact boundaries before planning material engineering work.
- `development-process-orchestrator` must select only risk-changing references, capabilities, gates, or domain extensions; do not load nearby material because it exists.
- `development-process-orchestrator` must close with fresh validation evidence, evidence limits, residual risk, and next owner or gate when work remains.

## Non-Negotiable Rules
- **Runtime phase evidence is required**: for non-trivial engineering work,
  PDD, DDD, SDD, and TDD are ordered runtime phases in a bounded
  `process_phase_ledger`; final prose does not substitute for phase evidence.
- **Independent review gates each phase**: a phase is reviewed only when the
  latest independent `phase_review_result` passes with score >= 4, no
  critical/high blocker, and a reviewed artifact digest matching the current
  capsule or phase-ledger artifact. Reviewed phase status also requires a review
  ID. Implementer self-approval does not count.
- **PDD before implementation**: identify the problem, affected users or systems, acceptance criteria, constraints, non-goals, risk surfaces, and validation signal before coding.
- **DDD before placement**: identify domain terms, entity or value-object ownership, invariants, side-effect boundaries, and existing code owner before moving behavior.
- **SDD before edits**: name modules, files, public API, data flow, error contract, logging decision, design decision points, metrics/traces/alerts, performance, security, compatibility, migration, and rollback implications.
- **Design Choice Gate before implementation**: when a wrong answer could change architecture, public API, data, security, migration, rollback, acceptance, or user-visible behavior, stop and present user-facing options instead of silently choosing. Low-risk, local, reversible choices may proceed only as a documented safe assumption.
- **TDD closes the loop**: map PDD acceptance to tests, DDD invariants to tests or code constraints, SDD public API to tests, failure modes to tests, and logging/security decisions to tests or validation commands.
- **Repair requires re-review**: a failed phase or implementation review blocks
  the next stage until a repair event and passing re-review are tied to the
  original finding ID.
- **Evidence cannot be synthesized as complete**: case metadata may infer expected phases, but `present` requires parsed final trace, hook telemetry, explicit trace artifact, or grading evidence with specific content.
- **Generic process facts are insufficient**: template-only PDD/DDD/SDD/TDD language must fail unless it maps to case-specific tests, code constraints, or an explicit no-log rationale.
- **Do not over-document**: produce a compact trace that names concrete evidence, not a large planning document.

## Industry Benchmarks
- **IEEE 29148 requirements engineering**: acceptance and constraints must be verifiable and traceable.
- **Domain-Driven Design (Evans)**: domain terms, invariants, service boundaries, and side effects need explicit ownership.
- **C4 and architecture decision records**: system structure, interfaces, and tradeoffs should be visible at the right granularity.
- **Test-Driven Development and regression testing practice**: tests must prove behavior and failure modes, not just execute code.
- **OpenTelemetry and secure logging guidance**: logging decisions belong in system design and test evidence when they affect operations or security.

## Technical Selection Criteria
Use PDD, DDD, SDD, and TDD as a dependency chain. Later phases must reference earlier facts. For full phase schemas, expanded pass criteria, and anti-pattern detail, read `references/process-phase-contracts.md` when authoring or grading a process trace.

### Compact Trace Anchors
- PDD pass criteria: include `"problem": "one sentence"`, observable acceptance, constraints, non-goals, risk surfaces, validation signal, and evidence source.
- PDD anti-patterns: vague bug statement, untestable acceptance, hidden future scope, and completion without validation signal.
- DDD rules: include `"domain_terms": []`, ownership decision, invariants, side-effect boundary, and existing owner evidence.
- DDD pass criteria: invariants are concrete, ownership is named, side effects are placed outside pure domain objects, and each rule maps to a test or code constraint.
- Strict SDD trace skeleton: include `"logging_decision"`, `"design_decision_points"`, `user_choice_status`, `why_user_choice_is_needed`, `blocking` is a boolean, `"assumption_policy"`, and `block_when_wrong_answer_changes`.
- Do not use generic no-choice rationales; a safe assumption must be low-risk, local, reversible, conventional, and acceptance-neutral.
- SDD logging decision rules: name log type, level, placement, fields, redaction, correlation, cardinality, sink, retention, and tests or no-log rationale.
- SDD pass criteria: public API, data flow, error contract, failure modes, logging decision, compatibility, migration, rollback, and unresolved design choices are mapped to evidence.
- TDD pass criteria: include `"acceptance_to_tests": {}`, invariant/API/failure/logging/security mappings, validation commands, freshness, and red/green/refactor evidence.
- TDD anti-patterns: file-existence checks, private-helper assertions, lint-only proof, telemetry-only failures, stale reports, and empty boolean traceability.

## PDD - Problem / Product / Purpose Definition Discipline
PDD defines why the change exists. Capture `"problem"` plus impact, observable acceptance, constraints, non-goals, risk surfaces, and validation signal; reject vague bug statements, untestable acceptance, and future-feature scope expansion.

## DDD - Domain-Driven Design Discipline
DDD defines ownership without heavyweight tactical DDD. Capture `domain_terms`, entities/value objects/services/adapters, invariants, ownership decision, and side-effect boundaries; invariants map to tests or constraints, side effects stay outside pure domain objects, and helpers do not own business rules.

## SDD - System / Software / Structure Design Discipline
SDD defines how the change will be implemented and operated.

Schema anchor: `"logging_decision"` plus modules, files, public API, data flow, error contract, failure modes, observability, constraints, migration, and rollback.

SDD requires `"design_decision_points"` plus `no_design_choice_rationale` when empty. Ask the user when an answer can change architecture, public API, data, security, migration, rollback, acceptance, maintenance shape, or user-visible behavior; use bounded assumptions only for low-risk, local, reversible, conventional, and acceptance-neutral choices. Logging decisions name type, placement, fields, redaction, cardinality, sink, retention, and tests or no-log rationale; load `references/process-phase-contracts.md` for the full schema.

### Design Readiness Output

When there is design space, present alternatives before locking SDD:

- **Option A / Option B**: what it does, tradeoff, risk, and when to choose.
- **Recommendation**: the preferred option and why it best fits the inspected project context.
- **Design Summary**: Problem, Selected Approach, Rejected Alternatives, Open Decisions, and `Ready for implementation planning: Yes/No`.

If readiness is `No`, include one blocking question, owner, and why it blocks. Do not create an implementation plan while unresolved choices can change contract, architecture, data, security, migration, rollback, user-visible behavior, or acceptance.

## Anti-Patterns
- **Template phase completion**: reporting PDD, DDD, SDD, or TDD as done when only generic fallback fields exist; detect by missing concrete acceptance, invariant, API, and validation mappings; repair by downgrading status to inferred or missing.
- **Ownerless design choice**: deciding architecture, data model, security, rollback, or public API options without user/owner evidence; detect by material choice with no resolution evidence; repair by blocking or recording a bounded assumption.
- **Validation theater**: mapping phases to lint, file existence, or stale reports instead of changed-path behavior; detect by absent command, artifact, or freshness; repair through `quality-test-gate`.

## TDD - Test-Driven Development Discipline
TDD maps PDD, DDD, and SDD to validation. Capture `acceptance_to_tests`, invariant/public-API/failure-mode/logging/security mappings, concrete validation commands, and red/green/refactor evidence; reject file-existence checks, private-helper call assertions, empty boolean traceability, linter-only behavior proof, and telemetry-only failures.

## Mode Selection
Select the smallest process orchestration mode that can prove traceability.

| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities / gates | Skip guidance |
|---|---|---|---|---|---|
| Compact code-change trace | Non-documentation code change with acceptance, ownership, design, and validation implications. | Build one PDD/DDD/SDD/TDD trace without expanding into a planning document. | PDD acceptance, DDD invariants, SDD public API/failure modes, TDD mappings, validation commands, residual risk. | `change-intake-compiler`, `domain-impact-modeler`, `architecture-impact-reviewer`, `quality-test-gate` | Skip release, migration, or domain extensions unless surfaced by risk evidence. |
| Missing process evidence repair | final.md, hook telemetry, or reports claim completion but process facts are missing, generic, or inferred only. | Distinguish present, inferred, degraded, and missing evidence before counting compliance. | Parsed final trace or telemetry source, inferred fallback fields, missing mappings, validator output. | `agent-execution-discipline`, `ai-code-review-refactor`, `validation-broker` | Skip case-metadata fallback as completion evidence. |
| Logging-sensitive process trace | Logging, audit, security, retry, fallback, degradation, trace_id, request_id, or redaction is part of SDD/TDD. | Ensure the SDD logging decision maps to TDD logging/security validation. | Log type, placement, level, fields, redaction, correlation, cardinality control, tests or no-log rationale. | `logging-design-gate`, `security-privacy-gate`, `reliability-observability-gate` | Skip product logging when metrics/traces/tests are the explicit evidence source. |
| Coverage/reporting trace audit | Benchmark summary, Level 1 coverage, or professionalism report depends on process completion claims. | Keep registered coverage separate from actual run coverage and present evidence. | Run manifest, process-trace.json, coverage summary, actual run counts, validation command output. | `quality-test-gate`, `validate-report-consistency`, `eval-routing` | Skip live benchmark execution unless explicitly opted in. |

## Proactive Professional Triggers
These triggers are hidden-risk escalators, not ordinary checklist items.

- **Signal:** A final answer says PDD, DDD, SDD, or TDD was done but provides only generic fallback facts. **Hidden risk:** reports count template text as professional process completion. **Required professional action:** mark fallback fields inferred, require concrete phase content for present status, and validate mappings. **Route to:** `quality-test-gate`, `ai-code-review-refactor`. **Evidence required:** process-trace.json with evidence_sources, phase_status, and TDD mappings to validation commands.
- **Signal:** A case-specific mapping is accepted because case_id text appears beside mapping keys. **Hidden risk:** generic acceptance, owner-boundary templates, and candidate API placeholders pass as case-specific reasoning. **Required professional action:** require domain terms, concrete failure mode, non-generic invariants, public API evidence, and test/command references. **Route to:** `agent-execution-discipline`, `validation-broker`. **Evidence required:** validator failure or pass output naming concrete process facts.
- **Signal:** run.log records phase_completed ok for PDD/DDD/SDD/TDD without parsed final trace or telemetry. **Hidden risk:** synthetic logs misrepresent inferred process status as completed work. **Required professional action:** emit process_phase_evaluated with present, inferred, degraded, missing, or not_applicable status. **Route to:** `logging-design-gate`, `quality-test-gate`. **Evidence required:** structured log entries with status and error_category.
- **Signal:** A logging decision appears inside SDD without redaction, correlation, cardinality control, or tests. **Hidden risk:** operational logging leaks secrets or cannot be verified. **Required professional action:** invoke logging design validation and map logging decisions to TDD evidence or no-log rationale. **Route to:** `logging-design-gate`, `security-privacy-gate`. **Evidence required:** logging_decision object and validator output.
- **Signal:** Level 1 cases are listed in the registry and then described as actual run coverage. **Hidden risk:** hidden unverified coverage claims make release notes overstate benchmark evidence. **Required professional action:** verify registered cases separately from actual run cases in summaries and handoff. **Route to:** `quality-test-gate`, `change-documentation-gate`. **Evidence required:** cases.yaml registration, run summary actual_run counts, validation command output, and dry-run/live-run status.

## Risk Escalation
- Escalate PDD ownership to `change-intake-compiler` when problem, affected party, acceptance, constraints, non-goals, or validation signal are unclear.
- Escalate DDD ownership to `domain-impact-modeler` when domain terms, invariants, object ownership, or side-effect boundaries are unclear.
- Escalate SDD ownership to `architecture-impact-reviewer` when module boundaries, public API, data flow, error contract, compatibility, or rollback are unclear.
- Escalate TDD ownership to `quality-test-gate` when mapping, fixture, test level, negative path, or validation command is unclear.
- Escalate logging decisions to `logging-design-gate`.
- Escalate security and redaction to `security-privacy-gate`.
- Escalate observability beyond logs to `reliability-observability-gate`.
- Escalate implementation placement to `backend-change-builder`, `data-middleware-change-builder`, or `integration-change-builder` according to the changed layer.

## Critical Details
Compact trace format:

```text
Process Trace:
PDD: problem + acceptance + constraints
DDD: domain ownership + invariants + side-effect boundary
SDD: modules + public API + error/logging decision
TDD: tests/validation mapping
Validation:
Residual Risk:
```

The compact trace parser supports a bounded YAML-like subset: `key: value`, `key:` with indented child keys, nested `- item` lists, and simple scalar booleans. It is not a full YAML parser; avoid anchors, flow collections, folded or block scalars, multi-document YAML, and deeply nested structures in final.md process traces.

Use `present` only when concrete evidence exists in final.md compact trace, hook telemetry, explicit trace artifacts, or grading evidence. Use `inferred` for case metadata fallback, `degraded` for partial evidence, `missing` for no evidence, and `not_applicable` only with a specific reason.

## Failure Modes
Each failure mode must name condition or symptom, consequence or impact,
detection signal, prevention or repair, and required evidence. Otherwise,
return residual process, design, validation, or owner-decision risk.

- **Synthetic present phase**: the runner marks every phase `present` without parsed evidence.
- **Generic process facts**: `process_facts` use template claims that could fit any case.
- **Unmapped acceptance**: PDD acceptance criteria do not map to TDD tests.
- **Unproved invariant**: DDD invariants do not map to tests or code constraints.
- **Private or absent API proof**: SDD public API does not map to tests.
- **Untested failure mode**: failure modes lack tests.
- **Unsafe logging gap**: logging is required but redaction, fields, cardinality controls, and log/security tests are missing.
- **Coverage overclaim**: reports claim Level 1 actual coverage when only registration exists.

## Reference Loading Policy
Do not load every reference by default. For L1 `development-process-orchestrator` work, use this body unless selected risk requires more detail.
For L2, L3, L4, and L5 `development-process-orchestrator` work, read `references/capabilities/index.md` only to locate selected capability references; load selected files at `references/capabilities/<capability-id>-<capability-name>.md`, then add `references/process-output-and-gates.md` or domain references only when route risk requires them.

## Execution Procedure

For `development-process-orchestrator`: confirm activation and role; classify missing context; inspect relevant source/test/config/doc evidence; select mode, complexity, risk, and minimal references; execute or review only the owned surface; validate with concrete commands, diffs, tests, evals, or not-run limits; route repair through the owner; hand off with residual risk and next gate.

## Output Contract
Produce a compact process trace with `phase_status`, `process_facts`, and `traceability` for pdd, ddd, sdd, and tdd.

Booleans are not proof. The mappings inside `process_facts.tdd` are the proof.

- **Phase status:** return `present`, `inferred`, `degraded`, `missing`, or `not_applicable` for each core phase with evidence source.
- **Evidence sources:** name final.md, process-trace.json, hook telemetry, run.log, case metadata, report artifact, validator output, or explicit unavailable source.
- **Phase dependency chain:** show which PDD fact feeds which DDD owner/invariant, which SDD file/API/logging decision, and which TDD validator.
- **PDD fields required:** include problem, impact, acceptance criteria, constraints, non-goals, risk surfaces, and validation signal.
- **DDD fields required:** include domain terms, ownership decision, invariants, and side-effect boundaries.
- **SDD fields required:** include modules, files, public API, data flow, error contract, failure modes, logging decision, design decision points, no-choice rationale when empty, and assumption policy.
- **TDD fields required:** include acceptance, invariant, public API, failure-mode, logging/security, and validation command mappings.
- **Validation commands:** name command, exit code or not-run status, freshness, what evidence proves, and what it does not prove.
- **Coverage run status:** separate registered cases, dry-run cases, promoted cases, and actual live-run coverage.
- **Residual risk:** state inferred fields, missing evidence, unsupported final.md formatting, and coverage limits.
- **Handoff boundaries:** name process owner, independent review owner, skipped surfaces, and evidence limits.
- **Handoff:** name the next gate for mapping gaps, logging gaps, report consistency gaps, or release-evidence gaps.

## Evidence Contract
Close process orchestration only when the trace answers these evidence questions:
- **Files and boundaries inspected**: final.md, process-trace.json, hook telemetry, run.log, case metadata, prompt wrapper, and report artifacts inspected or explicitly unavailable.
- **Reuse / placement rationale**: final trace evidence is used first, hook telemetry second, and case metadata only as inferred fallback for missing fields; process ownership stays with PDD/DDD/SDD/TDD owner skills.
- **Behavior preservation**: existing benchmark assertions, validation commands, report consistency, and coverage semantics are preserved unless an explicit change request says otherwise.
- **Validation evidence**: process validator output, logging design validator output when SDD logging is present, deterministic tests, and benchmark dry-run/report validation.
- **What evidence proves**: present phases have concrete trace content and mapped tests; inferred phases are visible and cannot count as professional completion.
- **What evidence does not prove**: registered Level 1 cases are not actual run coverage, dry-run output is not live benchmark evidence, and generic fallback is not case-specific reasoning.
- **Residual risk**: parser support can miss unusual final.md formatting; strict mode should be used when release evidence requires all core phases present.
- **Next gate**: `quality-test-gate` for mapping gaps, `logging-design-gate` for logging decisions, and `ai-code-review-refactor` for cross-stage trace review.

## Quality Gate
- PDD, DDD, SDD, and TDD schemas are populated with case-specific facts.
- `present` is evidence-backed, not metadata-synthesized.
- Inferred evidence is counted separately from present evidence.
- PDD acceptance maps to TDD acceptance tests.
- DDD invariants map to tests or code constraints.
- SDD public API maps to tests.
- SDD error contract and failure modes map to failure tests.
- SDD logging decision maps to log/security tests or a no-log rationale.
- SDD design decision points are resolved, blocked, not required with concrete rationale, or assumed only under the safe-assumption policy.

## Handoff
Report the compact process trace, validation commands and results, residual risk, inferred versus present evidence, any missing mappings, and whether Level 1 coverage is registered only or actually run.

## Completion Criteria
- A reviewer can trace from problem to tests without reading private reasoning.
- Generic synthetic traces fail validation.
- Case-specific traces with mappings pass validation.
- Logging decisions are part of SDD and TDD when relevant.
- The final handoff names validation evidence and any limits.
