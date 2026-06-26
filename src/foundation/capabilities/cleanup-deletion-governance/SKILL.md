---
name: cleanup-deletion-governance
description: Governs deletion of dead code, stale feature flags, fallbacks, compatibility branches, deprecated APIs, expand-contract remnants, generated artifacts, and cleanup issues with caller search, telemetry, rollback, and owner evidence.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "116"
changeforge_version: 0.1.0
---

# Mission

Make deletion as intentional as addition. Every obsolete flag, fallback, compatibility branch, generated artifact, deprecated contract, shortcut, scaffold, or dead code path needs proof that removal is safe, a named owner, current graph and consumer evidence, validation freshness, rollback mechanics, and a cleanup path that does not silently discard behavior users or systems still depend on.

# When To Use

- When removing or planning removal of dead code, feature flags, fallback paths, compatibility branches, deprecated APIs, generated files, unused exports, old migrations, expand/contract remnants, duplicate adapters, stale configuration, obsolete scripts, or temporary scaffolding.
- When adding temporary behavior that must later be removed: feature flag, fallback, compatibility bridge, dual-read/write, migration alias, adapter shim, deprecation path, temporary config, test bypass, or shortcut.
- When an intentional shortcut is accepted and needs a `changeforge-shortcut` ledger entry with a ceiling, owner, validation signal, review date, and upgrade or deletion trigger.
- When graph, memory, execution trajectory, audit report, or validation evidence suggests a deletion path is missing, stale, unsafe, or based only on local static tests.
- When cleanup affects public contracts, generated clients, config keys, scripts, runtime registration, reflection, docs, metrics, alerts, dashboards, or operator procedures.

# Do Not Use When

Do not use to delete code based only on intuition, line count, local tests, AI confidence, or absence of obvious static callers.

Do not use to remove public contracts before consumer impact, compatibility, migration, documentation, and release evidence are resolved.

Do not use to disguise a behavior change as cleanup; route behavior changes to the owner skill first, then return here for removal governance.

# Stage Fit

Use during implementation planning, refactoring, review, validation, release readiness, and final handoff whenever deletion, cleanup, deprecation, shortcut, or stale temporary behavior affects closure. Re-enter after graph refresh, memory signal, caller search, telemetry update, release status change, validation rerun, or repair that can make deletion evidence stale.

# Non-Negotiable Rules

- **Deletion path is designed at creation time:** temporary flags, fallbacks, compatibility branches, shortcuts, migration bridges, and deprecated APIs are incomplete without owner, expiry/removal trigger, validation signal, and cleanup issue.
- **No caller search, no deletion:** caller search must cover static imports, generated references, runtime registration, reflection, config values, scripts, migrations, templates, docs, dashboards, alerts, and known external consumers where relevant.
- **Runtime evidence beats local silence:** telemetry, release records, exposure metrics, logs, package/download data, API usage, event schema usage, or explicit no-telemetry rationale is required when production consumers are possible.
- **Public contracts require consumer impact review:** API, schema, event, SDK, CLI, config key, public export, metric, log field, or generated client removal must pass consumer impact and compatibility gates.
- **Flags remove branches, not just keys:** feature flag cleanup removes obsolete old/new branches, tests, config, metrics, docs, rollout notes, and dead references as appropriate.
- **Fallback and compatibility owners are explicit:** fallback expiry, compatibility branch owner, deprecation window, removal condition, and rollback path must be named.
- **Shortcut ledger is mandatory:** `changeforge-shortcut` or equivalent issue must name accepted scope, ceiling, owner, review date, validation, upgrade trigger, and conversion or deletion path.
- **Generated and runtime artifacts are source-traced:** generated files are not deleted without source generator mapping; runtime-registered paths are not deleted without registration evidence.
- **Rollback is feasible:** deletion rollback can be revert, re-enable flag, redeploy compatibility branch, restore schema/field, re-run generator, or forward fix, and must name state/data limits.
- **Memory is advisory:** prior cleanup incidents or stale notes can widen search, but current source, graph, telemetry, registry, and validation evidence decide closure.

# Industry Benchmarks

Anchor against expand/contract cleanup, deprecation policy, semantic versioning, feature flag lifecycle, dead-code detection, telemetry-based removal, migration cleanup, rollback planning, generated-artifact provenance, consumer compatibility management, incident learning, and audit-ready change evidence. Keep this capability focused on deletion safety and cleanup lifecycle; route behavior-preserving movement to `refactoring`, consumer risk to `consumer-impact-analysis`, and release execution to `delivery-release-gate`.

# Mode Matrix

| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities | Exit risk |
| --- | --- | --- | --- | --- | --- |
| Dead code or unused export | Unused function, class, file, export, adapter, helper, script, or config appears removable. | Caller proof across static, generated, runtime, and docs. | Same-pattern scan, references searched, generated/runtime checks, tests. | `architecture-enforcement-tooling`, `refactoring` | Static-only deletion breaks dynamic caller. |
| Feature flag cleanup | Rollout complete, stale flag, permanent boolean, old/new branch. | Remove key, branches, tests, metrics, docs, and rollout debt. | Owner, flag type, exposure/branch telemetry, removal trigger, old/new path tests. | `configuration-runtime-policy`, `quality-test-gate` | Flag remains as permanent architecture. |
| Fallback/degradation cleanup | Fallback, circuit breaker bypass, degraded path, emergency mitigation, kill switch. | Prove fallback is obsolete or bounded; preserve safe rollback. | Incident/release state, fail-open/closed risk, telemetry, re-enable path. | `degradation-circuit-breaking`, `reliability-observability-gate` | Cleanup removes last safe degraded mode. |
| Compatibility/deprecation cleanup | Deprecated API, old event/schema/SDK, compatibility branch, alias, upcaster. | Consumer migration and compatibility window. | Consumer list, usage threshold/window, migration docs, version policy, rollback. | `consumer-impact-analysis`, `data-api-contract-changer` | Unknown consumer breaks after removal. |
| Expand/contract cleanup | Dual-read/write, temporary column, alias, bridge, migration adapter. | Remove only after old path is unused and data is safe. | Backfill/migration state, telemetry, data retention, contract phase, tests. | `data-api-contract-changer`, `delivery-release-gate` | Rollback impossible after state removal. |
| Generated/runtime artifact cleanup | Generated client/file, registry entry, plugin asset, reflection registration, cron, CLI command. | Trace source-of-truth before deletion. | Generator source, rebuild command, registration search, package/install impact. | `repository-graph-analysis`, `validation-broker` | Generated drift or runtime registration failure. |
| Shortcut ledger cleanup | `changeforge-shortcut`, TODO accepted as shortcut, scaffold-for-later, wrapper-only delegation. | Bound shortcut or convert/delete. | Scope, ceiling, owner, review date, upgrade trigger, validation, residual risk. | `minimal-correct-implementation`, `agent-execution-discipline` | Shortcut becomes unowned debt. |

# Selection Rules

Select this capability when **cleanup or deletion safety** is the main risk: what can be removed, what proves it is unused, who owns the removal, what consumers or runtime paths may still depend on it, how rollback works, and how deferred cleanup is tracked.

Use `refactoring` for behavior-preserving movement before or instead of deletion. Use `consumer-impact-analysis` for public contract removal and unknown consumer risk. Use `configuration-runtime-policy` for stale flags and temporary config lifecycle. Use `architecture-enforcement-tooling` for dead-code/import enforcement and suppressions. Use `delivery-release-gate` for rollout, rollback, package/install, or environment execution. Use `repository-graph-analysis`, `project-memory-governance`, `execution-trajectory-analysis`, and `validation-broker` when graph edges, stale memory, command order, generated artifacts, or validation freshness affect the deletion claim.

# Proactive Professional Triggers

- **Signal:** Code, config, flag, fallback, adapter, or generated file is described as "unused", "dead", "legacy", "temporary", "old", or "safe to remove" with only local/static evidence. **Hidden risk:** dynamic, generated, scripted, or external caller still uses it. **Required professional action:** run bounded same-pattern and caller search before deletion. **Route to:** `repository-graph-analysis`, `validation-broker`. **Evidence required:** searched paths, reference classes, test/validation map, evidence limits.
- **Signal:** A new feature flag, fallback, compatibility branch, migration bridge, or shortcut is added without removal trigger. **Hidden risk:** temporary code becomes permanent design. **Required professional action:** create deletion path at addition time. **Route to:** `configuration-runtime-policy`, `minimal-correct-implementation`. **Evidence required:** owner, expiry/removal trigger, cleanup issue, validation signal.
- **Signal:** Deprecated API, event, schema, SDK, CLI command, config key, metric, log field, or public export is removed. **Hidden risk:** known or unknown consumers break despite local tests. **Required professional action:** require consumer impact and compatibility evidence. **Route to:** `consumer-impact-analysis`, `change-documentation-gate`. **Evidence required:** consumer search, usage threshold/window, migration docs, rollback.
- **Signal:** Expand/contract remnants, dual-write, dual-read, alias, upcaster, temporary column, or compatibility adapter are cleaned up. **Hidden risk:** state rollback or old-version consumers still require the old path. **Required professional action:** confirm migration phase, data safety, and rollback boundary. **Route to:** `data-api-contract-changer`, `delivery-release-gate`. **Evidence required:** migration state, telemetry, old-path usage, rollback limit.
- **Signal:** Cleanup removes fallback, degraded path, security fallback, bypass guard, emergency mitigation, or kill switch. **Hidden risk:** incident recovery or safety posture regresses. **Required professional action:** escalate reliability/security review and prove safe replacement or re-enable path. **Route to:** `reliability-observability-gate`, `security-privacy-gate`. **Evidence required:** safety analysis, telemetry, runbook, rollback.
- **Signal:** Memory or previous run claims a file is fragile, cleanup failed before, or a stale branch caused a defect. **Hidden risk:** stale memory overrules current source or misses new callers. **Required professional action:** reconcile memory with current graph, source, and validation order. **Route to:** `project-memory-governance`, `execution-trajectory-analysis`. **Evidence required:** accepted/rejected memory claim, current-source proof, validator freshness.
- **Signal:** Validation passes after deletion but no absence test, contract test, generated rebuild, or affected integration path is mapped. **Hidden risk:** tests did not exercise the removed path or generated artifact. **Required professional action:** map deletion to affected validators or disclose partial proof. **Route to:** `quality-test-gate`, `validation-broker`. **Evidence required:** deleted path map, commands, uncovered consumers, residual risk.

# Risk Escalation Rules

Escalate to `data-api-contract-changer` when deleting API, schema, event, migration, database field, generated client, or persistence contract. Escalate to `security-privacy-gate` when cleanup removes security fallback, auth guard, permission path, redaction, audit trail, encryption control, or access path. Escalate to `reliability-observability-gate` when fallback deletion changes degraded-mode behavior, incident mitigation, telemetry, alerting, or operational recovery. Escalate to `delivery-release-gate` when deletion requires staged rollout, package release, environment cleanup, config removal, or rollback coordination. Escalate to `change-documentation-gate` when public docs, migration guides, runbooks, deprecation notes, or changelog entries are needed.

# Critical Details

- Caller search includes static references, generated references, config values, reflection/registration, templates, migrations, scripts, cron, CLI commands, docs, dashboards, alerts, package manifests, and external consumers.
- Runtime evidence can include logs, metrics, event schema version, endpoint usage, flag exposure, SDK version, package download data, support ticket references, or release notes.
- Removal condition states what must be true before deletion, who confirms it, what time window or threshold applies, and what evidence expires.
- Rollback path may be revert, re-enable flag, redeploy compatibility branch, restore schema field, re-run generator, republish package, or forward-fix; state/data loss limits must be explicit.
- Expand/contract cleanup removes dual-write, dual-read, aliases, upcasters, temporary columns, generated clients, and compatibility adapters only after old path and old data shape are unused.
- Cleanup issues need owner, due date/review date, trigger condition, validation command, impacted artifact, and closure evidence.
- Shortcut ledgers need owner, accepted scope, ceiling, upgrade trigger, expiry or review date, validation command, and conversion/deletion path. A shortcut without those fields is stale debt.
- Generated artifacts require source-of-truth and rebuild command evidence; deleting generated output alone is not cleanup.
- Documentation and operator runbooks are part of cleanup when public or operational behavior changes.
- Absence tests should prove remaining behavior works without the old branch, not only that the old file disappeared.

# Failure Modes

- Feature flag remains forever after rollout, preserving old and new behavior in the same function.
- Compatibility branch stays without owner and accumulates bugs.
- Fallback path hides production failures and is never removed, or is removed before a safe degraded path exists.
- Dead code deletion misses reflection, generated client, cron, CLI, script, config, or documentation reference.
- Deprecated API is removed without telemetry, migration notice, or unknown-consumer residual risk.
- Expand/contract migration leaves dual-write code permanently, or deletes old state before rollback is impossible.
- Generated artifact is deleted without changing the generator, so build restores stale output or package/install validation fails.
- Cleanup removes a metric, alert, or log field used by operators or external automation.
- Shortcut comment remains after the ceiling is exceeded because no `changeforge-shortcut` ledger, trigger, or owner exists.
- Validation passes only default unit tests while integration, contract, generated rebuild, or public consumer paths remain untested.

# Reference Loading Policy

Current mode is inline-only: this capability has no deep reference files today, so this `SKILL.md` contains the active cleanup and deletion governance rules.

If deep references are added later, load them only for L3+ work, public or runtime deletion, stale flags/fallbacks/deprecated APIs, generated/reflection references, telemetry-driven removal, rollback-sensitive cleanup, expand/contract cleanup, shortcut ledger review, or validation freshness disputes.

Do not load deep references for L1/L2 local deletions where caller search, owner, removal condition, tests, rollback risk, and residual risk can be handled from the inline output contract.

# Output Contract

Return a `cleanup_deletion_plan` with:
- `target_artifact`: file/function/export/config/flag/API/schema/event/script/generated artifact, owner, source-of-truth, and why removal is proposed.
- `deletion_mode`: dead code, flag cleanup, fallback cleanup, compatibility/deprecation cleanup, expand/contract cleanup, generated/runtime artifact cleanup, or shortcut ledger cleanup.
- `removal_condition`: threshold/window, release state, telemetry condition, migration state, owner confirmation, and evidence expiry.
- `caller_and_graph_search`: static callers, generated references, runtime registration, reflection, config, scripts, docs, dashboards, alerts, package/install paths, and skipped search rationale.
- `runtime_and_consumer_evidence`: telemetry, logs, exposure metrics, endpoint/event/package usage, public consumer impact, no-telemetry rationale, and residual unknown consumers.
- `lifecycle_cleanup`: flag/fallback/compatibility/deprecation/shortcut state, cleanup issue, owner, review date, removal trigger, and old/new branch deletion.
- `validation_plan`: tests for remaining behavior, absence of obsolete path, contract/generation/build/install checks, command list, freshness, and evidence limits.
- `rollback_plan`: revert/re-enable/restore/redeploy/regenerate/forward-fix path, state/data limits, and who owns rollback.
- `documentation_and_release`: docs, migration guide, runbook, changelog, release note, operator notice, or explicit no-doc rationale.
- `graph_memory_execution_validation`: repository graph freshness, accepted/rejected memory signals, execution order, negative evidence, validator map, and residual deletion risk.

# Evidence Contract

Close the plan only when these answers are concrete:
- **Basis:** target artifact, owner, cleanup reason, deletion mode, and removal condition.
- **Search:** static, runtime, generated, reflection, config, scripts, docs, telemetry, and external consumer boundaries inspected or explicitly ruled out.
- **Safety:** public consumer impact, data/state rollback limits, fallback/degraded-mode risk, security/auth implications, and generated-source provenance.
- **Lifecycle:** cleanup issue, owner, due/review date, shortcut ceiling/upgrade trigger when applicable, and old/new branch removal plan.
- **Validation:** tests, contract checks, generated rebuilds, package/install checks, command outcomes, freshness, skipped coverage, and negative evidence.
- **Closure:** rollback note, documentation/release impact, evidence limits, residual risk, and next gate or owner.

# Benchmark Coverage

This capability covers deletion-path design, feature flag cleanup, stale fallback removal, compatibility/deprecation cleanup, expand/contract contraction, generated-artifact provenance, runtime/reflection/config caller search, telemetry-based unused proof, shortcut ledger governance, graph-memory-trajectory reconciliation, validation freshness, rollback readiness, and evidence-limited handoff.

# Routing Coverage

Routes from `change-forge-router`, `ai-code-review-refactor`, `backend-change-builder`, `frontend-change-builder`, `data-api-contract-changer`, `architecture-impact-reviewer`, `delivery-release-gate`, `change-documentation-gate`, `quality-test-gate`, `minimal-correct-implementation`, `refactoring`, and `code-clarity-maintainability` should arrive here when deletion path, stale flag, stale compatibility branch, deprecated surface, cleanup issue, dead code, shortcut ledger, fallback expiry, or unused configuration is at issue. Route away when the primary concern is behavior-preserving movement, public consumer analysis, runtime config policy, architecture enforcement rule design, or release execution without deletion proof.

# Quality Gate

1. Target artifact, deletion mode, source-of-truth, and owner are named.
2. Removal condition, threshold/window, and evidence expiry are explicit.
3. Static, runtime, generated, reflection, config, script, docs, dashboard, alert, package, and external caller searches are performed where relevant.
4. Telemetry, release evidence, or explicit no-telemetry rationale supports unused behavior when consumers are possible.
5. Public contract deletion has consumer impact, compatibility, migration, and documentation review.
6. Feature flag cleanup removes obsolete keys, branches, tests, metrics, docs, and rollout debt as appropriate.
7. Fallback, degraded-mode, security, and compatibility cleanup preserve or replace safe rollback behavior.
8. Generated artifacts map to source generator and rebuild/package/install validation before closure.
9. Tests cover remaining behavior and absence of obsolete path.
10. Rollback path exists and names state/data limitations.
11. Deferred cleanup has issue owner, due/review date, trigger condition, and validation signal.
12. Intentional shortcuts have a `changeforge-shortcut` ledger or equivalent issue with ceiling, upgrade trigger, owner, review date, and validation signal.
13. Graph, memory, execution trajectory, validation freshness, negative evidence, and residual deletion risk are reconciled before handoff.

# Used By

- ai-code-review-refactor
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
