# Benchmark Prompt

## Task

Fix an async request path that performs CPU-bound work and synchronous IO on
the event loop.

## Context

The starter repository has a Node.js or Python async endpoint that parses a
large report, reads a file synchronously, calls a blocking SDK, and then uses
unbounded `Promise.all` or `asyncio.gather` for downstream notifications.

## Requirements

- Identify CPU-bound work and blocking IO on the async request path.
- Move CPU-bound work to a worker, executor, or dedicated bounded pool.
- Use async IO or an isolated bounded pool for file and network IO.
- Add timeout, cancellation propagation, and backpressure for fan-out.
- Record event-loop lag or an equivalent measurement plan.

## Constraints

- Do not leave a blocking call on the event loop.
- Do not use unbounded `Promise.all`, `asyncio.gather`, or equivalent fan-out.
- Do not omit timeout or cancellation behavior.
- Do not claim performance improvement without measurement evidence.

## Deliverables

- Updated async endpoint and worker/executor boundary.
- Tests for timeout, cancellation, and overload.
- Performance-Aware Structure Decision and runtime assessment.

## Completion Evidence

- Event-loop blocking is removed or isolated.
- Fan-out is bounded.
- Review evidence names CPU-bound offload and blocking versus non-blocking IO
  boundaries.
