# Configuration Runtime Policy Benchmarks And Patterns

Use this reference when `configuration-runtime-policy` needs more depth than the main `SKILL.md` should carry efficiently. Keep the body focused on route-time policy and evidence.
Use this file for config taxonomy, precedence, lifecycle patterns, graph variants, cleanup debt, and anti-pattern review.

## Benchmark Anchors

- Twelve-factor config: environment-specific behavior belongs in explicit configuration, not hidden code branches.
- Typed config binding and JSON Schema/OpenAPI-style validation: invalid values should fail before use.
- Progressive delivery and feature flag lifecycle practice: rollout state needs owner, telemetry, cleanup, and rollback.
- Kill-switch design: mitigation should state fail-open/fail-closed posture, blast radius, and re-enable path.
- Policy-as-code and audit-ready change records: operator changes need visible owner, audit, and proof.
- Config observability: expose safe effective state and version without leaking secrets or tenant/user data.

## Config Classification Matrix

| Config class | Required policy | Escalate when |
| --- | --- | --- |
| Build/deploy config | Type, default, env/profile matrix, validation before artifact or deploy. | Artifact is baked with unsafe or ambiguous value. |
| Runtime/remote config | Atomic apply, validation-before-use, version, last-good rollback, audit. | Hot reload can produce mixed versions under traffic. |
| Feature flag | Type, owner, reason, expiry, telemetry, cleanup issue, old/new path tests. | Flag changes auth, tenant, money, migration, or availability. |
| Kill switch | Default posture, trigger, blast radius, runbook, re-enable and rollback. | Mitigation weakens security or data integrity. |
| Targeting/experiment | Assignment rule, precedence, exposure event, guardrail metrics, audit. | Cross-tenant leakage or SRM/sample-ratio risk is plausible. |
| Mode/kind/provider | Bounded enum, graph variant, rejected values, startup fail-fast. | It becomes an unowned strategy registry. |
| Stale cleanup | Usage evidence, owner, removal condition, rollback after deletion. | Deletion affects public/operator behavior or migration rollback. |

## Precedence Pattern

```text
effective_config =
  operator emergency override
  > tenant override
  > user or cohort assignment
  > remote runtime config
  > environment or deploy profile
  > config file
  > code default
```

State the real order used by the system. Do not copy this order unless it matches current source.

## Anti-Patterns To Reject

| Anti-pattern | Failure | Safer treatment |
| --- | --- | --- |
| Boolean flag without type, owner, or expiry. | Temporary behavior becomes permanent architecture. | Flag taxonomy, owner, telemetry, cleanup issue, and old/new tests. |
| Runtime config bypasses invariant. | Permission, tenant, validation, transaction, or audit rule becomes optional. | Move invariant into code or fail closed with specialist review. |
| Late validation. | Invalid config starts and fails under traffic. | Validate at build, deploy, startup, load, or before apply. |
| Mode string grows branches. | Hidden strategy registry bypasses design review. | Bounded enum, variant matrix, and design-pattern handoff. |
| Secret in ordinary config. | Secret leaks through logs, docs, frontend, traces, or generated artifacts. | Route to secret configuration boundary. |
| Happy-path-only validation. | Unsafe variant combinations escape tests. | Key-to-test matrix with skipped combinations disclosed. |

## Handoff Boundaries

- Use `secret-configuration-security` for secrets, public-prefix frontend variables, credentials, KMS, or sensitive defaults.
- Use `delivery-release-gate` for rollout execution, environment mutation, deploy sequencing, and rollback operations.
- Use `dependency-wiring-lifecycle` when config selects graph construction or provider variants.
- Use `cleanup-deletion-governance` for stale flag removal.
- Use `experience-impact-modeler` or `bigdata-product-extension` for experiment exposure, guardrails, or SRM concerns.
- Use `quality-test-gate` or `targeted-validation-selection` when variant coverage is the main gap.
