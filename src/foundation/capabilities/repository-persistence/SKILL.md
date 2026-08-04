---
name: repository-persistence
description: "`task-agent`: use for repository methods, query behavior, record mapping, visibility, errors, or transaction participation; skip schema, migration, DTO, and domain-rule work."
---

# repository-persistence

## Registry Trigger

**Use when**

- implement repository methods queries persistence record mapping visibility filters storage errors and transaction participation

**Do not use when**

- work is limited to logical/schema modeling, migration sequencing, domain rules, consumer inventory, or DTO/model translation

## Skill Role

Define the smallest repository port and adapter contract that preserves caller-visible persistence semantics. Own methods, queries, mapping lifecycle, visibility, storage-error translation, and transaction participation without leaking storage coupling.

## High-Value Rules

- Derive methods from current use cases and name results, visibility, ordering, pagination, consistency, deletion, and partial outcomes.
- Keep sessions, query builders, lazy behavior, rows, and provider errors behind the adapter boundary.
- Apply record/domain mapping inside the adapter when shapes or lifecycles differ.
- Follow the transaction owner and forbid independent commits that violate expected rollback.
- Put tenant, permission, retention, and soft-delete predicates at the authoritative query boundary.
- Translate storage outcomes without leaking sensitive or provider detail.
- Validate mapping, constraints, filters, rollback, lifecycle, and query bounds against a real or equivalent store.

## Anti-Patterns

- Reject generic query buckets, unbounded collection methods, implicit ordering, and caller-built storage predicates without an accepted contract need.
- Reject hidden commits, lazy loads outside the boundary, raw storage failures, and visibility rules duplicated as caller convention.
- Reject mock-only persistence approval and claims about production plans, volume, contention, or hidden callers that exceed inspected evidence.

## Stop Conditions

Stop for conflicting transaction ownership, visibility authority, mapping lifecycle, or method outcomes. Local integration evidence does not prove production cost, contention, replicas, or hidden consumers.

## Output Contract

- Return a repository-persistence contract: define methods, query semantics, mapping, visibility, transaction participation, error outcomes, validation, evidence, and proof limits

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | Repository contract mapping transaction visibility or query ownership remains unresolved | The existing repository boundary fully owns the changed persistence behavior | task-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | Change affects methods mappings transactions filters consistency storage errors or query bounds | Repository interface and persistence semantics remain unchanged | task-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | Mapping transaction tenant-filter storage-error or query claims need fresh proof | Current callers real-boundary tests schema and plans prove each bounded claim | task-agent | evidence-record, proof-limit, residual-risk |
