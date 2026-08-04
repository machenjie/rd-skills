# Node.js Event Loop And Cancellation Contracts

**Load when:** Event-loop phases, blocking callbacks, next-tick or microtask ordering, timers, cancellation, Worker offload, or asynchronous context behavior changes.

**Do not load when:** Scheduling, cancellation, offload, and context propagation remain unchanged and current focused evidence already settles them.

**Required by:** `analysis-agent`, `task-agent`, `review-agent`

**Required output:** `decision-record`, `failure-decision`, `proof-limit`

## One Decision

Select one scheduling and cancellation contract that preserves fairness, terminal outcomes, context ownership, and teardown.

## Decision Matrix

| Boundary | Required decision | Failure signal |
|---|---|---|
| Callback work | Maximum input, synchronous cost, yield point, and overload outcome | One callback delays unrelated timers or I/O |
| Ordering | Required phase, next-tick, promise-microtask, immediate, and timer relationship | Correctness depends on an assumed universal callback order |
| Microtasks | Chain bound, fairness point, error observation, and re-entry behavior | Recursive work starves poll or timer progress |
| Timer | Deadline meaning, drift tolerance, cancellation owner, late result, and whether `ref()`/`unref()` transfers process-liveness responsibility to a named owner | `unref()` is treated as cancellation or cleanup while work can still complete |
| Cancellation | Signal source, propagation path, irreversible boundary, cleanup, and terminal error | Abort is accepted but owned work continues silently |
| Async context | Store owner, `run()` scope, custom-boundary bridge, missing-store outcome, and cleanup | Context leaks between requests or disappears without detection |
| Offload | CPU evidence, Worker pool bound, queue limit, transfer/clone ownership, and termination | A Worker is added for ordinary asynchronous I/O |

## Verification

- Record event-loop delay or a deterministic ordering trace for the risk-carrying callback.
- Exercise abort before start, during suspension, after irreversible work, and after apparent completion.
- Exercise referenced and unreferenced timer paths separately; prove cancellation/cleanup independently from process-liveness ownership.
- Run bounded next-tick and promise chains alongside a timer and I/O checkpoint.
- Verify context inside each real callback bridge and confirm the missing-context outcome.
- Exercise Worker queue saturation, message error, termination, and late completion when offload is selected.

## Primary Sources

- [Node.js: Don't Block the Event Loop](https://nodejs.org/learn/asynchronous-work/dont-block-the-event-loop)
- [Node.js process documentation](https://nodejs.org/api/process.html)
- [Node.js timers documentation](https://nodejs.org/api/timers.html)
- [Node.js asynchronous context tracking](https://nodejs.org/api/async_context.html)
- [Node.js Worker threads documentation](https://nodejs.org/api/worker_threads.html)

Official Node.js pages were accessed on 2026-07-26.

## Proof Limits

Focused ordering and cancellation tests prove only the exercised Node.js version, flags, workload, and callback graph. They do not prove production fairness, operating-system scheduling, external cancellation support, or context propagation through untested libraries.
