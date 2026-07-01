---
name: language-performance-safety
description: Use when evaluating language-specific performance and safety across allocation, garbage collection, memory ownership, concurrency, async behavior, FFI, unsafe/native boundaries, blocking work, hot paths, pool/client lifecycle, backpressure, cancellation, cleanup, and bounded growth.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "87"
changeforge_version: 0.1.0
---

# Mission

Evaluate language- and runtime-specific performance and safety against measured behavior, not runtime reputation. The capability owns allocation shape, GC pressure, scheduler/event-loop interaction, async cancellation, blocking work, lock scope, unsafe/FFI boundaries, hot-path constraints, backpressure, client/pool lifecycle, resource cleanup, and growth bounds. It connects language choice, repository graph, runtime measurements, validation evidence, and release risk without turning performance advice into a generic tuning guide.

# When To Use

Use when a change touches or reviews:

- Hot paths, request paths, render paths, workers, batch jobs, parsers, serializers, or high-throughput loops.
- Allocation, GC, memory ownership, object pooling, cache locality, buffer growth, or payload/result-set size.
- Async runtimes, event loops, goroutines, coroutines, thread pools, worker pools, cancellation, backpressure, or fan-out.
- Native, unsafe, FFI, SIMD, lock-free, atomics, memory-ordering, file descriptor, socket, stream, cursor, timer, subscription, or handle lifecycle.
- Reusable HTTP/DB/SDK/queue/cache clients, connection pools, per-operation construction, response/body cleanup, timeout, retry, or shutdown behavior.
- Performance claims, optimization PRs, runtime safety claims, or design patterns whose allocation, IO, locking, lifecycle, or fan-out cost is unclear.

# Do Not Use When

- The path is cold, one-shot, or readability-driven and no performance, concurrency, memory, safety, resource, or runtime claim is made.
- A profile already proves the bottleneck is purely algorithmic, data-store, cache, or network architecture and another capability owns the substantive decision.
- The proposed action is micro-optimization by intuition, language reputation, benchmark theater, or complexity that does not map to a measured risk.

# Stage Fit

- **read / plan:** inspect runtime, language version, caller path, profile or absence of profile, resource owners, input bounds, client/pool construction, cancellation path, and existing tests.
- **coding / refactoring:** keep structure changes performance-aware by routing hot path, hidden IO, lock, pool, fan-out, cleanup, async, and unsafe concerns before accepting the design.
- **code-review:** reject unmeasured optimization claims, unbounded growth surfaces, per-operation client construction, event-loop blocking, unsafe invariants without review, and microbench-only approval.
- **testing / validation:** require profile, benchmark, race detector, sanitizer, stress, load, event-loop lag, pool metric, leak check, or explicit not-verified disclosure.
- **release / handoff:** state what evidence proves, what it does not prove, residual runtime risk, production threshold that reopens review, and the next gate.

# Mode Matrix

| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities | Skip guidance |
| --- | --- | --- | --- | --- | --- |
| Hot-path measurement | Request/render/worker path, CPU share, allocation regression, p95/p99 claim | Profile-backed classification, allocation budget, before/after metric | CPU/heap profile, benchmark/load command, SLO or not-verified limit | `profiling`, `solution-optimality-evaluation` | Skip micro-optimization when no profile points at the path |
| Async/concurrency safety | event loop, coroutine, goroutine, worker pool, lock, race, cancellation | Prevent blocking, leaks, deadlocks, pool starvation, missing cancellation | lag metric, lock/queue bound, race/stress command, cancellation test | `concurrency-control`, `quality-test-gate` | Skip broad redesign when a bounded executor or lock-scope fix suffices |
| Growth/resource lifecycle | collection, buffer, page, batch, retry queue, client, pool, stream, fd | Bound memory and lifecycle ownership at the correct graph node | item/byte cap, construction scope, close/shutdown path, leak/pool metric | `dependency-wiring-lifecycle`, `reliability-observability-gate` | Skip object pools unless profile justifies reuse over allocation |
| Unsafe/native boundary | FFI, unsafe, native extension, atomics, lock-free, ABI, SIMD | Prove ownership, lifetime, panic/exception boundary, thread safety | invariant contract, sanitizer/race command, reviewer requirement | `low-level-systems-extension`, `security-privacy-gate` | Skip native optimization when managed/runtime path meets budget |
| Pattern/runtime review | factory, proxy, repository, observer, singleton, worker, decorator hides IO or lifecycle | Expose hidden allocation, IO, locks, fan-out, retries, cleanup, backpressure | pattern impact map, side-effect boundary, timeout/retry/cleanup proof | `implementation-structure-design`, `design-pattern-selection` | Skip new pattern when direct code keeps lifecycle visible |

# Non-Negotiable Rules

1. **Profile before optimizing:** every optimization claim names the measured bottleneck, metric, command, and before/after target or is marked not verified.
2. **Hot-path classification is evidence-backed:** author intuition is insufficient; use profile, trace, load/stress result, call frequency, or explicit no-hot-path finding.
3. **H1/H2 paths need allocation budgets:** track bytes/op, allocs/op, allocation rate, retained heap, and GC pause distribution against latency SLO.
4. **Async runtimes do not block:** CPU-heavy or synchronous IO work leaves the event loop/reactor; bounded executors, timeouts, cancellation, and backpressure are required.
5. **Growth surfaces are bounded before allocation:** collections, pages, buffers, batches, caches, queues, fan-out lists, and retry accumulators have count and/or byte ceilings.
6. **Reusable clients and pools have lifecycle owners:** construction scope, keep-alive, idle/lifetime limits, DNS/credential refresh, shutdown, and metrics are stated.
7. **Resource acquisition has symmetric cleanup:** response bodies, streams, cursors, timers, subscriptions, locks, temp files, and file descriptors close on success, error, timeout, cancellation, and shutdown.
8. **Unsafe/FFI/native changes need a safety contract:** ownership, lifetime, alignment, panic/exception boundary, thread safety, error convention, sanitizer coverage, and qualified review.
9. **Concurrency changes need race/stress evidence:** locks, atomics, shared state, worker pools, cancellation, queueing, and backpressure cannot close on reasoning alone.
10. **Safety and readability outrank unmeasured speed:** faster code is accepted only with numbers and an explicit residual risk boundary.

# Industry Benchmarks

Use Google SRE latency budgets, USE/RED methods, Amdahl's Law, Universal Scalability Law, Little's Law, pprof/JFR/async-profiler/py-spy/scalene/memray/perf/eBPF/clinic.js/tokio-console, ASan/UBSan/TSan/MSan/LSan, race detectors, language memory models, GC tuning guides, and system-level benchmarks as calibration points.

# Selection Rules

Select this capability when runtime performance or safety depends on language/runtime behavior. Pair with `profiling` for measured bottlenecks, `solution-optimality-evaluation` for alternatives, `concurrency-control` for synchronization and cancellation design, `dependency-wiring-lifecycle` for client/pool ownership, `cache-design` when cache behavior is the mitigation, `quality-test-gate` for race/sanitizer/stress/load evidence, and the matching `<lang>-professional-usage` capability for runtime-specific tools.

Skip it only when the inspected path has no runtime sensitivity and no performance/safety claim. If skipped during implementation or review, state the reason and the evidence boundary.

# Risk Escalation Rules

- Escalate to `reliability-observability-gate` when p95/p99/p99.9 latency, saturation, error budget, capacity, or production SLO can be affected.
- Escalate to `low-level-systems-extension` for unsafe, FFI, native, SIMD, ABI, lock-free, memory-ordering, kernel, driver, or descriptor behavior.
- Escalate to `quality-test-gate` when race detector, sanitizer, stress, load, benchmark, leak, or event-loop lag evidence is required but missing.
- Escalate to `concurrency-control` when lock order, shared state, worker pool, cancellation, backpressure, deadlock, or race behavior is the primary design question.
- Escalate to `dependency-wiring-lifecycle` when client, pool, timer, subscription, watcher, stream, cursor, or shutdown ownership is unclear.
- Escalate to `security-privacy-gate` when unsafe/native parsing, untrusted payload size, resource exhaustion, prompt/tool output, secret-bearing logs, or denial-of-service risk crosses a trust boundary.
- Escalate to `delivery-release-gate` when performance or safety evidence is required before rollout, rollback, canary, capacity change, or runtime profile release.

# Proactive Professional Triggers

- **Signal:** A change claims lower latency, higher throughput, fewer allocations, faster parsing, or "hot path" status without profile or benchmark evidence.
  **Hidden risk:** wrong optimization may add complexity to a cold path or hide the real bottleneck in GC, locks, IO, pool wait, or memory.
  **Required professional action:** classify the path and require a before/after measurement or not-verified disclosure before approval.
  **Route to:** `profiling`, `solution-optimality-evaluation`, `quality-test-gate`.
  **Evidence required:** profile/benchmark command, top bottleneck, baseline metric, target metric, and residual measurement gap.
- **Signal:** CPU-bound work, sync IO, parser, compression, crypto, file read, DB call, or SDK call runs inside an event loop, coroutine, reactive stream, or async handler.
  **Hidden risk:** head-of-line blocking and cancellation leaks pass unit tests but collapse p99 latency under load.
  **Required professional action:** move blocking work to a bounded executor or prove non-blocking behavior with lag and cancellation evidence.
  **Route to:** `concurrency-control`, `reliability-observability-gate`, `quality-test-gate`.
  **Evidence required:** event-loop lag metric, executor/worker bound, timeout/cancellation test, and load or stress output.
- **Signal:** Collection, buffer, cache, page, batch, retry state, queue, fan-out, SQL `IN` list, or `Promise.all` size is driven by input or result count.
  **Hidden risk:** hidden memory loss, GC collapse, fd leak, pool starvation, or downstream saturation is invisible in small fixtures.
  **Required professional action:** require count/byte caps before allocation, verify stream/chunk behavior, and define reject/partial-failure behavior.
  **Route to:** `algorithm-data-structure-selection`, `concurrency-control`, `quality-test-gate`.
  **Evidence required:** max item/byte budget, clamp point, chunk/fan-out ceiling, oversized-input test, and what remains unmeasured.
- **Signal:** HTTP, DB, Redis, Kafka, SDK, telemetry client, connection pool, response body, cursor, stream, timer, subscription, watcher, or temp file lifecycle changes.
  **Hidden risk:** per-operation construction, leaked handles, socket exhaustion, DNS churn, stale credentials, or missing shutdown creates production-only failure.
  **Required professional action:** verify lifecycle owner, reuse scope, close path, refresh behavior, and pool/handle observability before approval.
  **Route to:** `dependency-wiring-lifecycle`, `integration-change-builder`, `reliability-observability-gate`.
  **Evidence required:** construction site, ownership scope, cleanup path, pool/handle metric, leak or cancellation test.
- **Signal:** unsafe, FFI, native extension, lock-free, atomic, memory-ordering, SIMD, or concurrency primitive change is proposed without invariant and sanitizer/race evidence.
  **Hidden risk:** undefined behavior, data race, lifetime bug, or host-runtime corruption can pass normal tests.
  **Required professional action:** write the safety contract, require qualified review, and run sanitizer/race/stress validation or block release.
  **Route to:** `low-level-systems-extension`, `concurrency-control`, `security-privacy-gate`, `quality-test-gate`.
  **Evidence required:** invariant contract, reviewer requirement, sanitizer/race command, stress result, and unresolved safety risk.

# Hot-Path Classification

| Class | Criteria | Discipline |
| --- | --- | --- |
| H1 | Request path and CPU profile share >= 5%, or SLO-critical path with measured allocation/pool pressure | Allocation budget, system benchmark, profile artifact, and CI or release validation |
| H2 | Request path and >= 1% total CPU, recurring worker path, or measured allocation regression | Benchmark/load check and allocation tracking |
| H3 | Background, batch, startup, or admin path with bounded input and no SLO claim | Standard care, bounded resources, no unmeasured complexity |
| C | Cold, rare, one-shot, or readability-driven path | Prefer simplicity; reject optimization unless evidence changes classification |

# Critical Details

- **Little's Law:** in-flight work = throughput x latency; DB/HTTP/worker pool guesses are rejected when peak rate and latency are knowable.
- **GC pause mapping:** GC pause budget must fit the latency budget; sub-ms or hard real-time paths may require no-GC or native/runtime alternatives.
- **Event-loop lag:** Node, asyncio, reactor, and tokio paths need lag/cancellation evidence when blocking risk is plausible.
- **Lock scope:** never hold a lock across storage, network, user, file, or external IO; measure contention before changing primitives.
- **Backpressure:** use bounded channels, semaphores, token buckets, rate limits, batch ceilings, and reject/defer behavior at every fan-in/fan-out point.
- **Preallocation:** pre-size only from trusted or clamped counts; hostile length/page/limit headers are denial-of-service inputs.
- **Client/pool reuse:** construct reusable clients at composition roots or scoped factories, not inside request/message/query loops.
- **Response cleanup:** close or cancel response bodies, streams, cursors, readers, writers, timers, watchers, and temp files on all paths.
- **Pattern cost:** factories/builders may allocate per request; proxies/decorators can hide IO; observers can leak subscriptions; singletons need synchronization, reset, and shutdown.
- **Microbench limits:** microbenchmarks validate a narrow hypothesis; system benchmarks decide user-visible latency, saturation, and throughput.

# Reference Loading Policy

The body carries routing, decision, evidence, and output rules. Load [references/checklist.md](references/checklist.md) when a change touches hot paths, allocation, GC, async/event-loop behavior, pools, locks, backpressure, cancellation, unsafe/FFI boundaries, native resources, reusable clients, cleanup, unbounded growth, or when drafting the concrete assessment. Load [references/evidence-patterns.md](references/evidence-patterns.md) only when closure depends on current repository graph, project memory, execution trajectory, measurement freshness, source-to-validation mapping, tool permission boundaries, or residual-risk wording. Load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) only when choosing profiling/benchmark evidence, calibrating runtime safety patterns, comparing allocation/GC/async/pool/fan-out tradeoffs, or accepting a performance/safety deviation. Do not load deep references for cold-path readability edits with no performance/safety claim.

# Failure Modes

- **Event-loop block:** CPU or sync IO stalls all async work and creates a p99 latency cliff.
- **GC pause SLO breach:** high allocation rate or retained heap creates tail spikes despite average latency passing.
- **Task/thread/fd leak:** missing cancellation or cleanup grows handles until OOM, fd exhaustion, or restart loop.
- **Unbounded queue or collection:** input/result/fan-out growth exhausts memory or downstream capacity.
- **Per-operation client construction:** socket churn, TLS/DNS overhead, pool starvation, and provider throttling appear under load.
- **Response/stream leak:** idle connections never return to pool on error, timeout, or cancellation.
- **Lock held across IO:** service serializes under moderate concurrency while CPU remains low.
- **Unsafe invariant violation:** UB, race, or lifetime bug corrupts host runtime outside normal test visibility.
- **Microbench-only approval:** local function speedup does not improve system p99 or saturation.
- **Pool sized by guess:** undersized pools cause wait spikes; oversized pools waste memory and amplify downstream load.

# Evidence Contract

Close only when these answers are concrete:

- **Runtime risk:** allocation, GC, ownership, event-loop blocking, thread/pool saturation, lock contention, unsafe boundary, leak, or growth surface inspected.
- **Boundaries inspected:** runtime/language version, caller graph, input size, concurrency path, resource owners, client/pool lifecycle, tests, generated artifacts, and skipped areas.
- **Measurement contract:** profile, trace, benchmark, race/sanitizer, stress/load, event-loop lag, pool metric, leak check, or explicit not-verified reason.
- **Bounds and lifecycle:** queue, fan-out, batch, collection, retry, client, pool, handle, subscription, timer, stream, cursor, file, and cleanup limits.
- **What evidence proves:** the covered path is measured, bounded, safe, or intentionally not optimized.
- **What evidence does not prove:** production tail latency, every scheduler interleaving, every payload size, native ABI behavior, or unrelated hot paths.
- **Residual risk:** remaining gap, owner, threshold that reopens review, and next gate.
- **Validation evidence:** command, working directory, exit code, report or artifact, freshness after final edit, and residual risk owner.

# Output Contract

Return a **Performance & Safety Assessment** with:

- **Runtime in scope:** language, version, GC/scheduler/allocator, async runtime, and native/unsafe surface if any.
- **Mode selected:** hot-path measurement, async/concurrency safety, growth/resource lifecycle, unsafe/native boundary, or pattern/runtime review.
- **Hot-path classification:** H1/H2/H3/C with profile or explicit no-profile evidence.
- **Allocation and GC:** bytes/op, allocs/op, retained heap, GC pause distribution, target budget, or not-verified limit.
- **Concurrency / async risks:** blocking points, lock scope, worker/pool bounds, cancellation, backpressure, and race/stress evidence.
- **Growth and lifecycle audit:** input caps, item/byte ceilings, client/pool construction, cleanup path, leak checks, shutdown behavior.
- **Unsafe / FFI boundary:** invariants, ownership/lifetime, panic/exception/error boundary, thread safety, reviewers, sanitizer coverage.
- **Required measurements:** exact commands or artifacts needed before approval and what each proves.
- **Decision:** approved, blocked, not verified, release-gated, or handoff required.
- **Residual risk and next gate:** accepted gap, owner, threshold, and routed skill/capability.

# Quality Gate

1. Hot-path classification has profile, trace, load/stress, or explicit not-verified evidence.
2. H1/H2 paths have allocation budget and before/after metric for performance-changing edits.
3. GC pause distribution is compared to latency SLO when GC can affect the path.
4. Async/event-loop code avoids blocking or has bounded executor, lag metric, timeout, and cancellation evidence.
5. Queues, executors, retry loops, fan-out, batches, collections, buffers, caches, and pages are bounded by count and/or bytes.
6. Client/pool construction scope, keep-alive, idle/lifetime, refresh, shutdown, and observability are defined.
7. Response bodies, streams, cursors, timers, subscriptions, locks, temp files, and file descriptors clean up on all paths.
8. Unsafe/FFI/native changes have safety contract, qualified review, and sanitizer/race coverage.
9. Concurrency changes have race detector, sanitizer, stress, or explicitly accepted residual risk.
10. Pattern-based structure exposes allocation, hidden IO, lock, lifecycle, fan-out, retry, backpressure, cancellation, and cleanup impact.
11. Every optimization claim has system-level before/after numbers or is rejected as unverified.
12. Final handoff states what evidence proves, what it does not prove, residual risk, rollback/mitigation, and next gate.

# Used By

Used by `reliability-observability-gate`, `backend-change-builder`, `frontend-change-builder`, `low-level-systems-extension`, `solution-optimality-evaluation`, `implementation-structure-design`, `design-pattern-selection`, `ai-code-review-refactor`, and `quality-test-gate`.

# Handoff

- `profiling` for profile/trace/benchmark capture; matching `<lang>-professional-usage` for runtime-specific tool commands.
- `concurrency-control` for locks, races, scheduling, cancellation, backpressure, and worker coordination.
- `dependency-wiring-lifecycle`, `reliability-observability-gate`, and `cache-design` for client/pool ownership, production SLO/capacity, and cache mitigation.
- `algorithm-data-structure-selection` and `low-level-systems-extension` for complexity/streaming/input-size design and unsafe, FFI, SIMD, ABI, lock-free, or memory-ordering design.

# Completion Criteria

Assessment is complete when runtime risk is classified, hot-path status is evidence-backed or explicitly unverified, allocation/GC/async/concurrency/growth/lifecycle/unsafe concerns have measurement or accepted residual risk, resource bounds and cleanup are stated, optimization claims have system-level numbers, and the handoff preserves evidence limits, rollback/mitigation path, residual risk, and next gate.
