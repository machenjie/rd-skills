# Language Performance Evidence Patterns

Use this reference when closure depends on current repository inspection, prior task evidence, observable action sequence, validation freshness, benchmark scope, tool permission boundaries, or production-scale evidence limits. Keep it as an evidence map, not a tuning guide.

## Runtime Claim-To-Evidence Map

| Runtime claim | Minimum evidence | What it proves | What it does not prove |
| --- | --- | --- | --- |
| Path is hot or SLO-critical | Caller graph, traffic or job frequency, profile/trace/load artifact, metric name, baseline, and final source version | The inspected path matters for the named workload | Other traffic mixes, hardware, tenants, or future callers are covered |
| Allocation or GC risk is controlled | Allocation profile, heap diff, bytes/op, allocs/op, retained heap, GC pause distribution, and latency budget comparison | The inspected path fits the stated allocation/GC budget | Every payload size, long soak, or production heap state is safe |
| Async/event-loop path is non-blocking | Blocking-point scan, event-loop lag, bounded executor or offload proof, timeout, cancellation test, and stress/load output | The inspected async path avoids the named blocking risk | Every scheduler interleaving or dependency stall is covered |
| Growth surface is bounded | Input owner, max count/bytes, clamp point, stream/chunk/page rule, oversized-input test, and reject/defer behavior | The inspected allocation/fan-out cannot grow past the declared ceiling | Production distribution shifts or new producers are safe |
| Client, pool, or handle lifecycle is safe | Construction site, ownership scope, reuse rule, close/shutdown path, idle/lifetime settings, leak/pool metric, and cleanup test | The inspected resource has an owner and observable cleanup | Provider-side throttling, DNS churn, credential refresh, or OS limits cannot fail |
| Unsafe, FFI, native, or lock-free code is safe | Invariant contract, ownership/lifetime rules, ABI/platform matrix, reviewer requirement, sanitizer/race/stress command, and unresolved risk | The inspected boundary has explicit safety obligations | All undefined behavior or platform-specific failure modes are eliminated |
| Pattern hides IO, allocation, locks, or fan-out safely | Pattern impact map, side-effect boundary, timeout/retry/cleanup proof, allocation estimate, and rejected simpler option | The inspected abstraction keeps runtime effects visible | Future implementers or unrelated pattern uses remain safe |

## Current Evidence And Freshness

- Treat old benchmarks, incident notes, profiler artifacts, prior task evidence, and prior handoffs as discovery inputs until current source, caller graph, and fresh validation confirm them.
- Mark runtime evidence stale after edits to caller paths, async boundaries, allocation shape, pooling, cleanup, unsafe/native code, generated artifacts, workload fixtures, benchmark harnesses, or validation commands.
- Record inspected and skipped boundaries: language/runtime version, caller graph, input source, resource owner, async scheduler, thread or worker pool, unsafe boundary, generated output, benchmark workload, and release gate.
- Map every final performance or safety claim to a command, artifact, source path, owner review, or explicit not-verified residual risk.

## Tool Permission Boundary

- Heap dumps, traces, flame graphs, and production profiles require an owner, timestamped workload scope, sensitive-data redaction, retention limit, and explicit representativeness limit.
- For retained native, FFI, sanitizer, or kernel diagnostics, record the applicable platform and flags, generated inputs, crash or stall risk, cleanup boundary, secret-bearing output handling, and untested platforms or flags.

## Handoff Evidence Shape

```yaml
language_performance_evidence_closure:
  runtime_scope: ""
  inspected_boundaries: []
  accepted_prior_claims: []
  rejected_or_stale_claims: []
  measurement_to_decision_map: []
  tool_permission_boundary:
    action_class: ""
    sandbox: ""
    state_mutation: ""
    redaction: ""
  what_remains_unproved: []
  residual_runtime_risk: []
  next_gate: ""
```

## Blocking Conditions

Block completion when hot-path claims lack fresh measurement, async or blocking risks lack lag and cancellation evidence, or allocation or fan-out is unbounded. Also block assumed cleanup, unreviewed unsafe code, stale prior evidence, and artifact-writing commands without write-scope and rollback disclosure.
