# Benchmark Prompt

## Task

Implement a focused change to design a reversible migration rollout that keeps old and new application versions compatible.

## Context

The starter repo represents a release adds a normalized account status column while old workers still read the legacy field. In its initial state, the starter migration drops compatibility in the same deploy that writes the new shape. The implementation should be small enough to review but complete enough to prove the professional quality target.

## Requirements

- Old and new application versions can run during the migration window.
- Forward migration, backfill, read cutover, and cleanup are separated.
- Rollback returns traffic to the previous version without data loss.
- Deployment notes include stop conditions and verification commands.

## Constraints

- Migration scripts are idempotent and safe to resume.
- Compatibility tests cover mixed old and new writer behavior.
- Cleanup is gated behind explicit post rollout evidence.
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
