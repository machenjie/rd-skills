# Model Boundary Mapping Benchmarks And Patterns

Load for a named choice among model separation, mapping placement, semantic preservation, generated ownership, or leakage controls; skip when one owned mapper already preserves the boundary.

## Boundary Choice Matrix

| Boundary | Owns | Reject |
| --- | --- | --- |
| API DTO | Transport shape, boundary fields, client compatibility. | Domain behavior, persistence metadata, provider internals. |
| Command/query | Use-case intent and caller parameters. | Storage annotations, public response shape, hidden policy. |
| Domain/value | Identity, lifecycle, invariants, normalization, equality. | HTTP, ORM, schema, generated SDK, view concerns, repository calls. |
| Persistence | Storage shape, indexes, ORM fields. | Public API or SDK authority. |
| Event | Versioned historical producer/consumer meaning. | Mutable domain objects and private storage fields. |
| View | Rendering shape and affordances. | Domain rule authority. |
| Generated/provider | Schema or provider boundary. | Handwritten business logic and domain ownership. |

## Selection Rules

- Compare DDD evidence that transport, domain, persistence, event, and view models represent different facts with CQRS intent, anti-corruption mapping, and direct reuse for the active boundary.
- Assign translation, allowlisted fields, boundary defaults, validation, policy, serialization, and persistence to named owners.
- Preserve null, absent, empty, zero, false, unknown, not-applicable, server-default, client-omitted, enum, and value-object meaning.
- Keep generated models reproducible and handwritten policy outside generated output.
- Reject mapper-owned pricing, authorization, lifecycle, repository access, publication, nondeterminism, or other IO unless separately owned.
- Treat OpenAPI, JSON Schema, Protobuf, events, SDKs, ORM shapes, and public DTOs as versioned consumer boundaries when exposed.

## Evidence And Handoff

- Record source and target models, direction, owners, allowed and rejected fields, semantic cases, generated boundary, and direct-reuse rationale.
- Prove negative leakage, null/default compatibility, generated freshness, and representative consumer behavior.
- Route field schema to `dto-schema-design`, stored shape to `data-model-design`, domain semantics to `domain-impact-modeler`, API behavior to `api-contract-design`, compatibility or unknown consumers to `version-compatibility` or `consumer-impact-analysis`, effects to `data-side-effect-flow-tracing`, and sensitive leakage to `security-privacy-gate`.
- Mark uninspected consumers, sibling mappers, generated languages, production telemetry, and rollback as proof limits.
