# Statement Control And Exit Paths

This guide resolves local statement hazards that can change termination, cleanup, caller-visible failure, durable mutation, or async lifecycle.

## Statement Contract

| Statement hazard | Decision to expose | Accident signature |
| --- | --- | --- |
| Branch or early exit | Keep primary and exceptional outcomes visible while preserving cleanup, audit, rollback, and response obligations | A guard, empty branch, or fallthrough skips required work |
| Loop, page, poll, or retry | Give cursor or counter mutation, termination, bounds, cancellation, backoff, and partial progress an owner | Several control sites, arbitrary sleep, unbounded fan-out, or mutation invalidates iteration |
| Error or cleanup | Catch the intended boundary, preserve safe error meaning, and release owned resources across success, error, early return, cancellation, and timeout | A broad or empty catch swallows failure or non-success exits miss cleanup |
| Return, throw, or result | Preserve the caller contract, durable state, error category, and required cleanup or audit | An early return changes state or effect order, or an internal error escapes its boundary |
| Transaction or effect order | Expose validation, policy, mutation, commit, event, cache, notification, external effect, and response order | An effect publishes state that can roll back without a recovery mechanism owned elsewhere |
| Lock or async work | Bound lock scope and identify spawned work ownership, completion observation, cancellation, timeout, backpressure, shutdown, error propagation, and cleanup | Blocking I/O crosses a lock or detached work lacks lifecycle and failure ownership |

## Proof And Routing

Exercise applicable termination, boundary input, fallthrough, non-success cleanup, commit failure, duplicate or partial effect, lock scope, and async cancellation. Static and focused checks leave unexercised interleavings and production dependencies outside their proof.
Route commit or effect order to `transaction-consistency` or `data-side-effect-flow-tracing`, concurrency to `concurrency-control`, language cleanup semantics to `language-idiom-enforcement`, and async lifecycle to `reliability-observability-gate`.
