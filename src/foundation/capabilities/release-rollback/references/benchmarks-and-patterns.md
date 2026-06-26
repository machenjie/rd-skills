# Release Rollback Benchmarks And Patterns

Use this reference when the inline `release-rollback` contract is not enough to plan or review a real shared-environment release, migration-sensitive rollout, external provider reversal, or incident mitigation rollback.

## Benchmark Anchors

- DORA: track change failure rate, deployment frequency, lead time, failed-deployment blast radius, and mean time to restore.
- Progressive delivery: prefer canary, blue-green, rolling, feature flag, and traffic-shaping controls that reduce exposed users before full rollout.
- Continuous Delivery: require build provenance, repeatable deployment commands, smoke tests, automated gates, and rapid revert/forward-fix paths.
- Expand/migrate/contract: deploy additive schema first, shift reads/writes safely, then remove old structures only after old code is gone.
- ITIL/change management: classify standard, normal, emergency, and regulated changes; record approval and rollback authority where required.
- Cloud platform rollback practice: distinguish code rollback, config rollback, infrastructure rollback, traffic rollback, and state rollback.
- Incident response practice: separate release-owner rollback execution from incident commander coordination when rollback itself fails.

## Release Surface Rollback Matrix

| Surface | Rollback method | Precondition | Irreversibility risk |
| --- | --- | --- | --- |
| Application code | Redeploy previous image/tag or route traffic to previous environment | Previous artifact exists and old code is compatible with current state | Low if schema/config compatible |
| Database additive change | Leave in place, ignore new field, or run tested DOWN migration | Old code tolerates nullable/additive field | Low |
| Database destructive change | Pre-reviewed forward fix or backup restore plan | Data loss, restore RTO/RPO, and customer impact accepted | High |
| Runtime configuration | Restore prior value/version and restart/reload affected services | Prior value archived; secret/config version available | Medium |
| Feature flag | Disable, lower exposure, or switch to safe variant | Safe default and propagation latency tested | Low to medium |
| Background job/cron | Pause scheduler, cancel/requeue jobs, or replay idempotently | Job state, checkpoints, and idempotency are known | Medium |
| Cache/session format | Flush affected keys, invalidate namespace, or bridge old/new formats | DB/source of truth can absorb reload | Medium |
| CDN/edge/routing | Purge, route back, or restore previous rule | API access and previous rule version are available | Low to medium |
| External webhook/provider | Deregister, disable, dual-run, or provider-side rollback request | Self-service API or named provider escalation exists | Medium to high |
| Financial/auth/identity state | Disable path, reconcile ledger/session/token state, or compensate | Audit trail and reconciliation owner exist | High |
| Infrastructure/IaC | Apply previous module/state version or forward-fix drift | State lock, plan output, and dependency blast radius known | Medium to high |

## Irreversibility And Recovery Tiers

- Tier 0 reversible: previous artifact/config exists, state is unchanged, and rollback is one command plus validation.
- Tier 1 conditionally reversible: rollback is safe only if mixed-version compatibility, cache format, flag state, or provider config remains inside known bounds.
- Tier 2 forward-fix preferred: rollback may be slower or riskier than a prepared forward fix; require reviewed patch branch, validation, and owner approval.
- Tier 3 restore/compensate: data, external provider, financial, identity, or destructive state cannot be reversed directly; require backup restore, reconciliation, compensating transaction, customer communication, and incident management.

## Rollback Runbook Skeleton

```markdown
Release:
Owner and decision authority:
Deployment method and window:
Artifact/environment identity:
Changed surfaces:
Release order and mixed-version states:
Rollback triggers:
Decision deadline:
Per-surface rollback or forward-fix actions:
Validation after each action:
Communication and escalation:
Residual irreversibility risk:
Evidence limits:
```

## Graph, Memory, And Execution Coupling

- Graph: inspect deploy manifests, migration files, config references, flag definitions, job registrations, cache schema, provider clients, consumer contracts, and ownership files that are reachable from the changed release surface.
- Memory: treat previous runbooks, release notes, ADRs, incident records, generated docs, and project memory as hypotheses until current source and environment evidence confirm them.
- Execution: record which commands, validators, canary checks, smoke tests, queries, dashboards, or manual approvals ran; separate dry-run evidence from live-environment evidence.
- Coupling check: every accepted memory claim must map to a graph edge and every rollback action must map to executable validation or an explicit residual risk.

## Validation Checklist

- Changed surfaces inventory covers code, config, schema, flags, jobs, caches, providers, artifacts, infrastructure, and communication.
- Release order proves old-code/new-state and new-code/new-state compatibility during rolling, canary, or blue-green windows.
- Rollback triggers name metric, threshold, measurement source, duration, owner, and decision deadline.
- Artifact identity and environment target are captured before rollout and before rollback.
- Migration rollback or forward-fix plan has been reviewed against production-like data and known destructive operations.
- Flag/config rollback includes safe default, propagation latency, owner, stale-toggle cleanup, and observability.
- External provider reversal includes self-service command/API or named escalation path with expected delay.
- Cache/job rollback covers idempotency, in-flight work, replay, invalidation, and load impact.
- Post-rollback validation maps every changed surface to a command, monitor, query, manual check, owner approval, or residual risk.
- Evidence limits state which environments, providers, credentials, owner approvals, and live commands were not inspected or executed.
