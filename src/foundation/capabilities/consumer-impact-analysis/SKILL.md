---
name: consumer-impact-analysis
description: Analyzes known and unknown consumers of API, SDK, schema, event, package, CLI, and public export changes, including compatibility, migration, deprecation, telemetry, rollout, and rollback.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "115"
changeforge_version: 0.1.0
---

# Mission

Prevent accidental downstream breakage by identifying every known, generated, inferred, and unknown consumer of a changed public contract, then tying compatibility, migration, telemetry, rollout, rollback, and validation evidence to the actual consumer graph instead of a local provider-only diff.

# When To Use

Use when changing API fields, request or response semantics, error codes, pagination, filters, SDK or public package exports, generated clients, schemas, event payloads, webhooks, CLI machine output, configuration contracts, public module exports, plugin interfaces, examples, fixtures, or documentation that consumers may treat as contract.

Use when consumers are unknown, mobile/web/backend clients may lag, partners cannot update atomically, generated clients need regeneration, telemetry must prove migration, or repository graph, project memory, or prior execution claims about consumers may be stale.

# Do Not Use When

Do not use for private implementation changes with no public, package, schema, event, CLI, generated, config, documentation, or observable behavior contract impact.

Do not use as a substitute for designing the contract itself. Pair with the relevant API, schema, SDK, event, versioning, contract-testing, documentation, release, or mobile capability when that decision owns the primary risk.

# Stage Fit

Use during planning before the contract shape is finalized, during implementation review when diffs touch public surfaces, during release preparation when migration and telemetry gates decide rollout, and during cleanup when deprecated branches are removed. Re-enter after generated artifacts, docs, examples, schema registry entries, package exports, client versions, project memory, or repository graph evidence changes.

# Non-Negotiable Rules

- **Consumer inventory is evidence, not optimism.** Name known consumers, generated consumers, inferred consumers, omitted search areas, and unknown-consumer risk before approving a consumer-visible change.
- **Local caller search is not proof of no consumers.** Repository search must be paired with graph scope, generated artifacts, docs/examples, telemetry, registries, package/export metadata, and explicit evidence limits.
- **Breaking changes require a bridge, version, deprecation window, or no-ship decision.** Approval without a compatibility path is not a migration plan.
- **Generated clients and SDKs are first-class consumers.** Regenerate, diff, compile, and classify semver/package impact instead of treating generated code as incidental output.
- **Events and webhooks preserve old consumers.** Payload changes require schema compatibility mode, upcaster/adapter/versioning, replay behavior, and consumer fixture proof.
- **Telemetry gates removal.** Calendar dates and changelog entries do not prove migration; old/new usage, SDK version, endpoint version, event schema version, and error-rate telemetry must drive removal decisions where possible.
- **Rollout and rollback must handle mixed consumers.** Old clients, new clients, old producers, new producers, generated clients, queue retention, and immediate rollback after new writes must remain explainable.
- **Memory, graph, and trajectory claims must be refreshed.** Prior "no consumer" findings, old generated-client checks, and earlier validation passes are selectors until current source, graph, and command order confirm freshness.

# Mode Matrix

| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities | Skip by default |
| --- | --- | --- | --- | --- | --- |
| API/DTO consumer impact | Endpoint, field, validation, default, error, pagination, filter, or response semantic changes. | Known/unknown callers, generated clients, old/new behavior, migration. | API/schema diff, consumer inventory, compatibility class, contract tests. | `api-contract-design`, `dto-schema-design`, `version-compatibility`, `contract-testing` | Provider-only unit tests. |
| SDK/package/export impact | Public export, generated SDK, package surface, examples, runtime floor, or semver changes. | Source/binary/package compatibility and downstream build risk. | API diff, package semver, generated diff, examples, downstream smoke. | `sdk-library-contract-design`, `package-dependency-management` | Patch/minor assumption. |
| Event/webhook/schema impact | Event name, topic, payload, ordering, schema registry, webhook body, or replay semantics change. | Old consumers, retained messages, schema mode, upcaster/versioning. | Schema diff, registry mode, fixture replay, consumer list, rollback. | `domain-event-modeling`, `event-driven-architecture`, `contract-testing` | Producer-only proof. |
| CLI/config/machine output impact | CLI JSON/YAML/TSV, config key/default, plugin contract, or public automation output changes. | Scriptability, rolling config compatibility, parse stability. | Old/new output examples, config bridge, caller search, telemetry or residual risk. | `cli-daemon-interface-design`, `configuration-runtime-policy` | Human-output-only review. |
| Unknown consumer discovery | "Internal only", "no callers", public package/API, stale memory, dynamic references, or weak graph. | Treat absence of evidence as risk and bound search confidence. | Searched paths, graph edges, omitted areas, telemetry, owner for unknowns. | `repository-graph-analysis`, `project-memory-governance` | Certifying no consumers. |
| Deprecation/removal readiness | Compatibility branch, deprecated field, v1 endpoint, old event, or public export removal. | Telemetry-backed removal and rollback safety. | Usage threshold, window, notification, migration docs, rollback state. | `cleanup-deletion-governance`, `delivery-release-gate`, `change-documentation-gate` | Date-only removal. |

# Industry Benchmarks

Anchor against semantic versioning, API compatibility management, consumer-driven contract testing, OpenAPI/AsyncAPI/Protobuf breaking-change detection, schema registry BACKWARD/FORWARD/FULL compatibility, RFC 8594 Sunset signaling, expand/contract rollout, generated client governance, package API diffing, telemetry-based deprecation, and mobile/partner client lag management. Keep this body focused on routing, evidence, and gates; add deep references only if the benchmark matrices exceed the inline output contract.

# Selection Rules

Select this capability when the main risk is **who consumes the changed contract and how they migrate safely**. Use `version-compatibility` when compatibility mechanics across old/new producers and consumers dominate, `api-contract-design` or `dto-schema-design` when shape design dominates, `sdk-library-contract-design` when package/public type governance dominates, `domain-event-modeling` when event fact semantics dominate, `contract-testing` when executable proof dominates, `change-documentation-gate` when migration docs dominate, and `delivery-release-gate` when release clearance dominates.

# Proactive Professional Triggers

- **Signal:** A field, enum, error code, endpoint, event payload, CLI output, config key, package export, or generated client changes without consumer inventory. **Hidden risk:** local provider tests pass while deployed clients, jobs, dashboards, partners, or generated SDKs fail. **Required professional action:** build consumer inventory and unknown-consumer risk. **Route to:** `version-compatibility`, `repository-graph-analysis`. **Evidence required:** changed surface, searched paths, known/generated/inferred consumers, omitted areas, owner.
- **Signal:** A contract is called "internal only" or "no callers" based on local search, memory, or team assertion. **Hidden risk:** dynamic references, docs/examples, scripts, packages, event subscribers, mobile apps, or partners are outside the search. **Required professional action:** downgrade to unknown-consumer risk until graph, telemetry, registry, and owner evidence are reconciled. **Route to:** `project-memory-governance`, `repository-graph-analysis`. **Evidence required:** accepted/rejected memory, graph freshness, telemetry availability, residual risk.
- **Signal:** Generated clients, SDKs, examples, public exports, or package metadata change after the source contract changes. **Hidden risk:** generated or packaged consumers drift from the provider contract. **Required professional action:** regenerate/diff/compile or record why unavailable. **Route to:** `sdk-library-contract-design`, `contract-testing`. **Evidence required:** source spec hash, generator/config, public API diff, downstream smoke or compile result.
- **Signal:** A deprecation, compatibility branch, fallback, old endpoint, old field, or v1 event is scheduled for removal. **Hidden risk:** undiscovered consumers break after cleanup. **Required professional action:** require telemetry zero-use threshold, notification, removal owner, rollback, and cleanup gate. **Route to:** `cleanup-deletion-governance`, `change-documentation-gate`. **Evidence required:** usage metric, window, migration guide, rollback path, retained residual risk.
- **Signal:** A release plan assumes all consumers upgrade with the producer. **Hidden risk:** mobile, partner, queue, batch, dashboard, and multi-service consumers lag. **Required professional action:** model mixed-version rollout and immediate rollback. **Route to:** `delivery-release-gate`, `mobile-product-extension` when mobile matters. **Evidence required:** client/version lag, deployment order, old/new behavior, rollback state.
- **Signal:** Prior validation, report, or execution trajectory is reused after contract, generated artifact, registry, or docs changed. **Hidden risk:** stale proof closes a different diff. **Required professional action:** rerun mapped validators or mark evidence stale/partial. **Route to:** `execution-trajectory-analysis`, `validation-broker`. **Evidence required:** command order, later edits, freshness verdict, changed consumer-to-validation map.

# Risk Escalation Rules

Escalate to `data-api-contract-changer` when API, DTO, schema, event, webhook, config, or public export compatibility changes. Escalate to `delivery-release-gate` when rollout, rollback, deprecation, or generated artifact publication requires coordinated deployment. Escalate to `mobile-product-extension` when mobile release lag or app-store adoption controls the compatibility window. Escalate to `architecture-impact-reviewer` when public exports define module boundaries. Escalate to `security-privacy-gate` when changed contracts expose sensitive fields, tenant scope, auth behavior, or generated clients that can leak data. Escalate to `quality-test-gate` when consumer proof is missing or stale.

# Reference Loading Policy

Current mode is inline-only: the `SKILL.md` body carries L1/L2 routing, consumer inventory, graph/memory/trajectory coupling, output contract, evidence contract, and quality gate rules. There are no deep references today.

If deep references are added later, load them only for L3+ public API/SDK/schema/event/export changes, generated-client impact, unknown consumers, compatibility migrations, telemetry gates, deprecation/removal, rollout, rollback, or when the output contract cannot be completed from inline rules.

Do not load deep references for private changes where no public, package, schema, event, CLI, config, generated, documentation, or observable behavior contract is affected and the inline output contract is enough.

# Critical Details

- Current consumers include web clients, mobile apps, backend services, SDK users, partner integrations, dashboards, analytics jobs, batch jobs, scripts, examples, generated clients, tests/fixtures, and documentation users.
- Unknown consumers include public APIs, published packages, event streams, webhooks, CLI machine output parsed by scripts, public exports, plugin points, docs copied into external systems, and internal exports outside search scope.
- Consumer inventory should classify direct, generated, inferred, telemetry-observed, memory-suggested, graph-selected, owner-confirmed, and unknown consumers separately.
- Compatibility mechanisms include additive field, alias, dual-read, dual-write, adapter, upcaster, versioned endpoint/topic, deprecation/Sunset header, feature flag, config bridge, compatibility branch, or explicit no-ship.
- Consumer telemetry should measure old/new field usage, endpoint version, SDK/package version, user agent/app version, event schema version, CLI output mode, deprecation response, and error rate.
- Migration guidance states old contract, new contract, affected consumers, examples, timeline, deprecation signals, validation commands, rollback behavior, and residual risk owner.
- Rollback must not strand consumers on a contract no longer served or on data/events written in a shape old consumers cannot read.
- Search, graph, memory, telemetry, generated diff, and validation evidence each prove different things; none should be overclaimed as full consumer certainty.

# Failure Modes

- API field renamed and only server unit tests updated; generated TypeScript and mobile clients fail at runtime.
- Event payload field removed without schema version, upcaster, replay fixture, or subscriber inventory.
- SDK regenerated from a changed spec but package semver, examples, public export diff, and downstream build matrix are skipped.
- "No consumers" is concluded from `rg` while docs, dashboards, dynamic calls, package users, and event subscribers are outside scope.
- Producer deploys before old consumers can read the new schema; queue retention then replays unreadable messages.
- Compatibility branch removed because the calendar window elapsed, even though telemetry still shows old usage.
- Project memory says migration completed, but a later generated client or docs change invalidated the previous validation.
- Rollback restores old producer while new consumers depend on a contract introduced only in the failed release.

# Output Contract

Return a `consumer_impact_report` with:

- `mode_selected` (API/DTO, SDK/package/export, event/webhook/schema, CLI/config/output, unknown-consumer discovery, or deprecation/removal readiness).
- `source_evidence` (current contract files, specs, schemas, generated artifacts, package metadata, docs/examples, tests/fixtures, telemetry, registries, repository graph, project memory, execution trajectory, and skipped boundaries with reason).
- `graph_memory_trajectory_judgment` (accepted, rejected, stale, or not verified for caller search, consumer inventory, old validation, generated clients, telemetry, migration status, and rollout assumptions).
- `changed_contract` (endpoint, field, event, schema, package export, SDK method, CLI output, config key, public export, docs/example contract, or observable behavior).
- `consumer_inventory` (known direct consumers, generated clients, mobile/partner/public clients, backend services, event subscribers, jobs/reports/dashboards, docs/examples, inferred consumers, and unknown-consumer risk).
- `compatibility_assessment` (change class, old/new consumer behavior, mixed-version behavior, generated-client impact, semver/versioning impact, and breaking-change approval if needed).
- `migration_deprecation_plan` (bridge/version/upcaster/adapter/dual-read-write, migration guide, notification, deprecation/Sunset signals, window, telemetry threshold, and removal criteria).
- `rollout_and_rollback` (deployment order, feature/config flags, queue/replay concerns, immediate rollback state, retained compatibility branch, and cleanup owner).
- `validation_plan` (schema/API/export diff, generated-client regeneration and compile, consumer-driven contract tests, fixture replay, downstream smoke, telemetry check, manual owner review, or named residual risk).
- `changed_consumer_to_validation_map` (each changed surface and consumer class mapped to contract proof, generated-client proof, telemetry, docs, release gate, owner review, or residual risk).
- `documentation_updates` (migration guide, changelog/release notes, API docs, SDK examples, deprecation headers, owner notification).
- `handoff_boundaries` (what belongs to version compatibility, API/DTO design, SDK design, event design, contract testing, documentation, release, security, mobile, or cleanup).
- `evidence_limits` and `residual_consumer_risk` (unknown consumers, missing telemetry, untested generated client, stale graph/memory/trajectory, absent owner, or unproven rollback with owner and next gate).

# Evidence Contract

Close the report only when these answers are concrete:

- **Basis:** selected mode, changed contract surface, consumer-visible risk, and why consumer inventory changes the implementation, release, validation, or documentation path.
- **Current evidence:** source/spec/schema/export/generated/docs/test/telemetry/registry evidence inspected, search scope, graph edges, project-memory signals, execution-order freshness, and skipped boundaries.
- **Consumer and compatibility judgment:** known/generated/inferred/unknown consumers, compatibility classification, generated-client and semver impact, migration/deprecation strategy, rollout/rollback behavior, and approval state for breaking changes.
- **Validation mapping:** every changed surface, consumer class, migration phase, telemetry gate, generated artifact, doc update, rollback path, and cleanup criterion maps to executable proof, owner review, or named residual risk.
- **Evidence limits and handoff:** what search, graph, memory, telemetry, contract tests, generated-client checks, and manual review prove; what they do not prove; residual risk owner; rollback note; and next gate.

# Benchmark Coverage

This capability covers consumer inventory, unknown-consumer risk, semantic versioning, generated-client governance, OpenAPI/AsyncAPI/Protobuf/schema diffing, consumer-driven contract evidence, event schema evolution, deprecation/Sunset signaling, telemetry-gated removal, mixed-version rollout, mobile/partner lag, graph/memory/trajectory freshness, and changed-consumer-to-validation mapping without loading a broad repository context.

# Routing Coverage

Routes from `data-api-contract-changer`, `integration-change-builder`, `frontend-change-builder`, `backend-change-builder`, `architecture-impact-reviewer`, `change-documentation-gate`, `quality-test-gate`, and `ai-code-review-refactor` should arrive here when downstream consumer inventory, generated client impact, compatibility migration, unknown consumers, telemetry-gated deprecation, or public export effects are primary. Route away when the unresolved decision is target contract shape, compatibility mechanics, executable contract implementation, release approval, documentation writing, security/privacy exposure, mobile platform policy, or cleanup execution.

# Quality Gate

The consumer impact report is complete only when:

1. Selected mode, changed public contract, and source evidence are explicit.
2. Known direct, generated, inferred, mobile/partner/public, event, job/report/dashboard, docs/example, and unknown consumers are assessed.
3. Search scope, repository graph confidence, project-memory reuse, execution trajectory freshness, and omitted boundaries are recorded.
4. Compatibility strategy is explicit for old consumers, new consumers, generated clients, and mixed-version rollout.
5. Breaking changes have bridge, versioning, upcaster/adapter, deprecation window, explicit approval, or no-ship decision.
6. Generated clients, SDKs, package exports, examples, and semver/versioning impact are handled or named as residual risk.
7. Migration and deprecation path exists for consumer-visible or breaking changes.
8. Telemetry covers old/new usage where possible, or its absence is owned as residual risk.
9. Rollout and rollback handle lagging consumers and immediate rollback after new writes or events.
10. Contract tests, schema/API/export diffs, generated-client compile, fixture replay, downstream smoke, telemetry check, or owner review map to each changed surface.
11. Documentation and notification updates are named when consumers need action.
12. Handoff boundaries, evidence limits, residual consumer risk, and next gate are explicit so consumer-impact evidence is not overclaimed as full contract design, release approval, or cleanup completion.

# Used By

- data-api-contract-changer
- integration-change-builder
- frontend-change-builder
- backend-change-builder
- architecture-impact-reviewer
- change-documentation-gate
- quality-test-gate
- ai-code-review-refactor

# Handoff

Hand off to `version-compatibility`, `contract-testing`, `sdk-library-contract-design`, `api-contract-design`, `domain-event-modeling`, `delivery-release-gate`, and `change-documentation-gate` for the relevant contract surface.

# Completion Criteria

The capability is complete when consumer inventory or unknown-consumer risk, compatibility mechanism, migration/deprecation plan, telemetry, rollout/rollback path, contract tests, and residual risk are explicit.
