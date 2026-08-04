---
name: algorithm-data-structure-selection
description: "`analysis-agent`/`task-agent`/`review-agent`: use when scale, access, complexity, memory, streaming, or skew drives an algorithm/data-structure choice; skip when no choice exists."
---

# algorithm-data-structure-selection

## Registry Trigger

**Use when**

- algorithm data structure Big O input size worst case memory budget map set list heap queue deque tree trie graph bloom filter LRU LFU
- interval tree segment tree top K dedupe grouping sorting streaming chunking pagination nested scan load all hot key skew

**Do not use when**

- no task-local algorithm data structure selection decision is required

## Skill Role

Choose algorithms and data structures from problem shape, scale distribution, memory budget, identity and ordering semantics, access pattern, and operational constraints.

## High-Value Rules

- Select algorithms from current input scale, distribution, access pattern, worst-case behavior, and failure consequence.
- Set an explicit memory bound for unbounded or oversized input.
- Use streaming, chunking, spill, or pagination when load-all processing exceeds that bound.
- Reject nested scans without a bounded cardinality or explicit complexity acceptance from the affected owner.
- Define memory and identity bounds for sorting, grouping, deduplication, top-K, graph, or probabilistic structures.
- Validate performance-sensitive choices with a representative test or benchmark and state where production scale remains unverified.
- Require a rejected simpler alternative and validation plan before adding indexes, caches, concurrency, dependencies, or probabilistic structures as a performance fix.

## Anti-Patterns

- Choosing a familiar structure without naming the optimized access pattern substitutes habit for evidence.
- Fully sorting Top-K when K is much smaller than N wastes avoidable work.
- Hash deduplication without identity and collision semantics can corrupt results.
- Grouping unbounded keys without spill or chunking makes memory follow uncontrolled cardinality.
- Pagination without stable ordering and cursor semantics loses or duplicates work.
- Average-case selection that ignores skew or adversarial input hides the dominating case.
- Graph traversal without cycle handling and a frontier bound can loop or exhaust memory.

## Stop Conditions

Escalate SLO, batch-window, queue-lag, memory, or cost impact to `reliability-observability-gate`. Route distributed processing to `bigdata-product-extension` and adversarial complexity to `security-privacy-gate`.

## Output Contract

- Algorithm Decision: problem shape, input scale, selected structure, time/space bounds, memory budget, streaming/chunking choice, alternatives, benchmarks, and scale risk

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | Scale, skew, ordering, exactness, or memory changes the algorithm | The bounded operation has no material complexity tradeoff | task-agent, review-agent, analysis-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | Selection must cover worst-case growth, ordering, and oversize behavior | Input bounds and correctness semantics are already explicit | task-agent, review-agent, analysis-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | Performance claims require representative benchmarks, profiles, or query plans | No scale or hot-path claim needs empirical proof | task-agent, review-agent, analysis-agent | evidence-record, proof-limit, residual-risk |
