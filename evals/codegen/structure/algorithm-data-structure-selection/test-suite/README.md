# Test Suite

## Required Checks

- Tests or benchmark evidence cover 10M-scale reasoning without requiring a full 10M fixture in the repository.
- Nested scans over 10M records and load-all processing without memory budget are rejected.
- Data structure selection matches dedupe, grouping, sorting, top-K, prefix, range, graph, or stable-order access patterns.
- Streaming, chunking, pagination, and batch-size behavior are exercised.

## Fixtures

Synthetic fixtures belong to the reconciliation test boundary and must state the input distribution, skew, duplicate pattern, and expected order.

## Expected Commands

- `bash ../test-suite/run.sh`

## Regression Cases

- Worst-case unmatched input does not degrade to O(n squared).
- Hot-key skew does not create unbounded memory growth.
- Top-K output remains stable for ties.
- Approximate structures are rejected unless exactness tradeoff is documented.
