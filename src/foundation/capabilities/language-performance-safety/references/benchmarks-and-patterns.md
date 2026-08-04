# Language Performance Benchmarks And Patterns

Use this reference when `language-performance-safety` needs deeper tool selection, runtime calibration, performance/safety pattern review, or deviation records. Keep `SKILL.md` focused on routing, evidence, output, and gates.

## Measurement Selection Matrix

| Risk signal | Preferred evidence | Avoid |
| --- | --- | --- |
| CPU hot path or parser/serializer cost | CPU profile, trace, flame graph, representative benchmark/load run, and before/after metric | Microbenchmark-only approval when caller frequency is unknown |
| Allocation or GC pressure | Allocation profile, heap diff, bytes/op, allocs/op, retained heap, GC log, RSS soak trend | GC flag tuning without allocation or retention reduction |
| Event-loop or scheduler blocking | Event-loop lag, async profiler, thread dump, bounded executor proof, cancellation test, and load/stress result | Moving work blindly between threads without queue and timeout bounds |
| Lock, worker, pool, or queue saturation | Contention profile, pool wait metric, queue depth, Little's Law sizing, saturation alert, and rejection/defer behavior | Pool size guessed from CPU count or local developer data |
| Input growth, fan-out, or buffer expansion | Count/byte ceiling, streaming/chunking/page rule, oversized-input test, backpressure metric, and downstream capacity | Preallocation from untrusted length/page/count fields |
| Unsafe, FFI, native, atomics, or lock-free path | Safety invariant, language memory-model check, sanitizer/race/stress output, ABI/platform matrix, and qualified review | Normal unit tests as proof of memory safety |
| Client, handle, stream, cursor, or timer lifecycle | Construction scope, reuse rule, close/shutdown path, idle/lifetime settings, leak check, and pool/handle metric | Per-operation construction hidden behind factories or repositories |

## Calibration Anchors

- **Amdahl's Law:** Prioritize the fraction whose measured contribution can materially move the named end-to-end latency or throughput objective; treat correctness, safety, cost, memory, and tail-risk work as separate justified objectives.
- **Universal Scalability Law:** model contention and coherency when concurrency gains flatten or reverse.
- **Little's Law:** align in-flight work, queue depth, and pool size with throughput and service time.
- **USE and RED methods:** separate utilization, saturation, errors, rate, and duration before changing code.
- **Latency percentiles:** compare p95/p99/p99.9 and GC pause distributions to the user-visible budget.
- **Language memory models:** treat atomics, locks, unsafe pointers, FFI ownership, and data races as safety contracts, not style choices.
- **Representative workload:** match data size, concurrency, dependency latency, runtime version, hardware/container limits, and warmup behavior before accepting results.

## Runtime Safety Patterns

- Offload CPU-bound and synchronous IO work from event loops to bounded executors with cancellation and queue limits.
- For each queue, channel, fan-out list, retry accumulator, batch, buffer, cache, or page, determine whether untrusted, external, or workload-dependent input drives it. When it does, define a count/byte ceiling before allocation or prove the source is already bounded.
- Construct reusable clients, pools, timers, subscriptions, and watchers at the composition root or a scoped factory with explicit shutdown.
- Close response bodies, streams, cursors, readers, temp files, timers, and descriptors on success, error, timeout, cancellation, and shutdown paths.
- Avoid holding an in-process lock across potentially blocking or unbounded I/O. If correctness requires serialization spanning I/O, use a boundary-appropriate transaction, lease, or fencing protocol, or document bounded wait, cancellation, failure cleanup, and contention evidence.
- Prefer streaming, chunking, pagination, spill-to-disk, or rejection over load-all processing for untrusted or large inputs.
- Use object pools only when profiling proves allocation cost and lifecycle reset is correct; otherwise prefer simple ownership and GC.
- Require invariant review plus sanitizer/race/stress evidence for unsafe/native/FFI changes before release approval.

## Deviation Record

Use this compact record when accepting an unmeasured optimization, unsupported runtime tradeoff, incomplete profiler run, or residual performance/safety risk:

```markdown
Language Performance Deviation
- Rule:
- Reason:
- Scope:
- Owner:
- Expiration or reopen trigger:
- Evidence that bounds the exception:
- Risk that remains unproved:
```
