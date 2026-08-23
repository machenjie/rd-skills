# Split, Merge, and Move Decisions

Language and build mechanisms prove only the scopes, imports, targets, deps, and visibility they actually enforce. They do not prove semantic responsibility, state authority, generated or dynamic edges, runtime calls, external consumers, or incident ownership.

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
- Split when responsibility, invariant lifecycle, release/change reason, or consumer contract can vary independently without a cycle; merge when separation creates pass-through ownership or hidden coordination.

## Anti-Patterns

- Treating a framework, layer name, directory layout, file count, or coupling score as sufficient boundary proof.
- Moving business policy into `shared`, `common`, or `utils` to avoid choosing its owner.
- Publishing a facade that re-exports internals or mirrors another module without owning semantics.
- Renaming a cycle as a callback or event while state, ordering, failure, or retry ownership stays circular.
