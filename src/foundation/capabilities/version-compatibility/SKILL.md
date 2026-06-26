---
name: version-compatibility
description: Evaluates API, schema, event, configuration, and behavior compatibility with versioning, staged rollout, and bridge rules for breaking changes.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "29"
changeforge_version: 0.1.0
---

# Mission

**Evaluate compatibility across every contract surface — APIs, schemas, events, configuration, stored data, and observable behavior — so that old producers can talk to new consumers, new producers can talk to old consumers, rollbacks do not corrupt data, and mixed-version deployments during staged rollout remain safe**, by classifying every proposed change as backward-compatible, forward-compatible, or breaking, and by enforcing that breaking changes follow an explicit versioning, bridge, or expand-contract migration path before release.

# When To Use

Use this capability when a change: modifies the shape, semantics, validation rules, or defaults of a public or shared API; renames, removes, adds required fields, or changes field meaning in a request/response DTO or event schema; changes event structure, event name, or event ordering guarantees for an event-driven system; modifies configuration keys, config formats, or config defaults that are read by other services or deployment environments; changes behavior (error codes, retry semantics, SLA, rate limits) that consuming services depend on; introduces a staged or canary rollout where old and new code versions run concurrently; or triggers a deprecation of an existing contract surface.

# Do Not Use When

Do not use this capability to: certify that a change is compatible solely because no external clients are known (unknown consumers are the most dangerous assumption — event consumers, internal tools, and third-party integrations are frequently undocumented); replace `api-contract-design` for new endpoint design; or replace `data-migration-design` for storage schema migration sequencing.

# Stage Fit

Use during planning, implementation review, release preparation, and post-deprecation cleanup when a contract surface must survive old/new code, client, schema, event, configuration, package, SDK, or data-version skew. In planning, classify compatibility before implementation chooses a migration strategy. In review, reject stale project-memory or repository-graph claims about "no consumers", "internal only", "safe enum", or "rollback works" unless current source, generated artifacts, telemetry, and validation confirm them. Hand off when the unresolved decision is contract shape, DTO schema, data migration execution, consumer inventory, contract test implementation, release clearance, or documentation.

# Non-Negotiable Rules

- **Compatibility includes meaning, defaults, and behavior — not only structure.** A change that adds an optional field is structurally non-breaking. A change that interprets an existing field differently (e.g., `currency` now expects ISO-4217 instead of legacy code), tightens validation (e.g., `email` now requires DNS-validated format), or changes a default value (e.g., `timeout` default changes from 30s to 5s) is behaviorally breaking — even if the schema shape is identical. All four dimensions must be evaluated: structure, meaning, validation, and default behavior.
- **Evaluate both directions: old code reading new data, and new code reading old data.** A rollback scenario means old code runs against data written by new code. A staged rollout means new code reads data written by old code. Both directions must be verified. An additive migration (add new field with default) is safe in both directions if the old code ignores unknown fields. A removal migration (delete field) is safe only after all consumers have migrated.
- **Breaking changes require one of three mitigations: versioning, backward-compatible bridge, or expand-contract.** No breaking change may ship without a defined migration path. (1) **Versioning**: new `/v2/` endpoint; old endpoint supported for the deprecation window. (2) **Backward-compatible bridge**: new field added; old field deprecated but still accepted and mapped to the new field; both fields written during transition; old field removed only after migration window closes. (3) **Expand-contract**: expand phase (add new; keep old); migrate consumers; contract phase (remove old) — with CI tests that prove each phase is safe before proceeding.
- **Mobile clients, partner clients, and event consumers cannot be upgraded atomically.** A server-side API change that is deployed in minutes will be running against mobile app versions from 6–18 months ago. Event consumers in external partner systems may be upgraded on partner schedules, not yours. The compatibility window must be the longest-lived client version still supported, not the latest version.
- **Rollback must produce valid data.** If the new version writes data that the old version cannot read (e.g., a new enum value that the old version does not recognize, a new table that the old version's ORM does not map), rollback will produce errors or data loss. Every migration must verify: "if we roll back to the previous version immediately after this release, what state is the system in?" If the answer is "corrupt" or "error", the release is not rollback-safe and must be redesigned.
- **Deprecation must be backed by telemetry proving consumers have migrated.** A deprecation notice in documentation does not migrate consumers. Before removing a deprecated API, field, or event, production telemetry must confirm: (a) usage of the deprecated surface has reached zero (or below an agreed threshold), (b) a migration window of adequate length has passed (minimum 90 days for internal services; longer for partner integrations), (c) breaking change approval has been recorded. Removing a deprecated surface without telemetry confirmation is a production incident waiting to happen.

# Mode Matrix

| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities | Skip by default |
| --- | --- | --- | --- | --- | --- |
| API/DTO compatibility | Endpoint, request/response, error code, enum, pagination, filter, validation, default, or generated client changes. | Structural and semantic compatibility, old/new client behavior, versioning or bridge. | Old/new schema diff, consumer list, generated-client impact, contract tests. | `api-contract-design`, `dto-schema-design`, `error-code-design`, `contract-testing` | Release approval without consumer evidence. |
| Event/schema compatibility | Event type, payload, topic, partition key, ordering, schema registry mode, upcaster, or replay behavior changes. | Old producer/new consumer and new producer/old consumer deserialization and semantics. | Schema registry mode, consumer inventory, replay/retention window, fixture compatibility. | `event-driven-architecture`, `domain-event-modeling`, `message-queue-design` | Producer-only proof. |
| Stored data and config compatibility | DB schema version, persisted enum, config key, default, feature flag, or environment contract changes. | Mixed old/new code, rollback-safe written data, dual-read/write, config bridge. | Expand/migrate/contract phase, old/new reader/writer matrix, rollback state. | `data-migration-design`, `data-model-design`, `delivery-release-gate` | Contract cleanup in same deploy. |
| SDK/package/export compatibility | Public package export, CLI output, plugin API, generated SDK, semver, dependency version, or binary/API surface changes. | Semver class, source/binary compatibility, deprecation, consumer migration. | Public API diff, changelog, examples, generated artifact diff, downstream tests. | `sdk-library-contract-design`, `package-dependency-management`, `contract-testing` | Patch-version breaking change. |
| Mobile/partner/public client lag | Mobile app, partner integration, public API, webhook, or long-lived client cannot update atomically. | Long compatibility window, telemetry, notification, Sunset/Deprecation signals. | Supported client versions, partner schedule, usage telemetry, migration guide. | `consumer-impact-analysis`, `change-documentation-gate`, `mobile-product-extension` | Short internal-only deprecation window. |
| Rollout and rollback compatibility | Canary, blue/green, feature flag, rollback, queue retention, dual-write, or multi-service deploy order. | Coexistence of old/new binaries and data during rollout and immediate rollback. | Deployment sequence, flag/bridge rules, rollback behavior, validation gates. | `delivery-release-gate`, `release-rollback`, `reliability-observability-gate` | Calendar-only release decision. |

# Industry Benchmarks

Anchor compatibility review on semantic versioning, Postel/robustness principles, Google AIP compatibility guidance, expand/contract and parallel change, Protobuf/gRPC field-number rules, OpenAPI/AsyncAPI diffing, schema registry BACKWARD/FORWARD/FULL modes, RFC 8594 Sunset header, consumer-driven contract testing, mobile client lag practice, and rollback-safe release engineering. Keep this body focused on routing, compatibility judgment, evidence, and gates; load [references/compatibility-benchmarks.md](references/compatibility-benchmarks.md) for detailed surface, classification, rollout, telemetry, graph/memory/trajectory, and validation matrices.

# Selection Rules

Select this capability when **the primary risk is that a contract change breaks existing callers, consumers, mobile clients, or concurrent old-version deployments**. Route to `api-contract-design` for designing new endpoints and their request/response contracts. Route to `dto-schema-design` for field-level schema design decisions. Route to `data-migration-design` for sequencing storage schema changes during deployment. Route to `event-driven-architecture` for event schema evolution and consumer fan-out compatibility. Route to `delivery-release-gate` when the compatibility assessment determines whether the release is cleared to ship.

# Proactive Professional Triggers

- **Signal:** A request/response/event/config/SDK field is added, removed, renamed, retyped, made required, assigned a new default, or given a new meaning without old-client behavior. **Hidden risk:** structure appears compatible while deployed consumers fail or silently corrupt data. **Required professional action:** classify structure, meaning, validation, default, and behavior compatibility. **Route to:** `api-contract-design`, `dto-schema-design`, `contract-testing`. **Evidence required:** old/new diff, consumer impact, compatibility matrix, executable contract proof.
- **Signal:** Enum/status/state values are added or changed in API responses, events, persisted records, or generated clients. **Hidden risk:** strict consumers, exhaustive switches, generated SDKs, and old binaries reject unknown values. **Required professional action:** require open-enum/unknown handling or staged versioning. **Route to:** `state-machine-modeling`, `contract-testing`, `data-migration-design` when persisted. **Evidence required:** old-consumer behavior, generated-client impact, rollback behavior.
- **Signal:** A contract is called "internal only" or "no consumers" based only on local search, memory, or team assertion. **Hidden risk:** jobs, dashboards, mobile apps, partners, generated clients, or queue consumers are missed. **Required professional action:** record known consumers and unknown-consumer risk. **Route to:** `consumer-impact-analysis`, `repository-graph-analysis`, `project-memory-governance`. **Evidence required:** searched paths/schemas/topics/logs, telemetry, owner for unknown risk.
- **Signal:** Data/config/schema changes ship in one deploy with code that stops reading the old shape. **Hidden risk:** canary, rollback, and mixed-version windows break old code or produce unreadable data. **Required professional action:** require expand/migrate/contract or bridge sequence. **Route to:** `data-migration-design`, `delivery-release-gate`. **Evidence required:** old/new reader-writer matrix, deployment order, rollback state, cleanup gate.
- **Signal:** Deprecation removal is planned by date or documentation alone. **Hidden risk:** undiscovered consumers break when removal happens. **Required professional action:** require telemetry zero-use gate, minimum window, notification, and approval. **Route to:** `change-documentation-gate`, `delivery-release-gate`. **Evidence required:** usage metric, threshold, window, owner signoff, Sunset/Deprecation signal when HTTP.
- **Signal:** Project memory, repository graph, generated artifacts, or earlier execution says compatibility was already validated. **Hidden risk:** stale validation survives after schema, generated client, topic, deployment, or consumer changes. **Required professional action:** confirm current source, generated outputs, telemetry, and validation freshness before reuse. **Route to:** `repository-context-map`, `repository-graph-analysis`, `project-memory-governance`, `execution-trajectory-analysis`. **Evidence required:** inspected paths, accepted/rejected pattern, freshness limit, validation command or residual risk.

# Risk Escalation Rules

Escalate when: mobile or partner clients exist that cannot be upgraded atomically (compatibility window must be determined by the client, not the server); an event schema change has unknown downstream consumers (schema registry enforcement required before publication); rollback of the release would produce corrupt or unreadable data (expand-contract redesign required before release); a configuration change activates new behavior before all running instances have received the new config (config rollout coordination required); or a breaking change has no telemetry to confirm when the migration window can safely close.

# Critical Details

- **The most dangerous compatibility assumption: "we'll just require all consumers to upgrade at the same time."** This is never true for: mobile apps in users' hands; partner integrations on partner release schedules; microservices in different deployment pipelines; event consumers processing messages from queues with retention windows. Always design for mixed-version coexistence. The compatibility window must be the maximum observed deployment skew — typically days for internal services, months for mobile, potentially indefinite for partner integrations.
- **Enum values added in responses break consumers that have exhaustive switch statements or strict validation.** A new `PAYMENT_METHOD_ADDED` event type on a `UserActivity` event stream will cause consumers that use `switch` without a default case to throw unhandled exceptions. New enum values in responses require communication to consumers and defensive handling requirements before addition. This is one of the most common "non-breaking in schema but breaking in practice" changes.
- **Schema registry enforcement prevents "works locally, breaks in production" schema evolution.** For Apache Kafka / event-driven systems, use a schema registry (Confluent, AWS Glue, Apicurio) configured with BACKWARD or FULL compatibility mode. This prevents a producer from publishing an event that existing consumers cannot deserialize — even if the producer's team believes the change is backward-compatible. Compatibility is validated by the registry, not by team opinion.
- **`Sunset` response header (RFC 8594) is the machine-readable deprecation signal.** Adding `Sunset: Sat, 01 Jan 2027 00:00:00 GMT` to deprecated API responses enables SDK and proxy tooling to automatically surface deprecation warnings to consumers. This is more effective than documentation because it reaches developers at the moment they call the deprecated endpoint, not when they happen to read the changelog.
- **Generated clients make "small" changes visible.** Field optionality, enum expansion, package exports, and method signatures can be source-compatible in one language and breaking in another. Generated client diffs and downstream compile tests are compatibility evidence, not optional cleanup.
- **Config compatibility is a contract.** Renaming a key, changing a default, or flipping a feature flag behavior can split running instances during rolling deploys. Accept old and new keys during transition and define precedence, telemetry, and cleanup.

### Anti-examples

| Anti-pattern | Problem | Fix |
| --- | --- | --- |
| "Only internal callers, so breaking change is fine" | Internal services have deployment skew; rollback exposes old clients to new responses | Treat internal contracts with same rigor; expand-contract even for internal APIs |
| New `status` enum value `PENDING_REVIEW` added to event | Partner consumer's switch statement throws on unknown value; event processing halts | Pre-announce; require defensive handling; phase rollout behind flag |
| Required field added to existing endpoint without versioning | All existing callers fail with 400 until they update; coordinated deployment required | Add as optional with default in transition period; or create `/v2/` endpoint |
| Rollback deployed: new `settings` table not readable by v1 ORM | v1 ORM throws mapping error; service degraded until v2 re-deployed | Expand phase: create table; deploy; verify; remove old path later |
| Deprecation announced in docs; no telemetry; field removed 30 days later | Undiscovered consumer still calling deprecated field; 500 errors at partner | Telemetry gate: usage must reach zero before removal; minimum 90-day window |
| Config key renamed; old and new names not both accepted | Services on old config that haven't restarted lose configuration; silent failure | Accept both key names during transition; remove old key only after all instances restart |
| "rg found no callers" as consumer proof | Generated clients, dashboards, jobs, partners, or event consumers are missed | Treat local search as one evidence source; add telemetry/registry/owner review |
| Optional field added but meaning of old field changed | Schema diff passes while consumers compute wrong result | Classify semantic compatibility and version or bridge the behavior |

# Failure Modes

- New required request field breaks all clients that haven't updated simultaneously.
- New enum value in event stream causes consumer exhaustive-match to throw unhandled exception.
- Rollback after migration: old ORM cannot read new table schema; service enters error state.
- Deprecation window closed without telemetry confirmation; undiscovered partner still using deprecated endpoint.
- Mobile client version from 12 months ago calls renamed field; receives null; silent data corruption.
- Config key renamed; some pods restart on new config; others run on old config; split-brain behavior.

# Reference Loading Policy

The `SKILL.md` body carries normal L1/L2 compatibility routing, classification, output, and gate rules. Load [references/checklist.md](references/checklist.md) when drafting or reviewing a concrete compatibility assessment, release plan, deprecation, generated-client impact, event schema change, config compatibility decision, or rollback claim. Load [references/compatibility-benchmarks.md](references/compatibility-benchmarks.md) when detailed benchmark anchors, classification matrices, old/new producer-consumer grids, telemetry gates, graph/memory/trajectory coupling, or anti-pattern review is needed. Use [examples/example-output.md](examples/example-output.md) only when the expected output shape is unclear. Do not load references for pure routing or minor wording work where the inline output contract and quality gate are enough.

# Output Contract

Return a compatibility assessment with:

- `mode_selected` (API/DTO compatibility / event-schema compatibility / stored data and config compatibility / SDK-package-export compatibility / mobile-partner-public client lag / rollout and rollback compatibility)
- `source_evidence` (current API/schema/spec/proto/event/config/package/migration files, generated clients, consumers, tests, telemetry, repository graph, project memory, or execution trajectory inspected with freshness limits)
- `graph_memory_trajectory_judgment` (accepted, rejected, or not verified for every reused compatibility claim, consumer inventory, old validation, generated artifact, migration phase, or rollout assumption)
- `affected_contract` (API endpoint / event type / schema / config key / behavior surface)
- `change_description` (what changes)
- `consumer_inventory` (known consumers, generated clients, mobile/partner/public clients, event subscribers, jobs/reports/dashboards, unknown-consumer risk)
- `compatibility_matrix` (old producer to new consumer, new producer to old consumer, old code reading new data, new code reading old data, rollback to old binary after new writes)
- `compatibility_classification` (backward-compatible / forward-compatible / conditional / breaking for structure, meaning, validation, default, timing, error behavior, ordering, and persistence)
- `breaking_changes` (list with explanation per dimension and affected consumer class)
- `migration_strategy` (versioning / expand-contract / bridge / no change)
- `rollout_sequence` (ordered deployment steps; expand phase before contract phase)
- `mixed_version_behavior` (what happens when old and new run concurrently)
- `rollback_behavior` (what state is the system in if we roll back immediately)
- `deprecation_window` (length; telemetry gate; removal criteria)
- `consumer_notification_plan` (internal teams, mobile SDK release, partner notification)
- `schema_registry_compatibility_mode` (if event-driven: BACKWARD / FORWARD / FULL)
- `generated_client_impact` (language SDKs, compiled clients, public exports, semver/version bump, regeneration and compile-test plan)
- `bridge_or_feature_flag` (dual-read/write, alias, upcaster, adapter, opt-in flag, config bridge, or version selector)
- `telemetry_gate` (metric and threshold that confirms migration is complete)
- `contract_test_plan` (schema diff, Pact/provider verification, generated-client compile, fixture replay, event registry check, or manual residual risk)
- `breaking_change_approval` (required if breaking, with justification)
- `changed_compatibility_to_validation_map` (each changed surface, consumer class, compatibility direction, migration phase, telemetry gate, rollback path, and removal criterion mapped to validation evidence or residual risk)
- `handoff_boundaries` (what belongs to API/DTO shape, event design, data migration execution, consumer impact, contract testing, release gate, documentation, or security/privacy)
- `evidence_limits` (unknown consumers, missing telemetry, untested rollback, generated client not rebuilt, production schema registry not queried, mobile/partner behavior not proven)

# Evidence Contract

Close a compatibility assessment only when it names selected mode, source evidence inspected, graph/memory/trajectory reuse judgment, affected contract surfaces, known and unknown consumers, old/new producer-consumer and rollback matrix, compatibility classification by structure/meaning/validation/default/behavior, mitigation strategy, rollout order, rollback behavior, deprecation telemetry, generated-client impact, contract-test plan, changed-compatibility-to-validation map, handoff boundaries, residual risk, and evidence limits. A generic "backward compatible" assertion or "no callers found" statement is not sufficient evidence.

# Benchmark Coverage

Improved compatibility reviews reject common weak patterns: local caller search as proof of no consumers, schema-only compatibility that ignores semantic/default/error changes, enum expansion without unknown handling, one-deploy rename/drop, event producer-only testing, generated-client drift, date-only deprecation, rollback that writes unreadable data, config default flips during rolling deploy, and stale repository-memory claims. Detailed matrices and examples belong in references so this body stays efficient.

# Routing Coverage

Route here when contract evolution across old/new clients, producers, consumers, schemas, events, SDKs, configs, data versions, or staged deployments is primary. Hand off when the primary work is new API shape (`api-contract-design`), field schema (`dto-schema-design`), error taxonomy (`error-code-design`), stored-data migration execution (`data-migration-design`), consumer inventory (`consumer-impact-analysis`), executable contract proof (`contract-testing`), package surface design (`sdk-library-contract-design`), release readiness (`delivery-release-gate`), or migration docs (`change-documentation-gate`).

# Quality Gate

The compatibility assessment is complete only when:

1. Selected mode, affected contract, current source evidence, and graph/memory/trajectory reuse judgment are explicit.
2. All compatibility dimensions are evaluated: structure, meaning, validation, defaults, timing, ordering, error behavior, and persistence when relevant.
3. Both producer/consumer directions are verified: old producer to new consumer and new producer to old consumer.
4. Old code reading new data, new code reading old data, and immediate rollback after new writes are assessed.
5. Known consumers, generated clients, mobile/partner/public clients, event subscribers, jobs/reports/dashboards, and unknown-consumer risk are recorded.
6. Breaking changes have an explicit mitigation strategy (versioning, expand-contract, bridge, adapter, upcaster, or no-ship decision).
7. Rollback safety is confirmed or redesigned before release.
8. Mixed-version deployment behavior during staged rollout is defined.
9. Mobile/partner/external consumer compatibility window is established.
10. Deprecation has telemetry gate, minimum window length, notification plan, and removal criteria.
11. Schema registry compatibility mode is set for event-driven changes.
12. Generated clients, SDKs, public exports, and semver/versioning impact are handled.
13. Rollout sequence is ordered with expand or bridge phase before contract/removal phase.
14. Every changed surface, compatibility direction, migration phase, telemetry gate, rollback path, and removal criterion maps to contract tests, schema diff, generated-client compile, fixture replay, runtime telemetry, manual review, or named residual risk.
15. Breaking change approval is recorded for any change that cannot be made backward-compatible.
16. Handoff boundaries and evidence limits are explicit so compatibility evidence is not over-claimed as target contract design, data migration safety, production release approval, or documentation completion.

# Used By

- data-api-contract-changer
- delivery-release-gate

# Handoff

Hand off to `api-contract-design` for new endpoint design; `dto-schema-design` for field-level schema decisions; `event-driven-architecture` for consumer fan-out compatibility; `data-migration-design` for storage schema sequencing; `delivery-release-gate` for release clearance.

# Completion Criteria

The capability is complete when **every contract surface affected by the change has been evaluated for backward and forward compatibility, breaking changes have approved migration paths, rollback produces valid system state, and deprecation is gated on telemetry confirmation rather than calendar time alone**.
