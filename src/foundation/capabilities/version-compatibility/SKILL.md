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

# Non-Negotiable Rules

- **Compatibility includes meaning, defaults, and behavior — not only structure.** A change that adds an optional field is structurally non-breaking. A change that interprets an existing field differently (e.g., `currency` now expects ISO-4217 instead of legacy code), tightens validation (e.g., `email` now requires DNS-validated format), or changes a default value (e.g., `timeout` default changes from 30s to 5s) is behaviorally breaking — even if the schema shape is identical. All four dimensions must be evaluated: structure, meaning, validation, and default behavior.
- **Evaluate both directions: old code reading new data, and new code reading old data.** A rollback scenario means old code runs against data written by new code. A staged rollout means new code reads data written by old code. Both directions must be verified. An additive migration (add new field with default) is safe in both directions if the old code ignores unknown fields. A removal migration (delete field) is safe only after all consumers have migrated.
- **Breaking changes require one of three mitigations: versioning, backward-compatible bridge, or expand-contract.** No breaking change may ship without a defined migration path. (1) **Versioning**: new `/v2/` endpoint; old endpoint supported for the deprecation window. (2) **Backward-compatible bridge**: new field added; old field deprecated but still accepted and mapped to the new field; both fields written during transition; old field removed only after migration window closes. (3) **Expand-contract**: expand phase (add new; keep old); migrate consumers; contract phase (remove old) — with CI tests that prove each phase is safe before proceeding.
- **Mobile clients, partner clients, and event consumers cannot be upgraded atomically.** A server-side API change that is deployed in minutes will be running against mobile app versions from 6–18 months ago. Event consumers in external partner systems may be upgraded on partner schedules, not yours. The compatibility window must be the longest-lived client version still supported, not the latest version.
- **Rollback must produce valid data.** If the new version writes data that the old version cannot read (e.g., a new enum value that the old version does not recognize, a new table that the old version's ORM does not map), rollback will produce errors or data loss. Every migration must verify: "if we roll back to the previous version immediately after this release, what state is the system in?" If the answer is "corrupt" or "error", the release is not rollback-safe and must be redesigned.
- **Deprecation must be backed by telemetry proving consumers have migrated.** A deprecation notice in documentation does not migrate consumers. Before removing a deprecated API, field, or event, production telemetry must confirm: (a) usage of the deprecated surface has reached zero (or below an agreed threshold), (b) a migration window of adequate length has passed (minimum 90 days for internal services; longer for partner integrations), (c) breaking change approval has been recorded. Removing a deprecated surface without telemetry confirmation is a production incident waiting to happen.

# Industry Benchmarks

Anchor against: **Semantic Versioning (semver.org)** — MAJOR.MINOR.PATCH; breaking change increments MAJOR; consumer pinning strategies. **Postel's Law (Robustness Principle, RFC 793)** — "be conservative in what you send, liberal in what you accept" — relevant to forward compatibility design. **Google API Improvement Proposals (AIP-180)** — compatibility policy; what constitutes breaking vs. non-breaking; major version in URL path. **Expand-Contract (Parallel Change) — Martin Fowler** — the safest database/API migration pattern for rolling deployments. **Apache Avro / Confluent Schema Registry** — schema evolution rules (BACKWARD, FORWARD, FULL compatibility modes); schema registry enforcement before event publication. **gRPC Protocol Buffer compatibility rules** — field number stability; reserved fields; unknown field handling. **OpenAPI Specification (OAS) versioning** — semver in `info.version`; vendor extensions for deprecation annotations; overlay specs for client code generation stability. **Netflix API Evolution** — versioning strategy for long-lived mobile clients; sunset header (RFC 8594) for graceful API retirement. **RFC 8594 (Sunset Header)** — machine-readable deprecation date in HTTP response headers. **DORA Deployment Frequency / Change Failure Rate** — rollback safety as a DORA metric; expand-contract enables high-frequency deployment with zero-downtime migrations.

### Breaking Change Classification Matrix

| Change Type | Backward Compatible? | Forward Compatible? | Breaking? | Required Mitigation |
| --- | --- | --- | --- | --- |
| Add optional field to response | Yes (clients ignore it) | Yes | No | None |
| Add optional field to request | Yes | Yes | No | None |
| Add required field to request | No | No | **Yes** | Default value in transition; or versioning |
| Remove field from response | No | No | **Yes** | Expand-contract; deprecation window |
| Remove field from request | Yes (ignored if optional) | No | Potentially | Verify no consumer sends it |
| Rename field | No | No | **Yes** | Expand-contract (old + new both accepted) |
| Change field meaning/semantics | No | No | **Yes** | Versioning required |
| Tighten validation rule | No | No | **Yes** | Versioning or communication to all producers |
| Add new enum value in response | No (old code may not handle) | Yes | **Yes for old code** | Defensive handling required; communication |
| Remove enum value | No | No | **Yes** | Verify no producer emits; verify no consumer expects |
| Change error code / error shape | No | No | **Yes** | Versioning or explicit mapping layer |
| Change default value | No (breaks existing behavior) | No | **Yes** | Explicit opt-in required |
| Add new event type to stream | Yes (consumers ignore) | Yes | No | None |
| Rename event type | No | No | **Yes** | Dual publish; expand-contract |
| Change config key name | No | No | **Yes** | Both keys accepted in transition window |

### Rollback Safety Decision Tree

```
Before approving a release containing a migration:

1. What data does the NEW code write that the OLD code cannot read?
   NONE → Rollback-safe from data perspective
   SOME → Rollback will produce errors or corrupt state
          → MUST redesign: add expand phase before data writes change

2. What behavior does the NEW code expose that existing consumers depend on changing?
   NONE → Safe to rollback
   SOME → Existing consumers will break after rollback
          → MUST deploy backward-compatible bridge before removing old behavior

3. Can the migration be run BEFORE the code deployment (expand phase)?
   YES → Run migration first; deploy code second; verify; THEN run contract phase
   NO  → Cannot be deployed with zero-downtime; must schedule maintenance window

4. If we rollback, will the last 24h of written data be readable by old code?
   YES → Rollback-safe
   NO  → Add rollback data migration script BEFORE shipping; test it
```

# Selection Rules

Select this capability when **the primary risk is that a contract change breaks existing callers, consumers, mobile clients, or concurrent old-version deployments**. Route to `api-contract-design` for designing new endpoints and their request/response contracts. Route to `dto-schema-design` for field-level schema design decisions. Route to `data-migration-design` for sequencing storage schema changes during deployment. Route to `event-driven-architecture` for event schema evolution and consumer fan-out compatibility. Route to `delivery-release-gate` when the compatibility assessment determines whether the release is cleared to ship.

# Risk Escalation Rules

Escalate when: mobile or partner clients exist that cannot be upgraded atomically (compatibility window must be determined by the client, not the server); an event schema change has unknown downstream consumers (schema registry enforcement required before publication); rollback of the release would produce corrupt or unreadable data (expand-contract redesign required before release); a configuration change activates new behavior before all running instances have received the new config (config rollout coordination required); or a breaking change has no telemetry to confirm when the migration window can safely close.

# Critical Details

- **The most dangerous compatibility assumption: "we'll just require all consumers to upgrade at the same time."** This is never true for: mobile apps in users' hands; partner integrations on partner release schedules; microservices in different deployment pipelines; event consumers processing messages from queues with retention windows. Always design for mixed-version coexistence. The compatibility window must be the maximum observed deployment skew — typically days for internal services, months for mobile, potentially indefinite for partner integrations.
- **Enum values added in responses break consumers that have exhaustive switch statements or strict validation.** A new `PAYMENT_METHOD_ADDED` event type on a `UserActivity` event stream will cause consumers that use `switch` without a default case to throw unhandled exceptions. New enum values in responses require communication to consumers and defensive handling requirements before addition. This is one of the most common "non-breaking in schema but breaking in practice" changes.
- **Schema registry enforcement prevents "works locally, breaks in production" schema evolution.** For Apache Kafka / event-driven systems, use a schema registry (Confluent, AWS Glue, Apicurio) configured with BACKWARD or FULL compatibility mode. This prevents a producer from publishing an event that existing consumers cannot deserialize — even if the producer's team believes the change is backward-compatible. Compatibility is validated by the registry, not by team opinion.
- **`Sunset` response header (RFC 8594) is the machine-readable deprecation signal.** Adding `Sunset: Sat, 01 Jan 2027 00:00:00 GMT` to deprecated API responses enables SDK and proxy tooling to automatically surface deprecation warnings to consumers. This is more effective than documentation because it reaches developers at the moment they call the deprecated endpoint, not when they happen to read the changelog.

### Anti-examples

| Anti-pattern | Problem | Fix |
| --- | --- | --- |
| "Only internal callers, so breaking change is fine" | Internal services have deployment skew; rollback exposes old clients to new responses | Treat internal contracts with same rigor; expand-contract even for internal APIs |
| New `status` enum value `PENDING_REVIEW` added to event | Partner consumer's switch statement throws on unknown value; event processing halts | Pre-announce; require defensive handling; phase rollout behind flag |
| Required field added to existing endpoint without versioning | All existing callers fail with 400 until they update; coordinated deployment required | Add as optional with default in transition period; or create `/v2/` endpoint |
| Rollback deployed: new `settings` table not readable by v1 ORM | v1 ORM throws mapping error; service degraded until v2 re-deployed | Expand phase: create table; deploy; verify; remove old path later |
| Deprecation announced in docs; no telemetry; field removed 30 days later | Undiscovered consumer still calling deprecated field; 500 errors at partner | Telemetry gate: usage must reach zero before removal; minimum 90-day window |
| Config key renamed; old and new names not both accepted | Services on old config that haven't restarted lose configuration; silent failure | Accept both key names during transition; remove old key only after all instances restart |

# Failure Modes

- New required request field breaks all clients that haven't updated simultaneously.
- New enum value in event stream causes consumer exhaustive-match to throw unhandled exception.
- Rollback after migration: old ORM cannot read new table schema; service enters error state.
- Deprecation window closed without telemetry confirmation; undiscovered partner still using deprecated endpoint.
- Mobile client version from 12 months ago calls renamed field; receives null; silent data corruption.
- Config key renamed; some pods restart on new config; others run on old config; split-brain behavior.

# Output Contract

Return a compatibility assessment with:

- `affected_contract` (API endpoint / event type / schema / config key / behavior surface)
- `change_description` (what changes)
- `backward_compatible` (yes / no / conditional)
- `forward_compatible` (yes / no / conditional)
- `breaking_changes` (list, with explanation per dimension: structure / meaning / validation / default)
- `migration_strategy` (versioning / expand-contract / bridge / no change)
- `rollout_sequence` (ordered deployment steps; expand phase before contract phase)
- `mixed_version_behavior` (what happens when old and new run concurrently)
- `rollback_behavior` (what state is the system in if we roll back immediately)
- `deprecation_window` (length; telemetry gate; removal criteria)
- `consumer_notification_plan` (internal teams, mobile SDK release, partner notification)
- `schema_registry_compatibility_mode` (if event-driven: BACKWARD / FORWARD / FULL)
- `telemetry_gate` (metric and threshold that confirms migration is complete)
- `breaking_change_approval` (required if breaking, with justification)

# Quality Gate

The compatibility assessment is complete only when:

1. All four compatibility dimensions are evaluated: structure, meaning, validation, defaults.
2. Both directions are verified: old code reading new data; new code reading old data.
3. Breaking changes have an explicit mitigation strategy (versioning, expand-contract, or bridge).
4. Rollback safety is confirmed or redesigned before release.
5. Mixed-version deployment behavior during staged rollout is defined.
6. Mobile/partner/external consumer compatibility window is established.
7. Deprecation has telemetry gate and minimum window length defined.
8. Schema registry compatibility mode is set for event-driven changes.
9. Rollout sequence is ordered with expand phase before contract phase.
10. Breaking change approval is recorded for any change that cannot be made backward-compatible.

# Used By

- data-api-contract-changer
- delivery-release-gate

# Handoff

Hand off to `api-contract-design` for new endpoint design; `dto-schema-design` for field-level schema decisions; `event-driven-architecture` for consumer fan-out compatibility; `data-migration-design` for storage schema sequencing; `delivery-release-gate` for release clearance.

# Completion Criteria

The capability is complete when **every contract surface affected by the change has been evaluated for backward and forward compatibility, breaking changes have approved migration paths, rollback produces valid system state, and deprecation is gated on telemetry confirmation rather than calendar time alone**.
