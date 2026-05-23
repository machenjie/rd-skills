# Benchmark Prompt

## Task

Implement a focused change to implement OTA A/B update rollback behavior with health confirmation and staged rollout controls.

## Context

The starter repo represents edge devices download firmware updates and report boot health after activation. In its initial state, the starter behavior marks an update successful when the package downloads, before boot health is known. The implementation should be small enough to review but complete enough to prove the professional quality target.

## Requirements

- Update success is recorded only after boot health confirmation.
- Failed boot or missing heartbeat rolls back to the previous slot.
- Staged rollout pauses when health thresholds fail.
- Package identity and signature checks run before activation.

## Constraints

- State machine separates downloaded, activated, confirmed, failed, and rolled back states.
- Tests simulate reboot loss, failed health, and successful confirmation.
- Rollout metrics expose device cohort health and rollback counts.
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
