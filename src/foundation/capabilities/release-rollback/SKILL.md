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

# Non-Negotiable Rules

- **Rollback must be planned per changed surface, not as a single "redeploy previous version" action.** A code rollback that restores the previous Docker image does not undo: database schema changes that new application code wrote to; new configuration keys that old code cannot parse; external provider webhooks or API subscriptions that were registered; feature flags that were toggled; or background jobs that are mid-execution. Each surface requires an independent rollback assessment and action plan.
- **Every database migration must have a rollback script or a documented forward-fix strategy.** "We'll deal with it if something goes wrong" is not a migration rollback plan. Rule: for every migration, specify one of: (A) reversible — a DOWN migration script exists and has been tested against a copy of production data; (B) forward-fix only — a DOWN migration is technically infeasible (e.g., dropped column with data loss); in this case, the forward-fix path must be pre-written and reviewed before production deployment. Irreversible migration deployments require additional pre-deployment approval.
- **Release order must account for mixed-version compatibility.** During a rolling deployment, old and new application code run simultaneously. The code/schema/config combination must be valid in these states: (old code + old schema), (old code + new schema), (new code + new schema). The third state, (new code + old schema), must never be deployed — it will fail. The expand-contract migration pattern ensures this: schema change is deployed before code change; code change is deployed before schema cleanup.
- **Define rollback triggers before deployment, not during the incident.** A rollback trigger is a measurable threshold: error rate > X%, p99 latency > Y ms, payment failure rate > Z%, health check endpoint returns non-200 for > 30 seconds. The release owner must know: (1) what metric to watch; (2) what threshold triggers rollback; (3) who makes the rollback decision; (4) what the decision timeline is (e.g., "if trigger not met within 10 minutes of deployment, continue; if triggered, immediate rollback"). Rollback decisions made ad-hoc under incident pressure result in delayed action and compounding damage.
- **Feature flags must have a documented safe default state.** If a feature flag is disabled in an emergency (circuit-breaker pattern), what behavior does the application exhibit? The safe default must be defined and tested before the flag is deployed. "Disable the flag" is not a rollback action without knowing what the disabled state does.
- **External integration changes may be irreversible by the team.** If a release includes: registering a webhook with a third-party provider; enabling a new payment processor feature; subscribing to a new event stream; or changing an OAuth redirect URI — the rollback requires a provider-side action that may take time or may not be self-service. The rollback plan must name who contacts the provider, what the reversal request is, and the expected time-to-reversal.

# Industry Benchmarks

Anchor against: **DORA State of DevOps** — change failure rate and mean time to restore as elite-team metrics; progressive delivery reduces change failure rate by reducing blast radius. **Martin Fowler "Feature Toggles" (martinfowler.com/articles/feature-toggles.html)** — toggle types (release toggle, ops toggle, experiment toggle, permission toggle); safe defaults; toggle lifespan discipline. **Continuous Delivery (Humble & Farley)** — deployment pipeline gates; canary release; blue-green deployment; smoke tests as go/no-go signals. **Expand-contract migration pattern** — schema migration sequencing for zero-downtime compatibility. **ITIL Change Management** — change advisory board (CAB) for high-risk changes; emergency change procedure; change classification (standard, normal, emergency). **AWS / GCP / Azure deployment docs** — blue/green, canary, rolling update deployment strategies; automated rollback based on CloudWatch / Cloud Monitoring metrics. **PagerDuty Incident Response Guide** — incident commander role; rollback decision authority; communication timeline.

### Release Surface Rollback Matrix

| Surface | Rollback Method | Pre-condition for Rollback | Irreversibility Risk |
| --- | --- | --- | --- |
| Application code | Redeploy previous image / tag | Old image available in registry; no schema dependency | Low (if schema compatible) |
| Database schema (additive) | DOWN migration or ignore new column | Old code ignores new column (nullable, no default) | Low (if expand only) |
| Database schema (destructive) | Forward-fix only; restore from backup | Backup tested and restorable within RTO | HIGH — plan forward-fix pre-deploy |
| Configuration / env vars | Revert config change; restart pods | Old config values archived; secret versions available | Medium (cache/restart lag) |
| Feature flag (code gate) | Disable flag; verify safe default behavior | Safe default state tested; flag state monitored | Low (if default is safe) |
| External webhook registration | Contact provider to deregister; or maintain both | Provider API allows self-service deregister | Medium-HIGH (provider SLA) |
| Background job / cron | Cancel in-flight jobs; redeploy old scheduler | Job is idempotent; can be safely cancelled | Medium (in-flight data state) |
| Cache (Redis/Memcached) | Flush affected cache keys; warm from DB | TTL acceptable; DB can absorb cache miss load spike | Low (cache miss is recoverable) |
| CDN / edge cache | Purge CDN cache for affected paths | CDN API allows programmatic purge | Low |
| External provider contract | Provider-side reversal request | Defined provider contact and escalation path | HIGH (provider-dependent) |

### Rollback Runbook Template

```
Release: [version tag / PR number]
Release Owner: [name + escalation contact]
Deployment Method: [rolling / blue-green / canary]
Deployment Window: [start time — expected end time]

Changed Surfaces:
  Code: [image tag being deployed; previous image tag for rollback]
  Schema: [migration IDs; reversible Y/N; DOWN script location]
  Config: [keys changed; previous values archived at: ...]
  Feature Flags: [flag names; current state → new state; safe default state]
  External: [provider; change made; reversal method; contact]
  Jobs: [job names; in-flight behavior on rollback]

Rollback Triggers (monitor for 10 min post-deploy):
  - HTTP error rate (5xx) > 1% for 2 consecutive minutes → ROLLBACK
  - p99 latency > 2000ms for 2 consecutive minutes → ROLLBACK
  - Payment failure rate > 0.5% → ROLLBACK
  - Health check /healthz returns non-200 > 30 seconds → ROLLBACK
  - [Custom: define metric + threshold + measurement tool]

Rollback Decision Owner: [name; must be available during deployment window]
Rollback Decision Deadline: [e.g., 15 minutes after deployment start]

Per-Surface Rollback Actions (in order):
  1. Feature flag: disable [flag name] → verify safe default behavior
  2. Code: redeploy [previous image tag]
  3. Config: restore [previous config values] + restart pods
  4. Schema: run DOWN migration [script path] (if reversible)
         OR: accept forward-fix path [pre-written fix branch: ...]
  5. External: [contact provider; request: ...]
  6. Cache: flush [affected key patterns]
  7. Jobs: cancel in-flight [job name] (verify idempotent)

Validation After Rollback:
  - Run smoke tests: [test suite name / URL]
  - Verify payment flow: [manual test script]
  - Confirm monitoring dashboards return to pre-deploy baseline
  - Page release owner when all checks pass

Communication:
  Internal notification: [Slack channel / incident channel]
  Customer communication trigger: [if customer-visible impact > X minutes]
  Post-mortem scheduled: [yes / no; when]
```

# Selection Rules

Select this capability when **release recovery planning is the primary concern** — before or during a production deployment. Route elsewhere when: `data-migration-design` is primary (designing the migration itself — expand-contract sequencing, batching strategy); `backup-recovery` is primary (planning data restoration from backup as the primary recovery path); `ci-cd` is primary (designing the deployment pipeline and automated gate logic); `observability` is primary (defining what metrics to monitor during deployment — use `observability` to design the signal, then reference the signal in the rollback trigger).

# Risk Escalation Rules

Escalate when: any changed surface is classified as HIGH irreversibility (destructive schema change, external provider contract change, financial transaction state change) — requires explicit forward-fix plan reviewed before production deployment; the deployment crosses a compliance boundary (PCI-DSS, HIPAA, SOX) — requires change advisory board (CAB) approval and documented change record; a background job is running against customer-owned data and cannot be safely interrupted — requires job completion checkpoint or idempotency proof; a release window is missed and a partial rollback is needed (some surfaces rolled back, others not) — requires explicit partial-rollback compatibility analysis; the rollback decision deadline has passed without a clear go/no-go signal — requires immediate escalation to engineering lead.

# Critical Details

- **Blue-green deployment solves code rollback; it does not solve database schema rollback.** Blue-green (two identical environments; traffic switch) can instantly route traffic back to the previous code version. But if the database schema was already migrated and the old code cannot read the new schema, traffic switch restores old code running against new schema — which is the failure state. Blue-green is only safe for rollback when the schema change is additive and backward-compatible with the old code.
- **Canary releases reduce blast radius but require automated rollback triggers.** Routing 1% of traffic to the new version limits customer impact but requires automated metrics-based rollback to be useful. A canary without automated rollback triggers is just a slow full deployment.
- **Feature flag toggle latency must be measured.** If the application caches the flag state for 60 seconds, disabling the flag in the feature flag service does not instantly disable it in production — it takes up to 60 seconds. The rollback plan must account for this propagation delay.
- **Cached data invalidation is often forgotten in rollback plans.** If the new code writes a different cache format (e.g., new JSON structure for a user session), rolling back the code while leaving the new-format cached data means old code reads corrupt cache entries. The rollback plan must include cache flush for affected key patterns.
- **"Rollback" and "incident response" are separate processes.** A rollback is a planned, pre-approved action executed during the deployment window. An incident response is the process when something unexpected happens. Conflating them leads to slow, ad-hoc decisions under pressure. The rollback runbook is executed by the release owner; the incident response process is engaged if the rollback itself fails.

# Failure Modes

- Rollback plan says "redeploy previous version" — old code cannot read new schema — rollback produces a different failure mode — incident escalates.
- Feature flag disabled in emergency — flag's safe default is "show old behavior" — but old behavior path has a bug — disabling the flag introduces a regression.
- External webhook registered in production — rollback restores old code — webhook still fires at new endpoint — new endpoint receives traffic from old code that doesn't handle it.
- Migration rollback script tested against a fixture database — fails against production data with unexpected NULLs — rollback attempt causes data corruption.
- Rollback trigger defined post-incident: "we should have rolled back when latency spiked" — 15-minute delay in rollback decision — 15 extra minutes of customer impact.
- Background job was mid-execution during rollback — partially processed 50,000 records — old code reprocesses same records — duplicate transactions created.

# Output Contract

Return a release rollback plan with:

- `changed_surfaces` (per surface: name, change description, rollback method, irreversibility classification)
- `release_order` (deployment sequence; mixed-version compatibility confirmation)
- `preflight_checks` (smoke tests to run before enabling traffic)
- `deployment_method` (rolling / blue-green / canary; traffic % if canary)
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

# Used By

- delivery-release-gate

# Handoff

Hand off to `data-migration-design` for migration design and batching strategy; `backup-recovery` for data restoration planning; `observability` for release health signal design; `ci-cd` for automated deployment gate configuration; `failure-diagnosis` when post-rollback investigation is needed.

# Completion Criteria

The capability is complete when **every changed surface has a tested rollback or forward-fix path, rollback triggers and the decision owner are explicit before deployment begins, and the release owner can execute recovery within the defined decision timeline without ambiguity**.
