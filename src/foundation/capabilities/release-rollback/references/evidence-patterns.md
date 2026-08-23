# Release Recovery Evidence Patterns

These records bind release identity, compatibility, exposure, recovery, authority, and explicit proof limits.

## Release Identity Claim

- Record source revision, immutable artifacts, config/secret versions, migration/schema state, flags, jobs, routes, provider state, target environment, and final-edit freshness.
- Link promoted and recovery artifacts to the same inspected inputs, or state the equivalence and provenance gap.

## Compatibility And Exposure Claim

- Name old/new combinations exercised for readers, writers, APIs/events, config, jobs, caches, routes, and external consumers.
- Record the exposed scope, baseline and consequence source, watch signals, stop authority, containment, and conditions not observed.
- Treat a staged or partial exposure result as evidence for that selected scope rather than for broader traffic or provider behavior.

## Recovery Claim

- Map each changed surface to rollback, disable, compensation, restore, reconciliation, or forward repair plus prerequisites and a fresh validator.
- Record irreversible state, point of no return, backup/reconciliation proof, retained or in-flight work, and partial-recovery combinations.
- Keep first-failure and stop-signal evidence separate from later retry or recovery success.

## Authority And Limits

- Distinguish local, dry-run, staged, and live commands; name target, permission, mutation scope, redaction, and recovery path for authorized writes.
- Mark evidence stale after material artifact, config, schema, flag, job, route, provider, telemetry, environment, or recovery-plan changes.
- Close with untested environments, consumers, providers, credentials, scale, operational behavior, residual owners, and the delivery gate handoff.

## Anti-Patterns

- Calling the previous binary a rollback while schema, config, jobs, routes, provider, or visible state remains changed.
- Treating canary, blue-green, rolling, flags, approvals, or incident roles as universal.
- Inventing traffic, metric, watch, or deadline thresholds without baseline and consequence evidence.
- Deleting old artifacts or compatibility paths before the exposure and recovery windows that need them have closed.
