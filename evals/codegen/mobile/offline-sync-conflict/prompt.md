# Benchmark Prompt

## Task

Implement a focused change to resolve offline edit sync conflicts without losing local changes or violating server version rules.

## Context

The starter repo represents a mobile client edits task details while offline and later syncs with the API. In its initial state, the starter behavior overwrites server data when connectivity returns. The implementation should be small enough to review but complete enough to prove the professional quality target.

## Requirements

- Offline edits sync only when based on the expected server version.
- Conflicts preserve local draft data and expose a recovery path.
- Retry behavior handles network loss without duplicate mutation effects.
- Telemetry distinguishes success, retry, and conflict outcomes.

## Constraints

- Sync payloads include version or ETag preconditions.
- State management keeps pending, synced, failed, and conflict states distinct.
- Tests simulate offline, reconnect, conflict, and retry flows.
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
