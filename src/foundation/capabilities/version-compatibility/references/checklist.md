# Version Compatibility Checklist

- Select the mode: API/DTO, event/schema, stored data/config, SDK/package/export, mobile/partner/public client lag, or rollout/rollback compatibility.
- Identify every affected API, schema, event, config, SDK, package export, CLI output, generated client, stored data, and behavior surface.
- Record current source evidence, repository graph search, project-memory assumptions, execution-trajectory validation, and freshness limits.
- Inventory known consumers: services, web/mobile apps, SDKs, partners, event subscribers, jobs, dashboards, reports, scripts, and generated clients.
- Record unknown-consumer risk instead of treating "not found" as proof.
- Build old-producer to new-consumer and new-producer to old-consumer matrix.
- Build old-code reading new-data, new-code reading old-data, and immediate rollback-after-new-writes matrix.
- Check structure, meaning, validation, defaults, timing, ordering, error behavior, and persistence semantics.
- Check field additions, removals, renames, type changes, enum values, nullability, pagination, sort/filter behavior, and error code changes.
- Check generated client, SDK, package semver, public export, and mobile/partner compatibility impact.
- Define versioning, staged rollout, compatibility bridge, upcaster/adapter, feature flag, expand-contract, or breaking-change approval.
- Define deprecation window, telemetry metric, threshold, minimum window, notification plan, and removal criteria.
- Define rollback behavior, mixed-version deployment assumptions, config compatibility, and queue/event retention window.
- Define schema registry mode, OpenAPI/AsyncAPI/proto diff, contract test, fixture replay, generated-client compile, or manual residual-risk evidence.
- Map every changed surface, compatibility direction, migration phase, telemetry gate, rollback path, and removal criterion to validation evidence or residual risk.
- Name handoff boundaries, evidence limits, owner, and rollback path before completion.
