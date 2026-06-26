---
name: dto-schema-design
description: Designs DTO schemas that decouple external contracts from internal models with validation, nullability, defaults, and compatibility rules.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "27"
changeforge_version: 0.1.0
---

# Mission

Design DTO schemas as explicit, versioned, stable transfer contracts that decouple external API, event, form, SDK, view-model, and integration shapes from internal domain and persistence models. A DTO contract must define field types, nullability, absent/default semantics, validation, serialization, mapping ownership, compatibility, security/privacy filtering, and validation evidence without leaking ORM, database, generated-client, or domain internals.

# When To Use

Use this capability when a change adds or modifies request bodies, response bodies, query parameter objects, form submission models, SDK/public types, Protobuf messages, Avro/JSON schemas, event payload fields, view models, projection DTOs, error response payloads, generated client models, DTO-to-domain mappers, null/default behavior, field names, field types, enum values, validation constraints, or schema evolution for existing consumers.

# Do Not Use When

Do not use this capability to design the domain object, source-of-truth persistence model, endpoint operation semantics, transport retry behavior, or error taxonomy by itself. Do not expose ORM entities, database rows, ActiveRecord/Hibernate/JPA/SQLAlchemy models, generated provider models, or internal aggregate objects as DTOs. Route to `data-model-design` for stored data shape, `api-contract-design` for endpoint behavior, `error-code-design` for error taxonomy, `domain-event-modeling` for durable event facts, and `model-boundary-mapping` when DTO/domain/persistence ownership is unclear.

# Stage Fit

Use during planning when a DTO, schema, field, null/default rule, generated model, or consumer contract is being introduced or changed. Use during coding and refactoring review when mappers, assemblers, serializers, request validators, generated clients, SDK exports, or DTO/domain/persistence boundaries change. Use during bug-fix, debugging, testing, code-review, and release when mass assignment, null-vs-absent behavior, enum compatibility, sensitive-field exposure, or rollback/client skew needs evidence. Hand off when operation semantics, stored data, release sequencing, security review, or consumer contract tests become the primary decision.

# Non-Negotiable Rules

- **DTOs are contract boundaries, not internal models.** A database migration, ORM rename, or domain refactor must not automatically rename or expose DTO fields.
- **Request DTOs validate before domain logic.** Allowlist every accepted field, reject unknown request fields, and never spread/autobind request bodies into commands or domain objects.
- **Null, absent, empty, and defaulted are different states.** For each nullable or optional field, specify whether `null`, missing, empty string/list/object, and default value mean clear, no-op, unknown, not-applicable, or zero-content.
- **Required and optional are semantic decisions.** Required means the DTO cannot be interpreted without the field. Optional fields still need absence semantics, examples, and compatibility rules.
- **Serialization format drives field conventions.** JSON and GraphQL normally use `camelCase`; Protobuf uses `snake_case`; XML/SOAP may use `PascalCase`. Mixed conventions in one DTO require a migration rationale.
- **Field types must be exact enough for the risk.** Money uses decimal string or minor-unit integer plus ISO 4217 currency, datetimes use RFC 3339/ISO 8601 UTC, identifiers use stable opaque ids, and enums document unknown handling.
- **Schema evolution is compatibility-first.** Add optional fields safely; treat removal, rename, type change, optional-to-required, validation tightening, and semantic change as breaking until proven otherwise.
- **Sensitive and permission-dependent fields are explicit.** Tenant, object, role, permission, PII, financial, health, token, or audit fields need allowed consumers, redaction/filtering, and denied-case validation.

# Mode Matrix

| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities / gates | Skip guidance |
| --- | --- | --- | --- | --- | --- |
| New DTO contract | New request, response, event payload, form, SDK type, generated model, or view model. | Define field semantics, validation, mapping owner, examples, compatibility, and contract tests before implementation. | Schema convention, consumer/use case, field table, mapper owner, examples, validation command. | `api-contract-design`, `input-validation`, `contract-testing` | Storage schema and endpoint semantics unless they are changing. |
| Existing DTO evolution | Field added, removed, renamed, retyped, made required, defaulted, deprecated, or semantically changed. | Preserve old clients, generated clients, validation behavior, rollback, and mixed-version safety. | Old/new schema diff, consumer inventory, compatibility class, migration/deprecation plan. | `version-compatibility`, `consumer-impact-analysis`, `quality-test-gate` | In-place breaking edit without bridge/version. |
| Boundary separation repair | ORM/domain/generated/provider model leaks into request, response, SDK, or view model. | Reassert DTO/domain/persistence/event boundaries and mapping ownership. | Source/target model map, internal/public field split, mapper/assembler placement, behavior preservation. | `model-boundary-mapping`, `data-model-design`, `implementation-structure-design` | Returning entity rows as DTOs. |
| Validation and error payload | Request validation, field constraints, RFC 7807/9457 problem details, or invalid-shape handling changes. | Make validation enforceable and client-actionable without leaking internals. | Constraint table, unknown-field behavior, error DTO, negative examples, validator output. | `error-code-design`, `input-validation`, `security-privacy-gate` | Generic string errors. |
| Sensitive or permissioned DTO | Tenant, object, role, scope, PII, financial, health, audit, credential, or privileged fields appear. | Minimize fields, protect object authorization, and prove denied exposure paths. | Data classification, allowed consumers, redaction/filtering rule, denied test or not-verified risk. | `security-privacy-gate`, `permission-boundary-modeling` | Convenience exposure of internal fields. |
| Generated schema or SDK surface | OpenAPI, Protobuf, Avro, GraphQL, JSON Schema, SDK, or public export is generated or diffed. | Keep source schema, generated artifacts, and downstream compile/contract checks aligned. | Schema path, generator command, generated diff, reserved fields/numbers, contract test. | `sdk-library-contract-design`, `contract-testing`, `version-compatibility` | Manual DTO edits that drift from generated source. |

# Industry Benchmarks

Anchor against OpenAPI 3.1 and JSON Schema 2020-12 for request/response schemas, RFC 7807/9457 for error DTOs, Protobuf 3 field-number stability, Avro unions/defaults and schema registry compatibility, GraphQL SDL and generated clients, Google AIP field guidance, OWASP API3/API8 for mass assignment and internal-detail exposure, consumer-driven contract testing, and Postel-style forward compatibility for response readers. Keep this body focused on selection, evidence, output, and quality gates; load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) for detailed null-state, type, mapping, compatibility, generated-artifact, privacy, graph-memory-trajectory, and validation matrices.

# Selection Rules

Select this capability when **field-level transfer schema design** is primary. Adjacent routing:

- Prefer `api-contract-design` when endpoint behavior, HTTP/gRPC operation semantics, status codes, pagination, idempotency, or auth requirements are primary.
- Prefer `data-model-design` when the source-of-truth persistence model, invariants, relationships, or lifecycle states are primary.
- Prefer `domain-event-modeling` when the DTO is a durable domain or integration event fact.
- Prefer `error-code-design` when client-facing error taxonomy and remediation are primary.
- Prefer `version-compatibility` when mixed-version rollout, rollback, deprecation, generated-client impact, or unknown consumers dominate.
- Prefer `contract-testing` when executable provider/consumer verification is the main work.

# Risk Escalation Rules

Escalate when a DTO is public, partner-facing, mobile-facing, generated into SDKs, event-carried, permission-sensitive, tenant-scoped, PII/financial/health-bearing, used for mutating commands, or consumed by unknown clients. Escalate when null/absent behavior changes PATCH semantics, an enum expands without unknown handling, a required field is added, a field meaning changes without rename/versioning, an internal persistence field leaks, a generated artifact is stale, or prior memory claims consumers are absent without current source and telemetry evidence.

# Proactive Professional Triggers

- **Signal:** controller, handler, mapper, or client returns an entity, row, provider model, or generated internal type. **Hidden risk:** persistence or provider internals become a public contract. **Required professional action:** define DTO boundary and explicit mapper. **Route to:** `model-boundary-mapping`, `data-model-design`. **Evidence required:** source/target field map and rejected direct exposure.
- **Signal:** request binding spreads or auto-binds all incoming fields. **Hidden risk:** mass assignment, object-property authorization bypass, and unvalidated domain mutation. **Required professional action:** require allowlisted mapping and strict unknown-field handling. **Route to:** `input-validation`, `security-privacy-gate`. **Evidence required:** request schema, mapper snippet or test, denied unknown-field case.
- **Signal:** nullable/optional/defaulted field lacks null, absent, empty, and default semantics. **Hidden risk:** PATCH, form, mobile, and generated-client behavior diverge silently. **Required professional action:** write the four-state semantic table. **Route to:** `version-compatibility`, `quality-test-gate`. **Evidence required:** examples and validation/mapping cases.
- **Signal:** field is renamed, removed, retyped, made required, validation-tightened, or given new meaning. **Hidden risk:** old clients, SDKs, and stored fixtures break even if local code passes. **Required professional action:** classify compatibility and choose version, bridge, or deprecation. **Route to:** `consumer-impact-analysis`, `contract-testing`. **Evidence required:** old/new diff, consumer inventory, contract proof or residual risk.
- **Signal:** schema or generated client is referenced from project memory, repository graph, or prior trajectory without current source check. **Hidden risk:** stale generated artifacts or hidden consumers make the DTO contract wrong. **Required professional action:** confirm current schema, generated files, callers, tests, and reports. **Route to:** `repository-context-map`, `repository-graph-analysis`, `project-memory-governance`, `execution-trajectory-analysis`. **Evidence required:** inspected paths, accepted/rejected memory, freshness limits.
- **Signal:** DTO includes tenant, object, role, permission, PII, financial, health, token, or audit fields. **Hidden risk:** over-exposure, IDOR, or privacy breach through a stable contract. **Required professional action:** classify data, minimize fields, and require object/consumer authorization. **Route to:** `security-privacy-gate`, `permission-boundary-modeling`. **Evidence required:** allowed consumers, redaction/filtering rule, denied-case validation.

# Critical Details

DTO stability is a client contract commitment. Precision failures:

- **Mass assignment vulnerability.** `const cmd = { ...req.body }` lets an attacker send fields such as `isAdmin`, `role`, or `price` unless every field is allowlisted and unknown fields are rejected.
- **Null vs absent confusion.** In PATCH, `null` may mean clear, while absent may mean no change. Treating both the same can erase data or block valid updates.
- **Decimal precision loss.** JSON `number` is unsafe for money. Use decimal string or integer minor units plus currency.
- **Enum forward compatibility.** Consumers that exhaustively switch without default handling can fail when a response adds a valid enum value.
- **Generated contract drift.** Editing DTO code while OpenAPI/proto/GraphQL sources or generated clients stay stale makes validation lie.
- **Business logic in assemblers.** Response DTOs can format or select fields, but tax, permission, lifecycle, and pricing decisions belong in domain/service policy.
- **Circular DTO nesting.** Recursive DTO graphs need depth limits or id references; otherwise serializers can recurse indefinitely.
- **Protobuf field number reuse.** Removed field numbers must be reserved. Reusing a number corrupts binary compatibility.

### Anti-examples

| Anti-pattern | Failure |
| --- | --- |
| `return entity` from controller | Internal model exposed; storage rename breaks clients |
| `{ ...req.body }` into command | Mass assignment and object-property authorization bypass |
| Money as `number` | Rounding error and reconciliation drift |
| Nullable field with no absent/null semantics | PATCH behavior differs across clients |
| New enum value with no unknown handling | Strict clients reject or ignore valid responses |
| Response assembler owns tax or permission calculation | Domain rule drift between display and execution |
| Protobuf field number removed then reused | Old messages deserialize as the wrong field |
| Request DTO accepts undeclared fields | Hidden fields pass through validation boundary |

# Failure Modes

- Profile update accepts `role: "admin"` because request DTO is auto-bound to a domain command.
- ORM field `created_by_user_id` leaks into response and becomes a client dependency.
- `amount: 19.99` is parsed imprecisely and invoice totals differ across systems.
- Mobile client sends missing address to mean no-op, but server treats missing as clear.
- Enum value `SUSPENDED` is added and old generated client throws on unknown.
- Required `currency` is added to a payment request without a new version; deployed clients receive 422.
- OpenAPI schema is updated but generated TypeScript SDK is stale; consumers compile against the old shape.
- Response DTO includes internal tenant/object ids without permission filtering.
- Protobuf field number is reused and old stored binary messages deserialize incorrectly.
- Project memory says no consumers, but current repository contains a generated SDK and a dashboard fixture using the field.

# Reference Loading Policy

The `SKILL.md` body carries L1/L2 DTO selection, boundary, and evidence rules. Load [references/checklist.md](references/checklist.md) when drafting or reviewing a concrete DTO schema, field change, mapper, validation rule, generated artifact, or consumer contract. Load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) when null/default semantics, type selection, DTO-to-domain mapping, compatibility classification, Protobuf/Avro/OpenAPI/GraphQL details, privacy filtering, graph-memory-trajectory coupling, or validation matrices are needed. Use [examples/example-output.md](examples/example-output.md) only when the expected output shape is unclear. Do not load references for pure routing or metadata-only edits with no DTO contract decision.

# Output Contract

Return a DTO schema contract with:

- `mode_selected` (new DTO contract, existing DTO evolution, boundary separation repair, validation and error payload, sensitive/permissioned DTO, generated schema or SDK surface)
- `boundaries_inspected` (schema files, generated artifacts, DTO classes, mappers, validators, API docs, consumers, tests, registry/config, and prior memory accepted or rejected)
- `source_evidence` (current-source observations that prove the DTO shape, consumers, generated artifacts, and mapper behavior)
- `graph_memory_trajectory_judgment` (accepted, rejected, or not verified claims about consumers, field semantics, generated artifacts, prior validation, or ownership)
- `dto_name`, `direction`, `purpose`, `owner`, and `contract_surface` (request, response, event payload, error, form, SDK type, view model)
- `fields` (name, type/format, required/optional, nullable, absent semantics, empty semantics, default, validation, example, sensitivity, read/write mode, semantics)
- `additional_properties_policy` (request strictness, response forward-compatibility, and unknown-field behavior)
- `validation_rules` (field and cross-field constraints, unknown field handling, validation error mapping)
- `mapping_spec` (DTO to command/domain/persistence/view/event mapping with allowlisted fields and mapper owner)
- `compatibility_classification` (per field and per DTO: additive, conditional, breaking, bridge/version/deprecation needed)
- `schema_version_and_source` (OpenAPI/JSON Schema/proto/Avro/GraphQL location, registry/generator, generated-client impact)
- `examples` (happy path, null, absent, empty, default, boundary, invalid, sensitive-field-filtered, old/new compatibility)
- `consumer_contract_tests` (Pact, OpenAPI validator, Schemathesis, buf breaking, schema registry, generated-client compile, fixture replay, or residual risk)
- `changed_dto_to_validation_map` (each field, mapper, validation rule, generated artifact, consumer class, privacy rule, and compatibility path mapped to validation)
- `reuse_and_placement_rationale` (existing schema/DTO/mapper/generator reused or rejected; why no internal model or new shared abstraction was exposed)
- `behavior_preservation` (old DTO shape, old clients, old generated artifacts, old validators, old mappers, and rollback behavior preserved or migrated)
- `validation_evidence` (commands, validators, reports, fixtures, artifacts, exit codes, or not-verified disclosure)
- `handoff_boundaries` (API operation, data model, error taxonomy, compatibility, security, contract testing, release, docs)
- `evidence_limits` (unknown consumers, stale generated clients, unqueried telemetry, untested rollback, unverified privacy filtering, and residual risk owner)

# Evidence Contract

Close a DTO schema design only when these answers are concrete:

- **Boundaries inspected:** name schema files, DTO classes, mappers, validators, generated clients, API docs, consumers, tests, registry/config, and prior memory checked. If no implementation exists, say so.
- **What evidence proves:** state which current-source facts prove field semantics, null/default behavior, validation, mapping, compatibility, generated artifacts, consumers, and sensitive-field filtering.
- **What evidence does not prove:** call out unknown consumers, untested generated-client languages, production telemetry gaps, stale project memory, mobile/partner skew, rollback, or privacy paths not inspected.
- **Validation evidence:** include command names, validators, reports, fixture names, artifacts, exit code/result, and freshness after the final edit.
- **Reuse / placement rationale:** identify the existing schema, DTO, mapper, generator, or contract reference reused and the rejected internal-model exposure or speculative shared abstraction.
- **Behavior preservation:** state how old DTO fields, old clients, old generated artifacts, old validators, old mappers, and rollback behavior remain valid or are migrated.
- **Residual risk:** name remaining compatibility, privacy, validation, generated-client, consumer, or mapping risk and owner.
- **Next gate:** route unresolved operation behavior, storage model, error taxonomy, compatibility rollout, security/privacy, contract tests, release, or docs to the correct gate.

# Benchmark Coverage

This capability covers field-level contract design, serialization formats, four-state null/default semantics, request strictness, response forward compatibility, DTO/domain/persistence/event boundary separation, validation and error mapping, generated schema alignment, sensitive-field filtering, consumer compatibility, and DTO-to-validation mapping. Load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) for detailed matrices and implementation patterns.

# Routing Coverage

Routes from `data-api-contract-changer`, `api-contract-design`, `data-model-design`, `model-boundary-mapping`, `version-compatibility`, `consumer-impact-analysis`, `input-validation`, `frontend-api-integration`, `form-validation-design`, `domain-event-modeling`, and `contract-testing` should arrive here when field-level DTO schema evidence is primary. Route away when endpoint behavior, storage source of truth, error taxonomy, migration execution, release approval, or consumer inventory is primary.

# Quality Gate

The DTO schema is complete only when:

1. Mode, inspected boundaries, source evidence, graph-memory-trajectory judgment, and evidence limits are recorded.
2. DTO direction, owner, consumer class, contract surface, schema source, and generated artifacts are named.
3. Every field has type/format, required/optional status, nullable flag, absent/empty/default semantics, validation, example, sensitivity, and read/write mode.
4. Request DTOs reject unknown fields and map through an explicit allowlist before domain/service invocation.
5. Response DTOs avoid persistence/domain leakage and define forward-compatible unknown-field behavior for consumers.
6. Money, time, identifiers, enums, arrays, nested objects, and binary/file fields use risk-appropriate formats.
7. Null, absent, empty, and default states are documented for every nullable or optional field.
8. Validation constraints and error mapping are enforceable before domain mutation.
9. Breaking vs compatible classification is documented for every field and semantic change.
10. Schema version, registry/generator source, generated-client impact, reserved Protobuf fields/numbers, and rollback behavior are handled.
11. Sensitive and permission-dependent fields have allowed consumers, redaction/filtering, and denied exposure validation or residual risk.
12. DTO-to-domain/persistence/event/view mapping has a named owner and no mapper-owned business rule drift.
13. Examples include happy, null, absent, empty, default, boundary, invalid, and old/new compatibility cases where applicable.
14. Contract or schema validation evidence is recorded for public, cross-service, generated, mobile, partner, or event DTOs.
15. Changed DTO-to-validation map, behavior preservation, handoff boundaries, and residual risk owner are explicit.

# Used By

- data-api-contract-changer
- backend-change-builder
- frontend-change-builder

# Handoff

Hand off to `api-contract-design` for operation-level behavior; `data-model-design` for source-of-truth storage shape; `error-code-design` for validation error DTOs; `contract-testing` for consumer contract enforcement; `version-compatibility` for multi-consumer schema evolution; `model-boundary-mapping` for DTO/domain/persistence/event boundary ownership; `security-privacy-gate` for sensitive payload exposure; and `delivery-release-gate` when rollout, generated-client release, or rollback approval is needed.

# Completion Criteria

The capability is complete when every DTO has an explicit field schema, four-state null/default semantics, validation rules, allowlisted mapping, schema source/version, generated-artifact alignment, compatibility classification, behavior-preservation evidence, consumer contract validation, security/privacy filtering, handoff boundaries, and residual-risk owner, with no internal model exposure, mass-assignment risk, ambiguous null/absent behavior, stale generated clients, or unversioned breaking changes.
