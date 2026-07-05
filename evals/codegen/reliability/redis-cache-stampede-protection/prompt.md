# Benchmark Prompt

## Task

Implement a focused change that protects a Redis-backed read path from hot-key expiration storms while keeping failure behavior observable and bounded.

## Context

The starter repo represents product detail caching where a flash-sale hot key expires and all requests fall through to the database. The implementation should preserve the read path while adding stampede protection, TTL jitter, and safe degradation.

## Requirements

- Ensure hot key refresh is single-flight or lock-protected.
- Add TTL jitter so many keys do not expire at the same instant.
- Bound cache miss storms and protect the source of truth during Redis failures.
- Emit metrics for hot keys, miss storms, fallback usage, and lock contention.
- Prove the single-flight behavior with deterministic local tests that use a
  fake or in-memory cache plus a FakeBackend/source-of-truth seam, same-key
  concurrent workers, and an assertion that exactly one backend refresh occurs,
  such as `backend.calls == 1`.

## Constraints

- Cache keys must include tenant, permission, and variant dimensions when those dimensions affect correctness.
- Lock ownership and timeout behavior must be documented and testable.
- Do not replace the benchmark with documentation-only output.
- Avoid any network dependency, live Redis instance, network client, URL, or
  external service; scripts must run locally from the starter repo.

## Deliverables

- Source changes in the starter repo that implement the requested cache behavior.
- Tests or executable checks that prove the required behavior, Redis-down
  fallback, and stampede protection using local fakes instead of live services.
- A short implementation note describing important tradeoffs and residual risk.

## Completion Evidence

- `bash setup.sh`
- `bash ../test-suite/run.sh`
- `bash ../security-checks/run.sh`
- Review evidence that no automatic failure condition applies.
