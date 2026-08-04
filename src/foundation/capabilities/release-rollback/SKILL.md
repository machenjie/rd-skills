---
name: release-rollback
description: "`analysis-agent`/`task-agent`/`review-agent`: use for release identity, compatibility, exposure, stop, rollback, or recovery; skip pipeline-only and no-release work."
---

# release-rollback

## Registry Trigger

**Use when**

- design release identity ordering compatibility exposure observation stop rollback and forward recovery across changed surfaces

**Do not use when**

- work is limited to pipeline mechanics image construction cluster resources data migration execution or local validation with no release decision

## Skill Role

Define release exposure, recovery, irreversible boundaries, and proof limits. Consume `version-compatibility` decisions; exclude image, pipeline, and cluster mechanics. Route migration mechanics to `data-migration-design`.

## High-Value Rules

- Define one release identity from revision, immutable artifact, config, schema/migration state, flags, jobs, routes, provider state, and target; a previous image alone is incomplete.
- Consume the accepted `version-compatibility` decision's consumers, mixed-version behavior, migration, retirement, and rollback readability.
- Confirm that decision is current for the identity and changed surfaces before choosing release order, exposure, or recovery.
- Derive exposure, observation, stop signals, authority, and containment from blast radius, reversibility, consequence, telemetry, and policy; progressive exposure is not a fixed ladder.
- Give each changed surface a rollback, disable, compensate, restore, or forward-repair path with preconditions and validation; name when forward recovery becomes safer.
- **Potentially irreversible data protection:** Backup, reconciliation, old-code compatibility, and write fencing cover destructive or semantic data changes.
- Account for in-flight jobs, side effects, cached config, retained messages, provider actions, and partial rollback across versions.
- Refresh compatibility, artifact, environment, telemetry, and recovery evidence after edits. Separate staged proof from live authority and state; leave go/no-go to `delivery-release-gate`.

## Anti-Patterns

- Calling the previous binary a rollback while schema, config, jobs, routes, provider, or visible state remains changed.
- Treating canary, blue-green, rolling, flags, approvals, or incident roles as universal.
- Inventing traffic, metric, watch, or deadline thresholds without baseline and consequence evidence.
- Deleting old artifacts or compatibility paths before the exposure and recovery windows that need them have closed.

## Stop Conditions

- Escalate unknown identity, stop authority, external reversal, irreversibility, partial recovery, or validation.
- Block missing or stale compatibility evidence and route unresolved semantic compatibility design to `version-compatibility`.

## Output Contract

- Return a release-recovery decision: define identity, ordering, accepted compatibility decision, exposure, stop signals, per-surface recovery, evidence limits, and residual owner

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | a current accepted version-compatibility decision leaves release-specific exposure rollback compensation restore or forward-recovery mechanisms open | compatibility evidence is missing stale or unresolved or one bounded recovery path resolves the release | analysis-agent, task-agent, review-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | a release crosses artifacts states exposure signals irreversible effects or partial recovery after compatibility acceptance | compatibility evidence is missing stale or unresolved or no release recovery decision changes | analysis-agent, task-agent, review-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | Release identity compatibility exposure stop recovery authority or freshness claims need proof | Fresh scoped evidence closes each changed-surface recovery claim | analysis-agent, task-agent, review-agent | evidence-record, proof-limit, residual-risk |
