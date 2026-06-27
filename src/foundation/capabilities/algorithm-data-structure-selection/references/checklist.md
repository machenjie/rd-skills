# Algorithm Data Structure Selection Checklist

- Name the operation: filter, join, dedupe, group, sort, rank, search, paginate, stream, traverse, or cache.
- State expected N, worst-case N, item size, distribution, and trusted size source.
- Classify the input as bounded, unbounded, paged, streamed, generated, adversarial, or skewed.
- Match the data structure to the access pattern: membership, ordered lookup, top-K, prefix/range, graph traversal, or aggregation.
- State average and worst-case time complexity plus space complexity.
- Define memory budget, growth cap, spill/chunk/page/reject behavior, and cleanup owner.
- Preserve correctness semantics: stable ordering, identity/collision rules, exactness, and determinism.
- Compare the simplest acceptable approach, storage/index option, cache option, and parallel option.
- Validate hot paths with benchmark/profile/query-plan/load evidence or state the not-run rationale.
- Record graph/memory freshness, evidence limits, residual scale risk, and next gate.
