# DTO Schema Benchmarks And Patterns

Load this reference when field semantics, trust-boundary strictness, mapping, compatibility, generated artifacts, or sensitive-field exposure changes a DTO/schema decision.
## Field Semantics

| Concern | Required decision | Failure/proof |
| --- | --- | --- |
| Present value | Type, range, format, unit, and business meaning. | Schema plus boundary/domain case. |
| Null | Clear, unknown, not-applicable, or forbidden. | Null fixture differs from absent/empty as documented. |
| Absent | No-op, default, not requested, or legacy-client behavior. | Old/new fixture and PATCH semantics. |
| Empty | Whether empty string/list/object is a real value. | Empty does not silently mean null/default. |
| Default | Source, application point, compatibility, and rollback behavior. | Omitted-field behavior and changed-default consumer impact. |
| Data | Representation obligation |
| --- | --- |
| Identifier | Stable public/opaque identity; do not expose persistence identity by accident. |
| Money/measurement | Exact decimal or minor units with currency/unit; no binary-float ambiguity. |
| Time/date | Explicit instant/offset/timezone or date-only semantics. |
| Enum | Open/closed and unknown-value behavior, including generated clients. |
| Collection/nested/file | Typed items/named shape, bounded size where risk requires it, and empty/absent behavior. |
## Direction, Mapping, And Security

- Derive request strictness from the trust boundary and compatibility policy.
- Allowlist fields before mapping them into internal objects.
- Explicitly namespace, limit, and own any permitted extension fields.
- Never spread raw input into a command, domain, or persistence object.
- At an external response boundary, map authorized object and tenant data into an allowlisted contract shape.
- Keep presentation formatting in an assembler.
- Keep business decisions with domain or service owners.
- DTO, domain, persistence, view, event, and generated models remain distinct when their invariants, lifecycle, consumers, or compatibility differ.
- At an external DTO boundary, treat client-supplied tenant or object IDs as untrusted references.
- Derive role, scope, and permission from authenticated server-side context and authoritative object or tenant data.
- Expose allowlisted sensitive or permission-dependent fields only after object and tenant authorization.
- Apply minimization, redaction, or tokenization to those fields.
- Exclude credentials, secrets, tokens, and API keys from ordinary external DTOs.
- Permit them only when an endpoint contract explicitly issues, recovers, or exchanges them.
- Require authorized, purpose-bound, minimized one-time delivery for that endpoint.
- Forbid logging, caching, and uncontrolled replay of the delivered material.
- Define its scope, expiry, rotation, and recovery lifecycle.
- Keep unsafe diagnostics outside the external payload.
## Compatibility And Generated Evidence

| Change | Classification question | Required evidence/mitigation |
| --- | --- | --- |
| Add field | Can old parsers/generated types tolerate it, and does it alter meaning/default? | Consumer/schema/generated-client proof; optional/additive only when conditions hold. |
| Require/remove/rename | Do current producers/consumers still send/read it? | Bridge/version, deprecation and usage evidence before removal. |
| Type/format/null/default change | Is old data/input still valid and interpreted identically? | Old/new fixture replay, mapper and generated compile proof. |
| Validation tightening/relaxing | Who becomes rejected or which invariant/security control weakens? | Consumer migration or threat/invariant review. |
| Enum expansion | Are clients exhaustive or generated as closed enums? | Unknown-value fixture, compile proof, or versioned contract. |
| Meaning/error behavior | Shape may be unchanged while behavior breaks. | New field/version or explicit compatibility mapping and rollout. |
Keep generated sources aligned with the current schema. Use the applicable schema diff, compatibility checker, reserved-field rule, fixture serialization, generated-code diff, and downstream compile or test. Regenerate evidence after the last DTO, schema, mapper, or generated-client edit when it supports a final claim. Otherwise, mark retained evidence stale or partial.
## Proof Limits And Routing

- Inspect current schemas, DTOs, mappers, validators, generated clients, consumers, telemetry or registry evidence, examples, and tests. Unknown public, mobile, partner, and SDK consumers remain outside local provider proof.
- Validate unknown/mass-assignment fields, null/absent/empty/default, formats, enum evolution, sensitive filtering, mapper allowlists, error shape, old/new compatibility, and generated artifacts only where changed risk requires them.
- Route operation, auth, pagination, and status semantics to `api-contract-design`.
- Route storage truth to `data-model-design` and mapping ownership to `model-boundary-mapping`.
- Route rollout and deprecation to `version-compatibility` and consumers to `consumer-impact-analysis`.
- Route executable provider and consumer proof to `contract-testing`.
- Route sensitive payload review to `security-privacy-gate`.
Reject DTO, domain, or ORM reuse by convenience and raw request spreading. Reject entity responses, undocumented null or default semantics, binary-float money, and closed-enum assumptions. Reject stale generated artifacts, sensitive-field overexposure, and “optional means compatible” without consumer proof.
