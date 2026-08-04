# Workflow Compensation, Convergence, And Reconciliation

**Load when:** Partial success requires semantic compensation, forward recovery, convergence criteria, or reconciliation across participant state.

**Do not load when:** One atomic transaction rolls back all effects or a proven local retry reaches the required state safely.

**Required by:** `analysis-agent`, `task-agent`, `review-agent`

**Required output:** `failure-decision`, `selected-approach`, `residual-risk`

## One Decision

Select one recovery strategy that reaches an explicit valid state without assuming compensation is rollback or retries converge.

## Decision Matrix

| Boundary | Required decision | Failure signal |
|---|---|---|
| Failure class | Transient, permanent, unknown, business rejection, partial, or irreversible outcome | A uniform retry or compensation is applied to distinct failure classes |
| Recovery direction | Continue, alternate path, compensate, reconcile, pause, or accept loss with authority | Recovery direction is chosen from transport error alone |
| Compensation input | Forward effect identity, recorded parameters, current participant state, and retention | Undo data is reconstructed after the effect |
| Compensation meaning | Target business state, allowed loss, concurrent-change rule, and visible outcome | Compensation means restore the original bytes |
| Ordering | Dependency order, safe parallelism, pivot, irreversible boundary, and cancellation | Compensation is assumed to run in reverse order without dependency evidence |
| Repeat safety | Compensation identity, deduplication, unknown result, retry limit, and terminal owner | Failed compensation is retried without effect authority |
| Desired state | Workflow invariant, participant facts, convergence tolerance, and deadline | A terminal label replaces participant validation |
| Reconciliation | Source facts, comparison key, drift classes, corrective action, checkpoint, and audit | Reconciliation reports drift but cannot repair or escalate |

## Verification

- Inject failures into each forward and compensation step before and after its participant effect.
- Apply concurrent participant changes before compensation.
- Reorder independent and dependent completions.
- Run reconciliation against missing, duplicate, conflicting, unknown, and already-correct facts.
- Repeat corrective actions and verify convergence or owned terminal escalation.

## Primary Sources

- [Azure Compensating Transaction pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/compensating-transaction)
- [Azure Saga distributed transactions pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/saga)
- [Kubernetes Controllers](https://kubernetes.io/docs/concepts/architecture/controller/)

Official platform pages were accessed on 2026-07-26.

## Proof Limits

Saga, compensation, and controller guidance describes patterns rather than universal ordering or delivery guarantees. Tests cannot prove an external participant is reversible, a compensation always succeeds, or reconciliation covers uninspected effects and concurrent changes.
