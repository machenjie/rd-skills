# Release Recovery Checklist

- Bind source revision, artifacts, config/secrets, migrations/schema, flags, jobs, routes, providers, infrastructure, and target environment into the changed-surface inventory.
- Consume the current accepted `version-compatibility` decision for consumer inventory, allowed and forbidden old/new states, migration, retirement, and rollback readability.
- Verify its source binding and freshness against the release identity and changed-surface inventory.
- Derive exposure, observation, stop signals, decision authority, and containment from consequence, baseline, reversibility, telemetry, and policy.
- Give each changed surface a rollback, disable, compensate, restore, reconcile, or forward-repair path with prerequisites and validators.
- Name points of no return, data-loss or semantic irreversibility, old-code/write-fencing needs, and backup or reconciliation evidence.
- Cover in-flight jobs, duplicate/missing side effects, cached control propagation, retained messages, external provider state, and cleanup timing.
- Tie planned recovery actions to fresh artifact, compatibility, environment, telemetry, command/query, or accountable residual-risk evidence.
- Distinguish local, dry-run, staged, and live evidence; record untested targets, providers, credentials, scale, and authority.
- Route missing, stale, or unresolved compatibility semantics to `version-compatibility`.
- Leave operational evidence to `reliability-observability-gate` and the final go/no-go verdict to `delivery-release-gate`.
