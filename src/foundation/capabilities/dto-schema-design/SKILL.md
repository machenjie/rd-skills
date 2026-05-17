---
name: dto-schema-design
description: Designs DTO schemas that decouple external contracts from internal models with validation, nullability, defaults, and compatibility rules.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "27"
changeforge_version: 0.1.0
---

# Mission

Design DTO (Data Transfer Object) schemas that serve as **explicit, versioned, stable transfer contracts** — decoupling external API, event, and integration surface shapes from internal domain models and persistence layers — with precisely specified field types, nullability semantics, validation rules, default values, serialization formats, mapping strategies, and forward-backward compatibility rules.

# When To Use

Use this capability when a change: adds or modifies request body or response body schemas for HTTP or gRPC endpoints; designs Protobuf message types or Avro schemas for event payloads; defines form submission models or query parameter DTOs; creates view models or projection DTOs for read-side CQRS queries; establishes DTO-to-domain-object mapping logic (assemblers, converters, mappers); updates field names, types, required/optional status, validation constraints, or nullability; plans schema evolution for a DTO that has existing consumers; designs error response DTOs per RFC 7807 / RFC 9457.

# Do Not Use When

Do not use this capability to expose internal ORM entities, database row objects, Hibernate/ActiveRecord models, SQLAlchemy models, or JPA entities as API response types. Internal models have different lifecycles, contain persistence metadata, and leak schema details. Do not use it to design the domain object itself — domain invariants, business rules, and aggregate identity belong in domain model design, not DTO design.

# Non-Negotiable Rules

- **DTOs decouple external contract from internal model.** A DTO change must never be forced by a database migration alone. A domain model rename must never automatically propagate to the public API. The DTO is the stability boundary between the outside world and internal implementation.
- **Request DTOs must validate and block before reaching domain logic.** Input validation on request DTOs is a security boundary. Allowlist all expected fields. Reject unknown fields with 400. Prevent mass assignment: never auto-bind all incoming fields to domain commands without explicit field allowlisting. OWASP API3:2023 Broken Object Property Level Authorization is directly caused by mass-assignment in request binding.
- **`additionalProperties: false` on request schemas; `additionalProperties: true` on response schemas.** Strict input: reject unexpected properties. Permissive output: consumers must ignore unknown fields for forward compatibility (Postel's Law applied at schema level).
- **Four null states are distinct contract states; all must be specified.** For every field: (1) **Present with value** — field included with a non-null value; (2) **Present as `null`** — field included explicitly as JSON `null`; (3) **Absent** — field not included in the object at all; (4) **Present as empty** (`""`, `[]`, `{}`) — field present but empty. Each state means something different to clients. Ambiguity causes bugs. Document all four states or prove they are equivalent for the field.
- **Required and optional are semantic, not technical, distinctions.** Required = the meaning of the DTO cannot be determined without this field. Optional = the field provides additional context but the DTO is valid without it. Do not mark fields optional to avoid validation; optional fields still need a documented absence semantic.
- **Field names follow one consistent convention per serialization format.** JSON → `camelCase` (per JS convention; confirmed by majority of public APIs). Protobuf 3 → `snake_case` (per Language Guide). Avro → `camelCase` (per convention). GraphQL → `camelCase`. SOAP/XML → `PascalCase`. Never mix conventions within one DTO schema. Rename requires a versioning plan, not an ad hoc change.
- **Schema versioning is additive-only for minor versions.** Allowed without a new version: add optional fields with default values; add new enum members (consumers must handle unknown enum values). Not allowed without a version bump: remove fields; rename fields; change a field's type; change a field from optional to required; change enum member meaning. Breaking changes require a new versioned DTO class or a new API version, not an in-place mutation.
- **Derived and computed display values belong in response DTOs, not domain objects.** A response DTO may include `displayName`, `formattedTotal`, `statusLabel` — values computed from domain data for UI consumption. These are DTO concerns, not domain concerns. Domain objects return raw facts; DTOs format for consumers.

# Industry Benchmarks

Anchor against: **OpenAPI 3.1.0** — `requestBody.content.application/json.schema` (request DTOs) and `responses.200.content.application/json.schema` (response DTOs); `required` array for required fields; `nullable: true` for nullable; `additionalProperties: false` for strict input. **JSON Schema Draft 2020-12** — `$schema`, `properties`, `required`, `additionalProperties`, `type`, `format`, `examples`, `$ref`. **Protobuf 3** — `message`, `field` labels (`optional`, `repeated`); `google.protobuf.Timestamp` for datetime; field number stability is a binary contract; do not reuse field numbers. **Apache Avro** — `"type": ["null", "string"]` union for nullable; `"default": null` for optional fields; schema fingerprint for registry lookup. **RFC 7807 / RFC 9457** — Problem Details for HTTP APIs: `type` (URI), `title`, `status`, `detail`, `instance`; JSON media type `application/problem+json`; error DTOs must follow this standard. **gRPC / google.rpc.Status** — `code`, `message`, `details[]`; error detail types per `google.rpc.ErrorInfo`, `BadRequest`, `QuotaFailure`. **Zalando RESTful API Guidelines** — must-have: `required` fields array explicit; nullable fields explicit; `additionalProperties` declared. **Google AIP-140** — field naming guidelines: use plain names, not type suffixes (`order` not `orderObject`); avoid abbreviations. **OWASP API3:2023** — Broken Object Property Level Authorization; mass assignment must be blocked by explicit field allowlist in request DTOs. **OWASP API8:2023** — Security Misconfiguration; avoid exposing internal stack traces or model details in error DTOs. **Consumer-Driven Contract Testing (Pact v4)** — consumer tests define what fields they use from a response DTO; producer must satisfy all registered consumer expectations. **Postel's Law** — "be conservative in what you send, be liberal in what you accept" — applies to schema strictness direction.

### Four Null States Decision Table

| State | JSON representation | When to use | Consumer behavior |
| --- | --- | --- | --- |
| Present with value | `"field": "value"` | Normal case | Use the value |
| Present as `null` | `"field": null` | Explicit absence / cleared value | Treat as cleared; distinct from not-set |
| Absent (missing) | (field not in object) | Unknown / not applicable | Use default or treat as not-set |
| Present as empty | `"field": ""` or `"field": []` | Empty collection or empty string | Treat as zero-content; distinct from null |

### Field Type Selection Matrix (JSON/OpenAPI)

| Data type | OpenAPI type + format | Notes |
| --- | --- | --- |
| Integer (64-bit) | `type: integer, format: int64` | Use `int64`; `int32` for known-small values |
| Decimal money | `type: string, format: decimal` or `type: number` | String preferred for exactness; avoid float for money |
| Boolean | `type: boolean` | Never `0`/`1` or `"true"`/`"false"` string |
| ISO 8601 datetime (UTC) | `type: string, format: date-time` | `2024-01-15T09:30:00Z`; include timezone |
| Date only | `type: string, format: date` | `2024-01-15`; no time component |
| UUID identifier | `type: string, format: uuid` | `"3fa85f64-5717-4562-b3fc-2c963f66afa6"` |
| Enum | `type: string, enum: [...]` | Add `x-extensible-enum` note for forward-compat |
| Binary/file | `type: string, format: byte` (base64) | For small payloads; prefer multipart for large |
| Nested object | `$ref: '#/components/schemas/...'` | Named schema; reusable; avoid inline anonymous |
| Array | `type: array, items: {$ref: ...}` | Declare `minItems`/`maxItems` where bounded |

### DTO-to-Domain Mapping Rules

```
Request DTO → Command (or Use Case Input):
  1. Validate request DTO (input validation — BEFORE mapping)
  2. Explicitly allowlist fields for mapping; reject all others
  3. Apply DTO-level defaults (not domain defaults)
  4. Map: RequestDTO → Command/UseCase input (pure data transfer; no logic)
  5. Invoke domain: domainService.handle(command)
  NO: commandHandler.handle(requestDTO)   ← DTO leaks into domain

Domain Object → Response DTO:
  1. Extract domain facts needed by consumer
  2. Compute display values (format, localize, derive) in assembler
  3. Apply response DTO field selection (projection) based on consumer needs
  4. Return ResponseDTO with all fields explicitly assigned
  NO: return entity;   ← domain object leaks to API layer

Anti-pattern (mass assignment):
  const command = { ...requestDTO };   // ← assigns ALL fields including hidden ones
  
Correct pattern (explicit allowlist):
  const command = {
    userId: requestDTO.userId,
    amount: requestDTO.amount,
    currency: requestDTO.currency,
  };  // ← only declared fields; nothing else reaches domain
```

### Schema Compatibility Classification

| Change | Compatible? | Version action required |
| --- | --- | --- |
| Add optional field with default | ✅ Backward-compatible | None (existing consumers unaffected) |
| Add new enum value | ✅ Forward-compatible | Consumers must handle unknown enum |
| Remove optional field | ❌ Breaking | New major version; deprecation period |
| Remove required field | ❌ Breaking | New major version |
| Rename field | ❌ Breaking | New major version; alias old name in transition |
| Change field type (e.g., `int` → `string`) | ❌ Breaking | New major version |
| Make optional field required | ❌ Breaking | New major version |
| Change field semantics (same name, new meaning) | ❌ Breaking — most dangerous | New field name; do not reuse |
| Add new `required` field to request DTO | ❌ Breaking for existing clients | New version or feature-flag |
| Change validation constraint (min/max length) | ⚠️ Potentially breaking | Coordinate with consumers |

# Selection Rules

Select this capability when **field-level transfer schema design** is the primary concern. Adjacent routing:

- Prefer `api-contract-design` when endpoint semantics, HTTP methods, status codes, or operation behavior are primary.
- Prefer `data-model-design` when the source-of-truth storage schema (tables, collections, indexes) is primary.
- Prefer `domain-event-modeling` when the DTO is an event payload that crosses service boundaries with durability requirements.
- Prefer `error-code-design` when validation error response shape and error code taxonomy are primary.
- Prefer `version-compatibility` when schema evolution across multiple producers and consumers over time is the main concern.
- Prefer `contract-testing` when consumer-driven contract enforcement for existing DTOs is the focus.

# Risk Escalation Rules

Escalate when: a DTO field change is in a public API consumed by mobile apps (long upgrade cycle — breaking changes stranded in production for months); a DTO exposes sensitive fields that authorization logic should filter; a field changes meaning but keeps its name (semantic drift — silent corruption risk); a shared DTO is consumed by both external clients and internal services with different schema evolution windows; a response DTO computed value (derived field) depends on business logic that belongs in the domain.

# Critical Details

DTO stability is a client contract commitment. Precision failures:

- **Mass assignment vulnerability.** Auto-binding all request fields to a domain command without an allowlist allows an attacker to supply `isAdmin: true`, `role: "superuser"`, or `price: 0.01` in a request body and have it accepted. OpenAPI `additionalProperties: false` + explicit mapping per field is the defense. Never use spread-assignment from request DTO to command.
- **Null vs. absent semantic confusion.** A mobile client sends `"address": null` to clear a user's address. A web client omits `"address"` entirely to "not change" it. If the backend treats both as "clear address," the web client inadvertently clears it on every update. The PATCH semantics must be documented: null = clear; absent = no-op. This must be in the DTO schema contract, not just developer knowledge.
- **Decimal precision loss.** `"amount": 10.35` in JSON is a floating-point literal. IEEE 754 double precision cannot represent 10.35 exactly. For currency, prices, or financial calculations, use `type: string, format: decimal` (`"amount": "10.35"`) or integer minor units (`"amountCents": 1035`). Never use `number` for money.
- **Enum forward-compatibility.** A consumer that switches on enum values and throws on unknown will break when the producer adds a new enum member. All consumers must have a default/fallback case for unknown enum values. Response DTOs using enums must document this requirement explicitly.
- **Circular reference in nested DTOs.** A DTO that contains itself (directly or indirectly) causes infinite serialization recursion. Schemas with circular references need explicit depth limits or reference-by-ID instead of full nesting at depth > 2.
- **Protobuf field number reuse.** In Protobuf 3, each field is identified by its number, not its name. If field `3` was `string email`, removing it and later adding `int64 userId` as field `3` causes binary deserialization corruption for consumers holding old messages. **Never reuse Protobuf field numbers.** Reserve removed field numbers: `reserved 3;`.

### Anti-examples

| Anti-pattern | Failure |
| --- | --- |
| `return entity` from controller | Internal model exposed; DB column changes break API |
| `const cmd = { ...req.body }` | Mass assignment; attacker supplies `isAdmin: true` |
| `"amount": 10.35` (float) for money | `10.34999999999999929` in some parsers; financial calculation error |
| Nullable field undocumented: is `null` same as absent? | Client guesses; PATCH semantics broken |
| Enum `status: "ACTIVE"` — new value `"PENDING"` added without versioning note | Consumer `switch` falls to no-op; feature silently broken |
| Response DTO computed field containing business rule | Domain logic in DTO layer; calculation drifts between API and domain |
| Protobuf field number 5 removed, then reused for new field | Binary deserialization corruption for message consumers with stale schema |
| `additionalProperties` not declared on request DTO | Unknown fields silently passed through; OWASP API3 mass-assignment risk |

# Failure Modes

- Mass assignment: attacker sends `role: "admin"` in profile update request; backend auto-binds it; privilege escalation.
- Internal DB column `created_by_user_id` exposed in response DTO; frontend accidentally uses it for authorization; internal ID becomes a client dependency.
- `amount` serialized as float; `19.99` becomes `19.989999999999998`; invoice total displays incorrectly; customer dispute.
- PATCH endpoint: omitting a field treated as "clear" instead of "no change"; user updates phone number and loses address because it was not included in PATCH body.
- New enum value `SUSPENDED` added without consumer notification; consumer switch-statement has no default; account status silently ignored; suspended users retain access.
- Protobuf field 7 removed and reused; consumers that stored old binary messages deserialize wrong data type; crash on read.
- Required field `currency` added to payment request DTO without version bump; existing clients stop working; 422 errors in production.
- Response DTO assembler contains tax calculation logic; tax rate logic differs from domain service; inconsistency between display total and processed total.
- Circular DTO nesting: `Order → LineItems → Order`; serializer stack overflow in production on large orders.

# Output Contract

Return a DTO schema contract with:

- `dto_name` and `purpose` (request / response / event payload / error / view model)
- `fields` table: name, type (OpenAPI type + format), required/optional, nullable Y/N, default value, validation constraints, serialization format, semantics description
- `null_vs_absent_semantics` (documented per nullable/optional field)
- `additionalProperties` policy (request: `false`; response: `true`)
- `validation_rules` (per-field: minLength, maxLength, pattern, enum values, format, cross-field constraints)
- `mapping_spec` (DTO → domain command or domain object → DTO; explicit field allowlist)
- `compatibility_classification` (for each field change: backward-compatible / breaking / requires-version-bump)
- `schema_version` (current; OpenAPI version indicator or Avro/Protobuf schema registry entry)
- `derived_fields` (computed values in response DTO; computation rule documented)
- `examples` (at least: happy path, null fields, empty collections, validation error, boundary values)
- `consumer_contract_tests` (Pact / buf breaking / oasdiff reference)

# Quality Gate

The DTO schema is complete only when:

1. All four null states (present-with-value, present-null, absent, empty) are documented for every nullable/optional field.
2. `additionalProperties: false` on all request DTOs; explicit allowlist in mapping code.
3. All field types use format specifiers; no bare `number` for money or datetime.
4. Breaking vs. non-breaking classification documented for every field change.
5. Schema version present; registry entry created for Avro/Protobuf schemas.
6. DTO-to-domain mapping is explicit (no spread/auto-bind); no domain model leaked to API layer.
7. Derived/computed response fields documented with computation rules.
8. Examples include happy path, null fields, empty collections, and edge cases.
9. Validation constraints (required, min/max, pattern, enum) are enforced at DTO layer before domain invocation.
10. Consumer-driven contract test exists or is planned for public-facing or cross-service DTOs.

# Used By

- data-api-contract-changer
- backend-change-builder
- frontend-change-builder

# Handoff

Hand off to `api-contract-design` for operation-level behavior; `data-model-design` for source-of-truth storage shape; `error-code-design` for validation error DTOs; `contract-testing` for consumer contract enforcement; `version-compatibility` for multi-consumer schema evolution planning.

# Completion Criteria

The capability is complete when every DTO has **an explicit schema with typed fields, documented null semantics, validation rules, an allowlisted mapping strategy, a compatibility classification for all changes, and consumer-compatible versioning** — with no internal model exposure, no mass-assignment risk, and no ambiguous null/absent semantics.
