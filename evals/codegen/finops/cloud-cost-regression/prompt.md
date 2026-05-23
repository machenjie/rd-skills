# Benchmark Prompt

## Task

Implement a focused change to add cloud cost regression checks that block unexpected spend increases before deployment.

## Context

The starter repo represents an infrastructure change modifies queue retention, storage replication, and compute sizing. In its initial state, the starter behavior reports total cost after deployment but has no pre merge budget guard. The implementation should be small enough to review but complete enough to prove the professional quality target.

## Requirements

- Planned resource changes are compared against declared monthly cost thresholds.
- Unexpected storage, egress, or compute increases fail the check.
- Approved exceptions require owner, expiry, and budget note.
- Release evidence includes cost diff output and rollback signal.

## Constraints

- Cost checks run from deterministic infrastructure plan input.
- Thresholds are scoped by service and environment.
- Tests include below threshold, above threshold, and approved exception cases.
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
