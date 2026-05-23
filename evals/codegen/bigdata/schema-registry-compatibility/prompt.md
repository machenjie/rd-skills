# Benchmark Prompt

## Task

Implement a focused change to add schema registry compatibility validation for event producers and consumers.

## Context

The starter repo represents a streaming pipeline publishes account events consumed by analytics and operational jobs. In its initial state, the starter behavior updates event fields without checking compatibility against registered schemas. The implementation should be small enough to review but complete enough to prove the professional quality target.

## Requirements

- Producer schema changes are checked for declared compatibility mode.
- Consumer fixtures prove old and new event versions can be read.
- Incompatible changes fail before publication.
- Replay documentation covers versioned deserialization and dead letter handling.

## Constraints

- Schema checks run in CI and local benchmark scripts.
- Tests include removed field, renamed field, and additive nullable field cases.
- Compatibility policy is explicit per topic.
- Preserve the existing public contract unless the prompt explicitly asks for a compatible addition.
- Do not replace the benchmark with documentation-only output.

## Deliverables

- Source changes in the starter repo that implement the requested behavior.
- Tests or executable checks that prove the required behavior and denial paths.
- A short implementation note describing important tradeoffs and residual risk.

## Completion Evidence

- `bash setup.sh`
- `bash ../test-suite/run.sh`
- `bash ../security-checks/run.sh`
- Review evidence that no automatic failure condition applies.
