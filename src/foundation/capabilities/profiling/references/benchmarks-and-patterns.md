# Profiling Decision Patterns

Load this reference when a symptom and hypothesis leave competing measurement, workload, or bottleneck interpretations. Measurement methods are candidates, not a tool whitelist.

| Suspected cause | Evidence properties to select | Reject when |
| --- | --- | --- |
| Compute saturation | Samples attribute consumed compute to an owned path under representative work | Idle or wait time dominates the symptom |
| Wait or contention | Blocking, queue, lock, pool, or scheduler wait is separated from compute | The measurement cannot distinguish waiting from execution |
| Allocation or retention | Allocation rate, retained growth, lifetime, and owner path are distinguished | A runtime setting change is proposed without locating retained or created work |
| I/O or query work | Call count, wait, bytes/rows touched, plan/path, cache state, and caller frequency are correlated | One slow-call threshold hides repeated or aggregate work |
| Network or dependency | Fan-out, payload, retry, timeout, remote wait, and failure/rejection behavior are attributable | Endpoint aggregates hide the responsible dependency |
| Rendering or interaction | Main-thread, frame, layout/render, device/runtime/network, and content state are comparable | A developer-machine trace is generalized to target users |
| Unit cost | Runtime driver is joined to the owned request, job, tenant, data, model, storage, or egress unit | Aggregate spend has no changed-path attribution |

The W3C Long Tasks API defines a main-thread task over 50 ms as a long-task signal. Treat this as an external signal definition for profiler interpretation, not a product performance budget, release threshold, or evidence that shorter tasks are acceptable.

Choose sampling, tracing, instrumentation, snapshots, plans, or billing attribution according to signal resolution, overhead, authority, and artifact risk. Compare matched workloads and re-profile after the change; a model or benchmark remains a hypothesis until measured.

Proof scope: these patterns do not establish product budgets, production capacity, correctness, security, query or runtime ownership, release safety, or sensitive-artifact compliance. Require fresh evidence from the owning boundary before making those claims.
