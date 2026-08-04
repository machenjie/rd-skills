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
| Progress | Expected state duration, heartbeat/lease, last durable progress, clock, and deadline | Running state has no freshness meaning |
| Stuck detection | Query, threshold authority, false-positive handling, alert owner, and response deadline | Poison work loops below alert thresholds |
| Quarantine | Isolation scope, retained evidence, live-work protection, and disposition | One item blocks an ordered population indefinitely |
| Repair authority | Actor, target workflow/step/effect, purpose, permission, and approval | Operator edits state through a generic console |
| Repair command | Preconditions, dry run, repeat identity, allowed transition, participant check, and stop | Repair repeats an unknown external effect |
| Audit | Before/after state, actor, evidence, command, outcome, and follow-up reconciliation | Manual repair has no durable attribution |
| Definition version | Persisted version, command/event compatibility, participant support, and replay behavior | Old history executes under incompatible code |
| Evolution | Pin, patch, migrate, reset/redrive, continue, or retire choice with active-work inventory | Deployment silently changes in-flight semantics |

## Verification

- Age running workflows past each deadline and distinguish slow, lost, poison, and externally blocked cases.
- Exercise quarantine, authorized repair, repeated repair, failed repair, and post-repair reconciliation.
- Replay representative histories under compatible and incompatible definitions.
- Run old and new workers or participants concurrently where supported.
- Verify redrive or reset behavior against the exact selected platform and persisted version.

## Primary Sources

- [Temporal Visibility](https://docs.temporal.io/visibility)
- [Temporal Worker Versioning](https://docs.temporal.io/production-deployment/worker-deployments/worker-versioning)
- [AWS Step Functions execution redrive](https://docs.aws.amazon.com/step-functions/latest/dg/redrive-executions.html)
- [Azure Compensating Transaction pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/compensating-transaction)

Official workflow and platform pages were accessed on 2026-07-26.

## Proof Limits

Visibility, redrive, reset, and versioning behavior is product-, version-, history-, and configuration-specific. Local tests do not prove production operator permissions, active-workflow inventory completeness, external effect safety, or platform behavior outside the exercised workflow type.
