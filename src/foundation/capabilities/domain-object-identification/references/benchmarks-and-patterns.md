# Domain Object Identification Benchmarks And Patterns
Use this reference when `domain-object-identification` needs deeper support for object category selection, aggregate/resource separation, ownership and writer authority, current source/diff/validation coupling, validation maps, or anti-pattern review. Keep examples generic and do not include customer data, secret values, private policy text, or regulated identifiers.
## Object Category Decision Matrix
| Candidate Surface | Prefer Category | Evidence Required | False Proof |
| --- | --- | --- | --- |
| Stable identity, lifecycle, mutable state | Entity or aggregate root. | Identity source, lifecycle states, mutation authority, invariant owner. | A table has an `id` column. |
| Attribute-defined concept with no independent identity | Immutable value object with replacement semantics. | Equality attributes, normalization, precision, serialization boundary, and replacement behavior. | It is stored in its own table or DTO. |
| Consistency boundary | Aggregate root with child entities/value objects. | Root operations are the aggregate update and invariant entry point; invariants, transaction boundary, and writer authority are explicit. | Objects appear on the same screen or join query. |
| External API/event/provider name | Resource or boundary model. | Internal object mapping, compatibility owner, consumer impact. | The external field name matches a business noun. |
| Query-optimized projection | Read model. | Source aggregate/event, refresh semantics, write prohibition. | Projection has enough fields to mutate state. |
| Cross-object decision | Policy/specification or domain service. | Objects read, decision owner, no infrastructure effects. | A service method already branches on the fields. |

## Ownership And Writer Scan
For the named object or term and affected contexts, inspect defining, creating, mutating, merging, splitting, renaming, exposing, and translating paths. Record external or generated writers and translators outside the searched scope.
- API handlers, command handlers, admin screens, import scripts, background jobs, queue consumers, migrations, support tooling, fixtures, and tests.
- Repository save/update paths, ORM setters/hooks, direct SQL scripts, generated clients, and event replayers.
- DTOs, OpenAPI/GraphQL/protobuf schemas, domain events, provider payloads, reports, exports, and read models that reuse the same term.
- Permission policies, tenant filters, audit records, and support/admin override paths that imply ownership.
- Documentation, registry entries, and prior task evidence that name prior owners or fragile terms.

Strong evidence names scanned paths, accepted writer authority, rejected writers, boundary models that only translate, and paths not verified.
## Responsibility Chain
- `domain-object-identification` owns domain category, identity, lifecycle, aggregate, invariants, writer authority, relationships, and boundary mappings.
- A language Professional Skill owns reference identity, value representation, equality/hash contracts, and aliasing behavior in that language.
- `implementation-structure-design` owns object-versus-function/module and method/class/file placement after the domain classification and implementation owner are accepted.
- `module-boundary-design` owns cross-owner exports, dependencies, public surfaces, and packages. `refactoring` owns a behavior-preserving move only after the destination is fixed.
## Current Evidence And Freshness
- For a term classified in the current scope, record identity or equality semantics plus lifecycle and invariant ownership. Also record accepted and rejected writers and the boundary-model mappings found by the ownership and writer scan.
- After final object and schema edits, validate the rename or mapping, permission, persistence, event, generated-client, and read-model surfaces in the changed object boundary. Any skipped adjacent consumer or ownership risk carries a recorded rationale; unknown consumers remain proof limits.
## Object Validation Patterns
| Claim | Evidence Pattern | What It Proves | What It Does Not Prove |
| --- | --- | --- | --- |
| Entity identity is stable | Source path, identity field/source, tenant/merge/split semantics, tests or owner review. | Inspected code can distinguish the entity over time. | Future imports or external ids not inspected. |
| Value equality is attribute-based | Constructor/factory, normalization rules, equality tests, serialization boundary. | Tested values compare by declared attributes. | All locale/time/precision variants without coverage. |
| Aggregate boundary is enforceable | Invariant list, root operation, writer scan, transaction/consistency note. | Inspected invariants have an enforceable owner. | Production race windows without transaction/concurrency proof. |
| Resource does not replace domain language | Internal/external map, compatibility decision, generated/client/event impact. | Boundary naming is intentionally translated. | Unknown downstream consumers not inspected. |
| Read model stays read-only | Projection source, refresh owner, blocked mutation path, tests or review. | Inspected projection is not write authority. | Ad hoc support scripts outside searched scope. |
| Ownership is not split | Writer inventory, accepted mutation authority, rejected or rerouted writers. | Inspected writers have a single owner path. | Runtime-only tools or future jobs not inspected. |

## Anti-Patterns To Reject
- Treating table/DTO/schema/event/UI/provider names as domain truth, or creating an entity where a value object or resource boundary model is enough.
- Splitting aggregates by repository/screen/table convenience, or nesting aggregate objects across boundaries instead of referencing identity.
- Using prior task evidence, old tickets, or graph adjacency as ownership proof without current source confirmation.
- Renaming an internal object and silently changing public API/event/resource names.
- Leaving writer authority, permission implications, event impact, persistence mapping, or tests as later unowned work.
## Handoff Boundaries
- Use `business-rule-extraction` for unclear invariant wording/exception cases/rule authority; `state-machine-modeling` when lifecycle/terminal states/transitions need enumeration.
- Use `permission-boundary-modeling` when ownership changes actor rights; `data-model-design` when persistence/migration/index/storage constraints dominate.
- Use `dto-schema-design` or `model-boundary-mapping` for transfer schemas/generated clients/null-defaults/API compatibility; `domain-event-modeling` for event names/payloads/consumers/replay/versioning.
- Use `transaction-consistency` when ownership depends on concurrent writes, cross-aggregate consistency, or eventual consistency.

## Primary Sources
Official sources were accessed on 2026-07-26.
- [Microsoft: Implement value objects](https://learn.microsoft.com/en-us/dotnet/architecture/microservices/microservice-ddd-cqrs-patterns/implement-value-objects)
- [Microsoft: Introduction to Domain-Driven Design](https://learn.microsoft.com/en-us/archive/msdn-magazine/2009/february/best-practice-an-introduction-to-domain-driven-design)
- [Oracle Java Object](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/lang/Object.html)

## Proof Limits

Microsoft guidance supports the entity/value-object/aggregate vocabulary and the no-independent-identity, immutable-value, replacement, and aggregate-root concepts. It does not identify this repository's bounded context, domain owner, writers, or consistency boundary. Oracle `java.lang.Object` proves Java equality, hash, and reference contracts only; it does not prove domain identity, value-object semantics, aggregate boundaries, or writer authority.
