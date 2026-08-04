# Model Boundary Mapping Benchmarks And Patterns

Use this reference when `model-boundary-mapping` needs more depth than the main `SKILL.md` should carry efficiently.
Keep the body focused on routing, output, evidence, and gates.
Use this file for model separation, semantic preservation, generated-boundary governance, public-contract handling, and anti-pattern review.

## Benchmark Anchors

- Domain-driven design model separation: transport, domain, persistence, event, and view models represent different facts.
- CQRS command/query ownership: input intent should not become a domain object by accident.
- Anti-corruption layer mapping: provider and generated models should be translated at the boundary.
- OpenAPI, JSON Schema, Protobuf, and event compatibility: public and historical contracts require version-aware mapping.
- ORM persistence isolation: storage fields, lazy proxies, and database metadata should not leak outward.
- Consumer-driven contract testing: public DTO and event changes need consumer-aware proof.

## Model Boundary Matrix

| Model type | Owns | Must not own |
| --- | --- | --- |
| API DTO | Transport shape, boundary validation fields, client compatibility. | Domain behavior, persistence metadata, provider internals. |
| Command/query | Use-case intent and caller-supplied parameters. | Storage annotations, public response shape, hidden policy. |
| Domain object | Identity, lifecycle, invariants, behavior. | HTTP, ORM, JSON schema, generated SDK, UI rendering. |
| Value object | Normalization, equality, unit safety, value validation. | Repository calls, provider models, view formatting. |
| Persistence model | Storage shape, indexes, ORM annotations, database fields. | Public API or SDK contract. |
| Event payload | Versioned producer/consumer historical contract. | Mutable domain lifecycle or private storage fields. |
| View model | Rendering shape and display affordances. | Domain rule authority. |
| Generated model | Schema/provider boundary and generator output. | Handwritten business logic or domain ownership. |

## Semantic Preservation Pattern

```yaml
semantic_case:
  source_value: null | absent | empty | zero | false | unknown | not_applicable | server_default | client_omitted
  target_value: ""
  meaning_preserved: true
  intentional_remap: ""
  validator_or_test: ""
```

## Anti-Patterns To Reject

| Anti-pattern | Failure | Safer treatment |
| --- | --- | --- |
| ORM entity returned from controller. | Storage metadata becomes API contract. | Map through DTO/read model allowlist. |
| API DTO passed to domain method. | Transport defaults become domain facts. | Map DTO to command/value/domain object. |
| Mapper calculates policy. | Business rule hides in translation. | Move policy to domain/service or route as policy. |
| Generated model hand-edited. | Generator rerun erases behavior. | Keep generated surface isolated and map in owned code. |
| Null converted to empty value silently. | PATCH/import/client semantics drift. | Semantic table and negative/compatibility tests. |
| Happy fixture proves mapper. | Optional/default/generated leakage survives. | Test material negative and compatibility cases. |

## Handoff Boundaries

- Use `dto-schema-design` for transfer field schema, required/optional status, and field-level validation.
- Use `data-model-design` for stored source-of-truth shape, invariants, and relationships.
- Use `api-contract-design` when endpoint behavior, operation semantics, or response contract is primary.
- Use `version-compatibility` and `consumer-impact-analysis` for old/new compatibility and downstream inventory.
- Use `data-side-effect-flow-tracing` when mapper/assembler code mutates, publishes, caches, logs, calls IO, or reads nondeterministic sources.
- Use `security-privacy-gate` when internal, tenant, permission, PII, financial, health, token, audit, or provider-sensitive fields can leak.
