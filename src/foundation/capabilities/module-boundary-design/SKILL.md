---
name: module-boundary-design
description: "`analysis-agent`/`review-agent`: use when module ownership, public surface, dependency direction, cycles, or shared state changes; skip owner-internal placement."
---

# module-boundary-design

## Registry Trigger

**Use when**

- Module ownership, public/private surface, dependency direction, cycles, shared state, or a module split, merge, or move changes.

**Do not use when**

- The change stays inside one established module without changing its consumers, state authority, exports, or dependency edges.

## Skill Role

Define cross-module responsibility, state ownership, contractual surface, dependency direction, cycles, and split or merge decisions. Exclude system style, fixed-layer rules, model translation, and owner-internal placement.

Task-agent owner-internal placement belongs to `implementation-structure-design`.

## High-Value Rules

- `boundary-kind` is `plain directory | language package/module | build target/package | distributable SDK/library | runtime/service`, and its decision record names the authoritative mechanism and enforcement owner. A directory name is insufficient evidence of ownership.
- Anchor the boundary in one coherent responsibility with an accountable owner, invariant or policy authority, source of truth, and state lifecycle; folder names and team charts are selectors, not the boundary.
- Derive the public surface from verified consumers and their semantics, failures, compatibility, and versioning needs; keep repositories, persistence shapes, helpers, and mutable internals private without a proven contract.
- This capability owns in-repository responsibility, state authority, dependency direction, and public/private surface selection. For a distributable SDK/library, `sdk-library-contract-design` owns compatibility, migration, and external consumer proof while this capability retains state and dependency direction.
- Draw allowed and forbidden dependency edges before moving code. Resolve a cycle by relocating authority, introducing an owner-controlled contract, or changing coordination; a shared type does not remove the runtime cycle.
- Assign mutation and consistency authority for state crossing the boundary. Reject shared mutable state, direct reads of another module's storage, and writes that bypass the owning contract.
- Split when responsibility, invariant lifecycle, release/change reason, or consumer contract can vary independently without a cycle; merge when separation creates pass-through ownership or hidden coordination.
- Enforce the selected surface and edges with the authoritative language, build, package, or runtime mechanism; name the enforcement owner and expose unproved generated, dynamic, plugin, and runtime edges.

## Anti-Patterns

- Treating a framework, layer name, directory layout, file count, or coupling score as sufficient boundary proof.
- Moving business policy into `shared`, `common`, or `utils` to avoid choosing its owner.
- Publishing a facade that re-exports internals or mirrors another module without owning semantics.
- Renaming a cycle as a callback or event while state, ordering, failure, or retry ownership stays circular.

## Stop Conditions

Stop when state or source authority is unresolved, a required edge creates a cycle, a breaking surface has unknown consumers, or owners dispute mutation, compatibility, migration, or incident responsibility.

## Output Contract

- Module boundary decision with boundary-kind, authoritative mechanism, enforcement owner, responsibility and state authority, public/private surface, consumers, allowed/forbidden edges, cycle result, split/merge rationale, migration, evidence, proof limits, and residual risks.

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and enforcement](references/benchmarks-and-enforcement.md) | benchmark-pattern | module boundary enforcement choice or static generated and runtime proof limits remain disputed | the changed module edges are covered by fresh boundary enforcement results | analysis-agent, review-agent | option-comparison, selected-approach |
| [module decomposition](references/module-decomposition.md) | targeted | a module split merge or move remains open after responsibility state lifecycle and change-reason analysis | module owner state lifecycle and dependency direction already fix the boundary | analysis-agent, review-agent | boundary-decision, residual-risk |
