---
name: model-boundary-mapping
description: Maps API DTOs, commands, queries, domain objects, value objects, persistence models, events, and view models without leaking boundary-specific concerns or drifting null/default semantics.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "112"
changeforge_version: 0.1.0
---

# Mission

Keep models honest at their boundaries by defining what each model represents, who validates it, how it maps across layers, and which fields or semantics must not leak.

# When To Use

Use when API DTOs, command/query objects, domain objects, value objects, persistence models, ORM entities, event payloads, view models, generated clients, serializers, mappers, assemblers, or schema versions are added or changed.

Use when null, default, optional, generated, handwritten, validation, compatibility, or serialization semantics can drift across boundaries.

# Do Not Use When

Do not use for a private local value with no boundary crossing and no serialization or persistence semantics.

Do not use to create mapper layers when the local convention intentionally uses a simple direct projection and no boundary leakage exists.

# Non-Negotiable Rules

- DTO is not domain object.
- Persistence model must not leak to API.
- Domain object must not import ORM, HTTP, or JSON schema.
- Mapper must not own business rules unless explicitly a policy.
- Null, default, and optional semantics must be preserved across boundaries.
- Event payloads are versioned contracts.
- Generated models stay at the generated boundary.

# Industry Benchmarks

Anchor against domain-driven design model separation, command/query responsibility separation, anti-corruption layer mapping, OpenAPI/JSON Schema/Protobuf compatibility, ORM persistence isolation, versioned event contracts, and generated client boundary governance.

# Selection Rules

Select this capability when model leakage or mapping semantics are the risk. Use `dto-schema-design` for DTO field schema, `data-model-design` for persistence data shape, `api-contract-design` for endpoint contracts, `version-compatibility` for versioning, and `implementation-structure-design` for mapper placement.

# Risk Escalation Rules

Escalate to `data-api-contract-changer` when public API, SDK, schema, event, or generated client compatibility changes. Escalate to `domain-impact-modeler` when mapping changes domain invariants. Escalate to `consumer-impact-analysis` when existing consumers may depend on the old shape.

# Critical Details

- API DTO owns transport shape, validation-at-boundary fields, and client compatibility.
- Command/query object owns use-case intent and caller-supplied parameters.
- Domain object owns identity, lifecycle, invariants, and behavior.
- Value object owns validation, normalization, equality, and unit safety for a value.
- Persistence model owns storage shape, ORM annotations, indexes, and database-specific fields.
- Event payload owns versioned producer/consumer contract and immutable historical meaning.
- View model owns UI rendering shape and should not become a domain rule owner.
- Mapper/assembler owns translation and boundary defaults, not hidden business decisions.
- Boundary-specific fields include internal IDs, audit fields, permissions, calculated display fields, ORM metadata, transport links, and generated client fields.
- Null/default/optional semantics must define absent, unknown, empty, zero, false, server default, and client omitted separately when meaningful.

# Failure Modes

- Returning ORM entities directly from controllers.
- Passing API DTOs into domain methods as if they were domain objects.
- Domain object imports HTTP, JSON schema, ORM decorators, or generated client types.
- Mapper silently calculates price, permission, state transition, or policy decision.
- Event payload field is renamed without versioning or upcaster/compatibility plan.
- Generated model is edited by hand or leaks into domain code.
- Null becomes default empty value and changes business meaning.

# Output Contract

Return a Model Boundary Map:

- Source model.
- Target model.
- Mapping owner.
- Validation owner.
- Null, default, and optional semantics.
- Boundary-specific fields.
- Serialization behavior.
- Version compatibility.
- Generated and handwritten boundary.
- Mapper or assembler placement.
- Tests for mapping.
- Rejected leakage alternatives.

# Evidence Contract

Close the map only when source/target models, validation location, mapping owner, semantic preservation, version compatibility, generated boundary, tests, inspected contracts, evidence limits, and residual mapping risk are recorded.

# Quality Gate

1. DTO, domain, persistence, event, and view models have distinct responsibilities where boundaries exist.
2. Persistence model does not leak to API.
3. Domain model does not import framework, transport, serialization, or ORM concerns.
4. Mapper owns translation only unless a policy exception is explicit.
5. Null/default/optional semantics are preserved and tested.
6. Event payload compatibility is versioned.
7. Generated models remain at generated boundaries.

# Used By

- data-api-contract-changer
- backend-change-builder
- frontend-change-builder
- integration-change-builder
- ai-code-review-refactor
- quality-test-gate
- change-documentation-gate

# Handoff

Hand off to `dto-schema-design`, `api-contract-design`, `data-model-design`, `version-compatibility`, `implementation-structure-design`, `domain-impact-modeler`, or `consumer-impact-analysis` depending on which boundary is unclear.

# Completion Criteria

The capability is complete when every boundary-crossing model has an owner, mapping and validation are explicit, generated and handwritten surfaces are separated, semantics are preserved across null/default/optional fields, leakage alternatives are rejected, and mapping tests exist or are explicitly out of scope.
