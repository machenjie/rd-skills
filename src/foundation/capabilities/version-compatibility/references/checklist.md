# Version Compatibility Checklist

- Select the mode: API/DTO, event/schema, stored data/config, SDK/package/export, mobile/partner/public client lag, or rollout/rollback compatibility.
- For the current compatibility change, inventory discovered API, schema, event, config, SDK, package export, CLI output, and generated client surfaces. The same inventory covers stored data and behavior surfaces. It identifies old/new coexistence or rollback participation and unknown consumers or surfaces.
- Record current source evidence, repository inspection search, prior-task evidence assumptions, execution-observable action sequence validation, and freshness limits.
- Inventory known consumers: services, web/mobile apps, SDKs, partners, event subscribers, jobs, dashboards, reports, scripts, and generated clients.
- Record unknown-consumer risk instead of treating "not found" as proof.
- Build one compatibility matrix covering old-producer/new-consumer, new-producer/old-consumer, old-code/new-data, new-code/old-data, and immediate rollback after new writes.
- Check structure, meaning, validation, defaults, timing, ordering, error behavior, and persistence semantics.
- Check field additions, removals, renames, type changes, enum values, nullability, pagination, sort/filter behavior, and error code changes.
- Check generated client, SDK, package semver, public export, and mobile/partner compatibility impact.
- Define versioning, staged rollout, compatibility bridge, upcaster/adapter, feature flag, expand-contract, or breaking-change approval.
- Define deprecation window, telemetry metric, threshold, minimum window, notification plan, and removal criteria.
- Define rollback behavior, mixed-version deployment assumptions, config compatibility, and queue/event retention window.
- Define schema registry mode, OpenAPI/AsyncAPI/proto diff, contract test, fixture replay, generated-client compile, or manual residual-risk evidence.
- Map every changed surface, compatibility direction, migration phase, telemetry gate, rollback path, and removal criterion to validation evidence or residual risk.
- Name handoff boundaries, evidence limits, owner, and rollback path before completion.
Route field semantics to `dto-schema-design`, consumer inventory to `consumer-impact-analysis`, executable contracts to `contract-testing`, migration execution to `data-migration-design`, and rollout/rollback to `release-rollback`.
