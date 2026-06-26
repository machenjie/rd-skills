# Process Phase Contracts

Use this reference when the route selects `development-process-orchestrator` and the agent must author, grade, or repair detailed PDD, DDD, SDD, and TDD evidence. The `SKILL.md` body keeps the operational contract; this file preserves the detailed phase rules without forcing every invocation to load them.

## PDD - Problem / Product / Purpose Definition Discipline
PDD defines why the change exists. It answers:
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
DDD defines ownership and domain boundaries. It answers:
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
TDD maps the first three phases to validation. It answers:
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
