# Node.js Streams And Backpressure Contracts

**Load when:** Stream flow, completion, backpressure, cancellation, Buffer encoding, byte ownership, view aliasing, or binary conversion changes.

**Do not load when:** No stream or binary boundary changes and current tests already prove the established ownership and completion behavior.

**Required by:** `analysis-agent`, `task-agent`, `review-agent`

**Required output:** `boundary-decision`, `validation-plan`, `residual-risk`

## One Decision

Select one stream and binary contract that bounds memory, preserves bytes, observes completion, and owns cancellation and cleanup.

## Decision Matrix

| Boundary | Required decision | Failure signal |
|---|---|---|
| Stream mode | Byte or object mode, chunk contract, ordering, and cardinality | Byte limits are interpreted as object counts or conversely |
| Backpressure | Producer pause, `write()` false handling, drain/resume path, and queue bound | Producer continues while the consumer is saturated |
| Watermarks | Readable and writable units, selected threshold, workload evidence, and memory bound | `highWaterMark` is treated as a hard memory limit |
| Pipeline | Owner, stages, error propagation, abort signal, destroy behavior, and awaited completion | Earlier success hides a later stage failure or truncated tail |
| Lifecycle | End, finish, close, error, premature close, repeated cleanup, and listener removal | The caller reports success before the owned sink finishes |
| Async iteration | Abandonment, cancellation, return path, partial output, and error timing | A loop exits while the source remains active |
| Buffer boundary | Encoding, length, allocation initialization, bounds, and invalid input | Character count is used as byte length |
| Buffer ownership | Copy or view, pooled backing memory, mutation owner, transfer, and retention | A slice aliases bytes that another owner mutates or retains |

## Verification

- Run a slow or paused consumer and assert bounded producer behavior after `write()` returns false.
- Fail each pipeline stage and abort before start, during flow, and after partial output.
- Verify empty, oversized, split-boundary, malformed-encoding, and multibyte inputs.
- Mutate source and derived Buffer views to prove the selected alias-or-copy contract.
- Assert the caller-visible result only after the owned completion event or pipeline promise settles.

## Primary Sources

- [Node.js stream documentation](https://nodejs.org/api/stream.html)
- [Node.js: Backpressuring in Streams](https://nodejs.org/learn/modules/backpressuring-in-streams)
- [Node.js Buffer documentation](https://nodejs.org/api/buffer.html)

Official Node.js pages were accessed on 2026-07-26.

## Proof Limits

Slow-consumer and binary fixtures prove only the exercised stages, chunk shapes, encodings, watermarks, and Node.js version. They do not prove production memory ceilings, device or network throughput, third-party stream correctness, or safety of untested Buffer retention paths.
