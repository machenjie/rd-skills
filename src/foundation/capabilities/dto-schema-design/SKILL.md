---
name: dto-schema-design
description: "`task-agent`: use when DTO fields, validation, nullability, defaults, serialization, or compatibility change; skip persistence/domain-only work without an external schema."
---

# dto-schema-design

## Registry Trigger

**Use when**

- design DTO schemas fields validation defaults nullability and serialization

**Do not use when**

- no task-local dto schema design decision is required

## Skill Role

Design versioned transfer contracts that decouple API, event, form, SDK, view, and integration shapes from domain and persistence models. Define null/default semantics, validation, serialization, mapping ownership, compatibility, and sensitive-field filtering.

## High-Value Rules

- **DTOs are contract boundaries, not internal models.** A database migration, ORM rename, or domain refactor must not automatically rename or expose DTO fields.
- **Request DTOs validate before domain logic.** An explicit allowlisted mapper forbids request autobinding and derives unknown-field rejection or ignoring from the governing protocol, trust boundary, and compatibility policy.
- **Null, absent, empty, and defaulted are different states.** For each nullable or optional field, specify whether `null`, missing, empty string/list/object, and default value mean clear, no-op, unknown, not-applicable, or zero-content.
- **Required and optional are semantic decisions.** Required means the DTO cannot be interpreted without the field. Optional fields still need absence semantics, examples, and compatibility rules.
- **Serialization format drives field conventions.** JSON and GraphQL normally use `camelCase`; Protobuf uses `snake_case`; XML/SOAP may use `PascalCase`. Mixed conventions in one DTO require a migration rationale.
- **Field types must be exact enough for the risk.** Money uses exact decimals or scaled integers with explicit ISO or non-ISO currency/asset identity and an authoritative scale/exponent source. Precision, rounding, overflow, and validation stay explicit; datetimes use RFC 3339/ISO 8601 UTC, identifiers remain stable and opaque, and enums document unknown handling.
- **Schema evolution is compatibility-first.** Add optional fields safely; treat removal, rename, type change, optional-to-required, validation tightening, and semantic change as breaking until proven otherwise.
- **Sensitive and permission-dependent fields are explicit.** Define allowed consumers, redaction or filtering, and denied-case validation for tenant, permission, PII, financial, health, token, and audit fields.

## Anti-Patterns

- DTO stability is a client contract commitment; a storage or domain rename is not proof that a public DTO may change.
- Distinguish missing, `null`, empty, and defaulted values before compatibility or validation decisions.

## Stop Conditions

Escalate public or unknown consumers, permission/tenant/sensitive/mutation-bearing fields, PATCH nullability changes, enum growth without unknown handling, new required fields, unversioned meaning changes, persistence leakage, stale generation, or unproved consumer absence.

## Output Contract

- DTO schema contract with fields types defaults validation and examples

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | Field semantics, mapping, trust strictness, or compatibility needs selection | No DTO boundary or exposed field behavior changes | task-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | DTO changes nullability, unknown fields, sensitivity, or generated consumers | Only internal model names change behind stable mappings | task-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | Contract claims require fresh schemas, mappers, clients, or tests | No DTO compatibility or privacy claim awaits proof | task-agent | evidence-record, proof-limit, residual-risk |
