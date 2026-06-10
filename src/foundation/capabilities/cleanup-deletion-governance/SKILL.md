---
name: cleanup-deletion-governance
description: Governs deletion of dead code, stale feature flags, fallbacks, compatibility branches, deprecated APIs, expand-contract remnants, generated artifacts, and cleanup issues with caller search, telemetry, rollback, and owner evidence.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "116"
changeforge_version: 0.1.0
---

# Mission

Make deletion as intentional as addition by defining when obsolete code can be removed, what evidence proves it is unused, who owns cleanup, and how rollback works after removal.

# When To Use

Use when removing or planning removal of dead code, feature flags, fallback paths, compatibility branches, deprecated APIs, generated files, unused exports, old migrations, expand/contract temporary code, duplicate adapters, or stale configuration.

Use when new temporary behavior is introduced and needs an owner, expiry, telemetry, or cleanup issue.

# Do Not Use When

Do not use to delete code based only on intuition, line count, local tests, or absence of obvious callers.

Do not use to remove public contracts before consumer impact and compatibility are resolved.

# Non-Negotiable Rules

- Deletion path is required for temporary flags, fallbacks, compatibility branches, and deprecated APIs.
- Caller search must include runtime, generated, reflection, configuration, script, and documentation references where relevant.
- Telemetry or release evidence must prove unused behavior when production consumers are possible.
- Feature flag removal deletes both old and new dead branches as appropriate.
- Fallback expiry and compatibility branch owner are explicit.
- Deprecated API removal requires consumer impact review.
- Rollback after deletion is planned.
- Cleanup issue tracking exists when deletion cannot happen in the current change.

# Industry Benchmarks

Anchor against expand/contract cleanup, deprecation policy, feature flag lifecycle, dead-code detection, semantic versioning, telemetry-based removal, migration cleanup, and rollback planning.

# Selection Rules

Select this capability when cleanup or deletion is the main risk. Use `refactoring` for behavior-preserving movement, `consumer-impact-analysis` for public contract removal, `configuration-runtime-policy` for stale flags, `architecture-enforcement-tooling` for dead-code/import checks, and `delivery-release-gate` for rollout.

# Risk Escalation Rules

Escalate to `data-api-contract-changer` when deleting API, schema, event, or generated client surface. Escalate to `security-privacy-gate` when cleanup removes security fallback or changes access paths. Escalate to `reliability-observability-gate` when fallback deletion changes degraded-mode behavior.

# Critical Details

- Caller search includes static references, generated references, config values, reflection/registration, templates, migrations, scripts, docs, dashboards, alerts, and external consumers.
- Runtime evidence can include logs, metrics, event schema version, endpoint usage, flag exposure, SDK version, or package download data.
- Removal condition states what must be true before deletion.
- Rollback path may be revert, re-enable flag, redeploy compatibility branch, restore schema field, or forward-fix.
- Expand/contract cleanup removes dual-write, dual-read, aliases, upcasters, temporary columns, and compatibility adapters only after old path is unused.
- Cleanup issues need owner, due date, trigger condition, and validation command.

# Failure Modes

- Feature flag remains forever after rollout.
- Compatibility branch stays without owner and accumulates bugs.
- Fallback path hides production failures and is never removed.
- Dead code deletion misses reflection, generated client, cron, CLI, or config reference.
- Deprecated API is removed without telemetry or migration notice.
- Expand/contract migration leaves dual-write code permanently.
- Rollback after deletion is impossible because state or schema was removed first.

# Output Contract

Return a Cleanup / Deletion Plan:

- Target artifact.
- Owner.
- Removal condition.
- Callers searched.
- Runtime/generated/reflection/config references searched.
- Telemetry evidence.
- Feature flag, fallback, compatibility, or deprecated API lifecycle.
- Tests.
- Rollback path.
- Cleanup issue tracking.
- Residual deletion risk.

# Evidence Contract

Close the plan only when caller searches, telemetry or explicit no-telemetry rationale, consumer impact for public contracts, tests, rollback path, owner, cleanup issue, evidence limits, and residual deletion risk are recorded.

# Quality Gate

1. Target artifact and owner are named.
2. Removal condition is explicit.
3. Static, runtime, generated, reflection, config, and script callers are searched where relevant.
4. Telemetry or release evidence proves unused behavior when consumers are possible.
5. Public contract deletion has consumer impact review.
6. Tests cover remaining behavior and absence of obsolete path.
7. Rollback path exists.
8. Deferred cleanup has issue owner and date.

# Used By

- ai-code-review-refactor
- refactoring
- backend-change-builder
- frontend-change-builder
- data-api-contract-changer
- architecture-impact-reviewer
- delivery-release-gate
- change-documentation-gate
- quality-test-gate

# Handoff

Hand off to `refactoring` for behavior-preserving deletion, `consumer-impact-analysis` for public contracts, `configuration-runtime-policy` for flag cleanup, `architecture-enforcement-tooling` for static enforcement, and `delivery-release-gate` for coordinated rollout or rollback.

# Completion Criteria

The capability is complete when deletion has an owner, removal condition, caller and telemetry evidence, public consumer review where relevant, tests, rollback plan, cleanup tracking, and residual risk disclosure.
