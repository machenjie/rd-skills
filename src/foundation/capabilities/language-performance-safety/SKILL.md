---
name: language-performance-safety
description: Use when evaluating language-specific performance and safety across allocation, garbage collection, memory ownership, concurrency, async behavior, FFI, unsafe/native boundaries, blocking work, and hot-path constraints.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "87"
changeforge_version: 0.1.0
---

# Mission

Evaluate language- and runtime-specific performance and safety properties — allocation shape, GC behavior, scheduler/event-loop interaction, async cancellation, blocking work, lock scope, FFI / unsafe boundaries, hot-path constraints, backpressure, and resource lifecycle — against an explicit measurement contract. Reject optimization by intuition or by language reputation. Demand evidence: profile, trace, allocation log, GC log, sanitizer run, stress run.

# When To Use

Use when a change touches hot paths, high-throughput code, latency-sensitive APIs, concurrency primitives, async runtimes, native/FFI interop, memory-sensitive workloads, parsers/deserializers, or any code that can pass review and fail under representative load. Use whenever the change crosses an unsafe boundary or modifies a synchronization primitive.

# Do Not Use When

Do not use to apply micro-optimizations without a profile pointing at the line. Do not use to replace SLO-driven measurement with generic language claims ("Go is fast", "Rust is safe"). Do not use for cold/rare paths where simplicity outweighs perf.

# Non-Negotiable Rules

- **Optimization is evidence-driven.** Profile first, then change. No optimization PR merges without a before/after measurement attached.
- **Hot-path code is classified explicitly.** A function is "hot" only if profile data shows it. Author claims like "this might be hot" do not classify hot path.
- **GC-managed runtimes require allocation analysis on declared hot paths.** Allocation rate (B/req), allocation count (allocs/req), and GC pause distribution measured against SLO.
- **Async runtimes must not be blocked.** Node.js / Python asyncio / Java reactive / Rust async: no CPU-heavy or sync IO call on the event loop or async task. Blocking work goes to a dedicated executor / worker pool.
- **Unsafe / FFI / native boundaries require a written safety contract**: invariants, ownership transfer, error propagation, panic boundary, thread-safety assumption. Reviewed by ≥ 2 engineers including one fluent in the unsafe language.
- **Resource cleanup is paired with acquisition** in the language's idiomatic way (RAII, `defer`, `with`, try-with-resources, `Drop`). Asymmetric cleanup is rejected.
- **Concurrency changes require race-detector / sanitizer / stress evidence** in CI before merge.
- **Safety / readability are not traded for perf without documented justification + measurement**: "this is 3× faster" without numbers is rejected; "this is 3× faster (p99 1.2 ms → 0.4 ms at 10k RPS, profile attached)" is the minimum.
- **Backpressure and cancellation are first-class.** Any unbounded queue, fan-out, or retry loop is a defect until proven bounded.
- **Every growth surface is bounded.** Arrays, slices, lists, maps, sets, buffers, batches, caches, pagination windows, retry accumulators, and log/event aggregation must have an explicit item count and/or byte budget. Untrusted input counts must never drive allocation without a maximum.
- **Reusable clients and pools are lifecycle-managed.** HTTP clients, DB pools, Redis clients, Kafka producers/consumers, SDK clients, thread pools, and worker pools are created at process/module/request-scope boundaries appropriate to the runtime, not per operation. Keep-alive, max connections, idle timeout, max lifetime, cleanup, and observability must be configured.

# Industry Benchmarks

- **Google SRE Workbook — Latency Budgets** and **Error Budget Policy**.
- **Brendan Gregg — Systems Performance**, USE method (Utilization / Saturation / Errors), RED method (Rate / Errors / Duration) for service-level perf observation.
- **Amdahl's Law** and **Universal Scalability Law (Gunther)** for concurrency scaling limits.
- **Little's Law** for queue / pool / connection-pool sizing: `L = λW` (in-flight = throughput × latency).
- **Profilers per runtime**: pprof (Go), async-profiler / JFR / JMC (JVM), py-spy / scalene / memray (Python), perf + flamegraph + eBPF (C/C++/Linux), clinic.js / 0x / `--prof` (Node.js), tokio-console / `cargo flamegraph` / `samply` (Rust).
- **Sanitizers** (LLVM / GCC): AddressSanitizer (ASan), UndefinedBehaviorSanitizer (UBSan), ThreadSanitizer (TSan), MemorySanitizer (MSan), LeakSanitizer (LSan).
- **Race detectors**: `go test -race`, Java jcstress, Rust loom, C/C++ TSan.
- **Memory models**: Java JMM (JSR-133), C++11+ memory model, Go memory model (refreshed 2022), Rust's UCG (under development).
- **GC tuning references**: Go GC pacer (Hudson 2018), JVM ZGC / Shenandoah / G1 tuning guides, .NET background GC notes.

# Selection Rules

Select when performance or runtime safety depends on language/runtime choice. Pair with `solution-optimality-evaluation` (alternative-design comparison), `profiling` (measurement), `concurrency-control` (synchronization design), `cache-design` (when caching is in scope), and the matching `<lang>-professional-usage` capability for runtime-specific tooling.

### Hot-Path Classification Rules

```
Class | Criteria                                                  | Discipline
------|-----------------------------------------------------------|----------------------------------
H1    | On request path AND CPU profile share ≥ 5%                | Allocation budget mandatory,
      |                                                           | benchmark in CI, profile attached
H2    | On request path AND ≥ 1% of total CPU                     | Benchmark in CI, allocation tracked
H3    | Background / batch / startup                              | Standard care; allocations OK
C     | Cold / rare / one-shot                                    | Simplicity > perf
```

### Pool / Connection / Worker Sizing (Little's Law)

```
In-flight requests   = throughput (req/s) × latency (s)
DB connection pool   = peak QPS × avg query latency × safety factor (1.5-2)
HTTP client pool     = peak outbound RPS × p99 upstream latency × safety factor
Worker pool (CPU)    = num_cores (CPU-bound) ; or measured (mixed)
Worker pool (IO)     = bounded; never unbounded; backpressure required
```

# Risk Escalation Rules

- Escalate to `reliability-observability-gate` when production SLO (latency p99 / p99.9, error rate, saturation) may be breached.
- Escalate to `low-level-systems-extension` for unsafe / FFI / native / SIMD / lock-free / memory-ordering changes.
- Escalate to `quality-test-gate` when race / sanitizer / stress / load / fuzz evidence is required but missing.
- Escalate to `concurrency-control` for synchronization primitive design or change.
- Escalate to `solution-optimality-evaluation` when an algorithmic alternative exists and tradeoff requires explicit comparison.
- Escalate to `cache-design` when the change adds a cache or modifies caching behavior.

# Reference Loading Policy

- Load `references/checklist.md` when a change touches hot paths, allocation shape, garbage collection, async/event-loop behavior, thread or worker pools, lock scope, backpressure, cancellation, unsafe/FFI boundaries, native resources, reusable client/pool lifecycle, or any unbounded growth surface.
- Do not load the checklist for cold-path readability changes unless the author makes a performance or safety claim.
- When the matching `<lang>-professional-usage` capability is selected, load it for runtime-specific tool commands first, then load this checklist for the performance/safety evidence contract and measurement requirements.

# Critical Details

- **Design pattern performance risk is runtime risk.** Pattern-induced allocation, indirection, hidden IO, lifecycle state, lock contention, task fan-out, and pool/client creation must be assessed before accepting the structure. Factories and builders can create expensive objects per request; decorators and proxies can hide IO or order-dependent side effects; repositories and adapters can hide network/storage IO; observers and workers can create unbounded fan-out; commands require idempotency, retry, cancellation, and backpressure; singletons/global state require synchronization, test reset, and shutdown cleanup.
- **Allocation cost is not zero in any runtime.** Even Go and Rust pay for allocation in cache pressure, GC scan time (Go), or sync allocator overhead. Hot-path allocations should be measured and budgeted; pooling (sync.Pool, object pool, arena) considered only after profile justifies.
- **GC pause SLO mapping**: if p99.9 latency budget is 50 ms, GC pause budget is typically < 10 ms. JVM G1 default may exceed; ZGC / Shenandoah / Go's concurrent GC fit better. Hard real-time / sub-ms requires no-GC (Rust / C++).
- **Event-loop block detection**: instrument event-loop lag (`@nodejs/perf_hooks` `monitorEventLoopDelay`, Python `asyncio.get_event_loop().slow_callback_duration`, JVM reactor `Schedulers.metrics()`). Lag > 10 ms p99 indicates blocking work on the loop.
- **Lock scope**: hold a lock only over the smallest critical section. A lock held across an IO call serializes the whole service. Read-write locks vs mutex chosen by measured contention ratio.
- **Backpressure design**: bounded channels / queues / executor pools. Unbounded means "OOM under load". Use semaphore / token bucket / rate limiter at every fan-in point.
- **Cancellation propagation**: pass `context.Context` (Go), `AbortSignal` (TS/JS), `CancellationToken` (.NET), `CancelToken` (tokio), `asyncio.CancelledError`-aware paths (Python) through every async boundary. Code that ignores cancellation leaks resources under timeout.
- **FFI invariants**: document who owns memory, lifetime, alignment, thread-safety, panic/exception boundary, error-code convention. UB on the FFI boundary corrupts the host runtime silently.
- **Microbenchmarks vs system benchmarks**: a microbench shows function cost; a system bench shows tail-latency under load. Optimize against the system bench; use microbench only to validate a specific hypothesis.
- **GC-friendly patterns**: prefer flat structs over linked structures (cache locality), pre-sized slices/lists, pooled buffers for IO, escape-analysis hints (Go: avoid pointer escape; Java: avoid boxing).
- **Collection growth budgets**: every collection that can grow from input, database result size, message backlog, retry state, recursion, or fan-out must state its maximum cardinality and memory budget. Prefer streaming, pagination, chunking, bounded LRU/TTL caches, and early rejection over "load all then process". Validate `count * element_size` overflow and reject payloads that exceed the budget before allocation.
- **Preallocation is not permission to trust input.** Pre-size collections only from trusted or capped counts. A hostile `Content-Length`, declared array length, CSV row count, GraphQL page size, or API `limit` must be clamped before allocation. Huge preallocation is a denial-of-service vector even when the subsequent loop is correct.
- **Connection/client reuse**: construct reusable clients once per intended lifecycle and inject them. Per-request `new HttpClient`, per-call DB engine creation, per-message SDK construction, or per-query connection open/close is a defect unless the runtime explicitly requires it and cost is measured. Reused clients still require bounded pools, keep-alive, idle/lifetime eviction, DNS/credential refresh behavior, and graceful shutdown.
- **Response/body cleanup**: every successful or failed outbound call must release network resources in the runtime's idiom: close response bodies, consume/drain only when required for connection reuse, cancel inflight requests on timeout, and close streams/readers/writers on all paths.
- **Fan-out and batch ceilings**: `Promise.all`, goroutine/task spawning, thread creation, queue publishing, SQL `IN` clauses, and bulk writes must have a concurrency or batch-size ceiling. Large work is chunked with checkpoints, partial-failure handling, and cancellation.
- **Long-lived handles are leak surfaces.** Timers, intervals, subscriptions, watchers, file descriptors, cursors, prepared statements, transactions, locks, and temporary files require explicit ownership and cleanup on success, failure, cancellation, and shutdown.

## Pattern Performance Impact

| Pattern | Runtime impact to prove |
| --- | --- |
| Singleton | global mutable state, lock contention, test reset, shutdown cleanup |
| Object Pool | allocation profile required, contention, stale object reset, leak detection |
| Observer/PubSub | subscription lifecycle, bounded fan-out, backpressure, error isolation |
| Decorator/Proxy | hidden IO, order dependency, latency budget, resource cleanup |
| Factory/Builder | construction cost, per-request client creation risk, object graph churn |
| Strategy/Command | allocation and dispatch overhead; idempotency/retry for commands |
| Repository/Adapter | network/storage IO visibility, timeout, retry, pool, cleanup |
| Pipeline/Worker Pool | queue size, pool sizing, backpressure, cancellation, partial failure |

# Failure Modes

- **Event-loop block** — Symptom: Node.js / Python asyncio service stalls; p99 latency cliff at modest RPS. Cause: blocking call on event loop. Detection: event-loop lag metric. Impact: head-of-line blocking, customer-visible latency.
- **GC pause SLO breach** — Symptom: p99.9 latency spikes correlated with GC. Cause: high allocation rate + GC algorithm mismatch. Detection: GC log + allocation-rate metric. Impact: SLO breach.
- **Goroutine / task / thread / fd leak** — Symptom: memory / fd count grows monotonically. Cause: missing cancellation / context propagation. Detection: pprof goroutine profile, fd-count metric. Impact: OOM, restart loop.
- **Unbounded queue OOM** — Symptom: OOM under load spike. Cause: unbounded channel / executor / retry queue. Detection: queue-depth metric, load test. Impact: cascading failure.
- **Unbounded collection OOM** — Symptom: memory grows with request size, result-set size, or message backlog. Cause: list/map/buffer accumulates all inputs before processing. Detection: allocation profile, heap growth by payload size, fuzz/load test with large `limit` or payload. Impact: denial of service, GC collapse, pod eviction.
- **Per-operation client construction** — Symptom: high latency, socket exhaustion, DNS churn, TLS handshakes per call. Cause: HTTP/DB/SDK client created inside request loop. Detection: connection churn metrics, fd count, upstream SYN/TLS volume. Impact: pool starvation, provider throttling, cascading latency.
- **Response body leak** — Symptom: idle connections never return to pool; fd count climbs under error rate. Cause: response body/stream not closed on non-2xx, exception, or cancellation path. Detection: pool wait metric, fd-count metric, leak test. Impact: connection exhaustion and request failures.
- **Lock held across IO** — Symptom: throughput cliff under modest concurrency; CPU low, latency high. Cause: lock scope includes IO call. Detection: lock contention profile (`pprof mutex`, JFR LockContention). Impact: artificial bottleneck.
- **FFI UB / unsafe invariant violation** — Symptom: heisenbug, sporadic corruption, ASan/MSan report. Cause: undocumented invariant violated. Detection: sanitizer in CI, peer review. Impact: silent data corruption, security exposure.
- **Cold-path "optimization"** — Symptom: complex code in rare path; profile shows < 0.1% impact. Cause: optimization without profile. Detection: profile review pre-merge. Impact: complexity tax, no perf gain.
- **Microbench-only validation** — Symptom: 10× faster in microbench, no change in system p99. Cause: microbench did not reflect real shape. Detection: system-level benchmark. Impact: wasted effort, false claim.
- **Pool sized by guess** — Symptom: connection-pool exhaustion or massive idle pool. Cause: pool size set without Little's-Law calculation. Detection: pool-wait metric, idle-conn metric. Impact: latency spike or wasted memory.

# Evidence Contract

Language performance/safety review is complete only when the output includes:

- **Runtime risk**: allocation, GC, ownership, event-loop blocking, thread-pool saturation, lock contention, unsafe memory boundary, resource leak, or unbounded growth surface identified.
- **Hot-path evidence**: profile, trace, load/stress result, or explicit statement that no hot-path claim is verified.
- **Measurement contract**: before/after metric, benchmark command, race/sanitizer command, event-loop lag metric, pool metric, or not-verified disclosure.
- **Bounds and lifecycle**: queue, fan-out, batch, collection, retry, client/pool, handle, subscription, timer, or file/resource limit and cleanup path.
- **Concurrency/safety proof**: cancellation/backpressure behavior, race/sanitizer coverage, lock-scope evidence, unsafe/FFI invariant, or reviewer requirement.
- **What evidence proves**: the inspected runtime risk is bounded, measured, or explicitly rejected for the covered path.
- **What evidence does not prove**: production tail latency, all scheduler interleavings, all payload sizes, or unrelated hot paths.
- **Residual risk**: remaining measurement gap, owner, and threshold that reopens the review.

# Output Contract

Return a **Performance & Safety Assessment** containing:
- **Runtime in scope** (language, version, GC/scheduler/allocator)
- **Hot-path classification** (H1 / H2 / H3 / C) with profile evidence (top-N CPU functions, allocation top-N)
- **Allocation budget** for H1 / H2 paths (B/req, allocs/req, target)
- **GC pause analysis** (algorithm, observed pause distribution vs SLO)
- **Concurrency / async risks**: blocking points, lock scope, cancellation propagation, backpressure design
- **Pattern Performance Impact**: pattern-induced allocation, indirection, hidden IO, object creation, lock contention, client/pool lifecycle, fan-out, backpressure, cancellation, and cleanup obligations
- **Pool sizing** with Little's-Law calculation (DB conn, HTTP client, worker pool)
- **Growth-surface audit**: collections, buffers, batches, caches, pagination windows, retry queues, and fan-out points with explicit item/byte limits
- **Client/pool lifecycle**: where reusable clients/pools are constructed, how they are reused, closed, refreshed, and observed
- **Unsafe / FFI boundaries**: invariants documented, reviewer names, sanitizer coverage
- **Required measurements**: profile commands, benchmark commands, sanitizer/race-detector commands
- **Mitigation plan** per identified risk with owner and target metric
- **Residual risk** with explicit acceptance, owner, threshold trigger for re-evaluation

# Quality Gate

1. Hot-path classification has profile evidence (not author intuition).
2. Allocation budget set and measured for H1 / H2 paths; before/after attached for changes.
3. GC pause distribution measured against p99.9 latency SLO; tuning or algorithm change cited if breached.
4. Async / event-loop code has no blocking call on the loop; blocking work is on dedicated executor; event-loop lag metric present.
5. Pool sizes calculated via Little's Law; bounded queues / executors / retry loops everywhere.
6. Cancellation token / context / signal propagated through every async boundary.
7. Design patterns on runtime-sensitive paths declare pattern performance risk, pattern-induced allocation/indirection, hidden IO, object pool evidence, observer cleanup, singleton/global-state synchronization, and command/worker backpressure or idempotency obligations.
8. Proxy, decorator, repository, and adapter do not hide network/storage IO, timeout, retry, or cleanup from the owning structure decision.
9. Unsafe / FFI changes have written invariant doc + ≥ 2 reviewers + sanitizer CI coverage.
10. Concurrency change has race-detector / sanitizer / stress-test evidence in CI.
11. Every optimization claim has before/after numbers from a system-level benchmark, not microbench-only.
12. Collections, buffers, caches, pages, batches, and fan-out lists have explicit count/byte ceilings and reject or stream oversized inputs.
13. Reusable clients/pools are not constructed per operation; response bodies, streams, timers, subscriptions, cursors, and file handles are cleaned up on all paths.

# Used By

reliability-observability-gate, backend-change-builder, frontend-change-builder, low-level-systems-extension, solution-optimality-evaluation

# Handoff

- **`profiling`** for measurement execution and profile artifact storage.
- **`concurrency-control`** for synchronization primitive design and stress design.
- **`reliability-observability-gate`** for production SLO risk and release-time evidence.
- **`cache-design`** when caching is the proposed mitigation.
- **Matching `<lang>-professional-usage` capability** for tool pins (profiler, sanitizer, race detector versions and commands).
- **`low-level-systems-extension`** for unsafe / FFI / SIMD / lock-free design.

# Completion Criteria

Assessment is complete when: hot-path classification is profile-backed; allocation, GC pause, lock scope, async-block, backpressure, cancellation, and pool sizing are each answered with measurement or explicit acceptance; unsafe/FFI boundaries are documented and sanitizer-covered; concurrency changes have race-detector evidence; and every optimization claim has system-level before/after numbers. "Should be fast" is not an acceptance condition.
