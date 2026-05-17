# Language Performance Safety Checklist

- Identify hot paths, throughput targets, and latency budgets.
- Review allocation rate, GC behavior, memory ownership, and resource cleanup.
- Check async runtime blocking and cancellation behavior.
- Review thread, goroutine, task, lock, and shared-state safety.
- Inspect FFI, native, or unsafe boundaries for invariants.
- Require profiling or load evidence where risk is material.
- Define mitigation, owner, and thresholds for accepted risk.
- Link tests to race, sanitizer, stress, or benchmark evidence.
