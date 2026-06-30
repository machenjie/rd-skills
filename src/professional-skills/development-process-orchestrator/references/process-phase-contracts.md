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
6. Design decision points that require user choice, are already resolved, are not required, or are safe assumptions.
7. Metrics, traces, and alerts.
8. Concurrency, performance, and security constraints.
9. Compatibility, migration, rollback, and recovery.

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
  "design_decision_points": [
    {
      "id": "sdd-choice-1",
      "decision": "What design decision must be made?",
      "trigger": "Why this decision exists",
      "why_user_choice_is_needed": "Why the agent must not silently choose",
      "options": [
        {
          "label": "A",
          "summary": "Option summary",
          "pros": ["specific benefit"],
          "cons": ["specific cost or risk"],
          "recommended_when": "When this option is appropriate"
        }
      ],
      "recommended_option": "A",
      "safe_default_if_user_unavailable": "A or none",
      "blocking": true,
      "user_choice_status": "required | resolved | not_required | assumed_with_rationale",
      "resolution_evidence": "user-selected option, explicit prior instruction, repository convention, or not resolved",
      "residual_risk": "what remains risky if any"
    }
  ],
  "no_design_choice_rationale": "why no material choice exists",
  "assumption_policy": "block_when_wrong_answer_changes_contract_architecture_data_security_acceptance_or_user_visible_behavior",
  "metrics_traces_alerts": [],
  "performance_or_concurrency_constraints": [],
  "compatibility_and_migration": [],
  "rollback_or_recovery": []
}
```

SDD Design Choice Gate rules:
- Ask the user when the answer can change architecture, public API, data model, security, permissions, migration, rollback, acceptance, long-term maintenance shape, or user-visible behavior.
- Typical blocking choices include new public APIs or exports, new modules/directories/services/shared packages, reuse versus new boundary, function versus class/object hierarchy, inheritance versus composition, cache/queue/worker/plugin/registry choices, config switches, migrations, permission/security/privacy changes, irreversible operations, and vague "optimize/enhance/refactor/professionalize" requests where cost/benefit depends on user preference.
- Do not ask for mechanical fixes, typo/format changes, local reversible choices, repository-conventional placement, code-fact-determined minimum fixes, or benchmark cases where the prompt/fixture already decides the option.
- Empty `design_decision_points` requires a concrete `no_design_choice_rationale`; generic "no choice needed" is not evidence.
- Required, blocking, material, or high-risk choices require `options`, `recommended_option`, `why_user_choice_is_needed`, and `residual_risk`; required/blocking choices need at least two options. Each option needs `label` and `summary`; required/blocking options also need `pros` or `cons`.
- `recommended_option` records the recommendation only, not user selection. Unresolved required/blocking choices cannot close as SDD present; resolved material choices require `resolution_evidence`; `not_required` material choices require prompt, fixture, user, repository, or reuse evidence.
- `assumed_with_rationale` requires a safe default plus local, reversible, conventional, and acceptance-neutral rationale, and must not be used for security, data, API, migration, rollback, auth, payment, irreversible, or permission choices.

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
- Design decision points are resolved, blocked for user choice, not required with concrete rationale, or safe assumptions under the assumption policy.
- Security, performance, and concurrency constraints are not ignored.

SDD anti-patterns:
- Adding a new module without reuse and placement rationale.
- Treating user-owned architecture, public API, data, security, migration, rollback, acceptance, or user-visible choices as agent defaults.
- Writing "no choice needed" without specific source, constraint, repository convention, or reuse evidence.
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
