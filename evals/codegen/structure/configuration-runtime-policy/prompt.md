# Benchmark Prompt

## Task

Repair a notification service where `mode`, `kind`, and several feature flags drive unrelated strategies with no owner, expiry, validation, or cleanup path.

## Context

The starter repository reads untyped environment variables at runtime. Invalid values silently fall back to legacy behavior, a tenant-level flag bypasses a domain invariant, and an experiment flag has been permanent for a year.

## Requirements

- Define typed config for build-time, deploy-time, runtime, tenant-level, user-level, and experiment-level settings that apply.
- Make defaults explicit and safe.
- Validate config and fail fast unless safe degradation is intentionally designed.
- Assign feature flag owner, type, expiry, cleanup path, kill switch, rollout, and rollback behavior.
- Prevent mode and kind switches from becoming hidden strategy systems or bypassing invariants.

## Constraints

- Do not add permanent flags without owner and expiry.
- Do not let runtime switches bypass domain or security rules.
- Do not accept invalid config silently.
- Do not hide multiple strategies behind stringly typed mode or kind parameters.

## Deliverables

- Configuration Policy.
- Typed config schema and validation behavior.
- Feature flag lifecycle and cleanup owner/date.
- Config test matrix and rollout/rollback plan.

## Completion Evidence

- Invalid config fails fast or degrades safely by design.
- Feature flags have removal criteria and cleanup issue.
- Tests cover default, invalid, rollout, rollback, and kill-switch behavior.
