# Domain Object Identification Benchmarks And Patterns

Use this reference when `domain-object-identification` needs deeper support for object category selection, aggregate/resource separation, ownership and writer authority, graph/memory/trajectory coupling, validation maps, or anti-pattern review. Keep examples generic and do not include customer data, secret values, private policy text, or regulated identifiers.

## Object Category Decision Matrix

| Candidate Surface | Prefer Category | Evidence Required | False Proof |
| --- | --- | --- | --- |
| Stable identity, lifecycle, mutable state | Entity or aggregate root. | Identity source, lifecycle states, mutation authority, invariant owner. | A table has an `id` column. |
| Attribute-defined concept | Value object. | Equality attributes, normalization, precision, serialization boundary. | It is stored in its own table or DTO. |
| Consistency boundary | Aggregate root with child entities/value objects. | Invariants enforced together, transaction boundary, external references by identity. | Objects appear on the same screen or join query. |
| External API/event/provider name | Resource or boundary model. | Internal object mapping, compatibility owner, consumer impact. | The external field name matches a business noun. |
| Query-optimized projection | Read model. | Source aggregate/event, refresh semantics, write prohibition. | Projection has enough fields to mutate state. |
| Cross-object decision | Policy/specification or domain service. | Objects read, decision owner, no infrastructure effects. | A service method already branches on the fields. |

## Ownership And Writer Scan

Inspect every path that can define, create, mutate, merge, split, rename, expose, or translate the object.

- API handlers, command handlers, admin screens, import scripts, background jobs, queue consumers, migrations, support tooling, fixtures, and tests.
- Repository save/update paths, ORM setters/hooks, direct SQL scripts, generated clients, and event replayers.
- DTOs, OpenAPI/GraphQL/protobuf schemas, domain events, provider payloads, reports, exports, and read models that reuse the same term.
- Permission policies, tenant filters, audit records, and support/admin override paths that imply ownership.
- Documentation, registry entries, and project memory that name prior owners or fragile terms.

Strong evidence names scanned paths, accepted writer authority, rejected writers, boundary models that only translate, and paths not verified.

## Graph, Memory, And Trajectory Coupling

| Input | Accept When | Reject Or Downgrade When |
| --- | --- | --- |
| Repository graph | Current definitions, callers, writers, tests, schemas, events, and docs for the term were inspected. | Graph proximity is treated as semantic proof without reading source. |
| Project memory | Prior owner, incident, rename, or fragile object note has timestamp and unchanged source boundary. | Memory predates schema moves, generated clients, event versions, or ownership changes. |
| Execution trajectory | Inventory validation, owner review, and graph scans ran after the final object/reference edit. | Evidence predates the final file, generated artifact, or registry change. |
| Validation broker | Each changed object claim maps to identity/equality, lifecycle, mapping, permission, event, or writer evidence. | A broad validator is reported without claim-level coverage. |

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

- Treating table names, DTOs, generated schemas, event payloads, UI labels, or provider objects as domain truth by default.
- Creating a new entity where a value object or resource boundary model is enough.
- Splitting aggregates by repository, screen, or table convenience instead of invariant consistency.
- Nesting aggregate objects across boundaries instead of referencing by identity.
- Using project memory, old tickets, or graph adjacency as ownership proof without current source confirmation.
- Renaming an internal object and silently changing public API/event/resource names.
- Leaving writer authority, permission implications, event impact, persistence mapping, or tests as later unowned work.

## Handoff Boundaries

- Use `business-rule-extraction` when object categories are known but invariant wording, exception cases, or rule authority are unclear.
- Use `state-machine-modeling` when lifecycle states, terminal states, or transitions need enumeration.
- Use `permission-boundary-modeling` when object ownership changes who can read, mutate, approve, export, or administer it.
- Use `data-model-design` when persistence shape, migration, indexes, or storage constraints are primary.
- Use `dto-schema-design` or `model-boundary-mapping` when external transfer schemas, generated clients, null/default semantics, or API compatibility dominate.
- Use `domain-event-modeling` when event names, payloads, consumers, replay, or versioning are affected.
- Use `transaction-consistency` when aggregate ownership depends on concurrent writes, cross-aggregate consistency, or eventual consistency.
