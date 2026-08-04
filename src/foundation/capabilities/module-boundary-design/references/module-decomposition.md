# Module Split Merge And Move Decision

These patterns compare keep, split, move, and merge decisions using responsibility, state lifecycle, change reason, consumers, dependency direction, ownership, and reversibility.

## Boundary Classification

Before comparing structure, record one `boundary-kind`:

| Boundary-kind | Authoritative mechanism | Enforcement owner |
| --- | --- | --- |
| Plain directory | Repository convention without language or build visibility | Named semantic owner and repository policy owner |
| Language package/module | Language package, import, export, scope, and visibility rules | Language and module owner |
| Build target/package | Build rule, label, target graph, declared deps, and visibility | Build target owner |
| Distributable SDK/library | Published artifact and consumer compatibility contract | `sdk-library-contract-design` owner |
| Runtime/service | Deployed process/service contract, state authority, and runtime call boundary | Runtime/service and incident owner |

A directory name, proximity, team name, or framework layer is insufficient evidence of the semantic owner. Confirm the authoritative mechanism and current enforcement before selecting keep, split, move, or merge.

## Decomposition Evidence

| Signal | Keep together | Split or move | Merge or decline split |
| --- | --- | --- | --- |
| Responsibility and invariant authority | One responsibility and authority protect a cohesive rule set. | A responsibility has independent policy authority and a stable contract. | A separate facade relays calls without owning semantics. |
| State and source lifecycle | Mutation, consistency, and recovery share one authority and lifecycle. | State has a distinct source, mutation owner, lifecycle, and boundary contract. | Hidden shared state or transaction ownership makes the apparent split false. |
| Change reason and release rhythm | Normal changes evolve together under one compatibility decision. | Accepted changes can evolve or release independently without hidden coordination. | Separate files or teams still change together because responsibility remains shared. |
| Consumers and public contract | Consumers need one coherent surface and failure model. | A sub-responsibility has verified consumers, stable semantics, and a compatibility owner. | The added surface merely re-exports internals or duplicates another contract. |
| Dependency direction | Separation would force cyclic coordination or shared mutable state. | An acyclic public edge preserves authority and keeps internals private. | Internal imports, callbacks, or shared types bypass the declared surface. |
| Ownership and operations | One reviewer and incident owner can maintain the responsibility. | A distinct owner accepts compatibility, migration, and incident duties. | The proposed boundary has no accountable contract or operational owner. |
| Migration and reversibility | Unknown consumers or state movement prevent a bounded transition. | A bridge, coexistence period, validation, rollback, and retirement path are viable. | The structural move adds permanent duplication without a retirement condition. |

## Required Decision

- Select keep, split, move, or merge and name the responsibility and authority preserved by that outcome.
- Record before/after owners, public surfaces, state authority, allowed edges, consumers, tests, migration, rollback, and residual unknowns.
- Route file and object placement inside the selected module to `implementation-structure-design`.

## Proof Limits

Language and build mechanisms prove only the scopes, imports, targets, deps, and visibility they actually enforce. They do not prove semantic responsibility, state authority, generated or dynamic edges, runtime calls, external consumers, or incident ownership.
