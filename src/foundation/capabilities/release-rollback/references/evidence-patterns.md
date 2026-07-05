# Release Rollback Evidence Patterns

Use this reference when closure depends on proving per-surface rollback, artifact/environment identity, mixed-version compatibility, irreversibility classification, stale runbook judgment, or live-vs-dry-run evidence limits. Keep `SKILL.md` for routing and output shape; load this file only for concrete evidence mapping.

## Claim To Evidence Map

| Claim | Strong evidence | Weak or invalid evidence | Residual risk if absent |
| --- | --- | --- | --- |
| Changed surfaces are complete | Diff/manifest/migration/config/flag/job/cache/provider inventory | Code-only file list | Stateful surface remains unrecoverable |
| Rollback is per-surface | Ordered rollback or forward-fix action for each surface with owner | "Redeploy previous version" only | Code rollback leaves schema/config/provider failure active |
| Mixed-version compatibility is safe | Old/new code-schema-config matrix and validator or review output | Prior runbook memory | Rolling or blue-green deploy hits invalid state |
| Irreversible surface is governed | Tier, trigger, deadline, forward-fix branch, restore/reconciliation proof, approval owner | "Irreversible but acceptable" note | Recovery exceeds release decision window |
| Artifact/environment identity is known | Image/tag/build ID, config version, migration ID, target env, permission boundary | Generic deploy command | Rollback targets wrong artifact or environment |
| Live evidence limit is honest | Dry-run/live command classification, owner approval, monitor/query result, not-run disclosure | Local build treated as production recovery proof | Handoff overclaims release approval or rollback proof |
| Runbook or memory is current | Current source/manifest/provider evidence accepts or rejects prior runbook claim | Old incident note or generated doc alone | Stale recovery path blocks rollback |

## Changed Release To Validation Map

For each code, config, schema, flag, job, cache, provider, artifact, monitor, communication, and cleanup change, record:

```yaml
release_validation_map:
  surface: ""
  change: ""
  rollback_or_forward_fix: ""
  irreversibility_tier: 0 | 1 | 2 | 3 | unknown
  artifact_or_environment: ""
  validation:
    command_or_monitor: ""
    exit_code: null
    artifact_or_report: ""
    proves: ""
    does_not_prove: ""
  owner_approval: ""
  residual_risk:
    owner: ""
    reason: ""
```

## Closure Checks

- Reject closure when a stateful surface exists and rollback evidence is only "redeploy previous version."
- Reject closure when migration, external provider, financial/auth/identity, cache format, or in-flight job changes lack irreversibility classification.
- Downgrade prior runbook, graph, memory, canary, and pipeline claims unless current source and environment evidence confirm them.
- Do not treat dry-run, local build, or test-environment validation as live rollback approval without explicit evidence limits.
