# Domain Object Identification Benchmarks And Patterns
Use this reference when `domain-object-identification` needs deeper support for object category selection, aggregate/resource separation, ownership and writer authority, current source/diff/validation coupling, validation maps, or anti-pattern review. Keep examples generic and do not include customer data, secret values, private policy text, or regulated identifiers.
- Classify each candidate as entity, value object, aggregate root, child entity, resource, policy, boundary model, or read model from domain meaning and bounded-context evidence.
## Object Category Decision Matrix
| Candidate Surface | Prefer Category | Evidence Required | False Proof |
| --- | --- | --- | --- |
| Stable identity, lifecycle, mutable state | Entity or aggregate root. | Identity source, lifecycle states, mutation authority, invariant owner. | A table has an `id` column. |
| Attribute-defined concept with no independent identity | Immutable value object with replacement semantics. | Equality attributes, normalization, precision, serialization boundary, and replacement behavior. | It is stored in its own table or DTO. |
| Consistency boundary | Aggregate root with child entities/value objects. | Root operations are the aggregate update and invariant entry point; invariants, transaction boundary, and writer authority are explicit. | Objects appear on the same screen or join query. |
| External API/event/provider name | Resource or boundary model. | Internal object mapping, compatibility owner, consumer impact. | The external field name matches a business noun. |
| Query-optimized projection | Read model. | Source aggregate/event, refresh semantics, write prohibition. | Projection has enough fields to mutate state. |
| Cross-object decision | Policy/specification or domain service. | Objects read, decision owner, no infrastructure effects. | A service method already branches on the fields. |

## Responsibility Chain
- `domain-object-identification` owns domain category, identity, lifecycle, aggregate, invariants, writer authority, relationships, and boundary mappings.
- A language Professional Skill owns reference identity, value representation, equality/hash contracts, and aliasing behavior in that language.
- `implementation-structure-design` owns object-versus-function/module and method/class/file placement after the domain classification and implementation owner are accepted.
- `module-boundary-design` owns cross-owner exports, dependencies, public surfaces, and packages. `refactoring` owns a behavior-preserving move only after the destination is fixed.
## Anti-Patterns To Reject
- Treating table/DTO/schema/event/UI/provider names as domain truth, or creating an entity where a value object or resource boundary model is enough.
- Splitting aggregates by repository/screen/table convenience, or nesting aggregate objects across boundaries instead of referencing identity.
- Using prior task evidence, old tickets, or graph adjacency as ownership proof without current source confirmation.
- Renaming an internal object and silently changing public API/event/resource names.
- Leaving writer authority, permission implications, event impact, persistence mapping, or tests as later unowned work.
## Primary Sources
Official sources were accessed on 2026-07-26.
- [Microsoft: Implement value objects](https://learn.microsoft.com/en-us/dotnet/architecture/microservices/microservice-ddd-cqrs-patterns/implement-value-objects)
- [Microsoft: Introduction to Domain-Driven Design](https://learn.microsoft.com/en-us/archive/msdn-magazine/2009/february/best-practice-an-introduction-to-domain-driven-design)
- [Oracle Java Object](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/lang/Object.html)

## Proof Limits

Microsoft guidance supports the entity/value-object/aggregate vocabulary and the no-independent-identity, immutable-value, replacement, and aggregate-root concepts. It does not identify this repository's bounded context, domain owner, writers, or consistency boundary. Oracle `java.lang.Object` proves Java equality, hash, and reference contracts only; it does not prove domain identity, value-object semantics, aggregate boundaries, or writer authority.
