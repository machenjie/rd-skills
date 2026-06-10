---
name: algorithm-data-structure-selection
description: Selects algorithms and data structures from input scale, access pattern, time and space complexity, memory budget, streaming needs, skew, and benchmark evidence; use to avoid unbounded load-all and accidental O(n squared) implementations.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "109"
changeforge_version: 0.1.0
---

# Mission

Choose algorithms and data structures that match the real problem shape, expected and worst-case input scale, memory budget, access pattern, and operational constraints.

# When To Use

Use when code filters, joins, deduplicates, groups, sorts, ranks, searches, paginates, streams, chunks, traverses graphs, maintains caches, processes batches, or handles unbounded user, file, table, event, or API inputs.

Use when nested scans, load-all processing, top-K, prefix/range queries, hot keys, skew, approximate answers, online processing, or performance-sensitive paths are present.

# Do Not Use When

Do not use to over-optimize tiny bounded inputs where N is known, stable, and documented.

Do not replace a clear simple solution with a complex structure unless input scale, access pattern, or benchmark evidence justifies it.

# Non-Negotiable Rules

- No algorithm choice without expected input size and worst-case behavior.
- No load-all when streaming or chunking is required by memory budget.
- No nested scan without bounded N or explicit complexity acceptance.
- Data structure must match access pattern.
- Memory budget must be explicit for unbounded inputs.
- Sorting, grouping, and top-K must justify complexity.
- Algorithmic optimization must be validated by test or benchmark when performance-sensitive.

# Industry Benchmarks

Anchor against Knuth algorithm analysis, CLRS data structure selection, database query planning principles, streaming processing practice, external sort and chunked processing, probabilistic data structures such as Bloom filters, cache eviction policies such as LRU/LFU, and benchmark-before-optimization discipline.

# Selection Rules

Select this capability when the main risk is computational complexity or data access pattern. Use `solution-optimality-evaluation` for broader tradeoff review, `profiling` for measured bottlenecks, `language-performance-safety` for runtime allocation and IO implications, and `data-middleware-change-builder` when indexes, SQL plans, queues, search, or storage engines own the performance shape.

# Risk Escalation Rules

Escalate to `reliability-observability-gate` when the algorithm affects SLOs, batch windows, queue lag, memory pressure, or cost. Escalate to `bigdata-product-extension` for distributed stream or batch jobs. Escalate to `security-privacy-gate` when adversarial input can trigger pathological complexity.

# Reference Loading Policy

Current mode is inline-only: this capability has no deep reference files today, so this `SKILL.md` contains the active algorithm and data-structure decision rules.

If deep references are added later, load them only for L3+ work, production-scale inputs, hot paths, unbounded load-all processing, unclear complexity, memory-budget risk, or benchmark/profile interpretation.

Do not load deep references for L1/L2 local changes where input size is bounded and the inline output contract for time, space, memory, and rejected alternatives is enough.

# Critical Details

- Map/list/set/heap/queue/deque/tree/trie/graph/Bloom filter/LRU/LFU/interval tree/segment tree choices must name the access pattern they optimize.
- Top-K usually prefers heap or selection over full sort when K is much smaller than N.
- Dedupe usually prefers set/hash index, but memory budget and collision/identity semantics must be clear.
- Grouping requires memory bound, spill strategy, or chunking plan for unbounded keys.
- Sorting requires stable ordering decision and O(n log n) or external sort rationale.
- Streaming beats load-all when input is unbounded, file-like, paged, or exceeds memory.
- Pagination and chunking need batch size, cursor/offset semantics, ordering, and retry behavior.
- Hot key and skew can dominate average complexity; name skew mitigation when distribution is uneven.
- Graph traversal requires BFS/DFS choice, visited set, cycle handling, and maximum frontier memory.
- Prefix/range queries require trie, ordered map/tree, index, or database range support.
- Probabilistic structures require false-positive rate and exactness acceptance.
- Online processing consumes inputs incrementally; offline processing can sort/index globally.

# Failure Modes

- Loading 10M records into memory because the unit test used 20 records.
- Nested scanning two large collections when a map, set, sort-merge, or index would bound work.
- Sorting a full list to return top 20 items.
- Grouping unbounded keys without memory budget or spill strategy.
- Using a list for membership checks in a hot path.
- Ignoring worst-case graph cycles, skewed keys, adversarial input, or stable ordering.
- Adding a complex probabilistic structure without explaining approximate versus exact semantics.

# Output Contract

Return an Algorithm/Data Structure Decision:

- Problem shape.
- Input size and distribution.
- Candidate approaches.
- Selected data structure.
- Time complexity.
- Space complexity.
- Average and worst-case behavior.
- Memory budget.
- Streaming, chunking, and pagination decision.
- Stable ordering and exact versus approximate decision.
- Rejected alternatives.
- Test, benchmark, or profile evidence.
- Residual scale risk.

# Evidence Contract

Close the decision only when it names the production-scale N, input distribution, bounded or unbounded status, complexity and memory estimates, benchmark or not-run rationale for hot paths, tests for edge/worst cases, evidence limits, residual risk owner, and the handoff for storage/runtime concerns.

# Quality Gate

1. Complexity is stated.
2. Worst-case behavior is stated.
3. Memory bound is stated.
4. Unbounded input is streamed, chunked, paginated, or explicitly rejected.
5. Data structure fits access pattern.
6. Sorting, grouping, dedupe, top-K, graph, prefix, or range query choice is justified.
7. Benchmark or profile evidence exists for hot paths.
8. Simpler alternative is considered and accepted or rejected with reason.

# Used By

- backend-change-builder
- frontend-change-builder
- data-middleware-change-builder
- reliability-observability-gate
- ai-code-review-refactor
- quality-test-gate
- architecture-impact-reviewer

# Handoff

Hand off to `solution-optimality-evaluation` for broader alternatives, `profiling` for measurement, `language-performance-safety` for allocation/runtime risks, `indexing-query-optimization` for database-backed access, `cache-design` for eviction, and `bigdata-product-extension` for distributed processing.

# Completion Criteria

The capability is complete when the implementation has a scale-aware algorithm decision, the selected structure matches access patterns, unbounded inputs are bounded by streaming/chunking/pagination, complexity and memory are explicit, and performance-sensitive choices have test or benchmark evidence.
