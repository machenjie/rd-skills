# Boundary Kind and Authority

Use this Reference only when the module boundary kind, authoritative mechanism, owner, state, surface, or dependency direction remains open.

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

## Decision Rules

- `boundary-kind` is `plain directory | language package/module | build target/package | distributable SDK/library | runtime/service`, and its decision record names the authoritative mechanism and enforcement owner. A directory name is insufficient evidence of ownership.
- Anchor the boundary in one coherent responsibility with an accountable owner, invariant or policy authority, source of truth, and state lifecycle; folder names and team charts are selectors, not the boundary.
- Derive the public surface from verified consumers and their semantics, failures, compatibility, and versioning needs; keep repositories, persistence shapes, helpers, and mutable internals private without a proven contract.
- This capability owns in-repository responsibility, state authority, dependency direction, and public/private surface selection. For a distributable SDK/library, `sdk-library-contract-design` owns compatibility, migration, and external consumer proof while this capability retains state and dependency direction.
- Draw allowed and forbidden dependency edges before moving code. Resolve a cycle by relocating authority, introducing an owner-controlled contract, or changing coordination; a shared type does not remove the runtime cycle.
- Assign mutation and consistency authority for state crossing the boundary. Reject shared mutable state, direct reads of another module's storage, and writes that bypass the owning contract.
