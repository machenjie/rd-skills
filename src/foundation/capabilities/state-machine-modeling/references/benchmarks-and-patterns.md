# State Machine Modeling Benchmarks And Patterns

Load this reference when lifecycle legality, concurrent transitions, timeouts, recovery, or persisted state evolution changes. Do not load it for a stateless rule or a UI-only flag with no meaningful transition contract.

## Transition Record

| Field | Required decision |
| --- | --- |
| Object and authority | Name lifecycle owner, persisted/source state, initial state, and terminal states. |
| Transition | Record origin, target, authoritative trigger, actor, guard/rule owner, and denial reason. |
| Effects | Separate state mutation, durable event/audit, and external effect; name commit order and idempotency key. |
| Concurrency | Define stale-version, competing-actor, duplicate-trigger, and retry behavior. |
| Liveness | Every in-progress state needs an exit, timeout/deadline, recovery or compensation, and operator owner when applicable. |
| Evolution | Name old/new stored values, unknown-state behavior, mixed-version readers/writers, backfill, and rollback. |

Use a simple transition table and one enforcing authority by default. Hierarchical/parallel/history statecharts are candidates only when nested or concurrent lifecycle semantics exist; BPMN/workflow engines are candidates only when long waits, timers, compensation, or human work justify their operational cost. Event sourcing is appropriate only when durable fact history is the chosen source of truth, not merely for audit convenience.

## Failure And Proof

- For each modeled object and current-scope transition path, route state changes through the authoritative domain or policy transition contract. Deny origins or targets absent from that contract. Record unsearched producers and migration scripts as proof limits.
- Persist the transition and outbox or audit fact atomically when both must agree.
- Run irreversible external effects after commit through an idempotent boundary or a documented proven alternative.
- When an in-progress state can fail or stall, distinguish each applicable failure and recovery outcome.
- Give recovery an authorized transition, repair command, compensation, or owned runbook instead of relying only on direct database editing.
- For state-machine behavior changed by the current task, test applicable initial/terminal states and the changed valid transitions; select invalid origin/actor/guard, stale-version/duplicate-trigger, timeout/recovery, side-effect-ordering, and stored-state-compatibility cases from the affected lifecycle risk.
- Source inspection proves only the entry points searched; local tests do not prove every producer, real scheduler/broker timing, production interleaving, or mixed-version rollout. Name those limits and owners.

Reject scattered status assignments, side effects before commit, copied graphs from a similar object, new values without compatibility handling, and recovery paths without authorization/audit.

Route business rules to `business-rule-extraction` and permission guards to `permission-boundary-modeling`. Route commit/effect ordering to `transaction-consistency` or `data-side-effect-flow-tracing`, durable events to `domain-event-modeling`, and async recovery to `async-job-design`. Route migration to `data-migration-design` and executable coverage to `test-strategy` or `quality-test-gate`.
