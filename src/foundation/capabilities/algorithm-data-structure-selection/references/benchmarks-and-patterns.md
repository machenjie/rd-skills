# Algorithm Data Structure Benchmarks And Patterns

Load this reference when input scale/distribution, time or memory complexity, ordering, exactness, streaming, storage ownership, or parallelism can change the implementation choice. Do not load it for a bounded obvious operation with no material performance or correctness tradeoff.

## Access Pattern Fit

| Need | Candidate families | Required proof before selection |
| --- | --- | --- |
| Membership/dedupe/hot lookup | Set/map, sort-and-unique, database constraint/index, or approximate membership. | Identity/collision semantics, N/frequency, exactness, memory, and source ownership. |
| Top-K/ordered page | Full sort, heap/selection, index-backed order, or cursor/partial sort. | K versus N, stable tie-breaker, update pattern, query plan, and measured hot-path need. |
| Group/aggregate/join | Hash, sorted stream, storage aggregation/join, chunk/spill. | Cardinality/skew, selected side, memory ceiling, source freshness, and overflow behavior. |
| Range/prefix/interval | Ordered tree/map, trie, interval structure, or database/search index. | Query/update frequency, range semantics, selectivity, and storage alternative. |
| Graph/tree traversal | BFS/DFS/priority/topological traversal as correctness requires. | Cycle guarantee, visited behavior, depth/frontier/node/edge bounds, and disconnected cases. |
| Stream/large input | Iterator/cursor/chunked or external algorithm. | Batch/byte ceiling, order, checkpoint/retry, partial failure, and whole-input dependency. |
| Approximate result | Bloom/sketch/sampling or equivalent. | Error/false-positive bound, exact fallback, decision consequence, monitoring, and owner acceptance. |

## Complexity And Failure Record

Record caller/input source, expected and worst-case N, distribution/skew, call frequency, and selected candidate. Record average/worst time, space and runtime-overhead estimates, stable ordering, identity/collision, exactness, and memory/item/byte ceiling. Record spill/chunk/page/reject behavior, the rejected strongest alternative, and the trigger/owner that reopens a bounded-simple choice.

Prefer current datastore primitives when they own data freshness and selectivity.
Candidate primitives include query plans, indexes, cursors, aggregations, and search.
An application-side index can create stale duplicate truth.
Stream or spill only when whole-input semantics allow it.
Parallelize only with independent partitions, bounded coordination or contention, ordering rules, cancellation, and combined-resource evidence.

## Evidence And Proof Limits

Use correctness cases for edges, ties, cycles, duplicates, ordering, overflow, and approximation. Use profile, benchmark, or load evidence on final code with representative scale and distribution. Big-O omits constants and skew. Byte estimates omit runtime overhead. Unit fixtures, query plans, and local benchmarks have environment-specific proof limits.

Reject “the list is small” without an owned bound, Big-O without memory, and habitual full sort, cache, or parallelism. Also reject application indexes over source-owned data, benchmark evidence predating final edits, and small fixtures reported as capacity proof.

Route query and index ownership to `indexing-query-optimization`.
Route cache semantics to `cache-design` and concurrency or coordination to `concurrency-control`.
Route resource budgets to `performance-budgeting` and empirical hot-path diagnosis to `profiling`.
Route final validation sufficiency to `quality-test-gate`.
