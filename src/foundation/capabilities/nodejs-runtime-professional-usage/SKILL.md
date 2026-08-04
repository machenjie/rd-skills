---
name: nodejs-runtime-professional-usage
description: "Use when Node.js event-loop, stream, Buffer, process, Worker, async-context, cancellation, or handle semantics change. Skip TypeScript, browser, build, and business rules."
---

# nodejs-runtime-professional-usage

## Registry Trigger

**Use when**

- Node.js behavior depends on scheduling, cancellation, streams, buffers, processes, workers, async context, modules, cache identity, or active resources.
- Runtime versions, flags, entrypoints, or lifecycle behavior can change the outcome.

**Do not use when**

- Route TypeScript design to `typescript-professional-usage`, browser APIs to `web-platform-professional-usage`, package/build policy to build guidance, and business rules to the backend owner.

## Skill Role

Own Node.js runtime and core-library semantics. Exclude product, build, package-policy, browser, and typing decisions.

## High-Value Rules

- Define the supported Node.js release, flags, entrypoint, module mode, and host constraints.
- Bound synchronous callbacks, promise continuations, and `process.nextTick()` chains. Use bounded Workers only for evidence-backed CPU work.
- Use one cancellation owner with supported `AbortSignal` propagation and reconciliation of abort, timeout, cleanup, and late completion.
- Enforce stream backpressure, byte/object modes, completion, and destroy/error paths.
- Define Buffer encoding, byte length, initialized allocation, copy/view choice, alias lifetime, and conversion.
- Define signals, exit codes, children, IPC, Workers, shutdown, and the terminal uncaught-exception boundary.
- Isolate `AsyncLocalStorage` context and resolve ESM/CommonJS, exports, side effects, cycles, and cache identity for supported consumers.
- Require every owned runtime resource to close, destroy, or terminate, or explicitly transfer liveness ownership to a named owner with bounded lifetime, shutdown, and reacquisition behavior; `unref()` alone is not cleanup.

## Anti-Patterns

- Next-tick or microtask recursion starves timers and I/O.
- Ignored backpressure grows memory or loses trailing output.
- A Buffer view outlives mutable or pooled backing memory.
- Exit or signal handling abandons cleanup and child resources.
- Module or cache mismatch breaks consumers or duplicates singleton state.
- Active handles keep the process alive after teardown, or unreferenced work outlives its declared owner.

## Execution Checklist

- Exercise the supported Node.js version, flags, metadata, and entrypoint.
- Probe starvation, cancellation, slow consumers, stream failure, Buffer boundaries, termination, Worker failure, module consumers, and post-teardown resources.
- Scope diagnostics and tests to the exercised workload and platform.

## Stop Conditions

- Stop on unknown runtime, module mode, lifecycle owner, cancellation path, binary contract, resource owner, or unproved liveness transfer.
- Stop loss, corruption, orphaning, leaks, or entrypoint changes without invalid and boundary evidence.
- Route non-Node.js decisions to their named owners.

## Output Contract

- Node.js runtime decision with scheduling cancellation stream binary process Worker context module cache resource ownership verification proof limits and residual risk

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [event loop and cancellation contracts](references/event-loop-and-cancellation-contracts.md) | targeted | Event-loop phase blocking microtask timer cancellation Worker or async-context behavior is unresolved | Scheduling cancellation and context behavior remain unchanged and focused evidence already settles them | analysis-agent, task-agent, review-agent | decision-record, failure-decision, proof-limit |
| [streams and backpressure contracts](references/streams-and-backpressure-contracts.md) | targeted | Stream flow completion backpressure Buffer encoding aliasing or binary ownership changes | No stream or binary boundary changes | analysis-agent, task-agent, review-agent | boundary-decision, validation-plan, residual-risk |
| [process modules and resources contracts](references/process-modules-and-resources-contracts.md) | targeted | Process signal child Worker module export cache or active-resource lifecycle changes | Process module and resource ownership remain unchanged | analysis-agent, task-agent, review-agent | boundary-decision, decision-record, proof-limit |
