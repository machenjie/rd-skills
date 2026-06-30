---
name: development-process-orchestrator
description: Orchestrates professional PDD, DDD, SDD, and TDD discipline for code changes by mapping problem definition, domain ownership, system design, logging decisions, and validation evidence into a compact trace.
license: MIT
changeforge_kind: professional-skill
changeforge_version: 0.1.0
---

# Development Process Orchestrator

## Mission
Keep code changes traceable from problem definition to domain ownership, system design, and validation evidence. This skill does not demand long documents. It requires a compact PDD, DDD, SDD, and TDD trace that proves the agent understood the problem, placed behavior in the right owner, designed failure and logging behavior, and validated the result.

## When To Use
- A code change spans multiple modules, ownership boundaries, or risk surfaces.
- A benchmark, review, or release gate needs evidence that PDD, DDD, SDD, and TDD were actually performed.
- Acceptance criteria, domain invariants, public API, failure modes, or logging decisions are unclear.
- An agent claims completion without mapping requirements to tests or validation commands.
- Work touches security, reliability, data, integration, backend, architecture, or public contracts.

## Do Not Use When
- A task is a pure documentation edit with no behavior, interface, validation, or operational evidence impact.
- The target project already contains an accepted and current process trace that maps acceptance, invariants, public API, failure modes, logging, and tests for the exact change.

## Non-Negotiable Rules
- **PDD before implementation**: identify the problem, affected users or systems, acceptance criteria, constraints, non-goals, risk surfaces, and validation signal before coding.
- **DDD before placement**: identify domain terms, entity or value-object ownership, invariants, side-effect boundaries, and existing code owner before moving behavior.
- **SDD before edits**: name modules, files, public API, data flow, error contract, logging decision, design decision points, metrics/traces/alerts, performance, security, compatibility, migration, and rollback implications.
- **Design Choice Gate before implementation**: when a wrong answer could change architecture, public API, data, security, migration, rollback, acceptance, or user-visible behavior, stop and present user-facing options instead of silently choosing. Low-risk, local, reversible choices may proceed only as a documented safe assumption.
- **TDD closes the loop**: map PDD acceptance to tests, DDD invariants to tests or code constraints, SDD public API to tests, failure modes to tests, and logging/security decisions to tests or validation commands.
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

## PDD - Problem / Product / Purpose Definition Discipline
PDD defines why the change exists. It is not a long requirements document.

Schema anchor: `"problem": "one sentence"` with impact, acceptance, constraints, non-goals, risk surfaces, and validation signal.

PDD pass criteria:
- Acceptance criteria are observable and can fail.
- Constraints cover compatibility, security, setup, and performance when relevant.
- Non-goals prevent scope expansion.
- Validation signal names commands, tests, or evidence artifacts.

PDD anti-patterns:
- "Fix the bug" without observed impact.
- Acceptance that cannot fail.
- Missing compatibility/security constraints.
- Future-feature scope expansion.

## DDD - Domain-Driven Design Discipline
DDD defines ownership and domain boundaries without forcing heavyweight tactical DDD.

Schema anchor: `"domain_terms": []` with entities, value objects, services, adapters, invariants, ownership decision, and side-effect boundaries.

DDD rules:
- Entities have identity/lifecycle; value objects are immutable values plus rules.
- Domain services hold pure cross-object domain rules.
- Application services orchestrate workflow, transactions, and adapters.
- Adapters own DB, HTTP, Kafka, Redis, SDK, filesystem, queue, and provider details.
- Helpers may hold generic technical logic but must not hide business semantics.
- Pure domain objects must not import transport, persistence, queue, filesystem, or provider SDK clients.

DDD pass criteria:
- Invariants map to tests or code constraints.
- Ownership and existing code owner are explicit.
- Side effects stay outside pure domain objects.
- Helpers do not own business rules.

DDD anti-patterns:
- Moving behavior into a shared utility for convenience.
- Testing private helpers instead of public domain behavior.
- Mixing provider calls into domain objects.
- Treating DTOs or persistence rows as domain entities.

## SDD - System / Software / Structure Design Discipline
SDD defines how the change will be implemented and operated.

Schema anchor: `"logging_decision"` plus modules, files, public API, data flow, error contract, failure modes, observability, constraints, migration, and rollback.

SDD Design Choice Gate schema anchor: include `"design_decision_points"` with `id`, `decision`, `trigger`, `options`, `recommended_option`, `blocking`, `user_choice_status`, `resolution_evidence`, and `residual_risk`; include `no_design_choice_rationale` when the list is empty; set `"assumption_policy"` to `block_when_wrong_answer_changes_contract_architecture_data_security_acceptance_or_user_visible_behavior`. Load `references/process-phase-contracts.md` for the full JSON schema.

SDD design choice rules:
- `design_decision_points` is always present and is a list. It may be empty only with a concrete `no_design_choice_rationale` tied to user constraints, source evidence, repository convention, or reuse evidence.
- `user_choice_status` is exactly one of `required`, `resolved`, `not_required`, or `assumed_with_rationale`.
- `blocking=true` with `user_choice_status=required` cannot close as implementable SDD evidence.
- `assumed_with_rationale` is only for low-risk, local, reversible, conventional, acceptance-neutral choices.
- If a wrong answer could alter contract, architecture, data, security, acceptance, migration, rollback, public API, or user-visible behavior, the choice must be `required` or `resolved`, not a safe assumption.

SDD logging decision rules:
- Retry, fallback, and degradation paths distinguish retryable, intermediate, and final failure.
- Security boundaries log denial category and policy, never raw secret-bearing input.
- Needed logs require type, placement, event, level, field, redaction, cardinality, and test evidence.
- Audit logs are separate from diagnostic logs, with sink/retention rationale when both exist.
- High-frequency paths prefer metrics, sampling, or rate limiting over per-event INFO.
- Production errors include error_code or error_category plus correlation identifiers.
- Raw payloads, tokens, cookies, auth headers, signatures, code, session IDs, and high-cardinality metric labels are forbidden.

SDD pass criteria:
- Public API can be imported or used by tests.
- File placement matches DDD ownership.
- Failure modes have error categories.
- Logging is explicit or has a no-log rationale.
- Material design choices are resolved, blocked for user selection, or justified as safe assumptions.
- Security, performance, and concurrency constraints are addressed.

SDD anti-patterns:
- Adding a new module without reuse and placement rationale.
- Silently choosing between material design options that require user or owner preference.
- Using generic "no choice needed" rationale instead of source, constraint, repository-convention, or reuse evidence.
- Exposing private helpers for tests.
- Hiding adapter side effects inside mappers or DTOs.
- Saying "structured logging" without type, level, fields, redaction, and tests.

## TDD - Test-Driven Development Discipline
TDD maps PDD, DDD, and SDD to validation. It is not formalism that every test must be written first.

Schema anchor: `"acceptance_to_tests": {}` plus invariant, public API, failure-mode, logging/security, validation command, and red/green/refactor mappings.

TDD pass criteria:
- Acceptance criteria trace to tests.
- DDD invariants trace to tests or code constraints.
- SDD public API, error contract, and failure modes trace to tests.
- Logging/security decisions trace to tests or explicit no-log rationale.
- Validation commands are concrete and avoid hidden external state.

TDD anti-patterns:
- Only checking that files exist.
- Testing private helper call order instead of public behavior.
- Claiming traceability with booleans while mappings are empty.
- Treating a linter pass as behavior evidence.
- Deleting assertion tests or turning failures into telemetry-only cases.

## Mode Matrix
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

## Risk Escalation Rules
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
- **Synthetic present phase**: the runner marks every phase `present` without parsed evidence.
- **Generic process facts**: `process_facts` use template claims that could fit any case.
- **Unmapped acceptance**: PDD acceptance criteria do not map to TDD tests.
- **Unproved invariant**: DDD invariants do not map to tests or code constraints.
- **Private or absent API proof**: SDD public API does not map to tests.
- **Untested failure mode**: failure modes lack tests.
- **Unsafe logging gap**: logging is required but redaction, fields, cardinality controls, and log/security tests are missing.
- **Coverage overclaim**: reports claim Level 1 actual coverage when only registration exists.

## Reference Loading Policy
Read `references/capabilities/index.md` only after the route selects the capabilities needed for this change. Load only the selected capability references for the active L1, L2, L3, L4, or L5 route. Do not load all references by default. Load [references/process-phase-contracts.md](references/process-phase-contracts.md) when authoring or grading detailed phase evidence. Load [references/process-output-and-gates.md](references/process-output-and-gates.md) when the full output fields, handoff routing, or closure gate are needed. Load [references/checklist.md](references/checklist.md) for a fast self-review before handoff. For deeper capability detail, read `references/capabilities/<capability-id>-<capability-name>.md` for the selected capability and any explicitly named companion reference.

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
