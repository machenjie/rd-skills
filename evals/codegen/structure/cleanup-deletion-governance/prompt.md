# Benchmark Prompt

## Task

Clean up a stale feature flag, legacy fallback branch, compatibility shim, and deprecated API that have remained after a migration.

## Context

The starter repository has a `new_profile_flow` flag with no owner, a fallback to legacy serialization, a compatibility branch for old SDKs, and a deprecated endpoint. There is no caller search, telemetry evidence, deletion issue, or rollback plan.

## Requirements

- Define target artifacts, owner, removal condition, caller search, telemetry, tests, rollback path, and residual deletion risk.
- Search static callers plus runtime, generated, reflection, package, and documentation references.
- Remove stale flag, fallback, compatibility branch, deprecated API, and expand-contract leftovers only when conditions are met.
- Document cleanup issue tracking and owner.
- Preserve rollback path after deletion.

## Constraints

- Do not leave feature flags, fallbacks, compatibility branches, or deprecated APIs permanently.
- Do not delete code without caller search and telemetry evidence.
- Do not ignore generated, runtime, or reflection references.
- Do not remove behavior without rollback path.

## Deliverables

- Cleanup / Deletion Plan.
- Caller search and telemetry evidence.
- Tests for removed and preserved behavior.
- Rollback path and cleanup tracking.

## Completion Evidence

- Stale artifacts have explicit deletion or retained-risk decision.
- Telemetry proves unused behavior or states accepted residual risk.
- Tests and docs no longer reference removed behavior.
