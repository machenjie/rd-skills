# DTO Schema Benchmarks And Patterns

Use this reference after `SKILL.md` selects DTO schema design and the task needs detailed contract, mapping, compatibility, generated-artifact, or validation guidance. Keep the main skill body concise; load only the sections needed for the current DTO design or review.

# Benchmark Anchors

- **OpenAPI 3.1 / JSON Schema 2020-12:** request and response schema definitions, `required`, `format`, `examples`, `$ref`, and `additionalProperties`.
- **RFC 7807 / RFC 9457:** problem details payloads for machine-readable error DTOs.
- **Protobuf 3:** field number stability, reserved names/numbers, optional/repeated fields, and generated-client compatibility.
- **Apache Avro:** nullable unions, defaults, schema fingerprints, and schema registry compatibility.
- **GraphQL SDL:** typed schema, nullable/non-null semantics, deprecation, and generated client effects.
- **Google AIP field guidance:** plain names, stable resource identifiers, and avoiding type suffixes.
- **OWASP API3/API8:** mass assignment, broken object property authorization, and internal-detail exposure.
- **Consumer-driven contract testing:** consumer expectations and provider verification for shared DTOs.
- **Postel-style response compatibility:** clients ignore unknown response fields; servers reject unknown request fields unless explicitly designed otherwise.

# Four-State Null And Default Matrix

| State | JSON example | Common meaning | Required decision |
| --- | --- | --- | --- |
| Present with value | `"field": "value"` | Normal value | Validate type, range, and semantics |
| Present as null | `"field": null` | Clear, unknown, or not applicable | State exact meaning and whether allowed |
| Absent | field omitted | No-op, default, not requested, or legacy client | State default and compatibility behavior |
| Present empty | `"field": ""`, `[]`, `{}` | Zero-content value | Distinguish from null and absent |
| Defaulted | field absent but server fills value | Compatibility or convenience default | State default source and rollback behavior |

PATCH contracts must be explicit: `null = clear` and `absent = no change` is common, but not universal. Document the rule per field.

# Field Type Selection

| Data concern | Preferred representation | Notes |
| --- | --- | --- |
| Identifier | Opaque string, UUID, ULID, or public resource id | Avoid database row ids unless they are the resource identity by design |
| Money | Decimal string or integer minor units plus ISO 4217 currency | Never use binary floating point for money |
| Timestamp | RFC 3339 / ISO 8601 UTC string | Include timezone or offset |
| Date only | ISO date string | Document timezone interpretation if derived from locale |
| Boolean | JSON boolean | Avoid `0`/`1` or string booleans |
| Enum | String enum with unknown handling | Document extensible/open enum behavior |
| Nested object | Named `$ref` or message type | Avoid anonymous deep nesting |
| Array | Typed item schema plus min/max if bounded | Specify empty vs absent behavior |
| Binary/file | Multipart or reference URL for large files | Base64 only for small bounded payloads |
| Decimal measurement | Decimal string with unit field | Unitless numbers are ambiguous |

# Request And Response Strictness

| Direction | Unknown fields | Rationale |
| --- | --- | --- |
| Request DTO | Reject by default | Prevent mass assignment and hidden input behavior |
| Response DTO | Consumers ignore by default | Allows additive fields without breaking old readers |
| Event payload | Depends on schema registry mode | Use compatibility mode and consumer inventory |
| SDK/public type | Depends on language generator | Generated clients may need open enum and optional field support |

If a request DTO intentionally allows extension fields, define namespace, allowed keys, max size, validation, and ownership.

# DTO-To-Domain Mapping

Request DTO to command/use-case input:

1. Validate raw input against schema.
2. Reject or quarantine unknown fields.
3. Apply DTO-level defaults.
4. Map allowlisted fields into command/use-case input.
5. Invoke domain/service logic.
6. Never pass the DTO object as the domain object.

Domain/persistence to response DTO:

1. Read domain or persistence data through the owning service/repository boundary.
2. Select only fields needed by the contract.
3. Apply permission filtering before serialization.
4. Format display-only values in an assembler/presenter.
5. Keep business decisions in domain/service policy.
6. Return a DTO with all field semantics documented.

Anti-pattern:

```typescript
const command = { ...requestBody };
return userEntity;
```

Preferred pattern:

```typescript
const command = {
  amount: requestDto.amount,
  currency: requestDto.currency,
  reason: requestDto.reason,
};

return {
  id: user.publicId,
  displayName: profile.displayName,
  status: toPublicStatus(user.status),
};
```

# Compatibility Classification

| Change | Default classification | Required action |
| --- | --- | --- |
| Add optional response field | Usually compatible | Document; consumers ignore unknown fields |
| Add optional request field with default | Usually compatible | Document default and validation |
| Add required request field | Breaking | Version or bridge |
| Remove response field | Breaking | Deprecate, telemetry gate, remove after migration |
| Rename field | Breaking | Add new field, bridge old, then deprecate |
| Change type/format | Breaking unless widened safely | Generated-client and consumer proof |
| Tighten validation | Potentially breaking | Consumer impact and migration path |
| Add enum value | Conditionally breaking | Unknown handling proof |
| Change field meaning | Breaking | New field or new DTO version |
| Change default | Behaviorally breaking | Compatibility classification and rollout |

# Generated Artifacts

Generated DTO surfaces require source and artifact alignment:

- OpenAPI/JSON Schema: schema diff, validator/linter, examples validation, generated client diff.
- Protobuf: `buf breaking`, reserved field numbers/names, generated code compile.
- Avro: registry compatibility mode, default/null union validation, fixture serialization/deserialization.
- GraphQL: schema diff, deprecated field policy, generated client compile.
- SDK/public exports: public API diff, semver decision, downstream compile or fixture test.

Generated artifacts are evidence only when current after the final schema edit.

# Sensitive Field And Permission Review

| Field class | DTO obligation |
| --- | --- |
| Tenant/object id | Confirm caller can access the object and tenant scope |
| Role/scope/permission | Do not trust client-supplied privilege fields |
| PII/health/financial | Minimize, redact, tokenize, or restrict consumers |
| Token/secret/credential | Do not expose in DTO or logs |
| Audit fields | Preserve actor/source/time where required; avoid diagnostic leakage |
| Internal ids/statuses | Translate to stable public representation |

# Graph, Memory, And Execution Coupling

| Evidence source | Use | Guardrail |
| --- | --- | --- |
| Repository graph | Find DTO classes, schemas, mappers, validators, generated clients, and consumers. | Verify with current source before relying on inferred edges. |
| Project memory | Recall prior field semantics, deprecation windows, or consumer agreements. | Mark accepted, rejected, or stale; never use as sole proof. |
| Execution trajectory | Connect planned edits, files changed, validators run, failures, and re-routes. | Re-run stale validation after final material edits. |
| Telemetry or registry | Confirm consumer use, schema compatibility, and migration progress. | State freshness and unknown-consumer limits. |

# DTO-To-Validation Matrix

| Concern | Validation evidence |
| --- | --- |
| Unknown request fields | Negative request fixture rejected |
| Mass assignment | Extra privileged field cannot reach command/domain object |
| Null vs absent | Null, missing, empty, default fixtures behave differently as documented |
| Field type/format | Schema validator or generated type check |
| Enum expansion | Unknown enum fixture or generated-client behavior check |
| Compatibility | Old/new schema diff plus consumer contract test |
| Generated artifacts | Generator command and generated diff/compile |
| Sensitive filtering | Denied consumer or role receives no restricted field |
| Mapper boundary | Mapping test or review artifact covers allowlisted fields |
| Error DTO | Invalid input returns stable problem-details shape |

# Review Checklist

- Is this DTO a transfer contract rather than a domain or persistence model?
- Are all fields typed and documented with examples?
- Are null, absent, empty, and default states unambiguous?
- Is request unknown-field handling strict enough for the trust boundary?
- Is mapping allowlisted and owned by a mapper/assembler boundary?
- Are money, time, identifiers, enums, arrays, and nested objects represented safely?
- Are sensitive fields minimized and permission-filtered?
- Are generated artifacts current?
- Are old clients and unknown consumers considered?
- Does each changed field map to validation or residual risk?

# Handoff Boundaries

- Use `api-contract-design` for operation semantics, auth requirements, pagination, idempotency, and status codes.
- Use `data-model-design` for source-of-truth storage shape and invariants.
- Use `model-boundary-mapping` for source/target model ownership and mapper placement.
- Use `version-compatibility` for rollout, rollback, generated-client, deprecation, and mixed-version behavior.
- Use `consumer-impact-analysis` for known/unknown consumer inventory.
- Use `contract-testing` for executable provider/consumer proof.
- Use `security-privacy-gate` for sensitive payload, object authorization, and privacy review.
