# Stuck Work, Manual Repair, And Workflow Versioning

**Load when:** Stuck or poison workflows, redrive, reset, manual repair, replay, or active-workflow version evolution changes.

**Do not load when:** No operational recovery or version-skew boundary changes and current evidence proves all active workflows reach owned terminal states.

**Required by:** `analysis-agent`, `task-agent`, `review-agent`

**Required output:** `failure-decision`, `validation-plan`, `proof-limit`

## One Decision

Select one detection, repair, and version-evolution contract that preserves identity, effect safety, history, and operator accountability.

## Decision Matrix

| Boundary | Required decision | Failure signal |
|---|---|---|
| Progress | State duration, heartbeat or lease, last durable progress, clock, and deadline. | Running has no freshness meaning. |
| Stuck detection | Query, threshold authority, false-positive handling, alert owner, and response deadline. | Poison work loops below alerts. |
| Quarantine | Isolation, retained evidence, live-work protection, and disposition. | One item blocks an ordered population. |
| Repair authority | Actor, workflow/step/effect target, purpose, permission, and approval. | A generic console edits state. |
| Repair command | Preconditions, dry run, repeat identity, allowed transition, participant check, and stop. | Repair repeats an unknown effect. |
| Audit | Before/after state, actor, evidence, command, outcome, and reconciliation. | Manual repair lacks attribution. |
| Definition version | Persisted version, command/event compatibility, participant support, and replay behavior. | Old history runs under incompatible code. |
| Evolution | Pin, patch, migrate, reset/redrive, continue, or retire from active-work inventory. | Deployment changes in-flight semantics silently. |

## Verification

- Distinguish slow, lost, poison, and externally blocked work at each deadline.
- Exercise quarantine, authorized/repeated/failed repair, and reconciliation.
- Replay representative histories under compatible and incompatible definitions.
- Exercise mixed old/new workers or participants where supported.
- Verify redrive or reset against the selected platform and persisted version.

## Primary Sources

- [Temporal Visibility](https://docs.temporal.io/visibility)
- [Temporal Worker Versioning](https://docs.temporal.io/production-deployment/worker-deployments/worker-versioning)
- [AWS Step Functions execution redrive](https://docs.aws.amazon.com/step-functions/latest/dg/redrive-executions.html)
- [Azure Compensating Transaction pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/compensating-transaction)

Official platform pages were accessed on 2026-07-26.

## Proof Limits

Platform visibility, redrive, reset, and versioning are product-, version-, history-, and configuration-specific. Local tests do not prove production permissions, active-work inventory, external-effect safety, or other workflow types.
