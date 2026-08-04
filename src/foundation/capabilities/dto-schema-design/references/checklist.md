# DTO Schema Design Checklist

- Select the mode: new DTO, evolution, boundary repair, validation/error payload, sensitive DTO, or generated schema/SDK surface.
- Record source evidence: schema files, DTO classes, mappers, validators, generated clients, API docs, consumers, tests, registry/config, and memory accepted or rejected.
- Define DTO name, direction, purpose, owner, contract surface, and consumer class.
- For a changed DTO field, define its name, type/format, required/optional status, nullable and absent semantics, and compatibility behavior. Add empty semantics, default, validation, example, sensitivity, and read/write mode when representation, consumer behavior, security, or direction makes them material.
- Record a protocol-, trust-boundary-, and compatibility-policy-derived reject-or-ignore decision with an explicit allowlisted mapper, no request autobinding, and schema/parser, compatibility, and negative-case evidence.
- Keep response DTOs separate from persistence, domain, provider, and generated internal models.
- Define validation rules, cross-field constraints, and error DTO mapping for invalid input.
- Include examples for happy, missing, null, empty, default, boundary, invalid, sensitive-field-filtered, and old/new compatibility cases where applicable.
- Classify compatibility for added, removed, renamed, retyped, required, validation-tightened, defaulted, deprecated, or semantic field changes.
- Define schema source, version, registry/generator, generated-client impact, reserved Protobuf field numbers, and rollback behavior.
- Confirm sensitive, tenant, object, role, permission, PII, financial, health, token, and audit fields are minimized and allowed only for named consumers.
- Map each field, mapper, validator, generated artifact, consumer class, compatibility path, and privacy rule to validation evidence.
- State behavior preservation for old DTO fields, old clients, old generated artifacts, old validators, old mappers, and rollback.
- Record what evidence proves, what it does not prove, residual risk, owner, handoff boundaries, and recommended next step.
