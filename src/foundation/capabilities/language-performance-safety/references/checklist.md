# Language Performance Safety Checklist

- Identify hot paths, throughput targets, and latency budgets.
- Review allocation rate, GC behavior, memory ownership, and resource cleanup.
- For collections, buffers, caches, batches, pagination windows, retry accumulators, or fan-out lists, determine whether untrusted, external, or workload-driven input controls size. Define a count or byte ceiling unless the source has a proven bound.
- Clamp untrusted sizes before allocation; prefer streaming, pagination, and chunking for large inputs/results.
- Reuse HTTP, DB, SDK, queue, cache, and worker-pool clients at the correct lifecycle; do not construct them per operation.
- Verify response bodies, streams, cursors, timers, subscriptions, file handles, and temporary files are cleaned up on success, error, timeout, and cancellation paths.
- Check async runtime blocking and cancellation behavior.
- Review thread, goroutine, task, lock, and shared-state safety.
- Inspect FFI, native, or unsafe boundaries for invariants.
- Require profiling or load evidence where risk is material.
- Define mitigation, owner, and thresholds for accepted risk.
- Link tests to race, sanitizer, stress, or benchmark evidence.
