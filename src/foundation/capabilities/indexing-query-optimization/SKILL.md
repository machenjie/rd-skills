---
name: indexing-query-optimization
description: "`task-agent`/`review-agent`: use when predicates, sorting, cardinality, query plans, pagination, indexes, or write cost change; skip when no query/index decision exists."
---

# indexing-query-optimization

## Registry Trigger

**Use when**

- optimize indexes query plans pagination filters sorting and read paths

**Do not use when**

- no task-local indexing query optimization decision is required

## Skill Role

Define beneficiary-query identity, plan evidence, data distribution, index or query choice, pagination stability, write and storage cost, statistics, rollout, and regression proof. Exclude data-model redesign and production capacity claims.

## High-Value Rules

- **Name the beneficiary query and objective.** Bind predicates, joins, projection, ordering, pagination, tenant scope, frequency, result size, and current latency or resource consequence before proposing an index.
- **Select documented plan evidence for the engine and version.** Bind the current engine/version, its documented plan command, representative parameters, statistics freshness, and estimated, executed, or telemetry-derived evidence class.
- **Bound plan execution.** Treat estimated plans and/or bounded query telemetry with explicit proof limits as fallback when representative parameters or data, side-effect, lock, and resource boundaries make execution unsafe or unavailable.
- **Match index order to access semantics.** Derive leading keys, equality and range behavior, ordering, covering columns, selectivity, null handling, and partial conditions from the current query family rather than isolated folklore.
- **Account for write and lifecycle cost.** Compare each candidate's insert and update amplification, storage, cache pressure, lock or build behavior, replication, maintenance, backup, and removal ownership.
- **Make pagination stable under change.** Define deterministic ordering, tie breakers, cursor meaning, visibility, duplicates, omissions, and behavior when rows are inserted, deleted, or updated between pages.
- **Challenge plan stability.** Validate relevant cardinality skew, hot tenants, parameter sensitivity, stale statistics, range extremes, cold cache, and supported engine variations.
- **Roll out with observable comparison.** Capture before and after plans and workload evidence, regression signals, fallback or removal path, and limits separating local measurement from production capacity.

## Anti-Patterns

- Add an index without a named query, representative plan, and measurable beneficiary.
- Optimize one sampled parameter while ignoring skew, parameter sensitivity, write cost, and competing queries.
- Use offset pagination or an unstable sort where concurrent data change can duplicate or omit results unnoticed.

## Stop Conditions

Escalate when the beneficiary query or objective is unknown, or neither safe engine/version plan evidence nor bounded query telemetry can support the decision. Also escalate when write cost threatens critical paths, online build or rollback is unsafe, pagination identity is ambiguous, or capacity claims exceed tested evidence. Do not claim measured runtime improvement from estimated plans or telemetry that cannot isolate the change.

## Output Contract

- query optimization decision with beneficiary query, plan and distribution evidence, index or query rationale, pagination semantics, write and lifecycle cost, rollout comparison, proof limits, and residual owners

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | Index type, pagination, plan, or write-cost choices compete | No material query plan or access pattern changes | task-agent, review-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | Optimization affects selectivity, ordering, writes, builds, or N-plus-one behavior | The query has no measurable resource or latency risk | task-agent, review-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | Optimization claims need current plans, volumes, and benchmark results | No plan or capacity claim is being approved | task-agent, review-agent | evidence-record, proof-limit, residual-risk |
