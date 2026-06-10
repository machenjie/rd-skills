---
name: consumer-impact-analysis
description: Analyzes known and unknown consumers of API, SDK, schema, event, package, CLI, and public export changes, including compatibility, migration, deprecation, telemetry, rollout, and rollback.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "115"
changeforge_version: 0.1.0
---

# Mission

Prevent accidental breaking changes by identifying who consumes a changed public contract, how compatibility is preserved, and how migration, telemetry, rollout, and rollback will work.

# When To Use

Use when changing API fields, SDK/public package exports, generated clients, schemas, event payloads, CLI output, configuration contracts, public module exports, error codes, pagination, or response semantics.

Use when consumers are unknown, mobile/web/backend clients may lag, or generated clients need regeneration.

# Do Not Use When

Do not use for private implementation changes with no public, package, schema, event, CLI, or generated contract impact.

Do not use as a substitute for designing the contract itself; pair with the relevant API, schema, SDK, event, or versioning capability.

# Non-Negotiable Rules

- Public contract changes must name current consumers or unknown-consumer risk.
- Breaking changes require compatibility bridge, deprecation window, or explicit approval.
- Generated clients must be regenerated or compatibility-tested.
- Event payload changes preserve old consumers or provide versioned migration.
- Migration guide and telemetry are required for consumer-visible changes.
- Rollout and rollback must account for mixed old/new consumers.
- Unknown consumers are treated as risk, not absence of risk.

# Industry Benchmarks

Anchor against semantic versioning, API compatibility review, consumer-driven contract testing, event schema evolution, generated client governance, deprecation policy, expand/contract rollout, telemetry-based migration, and mobile/client lag management.

# Selection Rules

Select this capability when the main risk is downstream consumer breakage. Use `version-compatibility` for compatibility mechanics, `api-contract-design` or `dto-schema-design` for shape design, `sdk-library-contract-design` for packages/SDKs, `contract-testing` for executable proof, and `change-documentation-gate` for migration docs.

# Risk Escalation Rules

Escalate to `data-api-contract-changer` when API/schema/event compatibility is affected. Escalate to `delivery-release-gate` when rollout or rollback requires coordinated deployment. Escalate to `mobile-product-extension` when mobile app release lag matters. Escalate to `architecture-impact-reviewer` when public exports define module boundaries.

# Critical Details

- Current consumers include web, mobile, backend services, SDK users, partner integrations, analytics jobs, dashboards, and generated clients.
- Unknown consumers include public APIs, published packages, event streams, CLI output parsed by scripts, and internal exports used outside search scope.
- Compatibility can be additive field, alias, dual-read, dual-write, upcaster, adapter, deprecation header, versioned endpoint, feature flag, or compatibility branch.
- Telemetry should measure old/new field usage, endpoint version, SDK version, event schema version, and error rate.
- Migration guide states old contract, new contract, timeline, examples, and rollback behavior.
- Rollback must not strand consumers on a contract no longer served.

# Failure Modes

- Renaming API field and updating only the server tests.
- Removing event payload field without schema version or upcaster.
- Regenerating SDK without checking public package semver or examples.
- Assuming no consumers because local `rg` found no callers.
- Deploying producer before consumers can read the new schema.
- Removing compatibility branch before telemetry proves old usage is gone.

# Output Contract

Return a Consumer Impact Report:

- Changed contract.
- Consumers.
- Unknown consumer risk.
- Compatibility.
- Generated client impact.
- Migration plan.
- Deprecation policy.
- Telemetry.
- Rollout and rollback.
- Tests.
- Documentation updates.
- Residual consumer risk.

# Evidence Contract

Close the report only when caller/consumer search, schema/API/export diff, generated client status, telemetry plan, compatibility tests or rationale, migration docs, rollout/rollback sequence, evidence limits, and residual risk owner are recorded.

# Quality Gate

1. Changed public contract is named.
2. Known and unknown consumers are assessed.
3. Compatibility strategy is explicit.
4. Generated clients are handled.
5. Migration and deprecation path exists for breaking changes.
6. Telemetry covers old/new usage where possible.
7. Rollout and rollback handle mixed versions.
8. Contract or consumer tests cover the change.

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
