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
- **SDD before edits**: name modules, files, public API, data flow, error contract, logging decision, metrics/traces/alerts, performance, security, compatibility, migration, and rollback implications.
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
Use PDD, DDD, SDD, and TDD as a dependency chain. Later phases must reference earlier facts.

## PDD - Problem / Product / Purpose Definition Discipline
PDD defines why the change exists. It is not a long requirements document. It answers:
1. Current problem.
2. User, caller, system, or operations impact.
3. Observable acceptance criteria.
4. Behaviors that must remain unchanged.
5. Non-goals.
6. Risk surfaces.
7. Validation signal.

Output schema:

```json
{
  "problem": "one sentence",
  "user_or_system_impact": [],
  "acceptance_criteria": [],
  "constraints": [],
  "non_goals": [],
  "risk_surfaces": [],
  "validation_signal": []
}
```

PDD pass criteria:
- Acceptance criteria can be verified by tests, logs, metrics, command output, or manual inspection.
- Constraints include compatibility, security, setup, and performance when relevant.
- Non-goals prevent unnecessary design expansion.
- Validation signals point to concrete commands, tests, or evidence artifacts.

PDD anti-patterns:
- "Fix the bug" without observed impact.
- Acceptance criteria that cannot fail.
- Ignoring compatibility or security constraints.
- Expanding scope because a future feature might need it.

## DDD - Domain-Driven Design Discipline
DDD defines ownership and domain boundaries. It does not force complex tactical DDD. It answers:
1. Domain terms.
2. Entities and lifecycle identity.
3. Value objects and immutable rule values.
4. Domain services for pure cross-object domain rules.
5. Application services that orchestrate workflow, transactions, and adapters.
6. Adapters or infrastructure for DB, HTTP, Kafka, Redis, SDKs, filesystem, and providers.
7. Invariants.
8. Allowed side-effect locations.
9. Existing code owner.

Output schema:

```json
{
  "domain_terms": [],
  "entities": [],
  "value_objects": [],
  "domain_services": [],
  "application_services": [],
  "adapters": [],
  "invariants": [],
  "ownership_decision": [],
  "side_effect_boundaries": []
}
```

DDD rules:
- An entity has identity and lifecycle.
- A value object is immutable value plus rules.
- A domain service contains pure domain logic across objects.
- An application service orchestrates workflow, transactions, and adapters.
- An adapter owns DB, HTTP, Kafka, Redis, SDK, filesystem, queue, and provider details.
- A helper may hold generic technical logic but must not hide business semantics.
- A pure domain object must not import requests, DB clients, payment SDKs, Kafka, Redis, filesystem, or provider SDKs.

DDD pass criteria:
- Invariants map to code or tests.
- Ownership decision is explicit.
- Side effects stay outside pure domain objects.
- Helpers do not own business rules.

DDD anti-patterns:
- Moving behavior into a shared utility because it is convenient.
- Testing private helpers instead of public domain behavior.
- Mixing provider calls into domain objects.
- Treating DTOs or persistence rows as domain entities.

## SDD - System / Software / Structure Design Discipline
SDD defines how the change will be implemented. It answers:
1. Modules and files to change, with rationale.
2. Public API.
3. Data flow.
4. Error contract and failure modes.
5. Logging decision.
6. Metrics, traces, and alerts.
7. Concurrency, performance, and security constraints.
8. Compatibility, migration, rollback, and recovery.

Output schema:

```json
{
  "modules": [],
  "files_to_change": [],
  "public_api": [],
  "data_flow": [],
  "error_contract": [],
  "failure_modes": [],
  "logging_decision": {
    "needed": true,
    "log_types": [],
    "placement": [],
    "events": [],
    "levels": [],
    "fields": [],
    "redaction": [],
    "correlation": [],
    "cardinality_controls": [],
    "tests_or_validation": [],
    "rationale": ""
  },
  "metrics_traces_alerts": [],
  "performance_or_concurrency_constraints": [],
  "compatibility_and_migration": [],
  "rollback_or_recovery": []
}
```

SDD logging decision rules:
- Retry, fallback, and degradation paths must distinguish retryable, intermediate, and final failure.
- Security boundaries log denial category and policy, never raw secret-bearing input.
- When logging is needed, `log_types`, `placement`, `events`, `levels`, `fields`, `redaction`, `cardinality_controls`, and tests or validation evidence are mandatory.
- Audit action logs are separate from diagnostic logs, with separate sink and retention rationale when both log types are present.
- High-frequency paths prefer metrics, sampling, or rate limiting over per-event INFO.
- Production error logs include error_code or error_category plus correlation identifiers.
- Raw payload, query, body, token, password, cookie, authorization header, signature, code, and session identifiers are forbidden.
- High-cardinality metric labels are forbidden.

SDD pass criteria:
- Public API can be imported or used by tests.
- File placement matches DDD ownership.
- Failure modes have error categories.
- Logging decision is explicit or includes a no-log rationale.
- Security, performance, and concurrency constraints are not ignored.

SDD anti-patterns:
- Adding a new module without reuse and placement rationale.
- Exposing private helpers for tests.
- Hiding adapter side effects inside mappers or DTOs.
- Saying "structured logging" without type, level, fields, redaction, and tests.

## TDD - Test-Driven Development Discipline
TDD maps the first three phases to validation. It is not formalism that every test must be written first. It answers:
1. Which tests prove PDD acceptance criteria.
2. Which tests or code constraints prove DDD invariants.
3. Which tests use SDD public API.
4. Which tests cover failure modes.
5. Which tests cover logging fields, redaction, or security denial when logging is needed.
6. Which validation commands produce evidence.

Output schema:

```json
{
  "acceptance_to_tests": {},
  "invariant_to_tests_or_code": {},
  "public_api_to_tests": {},
  "failure_mode_tests": [],
  "logging_or_security_tests": [],
  "validation_commands": [],
  "red_green_refactor_trace": []
}
```

TDD pass criteria:
- Happy path and relevant failure path are covered.
- Acceptance criteria trace to tests.
- Invariants trace to tests or code.
- Public API traces to imports or tests.
- Logging redaction and fields are tested when logging is needed.
- Validation commands exist and do not depend on hidden external state.

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
- The runner marks every phase `present` without parsed evidence.
- `process_facts` use generic template claims that could fit any case.
- PDD acceptance criteria do not map to TDD tests.
- DDD invariants do not map to tests or code constraints.
- SDD public API does not map to tests.
- Failure modes lack tests.
- Logging is required but redaction, fields, cardinality controls, and log/security tests are missing.
- Reports claim Level 1 actual coverage when only registration exists.

## Reference Loading Policy
Read `references/capabilities/index.md` only after the route selects the capabilities needed for this change. Load only the selected capability references for the active L1, L2, L3, L4, or L5 route. Do not load all references by default. For deeper capability detail, read `references/capabilities/<capability-id>-<capability-name>.md` for the selected capability and any explicitly named companion reference.

## Output Contract
Produce a compact process trace with four phase objects and a TDD mapping:

```json
{
  "phase_status": {
    "pdd": "present",
    "ddd": "present",
    "sdd": "present",
    "tdd": "present"
  },
  "process_facts": {
    "pdd": {},
    "ddd": {},
    "sdd": {},
    "tdd": {}
  },
  "traceability": {
    "pdd_acceptance_to_tdd_tests": true,
    "ddd_invariants_to_tdd_tests": true,
    "sdd_public_api_to_tdd_tests": true,
    "sdd_failure_modes_to_tdd_tests": true,
    "sdd_logging_to_tdd_tests": true
  }
}
```

Booleans are not proof. The mappings inside `process_facts.tdd` are the proof.

- **Phase status:** return `present`, `inferred`, `degraded`, `missing`, or `not_applicable` for each core phase with evidence source.
- **PDD fields required:** include problem, impact, acceptance criteria, constraints, non-goals, risk surfaces, and validation signal.
- **DDD fields required:** include domain terms, ownership decision, invariants, and side-effect boundaries.
- **SDD fields required:** include modules, files, public API, data flow, error contract, failure modes, and logging decision.
- **TDD fields required:** include acceptance, invariant, public API, failure-mode, logging/security, and validation command mappings.
- **Residual risk:** state inferred fields, missing evidence, unsupported final.md formatting, and coverage limits.
- **Handoff:** name the next gate for mapping gaps, logging gaps, or report consistency gaps.

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

## Handoff
Report the compact process trace, validation commands and results, residual risk, inferred versus present evidence, any missing mappings, and whether Level 1 coverage is registered only or actually run.

## Completion Criteria
- A reviewer can trace from problem to tests without reading private reasoning.
- Generic synthetic traces fail validation.
- Case-specific traces with mappings pass validation.
- Logging decisions are part of SDD and TDD when relevant.
- The final handoff names validation evidence and any limits.
