# Review Rubric

## Passing Standard

The solution passes when algorithm choice is tied to input scale, access pattern, memory budget, worst-case behavior, and benchmark or profile evidence for the hot path.

## Scoring

- 25 percent problem shape: expected size, distribution, hot-key/skew, and worst-case behavior are explicit.
- 25 percent data structure fit: map, set, heap, queue, tree, trie, graph, bloom filter, LRU, LFU, interval tree, or segment tree is selected only when justified.
- 20 percent memory discipline: streaming, chunking, pagination, and batch size bound unbounded input.
- 20 percent complexity evidence: time and space complexity are stated and tested or benchmarked.
- 10 percent simplicity: simpler rejected alternatives are considered.

## Automatic Failure Conditions

- Nested scans remain over 10M records without bounded N and explicit acceptance.
- Load-all processing remains for unbounded input with no memory budget.
- Data structure mismatch ignores lookup, grouping, top-K, prefix, range, stable ordering, or graph traversal needs.
- No benchmark or profile evidence is supplied for a performance-sensitive optimization.

## Reviewer Notes

Reward clear tradeoffs. Penalize premature exotic structures when a map, set, heap, sorted stream, database index, or chunked query is sufficient.
