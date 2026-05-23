# Benchmark Prompt

## Task

Implement a focused change to make cache invalidation consistent with database writes and reader freshness guarantees.

## Context

The starter repo represents a service stores account settings in SQL and caches read models for low latency reads. In its initial state, the starter behavior updates the database but leaves stale cache entries until TTL expiry. The implementation should be small enough to review but complete enough to prove the professional quality target.

## Requirements

- Settings reads reflect successful writes within the declared freshness boundary.
- Failed writes do not evict or repopulate cache with uncommitted data.
- Concurrent updates cannot restore stale values after a newer write.
- Invalidation failures are observable and retryable.

## Constraints

- Cache keys include tenant and account identity.
- Invalidation is ordered with transaction commit or uses a durable outbox.
- Tests cover stale read, failed write, and concurrent update cases.
- Preserve the existing public contract unless the prompt explicitly asks for a compatible addition.
- Do not replace the benchmark with documentation-only output.

## Deliverables

- Source changes in the starter repo that implement the requested behavior.
- Tests or executable checks that prove the required behavior and denial paths.
- A short implementation note describing important tradeoffs and residual risk.

## Completion Evidence

- `bash setup.sh`
- `bash ../test-suite/run.sh`
- `bash ../security-checks/run.sh`
- Review evidence that no automatic failure condition applies.
