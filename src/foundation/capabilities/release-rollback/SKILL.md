---
name: release-rollback
description: Plans release and rollback across code, configuration, database, feature flags, and external integrations with migration reversal or forward-fix strategy.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "75"
changeforge_version: 0.1.0
---

# Mission

**Plan every release as a reversible or forward-recoverable operation across all changed surfaces — code, configuration, database schema, feature flags, caches, background jobs, and external integrations** — so that the release owner has explicit rollback triggers, per-surface rollback actions, a decision timeline, and a validated recovery path before any production change is accepted.

# When To Use

Use this capability when: a change is promoted to a shared or production environment and any of the following apply — a database migration is included; configuration keys or environment variables change; external provider contracts change; feature flags are toggled; background jobs or scheduled tasks are added, modified, or removed; or a deployment introduces a mixed-version window where old and new application code may run simultaneously against the same data store. Also use when a prior release is being rolled back and a recovery plan is needed.

# Do Not Use When

Do not use this capability to: claim rollback safety from a code redeployment alone when data, configuration, flags, caches, or external contracts have also changed (each surface requires an independent rollback assessment); replace a post-mortem for a completed incident (use `failure-diagnosis`); design the migration itself (use `data-migration-design`); or plan backup restoration (use `backup-recovery`).

# Stage Fit

Use during release planning when code, configuration, migration, feature flag, cache, job, external integration, artifact, environment, or consumer coordination changes need recovery boundaries. Use during implementation and review when release order, mixed-version compatibility, rollback triggers, forward-fix path, or validation evidence is being shaped. Use during validation, release, and incident-mitigation review when repository graph, project memory, prior runbooks, generated docs, pipeline output, canary results, or prior execution evidence must be reconciled with current changed surfaces before deployment or rollback decisions are accepted.

# Non-Negotiable Rules

- **Rollback must be planned per changed surface, not as a single "redeploy previous version" action.** A code rollback that restores the previous Docker image does not undo: database schema changes that new application code wrote to; new configuration keys that old code cannot parse; external provider webhooks or API subscriptions that were registered; feature flags that were toggled; or background jobs that are mid-execution. Each surface requires an independent rollback assessment and action plan.
- **Every database migration must have a rollback script or a documented forward-fix strategy.** "We'll deal with it if something goes wrong" is not a migration rollback plan. Rule: for every migration, specify one of: (A) reversible — a DOWN migration script exists and has been tested against a copy of production data; (B) forward-fix only — a DOWN migration is technically infeasible (e.g., dropped column with data loss); in this case, the forward-fix path must be pre-written and reviewed before production deployment. Irreversible migration deployments require additional pre-deployment approval.
- **Release order must account for mixed-version compatibility.** During a rolling deployment, old and new application code run simultaneously. The code/schema/config combination must be valid in these states: (old code + old schema), (old code + new schema), (new code + new schema). The third state, (new code + old schema), must never be deployed — it will fail. The expand-contract migration pattern ensures this: schema change is deployed before code change; code change is deployed before schema cleanup.
- **Define rollback triggers before deployment, not during the incident.** A rollback trigger is a measurable threshold: error rate > X%, p99 latency > Y ms, payment failure rate > Z%, health check endpoint returns non-200 for > 30 seconds. The release owner must know: (1) what metric to watch; (2) what threshold triggers rollback; (3) who makes the rollback decision; (4) what the decision timeline is (e.g., "if trigger not met within 10 minutes of deployment, continue; if triggered, immediate rollback"). Rollback decisions made ad-hoc under incident pressure result in delayed action and compounding damage.
- **Feature flags must have a documented safe default state.** If a feature flag is disabled in an emergency (circuit-breaker pattern), what behavior does the application exhibit? The safe default must be defined and tested before the flag is deployed. "Disable the flag" is not a rollback action without knowing what the disabled state does.
- **External integration changes may be irreversible by the team.** If a release includes: registering a webhook with a third-party provider; enabling a new payment processor feature; subscribing to a new event stream; or changing an OAuth redirect URI — the rollback requires a provider-side action that may take time or may not be self-service. The rollback plan must name who contacts the provider, what the reversal request is, and the expected time-to-reversal.

# Industry Benchmarks

Anchor against DORA change failure rate and MTTR, progressive delivery, feature-toggle safe defaults, Continuous Delivery pipeline gates, expand/migrate/contract schema sequencing, ITIL normal and emergency change classes, cloud blue-green/canary/rolling rollback patterns, and PagerDuty incident role clarity. Keep this body focused on routing, evidence, output, and gates; load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) when surface rollback matrices, irreversibility tiers, runbook templates, decision timelines, graph/memory/execution coupling, or validation checklists need detail.

# Selection Rules

Select this capability when **release recovery planning is the primary concern** — before or during a production deployment. Route elsewhere when: `data-migration-design` is primary (designing the migration itself — expand-contract sequencing, batching strategy); `backup-recovery` is primary (planning data restoration from backup as the primary recovery path); `ci-cd` is primary (designing the deployment pipeline and automated gate logic); `observability` is primary (defining what metrics to monitor during deployment — use `observability` to design the signal, then reference the signal in the rollback trigger).

# Proactive Professional Triggers

- **Signal:** a rollback plan says only "redeploy the previous version" while schema, configuration, flag, cache, job, external integration, or provider state changes are present. **Hidden risk:** code rollback succeeds but stateful surfaces keep the incident active or create a new failure mode. **Required professional action:** inventory every changed surface and assign rollback or forward-fix owner, order, trigger, and validation. **Route to:** `data-migration-design`, `backup-recovery`, `configuration-runtime-policy`, `delivery-release-gate`. **Evidence required:** changed-surface list, compatibility matrix, migration rollback tier, config/flag prior state, provider reversal path, and residual irreversibility note.
- **Signal:** release order, mixed-version compatibility, or rollout safety is inferred from memory, old runbooks, generated docs, or pipeline defaults without current source, migration, config, manifest, flag, and dependency-graph checks. **Hidden risk:** stale memory approves an unsafe rolling, canary, or blue-green sequence. **Required professional action:** reconcile repository graph, project memory, generated artifacts, and execution trajectory before accepting release safety. **Route to:** `repository-context-map`, `repository-graph-analysis`, `project-memory-governance`, `execution-trajectory-analysis`, `version-compatibility`. **Evidence required:** inspected paths, graph edges, accepted/rejected memory claims, command freshness, and unknown consumer disclosure.
- **Signal:** feature flag, config, secret reference, kill switch, or runtime policy rollback lacks safe default behavior, propagation latency, owner, test evidence, cleanup path, or stale-toggle expiry. **Hidden risk:** emergency disablement or config revert does not take effect, exposes old-bug behavior, or leaves permanent operational drift. **Required professional action:** require safe default proof, propagation measurement, rollback command, owner, cleanup gate, and post-toggle validation. **Route to:** `configuration-runtime-policy`, `secret-configuration-security`, `cleanup-deletion-governance`, `observability`. **Evidence required:** prior/current values, flag state, cache/TTL behavior, validation command, monitor, owner approval, and cleanup expiry.
- **Signal:** a migration, external provider change, cache format, background job, payment/identity integration, destructive cleanup, or infrastructure state change is irreversible or partially reversible. **Hidden risk:** rollback requires provider SLA, backup restore, compensation, reconciliation, or forward fix that cannot fit the release decision window. **Required professional action:** classify irreversibility tier and require trigger, decision deadline, compensating control, owner, and validation proof before deployment. **Route to:** `data-migration-design`, `message-queue-design`, `backup-recovery`, `security-privacy-gate`, `reliability-observability-gate`. **Evidence required:** rollback or forward-fix branch, provider escalation path, restore/reconciliation proof, job idempotency, and compliance approval when applicable.
- **Signal:** canary, post-release validation, rollback command, or release gate lacks measurable thresholds, artifact/environment identity, tool permission evidence, or changed-surface-to-validator map. **Hidden risk:** the team cannot prove which artifact/environment was changed or whether recovery evidence applies to the live release. **Required professional action:** bind each release and rollback action to artifact identity, environment, permission boundary, monitor, query, manual approval, and evidence limit. **Route to:** `ci-cd`, `observability`, `validation-broker`, `quality-test-gate`, `agent-tool-permission-sandbox`. **Evidence required:** image/tag/build ID, deploy target, command output or dry-run limit, canary metric threshold, validator result, owner signoff, and unexecuted-live-action disclosure.

# Risk Escalation Rules

Escalate when: any changed surface is classified as HIGH irreversibility (destructive schema change, external provider contract change, financial transaction state change) — requires explicit forward-fix plan reviewed before production deployment; the deployment crosses a compliance boundary (PCI-DSS, HIPAA, SOX) — requires change advisory board (CAB) approval and documented change record; a background job is running against customer-owned data and cannot be safely interrupted — requires job completion checkpoint or idempotency proof; a release window is missed and a partial rollback is needed (some surfaces rolled back, others not) — requires explicit partial-rollback compatibility analysis; the rollback decision deadline has passed without a clear go/no-go signal — requires immediate escalation to engineering lead.

# Critical Details

- **Blue-green deployment solves code rollback; it does not solve database schema rollback.** Blue-green (two identical environments; traffic switch) can instantly route traffic back to the previous code version. But if the database schema was already migrated and the old code cannot read the new schema, traffic switch restores old code running against new schema — which is the failure state. Blue-green is only safe for rollback when the schema change is additive and backward-compatible with the old code.
- **Canary releases reduce blast radius but require automated rollback triggers.** Routing 1% of traffic to the new version limits customer impact but requires automated metrics-based rollback to be useful. A canary without automated rollback triggers is just a slow full deployment.
- **Feature flag toggle latency must be measured.** If the application caches the flag state for 60 seconds, disabling the flag in the feature flag service does not instantly disable it in production — it takes up to 60 seconds. The rollback plan must account for this propagation delay.
- **Cached data invalidation is often forgotten in rollback plans.** If the new code writes a different cache format (e.g., new JSON structure for a user session), rolling back the code while leaving the new-format cached data means old code reads corrupt cache entries. The rollback plan must include cache flush for affected key patterns.
- **"Rollback" and "incident response" are separate processes.** A rollback is a planned, pre-approved action executed during the deployment window. An incident response is the process when something unexpected happens. Conflating them leads to slow, ad-hoc decisions under pressure. The rollback runbook is executed by the release owner; the incident response process is engaged if the rollback itself fails.

# Failure Modes

- **Schema mismatch rollback:** rollback plan says "redeploy previous version" — old code cannot read new schema — rollback produces a different failure mode — incident escalates.
- **Unsafe flag default:** feature flag disabled in emergency — flag's safe default is "show old behavior" — but old behavior path has a bug — disabling the flag introduces a regression.
- **Provider state drift:** external webhook registered in production — rollback restores old code — webhook still fires at new endpoint — new endpoint receives traffic from old code that does not handle it.
- **Fixture-only migration proof:** migration rollback script tested against a fixture database — fails against production data with unexpected NULLs — rollback attempt causes data corruption.
- **Late trigger definition:** rollback trigger defined post-incident: "we should have rolled back when latency spiked" — 15-minute delay in rollback decision — 15 extra minutes of customer impact.
- **In-flight job duplication:** background job was mid-execution during rollback — partially processed 50,000 records — old code reprocesses same records — duplicate transactions created.
- **Artifact identity error:** rollback command targets the wrong image tag, namespace, cluster, region, or config version — validation passes in one environment while the live release remains broken.
- **Stale runbook memory:** prior runbook says provider rollback is self-service — provider changed the workflow — release owner waits for unavailable support path while customer impact continues.

# Reference Loading Policy

The `SKILL.md` body carries normal L1/L2 release rollback routing, evidence, output, and gate rules. Load [references/checklist.md](references/checklist.md) when drafting or reviewing a concrete shared-environment release, rollback plan, migration-sensitive rollout, config/flag rollback, external provider reversal, cache/job recovery path, or mixed-version window. Load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) when surface matrices, irreversibility tiers, runbook templates, graph/memory/execution coupling, canary/rollback decision detail, or validation matrices need depth. Use [examples/example-output.md](examples/example-output.md) only when output shape is unclear. Do not load references for local-only build artifacts or pure routing work where the inline output contract and quality gate are enough.

# Output Contract

Return a release rollback plan with:

- `mode_selected` (standard rollback / migration-sensitive rollout / config-or-flag rollback / external-integration rollback / incident mitigation / regulated release recovery)
- `source_evidence` (current source files, deployment manifests, migration scripts, config/secret references, feature flag definitions, job definitions, cache formats, external provider config, pipeline output, repository graph, project memory, execution trajectory, and validation freshness inspected)
- `changed_surfaces` (per surface: name, change description, rollback method, irreversibility classification)
- `release_order` (deployment sequence; mixed-version compatibility confirmation)
- `preflight_checks` (smoke tests to run before enabling traffic)
- `deployment_method` (rolling / blue-green / canary; traffic % if canary)
- `artifact_and_environment_state` (image/tag/build ID, config version, migration ID, feature flag state, provider state, target environment, command/tool permission boundary)
- `rollback_triggers` (per trigger: metric, threshold, measurement tool, duration)
- `rollback_decision` (owner name; decision deadline; escalation path)
- `per_surface_rollback_actions` (ordered steps; estimated time per step)
- `migration_strategy` (reversible with DOWN script OR forward-fix with pre-written branch)
- `feature_flag_controls` (flag name; current state; new state; safe default; propagation latency)
- `external_integration_steps` (provider; change; reversal method; contact; estimated time)
- `cache_invalidation` (affected key patterns; flush command)
- `post_rollback_validation` (smoke tests; manual verification steps; baseline metric confirmation)
- `communication_plan` (internal channel; customer notification trigger; post-mortem schedule)
- `residual_risk` (surfaces that cannot be fully rolled back; compensating controls)
- `graph_memory_execution_validation` (graph edges inspected, memory/runbook claims accepted or rejected, prior execution evidence reused or rejected, validator map, and evidence limits)
- `changed_release_to_validation_map` (each code, config, schema, flag, job, cache, provider, artifact, communication, and cleanup change mapped to validation command, monitor, query, manual check, owner approval, or residual risk)
- `handoff_boundaries` (what must move to `data-migration-design`, `backup-recovery`, `ci-cd`, `observability`, `failure-diagnosis`, or compliance/change-management review)
- `evidence_limits` (what was not inspected, which commands were not run, which environments/providers were not contacted, and what cannot be claimed from the current evidence)

# Evidence Contract

Close rollback planning only when the output names changed surfaces, release order, mixed-version compatibility, rollback triggers, decision owner, per-surface rollback or forward-fix action, validation command, what rollback evidence proves, what it does not prove for production data/external providers, residual irreversibility risk, and next gate. It must also state graph/memory/execution judgment: which repository edges, generated artifacts, prior runbooks, project memory claims, pipeline outputs, command outputs, or canary evidence were accepted or rejected, why they are current enough, and where freshness could not be proven. Do not present a plan as production-approved unless live environment identity, credentials/permissions, owner approval, and release-window evidence are explicitly present.

# Quality Gate

The release rollback plan is complete only when:

1. Every changed surface has an independent rollback action or forward-fix plan.
2. Rollback triggers are measurable thresholds, not subjective judgments.
3. Rollback decision owner is named and available during the deployment window.
4. Database migration rollback is tested against a production-scale data copy.
5. Feature flag safe default state is documented and tested.
6. Mixed-version compatibility is confirmed for all deployment phases.
7. External provider reversal path is defined (including contact and expected time).
8. Cache invalidation is included where new code changes cache format.
9. Irreversible surfaces have explicit forward-fix plans reviewed before deployment.
10. Post-rollback validation steps are defined and can be executed within 5 minutes.
11. Repository graph, project memory, generated docs, prior runbooks, and pipeline claims are reconciled with current code, config, migration, provider, and environment evidence.
12. Every rollback action maps to a validator, monitor, query, manual check, owner approval, or named residual risk.
13. Artifact identity, target environment, tool permission boundary, command freshness, and unexecuted-live-action limits are recorded.
14. Handoff boundaries and evidence limits are explicit; the plan does not over-claim release approval, provider reversal, data recovery, or live rollback proof.

# Used By

- delivery-release-gate

# Handoff

Hand off to `data-migration-design` for migration design and batching strategy; `backup-recovery` for data restoration planning; `observability` for release health signal design; `ci-cd` for automated deployment gate configuration; `failure-diagnosis` when post-rollback investigation is needed.

# Completion Criteria

The capability is complete when **every changed surface has a tested rollback or forward-fix path, rollback triggers and the decision owner are explicit before deployment begins, and the release owner can execute recovery within the defined decision timeline without ambiguity**.
