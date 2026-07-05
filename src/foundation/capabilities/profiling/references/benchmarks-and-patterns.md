# Profiling Benchmarks And Patterns

Use this reference when `profiling` needs more detail than the main `SKILL.md` can carry efficiently. Keep the body focused on routing, evidence, and gates; use this file for tool selection, benchmark anchors, privacy-safe capture, cost attribution, and graph/memory/execution coupling.

## Tool Selection Matrix

| Bottleneck signal | Preferred evidence | Avoid |
| --- | --- | --- |
| CPU-bound service path | CPU flame graph, `perf`, async-profiler, JFR, `pprof`, `py-spy`, or runtime profiler. | Microbenchmark-only proof when request frequency is unknown. |
| Off-CPU wait or lock contention | Off-CPU flame graph, thread dump, lock-wait profile, queue wait metric, or trace span wait time. | Rewriting CPU code when CPU is idle and p99 is wait-bound. |
| Allocation or GC pressure | Allocation profile, heap diff, GC log, retained-size report, RSS soak trend. | Tuning heap or GC without reducing allocation or retention. |
| Query or warehouse cost | `EXPLAIN ANALYZE`, `pg_stat_statements`, slow-query plus span count, scan bytes, partition read, warehouse dry-run. | Dev-data timing or a single slow-query threshold. |
| Network fan-out | Distributed trace span count, dependency p95/p99, retry count, timeout and circuit metrics. | Aggregated endpoint latency without dependency breakdown. |
| Frontend rendering | Chrome DevTools performance trace, Lighthouse/field CWV, long-task report, React/Vue profiler. | Fast developer-machine run as proof for median devices. |
| Cloud unit cost | Billing export joined to route, tenant, job, query, egress, storage, autoscaling, and retry metrics. | Monthly spend total without a runtime driver. |

## Benchmark Anchors

- **USE method:** utilization, saturation, and errors decide whether the bottleneck is CPU, disk, network, memory, lock, or pool pressure.
- **RED method:** rate, errors, and duration keep service-level symptoms tied to user-facing paths.
- **Amdahl's Law:** optimizing a small fraction of elapsed time cannot materially improve end-to-end latency.
- **Little's Law:** queue depth and pool size must be consistent with throughput and service time.
- **Core Web Vitals and Long Tasks:** LCP, INP, CLS, and main-thread tasks over 50ms guide browser profiling.
- **FinOps unit economics:** cost attribution must reduce spend to request, tenant, job, query scan, storage, egress, or autoscaling unit.

## Privacy-Safe Capture Pattern

1. State the artifact type: flame graph, heap dump, trace, query plan, billing export, browser trace, or profiler report.
2. Classify sensitive fields: request body, SQL parameters, user/tenant identifiers, token, cookie, payment data, free text, and secret-like values.
3. Choose capture boundary: staging mirror, shadow traffic, off-peak production sample, standby replica, or sanitized export.
4. Redact or normalize before sharing: normalized query text, request ID instead of body, aggregated spans, hashed tenant identifiers, stripped query strings.
5. Record owner, storage path, retention window, and deletion path for every artifact.

## Graph Memory Execution Coupling

- **Repository graph:** identify route, job, query, rendering path, dependency fan-out, caller frequency, ownership, and sibling hot paths before selecting a profiler.
- **Project memory:** treat old benchmarks, incident notes, and prior profiling artifacts as leads; accept them only with source date, unchanged graph, and comparable workload.
- **Execution trajectory:** compare command history, previous validation, generated reports, and final edit time; stale runs cannot close profiling evidence.
- **Validation broker:** map changed paths to correctness tests, performance reruns, privacy checks, and release gates before handoff.

## Handoff Boundaries

- Use `performance-budgeting` when the measured improvement should become a threshold or release gate.
- Use `indexing-query-optimization` when the confirmed bottleneck is a SQL/ORM query plan, index, pagination, or scan issue.
- Use `language-performance-safety` when allocation, GC, event loop, pool lifecycle, unsafe/native, or runtime cleanup owns the fix.
- Use `concurrency-control` when the confirmed bottleneck is lock contention, hot row, race, worker saturation, or queue ordering.
- Use `security-privacy-gate` when profiling artifacts can expose sensitive data or tool execution can leak command output.
- Use `delivery-release-gate` when the fix needs canary, capacity change, rollback trigger, or production restart coordination.
