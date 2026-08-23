---
name: module-boundary-design
description: "Use for cross-module ownership, surface, dependency, cycle, state, split, merge, or move decisions; skip owner-internal placement."
---

# module-boundary-design

## Registry Trigger

**Use when**

- Cross-module ownership, surface, dependency, state, split, merge, or move changes.

**Do not use when**

- One established module retains consumers, state authority, exports, and edges.

## Skill Role

Own cross-module responsibility, state, surface, dependency, and decomposition. Owner-internal placement belongs to `implementation-structure-design`.

## High-Value Rules

- Name the boundary kind, authoritative mechanism, and enforcement owner.
- Record responsibility, state authority, surface, and allowed/forbidden edges.
- Route SDK compatibility and owner-internal structure to their specialist owners.

## Anti-Patterns

- Local success is not boundary-contract evidence.

## Stop Conditions

- Stop on unresolved authority, cycles, consumers, migration, or incident ownership.

## Output Contract

- Module boundary decision with boundary-kind, authoritative mechanism, enforcement owner, responsibility and state authority, public/private surface, consumers, allowed/forbidden edges, cycle result, split/merge rationale, migration, evidence, proof limits, and residual risks.

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and enforcement](references/benchmarks-and-enforcement.md) | benchmark-pattern | module boundary enforcement choice or static generated and runtime proof limits remain disputed | the changed module edges are covered by fresh boundary enforcement results | analysis-agent, review-agent | option-comparison, selected-approach |
| [boundary kind and authority](references/boundary-kind-and-authority.md) | targeted | boundary kind authoritative mechanism owner state surface or dependency direction remains open | current mechanism owner state authority surface and allowed edges already fix the boundary | analysis-agent, review-agent | boundary-decision, decision-record, residual-risk |
| [split merge and move decisions](references/split-merge-and-move-decisions.md) | targeted | a module split merge or move remains open after authority lifecycle consumer and change-reason analysis | module owner state lifecycle and dependency direction already fix keep split move or merge | analysis-agent, review-agent | boundary-decision, selected-approach, residual-risk |
