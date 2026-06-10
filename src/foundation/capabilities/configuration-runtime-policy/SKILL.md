---
name: configuration-runtime-policy
description: Governs typed configuration, feature flags, runtime switches, mode and kind parameters, validation, fail-fast behavior, rollout, rollback, observability, and stale flag cleanup.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "111"
changeforge_version: 0.1.0
---

# Mission

Keep configuration and runtime switches explicit, typed, validated, observable, reversible, and temporary where intended, so they do not become hidden strategy systems or bypass invariants.

# When To Use

Use when adding or changing build-time, deploy-time, runtime, tenant-level, user-level, experiment-level config, feature flags, kill switches, rollout toggles, mode/kind parameters, provider selection, hot reload, or config-driven wiring.

Use when a flag lacks owner, expiry, cleanup path, tests, observability, or rollback behavior.

# Do Not Use When

Do not use for constants that are domain rules and should not vary by environment.

Do not use to justify runtime configurability when the behavior is a stable product invariant, security rule, or domain rule.

# Non-Negotiable Rules

- Config must be typed and validated.
- Defaults must be explicit and safe.
- Invalid config fails fast unless safe degradation is designed.
- Feature flags need owner, type, expiry, and cleanup path.
- Runtime switches must not bypass domain or security invariants.
- Mode and kind parameters must not become hidden strategy systems.
- Config changes must have tests and rollout safety.

# Industry Benchmarks

Anchor against twelve-factor configuration, JSON Schema and typed config binding, feature flag lifecycle governance, progressive delivery, kill switch design, experiment flag practice, secret separation, and config observability through effective runtime state reporting.

# Selection Rules

Select this capability when the main decision is runtime variability policy. Use `secret-configuration-security` for secret handling, `delivery-release-gate` for rollout/rollback execution, `dependency-wiring-lifecycle` for config-driven dependency graphs, `cleanup-deletion-governance` for stale flag removal, and `design-pattern-selection` when modes indicate real strategy variation.

# Risk Escalation Rules

Escalate to `security-privacy-gate` when config can alter auth, tenant isolation, data visibility, encryption, URLs, or secrets. Escalate to `domain-impact-modeler` when config changes business invariants. Escalate to `reliability-observability-gate` when kill switches, hot reload, or runtime config affects production availability.

# Reference Loading Policy

Current mode is inline-only: this capability has no deep reference files today, so this `SKILL.md` contains the active runtime configuration and feature-flag policy.

If deep references are added later, load them only for L3+ work, public or operator-visible config changes, runtime behavior switches, feature-flag lifecycle risk, invariant bypass, rollout/rollback impact, or stale cleanup debt.

Do not load deep references for L1/L2 local config edits where the inline output contract for schema, default, validation, owner, expiry, and cleanup can be satisfied.

# Critical Details

- Build-time config is baked into artifacts; deploy-time config changes with environment; runtime config can change without deploy and needs observability.
- Tenant, user, and experiment-level config needs targeting, auditability, and precedence.
- Defaults should be safe for production, not merely convenient for development.
- Hot reload requires atomic update, validation before apply, rollback to last good value, and metric/log visibility.
- Feature flags need type: release, ops, experiment, permission, migration, or kill switch.
- Flags need owner, creation reason, expiry/removal date, cleanup issue, and telemetry for old/new path usage.
- Mode/kind switches require bounded enum, explicit semantics, and rejection of unrelated strategies under one parameter.
- Config secrets belong in secret stores or secret config boundaries, not ordinary observable config.

# Failure Modes

- Permanent feature flag with no owner or removal condition.
- Boolean flag bypasses permission, validation, transaction, or domain invariant.
- Invalid config starts successfully and fails later under traffic.
- Mode parameter grows into a hidden strategy registry with unclear ownership.
- Hot reload applies partially and leaves mixed behavior.
- Default points to production dependency in tests or to unsafe development behavior in production.
- Config change has no test matrix or rollout/rollback path.

# Output Contract

Return a Configuration Policy:

- Config scope.
- Config schema and type.
- Default behavior.
- Validation and fail-fast behavior.
- Feature flag lifecycle.
- Kill switch behavior.
- Runtime switch rationale.
- Mode/kind governance.
- Config secrets boundary.
- Observability.
- Rollout and rollback config path.
- Test matrix.
- Cleanup owner and date.
- Residual config risk.

# Evidence Contract

Close the policy only when schema, defaults, validation, owners, expiry, cleanup path, tests, rollout/rollback steps, runtime observability, and invariant-preservation evidence are recorded with validation command or review artifact and residual risk.

# Quality Gate

1. Config is typed and validated.
2. Defaults are explicit and safe.
3. Invalid config fails fast or safely degrades by design.
4. Feature flag owner, type, expiry, and cleanup path are recorded.
5. Runtime switches do not bypass domain or security invariants.
6. Mode/kind switch remains bounded and not a hidden strategy system.
7. Test matrix covers meaningful config combinations.
8. Rollout and rollback path is explicit.

# Used By

- delivery-release-gate
- backend-change-builder
- frontend-change-builder
- integration-change-builder
- reliability-observability-gate
- architecture-impact-reviewer
- change-documentation-gate
- ai-code-review-refactor

# Handoff

Hand off to `secret-configuration-security` for secret exposure, `delivery-release-gate` for rollout, `dependency-wiring-lifecycle` for config-driven construction, `cleanup-deletion-governance` for stale flags, and `domain-impact-modeler` when config can alter business rules.

# Completion Criteria

The capability is complete when each config or flag has typed schema, safe defaults, validation, owner, lifecycle, invariant check, test matrix, observability, rollout/rollback path, and cleanup plan.
