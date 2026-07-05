# Algorithm Data Structure Benchmarks And Patterns

Use this reference when inline guidance is not enough to choose or review an algorithm or data structure. Keep the main skill focused on routing and gates; use this file for candidate comparisons, complexity anchors, memory planning, and benchmark interpretation.

## Benchmark Anchors

- **Big-O analysis:** state average and worst-case time and space complexity; Big-O without N and distribution is incomplete.
- **CLRS / Knuth:** arrays/lists, hash tables, trees, heaps, queues, graph traversal, dynamic programming, and amortized analysis provide the baseline vocabulary.
- **Database query planning:** prefer indexes, query plans, cursors, and storage-engine ordering when the datastore owns the scalable access path.
- **Streaming and external algorithms:** chunking, pagination, external sort, spill-to-disk, checkpointing, and backpressure handle inputs larger than memory.
- **Amdahl's Law:** parallel workers cannot overcome a mostly sequential pipeline or high coordination cost.
- **Cache theory:** LRU/LFU/TTL policies require source-of-truth, invalidation, cardinality, and cold-cache behavior, not only a faster lookup.
- **Probabilistic structures:** Bloom filters, HyperLogLog, sketches, and sampling require false-positive/error bounds and exactness acceptance.

## Access Pattern Decision Matrix

| Access pattern | Usually consider | Reject when | Required evidence |
| --- | --- | --- | --- |
| Membership check | Hash set, map, database index, Bloom filter | N is tiny and bounded or exactness forbids approximation | N, identity/collision rule, memory estimate |
| Dedupe | Set/hash index, sort then unique, storage constraint | Ordering, memory, or distributed ownership is unclear | Key semantics, duplicate behavior, memory cap |
| Top-K or first page | Heap, selection, index-backed order, cursor, bounded partial sort | Full sort is simpler and N is small/bounded | K vs N, stable tie-breaker, benchmark when hot |
| Grouping or aggregation | Hash map, sorted stream aggregation, database aggregation, chunk/spill | Key cardinality is unbounded without budget | Cardinality estimate, spill/reject behavior |
| Join | Hash join, sort-merge join, database join, bounded nested scan | Data ownership or freshness belongs to storage engine | N and M, ownership, selected side loaded |
| Prefix/range lookup | Trie, ordered map/tree, interval tree, segment tree, search/database index | Query count is tiny and scan is bounded | Range semantics, update cost, memory estimate |
| Graph/tree traversal | BFS, DFS, priority traversal, topological sort | Cycles/frontier/depth are unknown | Max nodes/edges/depth, visited set, frontier cap |
| Streaming transform | Iterator/generator, cursor pagination, chunked pipeline | Caller requires global order or whole-input context | Batch size, order contract, retry/checkpoint behavior |
| Approximate query | Bloom filter, sketch, sampling, HyperLogLog | Exact answer is required for correctness or billing | Error rate, fallback, monitoring, owner |

## Complexity And Memory Record

```yaml
algorithm_decision:
  operation: ""
  caller_path: ""
  input_origin: ""
  expected_n: ""
  worst_case_n: ""
  distribution: ""
  selected_structure: ""
  average_complexity: ""
  worst_case_complexity: ""
  space_complexity: ""
  memory_budget:
    item_size_estimate: ""
    max_items_or_bytes: ""
    spill_chunk_page_or_reject: ""
  correctness:
    stable_ordering: ""
    identity_collision_semantics: ""
    exactness: ""
  rejected_alternatives:
    - alternative: ""
      reason: ""
  validation:
    command_or_artifact: ""
    proves: ""
    does_not_prove: ""
```

## Scale Decision Patterns

- **Bounded local list:** keep the readable list/sort when N is documented and stable; record the bound and owner that must reopen the decision if N changes.
- **Unbounded import or API pagination:** stream or chunk with byte/item ceilings, stable order, checkpoint/retry behavior, and oversize rejection.
- **Hot membership path:** precompute a set or use a storage index; reject list membership when N or call frequency can grow.
- **Top-K ranking:** avoid full sort when K is much smaller than N; use heap/selection/index-backed order and preserve deterministic tie-breakers.
- **Skewed grouping:** cap keys, spill, shard by stable key, or reject oversized groups; average cardinality is not enough.
- **Graph walk:** choose BFS/DFS/priority traversal based on correctness semantics; always include visited set, cycle behavior, and frontier cap.
- **Database-owned access:** prefer query plans, indexes, cursors, or search engine features when source-of-truth freshness and selectivity live in storage.
- **Parallel batch:** split only when partitions are independent, coordination is bounded, and validation covers contention and ordering.

## Validation Matrix

| Claim | Minimum validation |
| --- | --- |
| Bounded simple structure is enough | Unit edge cases plus documented N and reopen trigger |
| Hot path improvement | Benchmark/profile with representative N, distribution, and final code |
| Memory safety | Item byte estimate, max items, chunk/spill/reject behavior, and oversize test |
| Stable ordering | Fixture/golden or property case with ties, pagination, replay, or dedupe |
| Approximation accepted | Error/false-positive test, fallback behavior, and owner approval |
| Storage/index alternative rejected | Current query path, query plan or owner rationale, and write/read tradeoff |
| Parallelism accepted | Stress/load evidence, partition independence, ordering, and contention limits |
| Graph traversal safe | Cycle, depth/frontier, disconnected graph, and maximum-node tests |

## Anti-Patterns To Reject

| Anti-pattern | Why it fails |
| --- | --- |
| "The list is small" without caller/source evidence | Caller changes can invalidate the assumption silently |
| Big-O statement without memory budget | Time can be acceptable while memory fails |
| Full sort for first page or top-K | Wastes CPU/memory when partial order is enough |
| Application-level index over database-owned data | Duplicates source of truth and creates stale state |
| Cache before fixing an O(n squared) path | Cold-cache and invalidation behavior still fail |
| Parallel workers without partition proof | Coordination and contention can dominate saved work |
| Benchmark before final edit | Evidence does not cover the shipped algorithm |
| Unit fixture as scale proof | Small fixtures prove correctness, not production memory or tail latency |
