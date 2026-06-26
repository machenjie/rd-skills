---
name: configuration-runtime-policy
description: Use when build, deploy, runtime, tenant, experiment, flag, kill-switch, rollout, mode, kind, provider, or config-driven wiring choices need typed validation, owner, rollback, observability, or cleanup.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "111"
changeforge_version: 0.1.0
---

# Mission

Keep build, deploy, runtime, tenant, experiment, and operator switches explicit, typed, validated, observable, reversible, and temporary where intended. A configuration choice must be a governed policy boundary, not a hidden strategy system, invariant bypass, stale rollout crutch, or untraceable source of graph, memory, validation, and execution drift.

# When To Use

- When adding or changing build-time, deploy-time, runtime, tenant-level, user-level, experiment-level, environment-level, CLI-level, or operator-managed configuration.
- When introducing or reviewing feature flags, kill switches, rollout toggles, experiment gates, permission flags, migration flags, hot reload, mode/kind/provider selection, config-driven dependency wiring, or config precedence rules.
- When a config value lacks schema, type, safe default, owner, expiry, cleanup path, validation, observability, audit trail, rollout/rollback behavior, or test matrix.
- When project memory, repository graph, validation output, or execution trajectory suggests stale flags, fragile config, hidden behavior switches, invalid defaults, or config-driven construction drift.
- When a runtime switch may alter auth, tenant isolation, data visibility, security posture, dependency selection, degraded-mode behavior, or production availability.

# Do Not Use When

Do not use for constants that are domain rules and should not vary by environment, tenant, user, experiment, or operator action.

Do not use to justify runtime configurability when the behavior is a stable product invariant, security rule, compliance rule, or domain rule.

Do not use as the primary secret-handling policy; route secrets and credential-bearing values to `secret-configuration-security`.

# Stage Fit

Use during implementation planning, coding, review, validation, release readiness, and cleanup when runtime variability affects behavior, wiring, rollout, or closure evidence. Re-enter after graph refresh, memory signal, config schema change, flag cleanup, rollout plan change, hot-reload behavior change, or validation report update that can make prior config evidence stale.

# Non-Negotiable Rules

- **Typed source of truth:** Every configurable behavior has a named schema, type, allowed values, owner, default, precedence, and read boundary.
- **Safe explicit defaults:** Defaults are intentional for production and test; security, privacy, money, data integrity, and tenant isolation defaults fail closed unless a reviewed safe-degradation design says otherwise.
- **Validate before use:** Invalid config fails fast at startup, deploy, load, or flag evaluation unless safe degradation, alerting, and rollback are explicitly designed.
- **No invariant bypass:** Runtime switches cannot bypass domain rules, permissions, auth, tenant isolation, validation, transactions, encryption, audit, or compliance controls.
- **Flag lifecycle is mandatory:** Feature flags have type, owner, creation reason, expiry/removal condition, cleanup issue, telemetry, and old/new path test evidence.
- **Mode/kind governance:** Mode, kind, provider, or strategy parameters remain bounded enums with explicit semantics and must not become unowned hidden strategy registries.
- **Hot reload is atomic:** Runtime reload validates before apply, publishes one coherent version, exposes current state, and can roll back to last good config.
- **Graph and validation coupling:** Config-driven wiring, routing, or behavior variants map to repository graph edges, affected tests, and validation commands before closure.
- **Memory is not source truth:** Prior flag or config incidents can widen review, but current source, registry, docs, telemetry, or owner evidence must confirm claims.
- **Cleanup is part of addition:** Temporary config and flags are not complete without owner, expiry, removal path, and rollback-compatible cleanup plan.

# Industry Benchmarks

Anchor against twelve-factor configuration, typed config binding, JSON Schema/OpenAPI-style validation, feature-flag lifecycle governance, progressive delivery, kill-switch design, experiment flag practice, secret separation, config observability, policy-as-code review, audit-ready change records, and runtime state reporting. Keep the capability focused on configuration governance; route to companion skills for secrets, release execution, dependency graphs, cleanup, security review, and reliability operations.

# Mode Matrix

| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities | Exit risk |
| --- | --- | --- | --- | --- | --- |
| Build/deploy config | Env var, values file, build arg, CLI option, config file, deploy profile, or platform setting changes behavior. | Source of truth, schema, default, environment precedence, deploy validation. | Key name, owner, type, allowed values, default, env/profile matrix, validation command. | `delivery-release-gate`, `secret-configuration-security` | Build artifact or environment starts with unsafe default. |
| Runtime config and hot reload | Dynamic config, remote config, reload endpoint, watcher, admin toggle, or operator update. | Atomic apply, last-good rollback, visible current state, audit. | Validation-before-apply, versioning, rollback value, audit log, metric/log field. | `reliability-observability-gate`, `observability` | Mixed runtime versions or partial apply under traffic. |
| Feature flag lifecycle | Release, ops, experiment, permission, migration, or kill-switch flag. | Owner, expiry, telemetry, cleanup, old/new path tests. | Flag type, owner, reason, removal condition/date, exposure metric, cleanup issue. | `cleanup-deletion-governance`, `quality-test-gate` | Permanent flag or untested dead branch. |
| Kill switch / degradation | Config disables feature, dependency, queue, integration, enforcement, or workload. | Fail-open/fail-closed policy, blast radius, operator runbook, rollback. | Trigger condition, default state, safety posture, alert, runbook, re-enable path. | `degradation-circuit-breaking`, `delivery-release-gate` | Mitigation creates larger security or availability failure. |
| Tenant/user/experiment targeting | Tenant, segment, cohort, user, percentage rollout, or experiment assignment. | Precedence, auditability, isolation, SRM or exposure correctness. | Targeting rules, precedence order, audit trail, exposure event, guardrail metrics. | `experience-impact-modeler`, `bigdata-product-extension` | Cross-tenant leakage or invalid experiment decision. |
| Mode/kind/provider selection | Mode, kind, type, provider, strategy, adapter, region, model, or backend switch. | Bounded enum, explicit semantics, graph variant matrix. | Allowed values, rejected values, variant graph, default, test matrix, owner. | `design-pattern-selection`, `dependency-wiring-lifecycle` | Hidden strategy system or invalid graph starts. |
| Stale config cleanup | Expired flag, rollout complete, fallback obsolete, migration done, shortcut accepted. | Removal condition, caller search, telemetry, rollback after deletion. | Usage evidence, cleanup owner/date, issue, old/new branch deletion plan. | `cleanup-deletion-governance`, `consumer-impact-analysis` | Configuration debt preserves obsolete behavior. |

# Selection Rules

Select this capability when the main decision is **runtime variability policy**: should a behavior vary, where is the source of truth, how is it validated, who owns it, how is it observed, and how is it removed or rolled back?

Use `secret-configuration-security` when the value is a secret, credential, public-prefix frontend variable, KMS/secret-manager policy, or security-sensitive config default. Use `delivery-release-gate` for rollout execution, environment mutation, deploy sequencing, and rollback operations. Use `dependency-wiring-lifecycle` when config selects dependency graph variants or implementation construction. Use `cleanup-deletion-governance` for stale flag removal and deferred cleanup. Use `design-pattern-selection` when a mode parameter reveals true strategy variation. Use `repository-graph-analysis`, `project-memory-governance`, `execution-trajectory-analysis`, and `validation-broker` when graph edges, stale memory, command order, or validation freshness affect the config claim.

# Proactive Professional Triggers

- **Signal:** A new boolean flag, env var, option, mode, kind, provider, or config key appears without schema, owner, default, and tests. **Hidden risk:** the change ships as untyped behavior variation. **Required professional action:** define typed policy and validation before use. **Route to:** `configuration-runtime-policy`, `quality-test-gate`. **Evidence required:** schema, default, owner, test matrix, validation result.
- **Signal:** A flag has no expiry, cleanup issue, removal condition, or telemetry for old/new path usage. **Hidden risk:** temporary rollout state becomes permanent architecture. **Required professional action:** add lifecycle, cleanup owner, and usage evidence. **Route to:** `cleanup-deletion-governance`. **Evidence required:** flag type, owner, expiry/removal condition, cleanup issue, telemetry.
- **Signal:** A mode/kind/provider string controls many branches, adapters, factories, or dependency graphs. **Hidden risk:** hidden strategy registry bypasses architecture review. **Required professional action:** bound enum values, map graph variants, and route true strategy variation. **Route to:** `design-pattern-selection`, `dependency-wiring-lifecycle`. **Evidence required:** allowed values, variant matrix, rejected alternatives, tests.
- **Signal:** Runtime config, remote config, or hot reload applies without validation-before-apply and last-good rollback. **Hidden risk:** invalid or partial config fails under traffic. **Required professional action:** make reload atomic and observable. **Route to:** `reliability-observability-gate`, `validation-broker`. **Evidence required:** versioned load path, rollback value, current-state reporting, alert/log/metric.
- **Signal:** Config can affect auth, tenant isolation, data visibility, encryption, rate limits, URLs, secrets, logging redaction, or frontend exposure. **Hidden risk:** a non-code change changes security posture. **Required professional action:** escalate security review and fail-closed default analysis. **Route to:** `security-privacy-gate`, `secret-configuration-security`. **Evidence required:** security-sensitive fields, default posture, owner review, tests.
- **Signal:** Memory or previous run notes say a config or flag is fragile, stale, or repeatedly broken. **Hidden risk:** stale memory substitutes for current evidence. **Required professional action:** reconcile current source, graph, reports, telemetry, and validation order. **Route to:** `project-memory-governance`, `repository-graph-analysis`, `execution-trajectory-analysis`. **Evidence required:** accepted/rejected memory claim, current source proof, validator freshness.
- **Signal:** Validation claims "config covered" without enumerating changed keys, variants, owners, or affected tests. **Hidden risk:** single happy path misses unsafe combinations. **Required professional action:** broker config matrix validation or disclose partial evidence. **Route to:** `validation-broker`, `quality-test-gate`. **Evidence required:** key-to-test map, skipped variants, evidence limits.

# Risk Escalation Rules

Escalate to `security-privacy-gate` when config can alter auth, tenant isolation, data visibility, encryption, URLs, CORS, CSP, rate limits, logging redaction, frontend exposure, or secrets. Escalate to `domain-impact-modeler` when config changes business invariants, eligibility, pricing, permissions, lifecycle state, or audit semantics. Escalate to `reliability-observability-gate` when kill switches, hot reload, remote config, backpressure, fail-open/closed behavior, or runtime config affects production availability. Escalate to `delivery-release-gate` when deploy profiles, environment mutation, rollout sequence, rollback, or operator runbook matters. Escalate to `change-documentation-gate` when public/operator config, runbooks, or migration instructions change.

# Reference Loading Policy

Current mode is inline-only: this capability has no deep reference files today, so this `SKILL.md` contains the active runtime configuration and feature-flag policy.

If deep references are added later, load them only for L3+ work, public or operator-visible config changes, runtime behavior switches, feature-flag lifecycle risk, invariant bypass, security-sensitive defaults, graph variant mapping, rollout/rollback impact, validation freshness, or stale cleanup debt.

Do not load deep references for L1/L2 local config edits where the inline output contract for schema, default, validation, owner, expiry, cleanup, observability, and test matrix can be satisfied.

# Critical Details

- Build-time config is baked into artifacts; deploy-time config changes with environment; runtime config can change without deploy and needs current-state reporting and audit.
- Config precedence must name the winner across code default, file, env var, CLI flag, remote config, tenant override, user override, experiment assignment, and emergency operator override.
- Tenant, user, and experiment-level config needs targeting, auditability, exposure logging, precedence, and isolation boundaries.
- Defaults should be safe for production and explicit for tests; test convenience cannot become production behavior.
- Hot reload requires atomic update, validation before apply, coherent version publication, rollback to last good value, and metric/log visibility.
- Feature flags need type: release, ops, experiment, permission, migration, kill switch, compatibility, or temporary shortcut.
- Flags need owner, creation reason, expiry/removal date or condition, cleanup issue, old/new path tests, and telemetry for exposure and branch usage.
- Mode/kind switches require bounded enum, explicit semantics, rejected-value behavior, and rejection of unrelated strategies under one parameter.
- Config-driven dependency wiring needs a graph variant matrix and construction-time fail-fast behavior.
- Config secrets belong in secret stores or secret config boundaries, not ordinary observable config, docs, frontend bundles, logs, traces, or generated artifacts.
- Validation must include invalid value, missing value, default value, precedence conflict, and representative variant combinations where behavior changes.
- Observability should expose safe config identifiers, version, owner, and current effective state without leaking secrets or tenant/user private data.

# Failure Modes

- Permanent feature flag with no owner, removal condition, telemetry, or cleanup issue.
- Boolean flag bypasses permission, validation, transaction, tenant isolation, audit, or domain invariant.
- Invalid config starts successfully and fails later under traffic.
- Mode parameter grows into a hidden strategy registry with unclear ownership.
- Hot reload applies partially and leaves mixed behavior across workers, threads, tenants, or requests.
- Default points to production dependency in tests or unsafe development behavior in production.
- Security-sensitive default fails open when the key is missing.
- Config precedence is undocumented, so tenant, user, experiment, env, and operator values fight silently.
- Config-driven dependency graph changes without affected test or rollback mapping.
- Validation covers only the happy default and misses invalid, missing, stale, or conflicting values.
- Config change has no test matrix, rollout path, rollback path, observability, or cleanup path.

# Output Contract

Return a `configuration_policy` with:
- `scope_and_source`: config keys, behavior controlled, source of truth, precedence, owner, and environments/tenants/users/experiments in scope.
- `schema_and_defaults`: type, allowed values, rejected values, default, fail-open/fail-closed posture, and security/domain invariant impact.
- `validation_behavior`: validation point, fail-fast or safe-degrade behavior, invalid/missing/conflicting value handling, and hot-reload atomicity.
- `runtime_switch_rationale`: why configurability is needed, alternatives rejected, bounded lifetime, and non-configurable invariants.
- `flag_lifecycle`: flag type, owner, creation reason, expiry/removal condition, cleanup issue, telemetry, and old/new path tests.
- `mode_kind_governance`: enum semantics, graph variant matrix, rejected strategy drift, dependency-wiring impact, and test coverage.
- `security_and_secret_boundary`: secret separation, frontend/public exposure boundary, sensitive defaults, redaction needs, and security gate result.
- `observability_and_audit`: effective-state reporting, safe fields, metrics/logs/traces, audit trail, alerts, and operator runbook link or rationale.
- `rollout_rollback_cleanup`: rollout path, kill-switch behavior, rollback value/procedure, cleanup owner/date, and deletion trigger.
- `graph_memory_execution_validation`: repository graph edges inspected, memory claims accepted/rejected, trajectory freshness, validator map, and evidence limits.
- `residual_config_risk`: remaining uncertainty, skipped variants, unsupported evidence, rollback note, and next owner.

# Evidence Contract

Close the policy only when these answers are concrete:
- **Basis:** config key or switch, behavior controlled, owner, source of truth, and reason configurability is justified.
- **Safety:** schema, defaults, validation point, fail-fast/safe-degrade behavior, invariant preservation, and secret/security boundary.
- **Lifecycle:** flag type, expiry/removal condition, cleanup issue, telemetry, rollout, rollback, and deletion trigger.
- **Graph and memory:** config-driven graph variants, affected paths/tests, current-source proof, accepted/rejected memory claims, and stale-context limits.
- **Execution and validation:** command order, validation freshness, test matrix, skipped combinations, negative evidence, and residual risk.
- **Closure:** rollback note, cleanup owner, documentation/operator impact, validation command or review artifact, and next gate.

# Benchmark Coverage

This capability covers typed config schemas, safe defaults, feature flag governance, kill switches, progressive rollout, hot reload, tenant/user/experiment targeting, config precedence, mode/kind strategy drift, config-driven graph variation, stale flag cleanup, secret separation handoff, graph-memory-trajectory reconciliation, validation matrix selection, and evidence-limited handoff.

# Routing Coverage

Routes from `change-forge-router`, `delivery-release-gate`, `backend-change-builder`, `frontend-change-builder`, `integration-change-builder`, `reliability-observability-gate`, `architecture-impact-reviewer`, `change-documentation-gate`, `quality-test-gate`, and `ai-code-review-refactor` should arrive here when runtime variability, feature flags, kill switches, mode/kind switches, config defaults, validation, rollout/rollback, or cleanup lifecycle are at issue. Route away when the primary concern is secret storage, dependency graph construction, deletion proof, implementation placement, strategy abstraction, release execution, or operational incident response.

# Quality Gate

1. Config scope, source of truth, precedence, owner, and environments are named.
2. Config is typed, bounded, and validated before behavior uses it.
3. Defaults are explicit, production-safe, and security/privacy/domain sensitive defaults fail closed unless reviewed otherwise.
4. Invalid, missing, stale, and conflicting config behavior is defined.
5. Runtime switches do not bypass domain, security, permission, tenant, data integrity, transaction, audit, or compliance invariants.
6. Feature flag owner, type, reason, expiry/removal condition, cleanup issue, telemetry, and old/new path tests are recorded.
7. Mode/kind/provider switches remain bounded and do not become hidden strategy systems.
8. Hot reload is atomic, observable, versioned, and rollback-capable.
9. Config-driven dependency or behavior variants have graph mapping and representative test coverage.
10. Test matrix covers defaults, invalid values, missing values, precedence conflicts, and behavior-changing variants.
11. Rollout, rollback, kill-switch, and cleanup paths are explicit.
12. Secret and security-sensitive configuration boundaries are routed to the correct gate.
13. Graph, memory, execution trajectory, and validation freshness are reconciled before closure.

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
