# State Machine Modeling Benchmarks And Patterns

Use this reference when state-machine-modeling output needs detailed transition shapes, guard enforcement examples, or test coverage matrices that would make the main `SKILL.md` too large. Keep the main body focused on routing, ownership, evidence, output contract, and quality gates.

## Benchmark Anchors

- UML State Machine Diagrams for states, transitions, guards, actions, entry/exit behavior, and composite states.
- Harel Statecharts for hierarchical states, parallel regions, and history states when a workflow resumes after interruption.
- XState and statechart practice for executable transition validation, guards, actions, invoked services, and async state behavior.
- Fowler State Pattern for keeping state-specific behavior out of scattered `if status == ...` branches.
- Event Sourcing and CQRS for transition history as durable fact history when events are the state source of truth.
- BPMN 2.0 for long-running business workflows, interrupting events, compensation, timers, and parallel paths.
- DORA change-failure analysis for incident review where invalid transitions, stuck states, or missing recovery paths produce production failures.
- IEEE/ISTQB state transition testing for all-states, all-transitions, invalid-transition, and boundary-condition coverage.

## Transition Table Template

```text
Object: Order
Source of truth: Order aggregate state stored as string enum in orders.status
Lifecycle owner: Commerce domain / Order aggregate
Terminal states: DELIVERED | CANCELLED | REFUNDED
In-progress states requiring exits: PENDING | PROCESSING | REFUNDING

From       | To         | Trigger        | Actor       | Guard              | Side effect         | Event              | Audit fields
---------- | ---------- | -------------- | ----------- | ------------------ | ------------------- | ------------------ | -------------------------
DRAFT      | PENDING    | submit         | customer    | cart_not_empty     | reserve_inventory   | OrderSubmitted     | orderId, customerId, items
PENDING    | PROCESSING | charge_start   | payment_job | inventory_reserved | call_gateway_after_commit(idempotency=orderId) | PaymentInitiated | orderId, amount, gateway
PROCESSING | CONFIRMED  | gateway_ok     | webhook     | payment_success    | release_hold        | OrderConfirmed     | orderId, transactionId
PROCESSING | FAILED     | gateway_fail   | webhook     | payment_failed     | release_inventory   | PaymentFailed      | orderId, failureReason
PROCESSING | FAILED     | timeout_15m    | scheduler   | no_gateway_result  | alert_support       | OrderTimedOut      | orderId, elapsedMs
CONFIRMED  | SHIPPED    | ship           | warehouse   | tracking_present   | notify_customer     | OrderShipped       | orderId, trackingId
SHIPPED    | DELIVERED  | delivery_scan  | courier     | scan_verified      | close_order         | OrderDelivered     | orderId, deliveredAt

Illegal transitions:
- DELIVERED -> any state: terminal.
- CANCELLED -> any state: terminal.
- SHIPPED -> CANCELLED: cancellation window closed.
- PROCESSING -> CONFIRMED without gateway_ok: missing authoritative trigger.
```

## Guard Validation Pattern

```typescript
// Enforced at the domain layer, after loading the current row/version.
class Order {
  private state: OrderState;
  private version: number;

  transition(target: OrderState, trigger: OrderTrigger, facts: TransitionFacts): DomainEvent[] {
    const rule = TRANSITIONS.find((row) =>
      row.from === this.state && row.to === target && row.trigger === trigger
    );

    if (!rule) {
      throw new IllegalStateTransitionException(this.state, target, trigger);
    }

    const guardResult = rule.guard(facts);
    if (!guardResult.allowed) {
      throw new TransitionGuardFailedException(rule.id, guardResult.reason);
    }

    this.state = target;
    this.version += 1;
    return [rule.eventFactory(this, facts)]; // persisted/outboxed with the state change
  }
}
```

## State Transition Test Coverage

| Coverage type | What it proves | Minimum evidence |
| --- | --- | --- |
| All-states coverage | Every declared state is reachable or intentionally initial/terminal. | Test or proof for initial, normal, failure, timeout, recovery, and terminal states. |
| All-valid-transitions coverage | Every legal transition works from the right origin with the right trigger. | Positive tests with actor, guard facts, event/audit assertion, and resulting state. |
| All-invalid-transitions coverage | Unlisted transitions are denied by default. | Negative tests for terminal states, wrong origin, wrong trigger, wrong actor, and stale version. |
| Guard coverage | Business preconditions return reasoned denial, not silent false. | Positive/negative guard cases tied to rule owner or rule id. |
| Side-effect coverage | External effects happen only after committed state. | Outbox/event/assertion proving no pre-commit call and idempotency key exists. |
| Timeout and recovery coverage | In-progress states do not become permanent dead ends. | Scheduler/manual/operator transition tests plus runbook or compensating evidence. |
| Concurrency coverage | Competing actors cannot execute duplicate side effects. | Row lock or optimistic-version conflict test, plus duplicate side-effect assertion. |
| Migration coverage | Stored records remain interpretable across new/old code and rollback. | Mapping query, backfill validation, mixed-version behavior, and rollback check. |

## Anti-Patterns To Reject

| Anti-pattern | Why it fails | Required correction |
| --- | --- | --- |
| Status enum added without transition table. | Code can write any value from any origin. | Add legal/illegal transition table and authoritative transition method. |
| Cancellation allowed from many files with local checks. | Entry points diverge and one path bypasses the guard. | Route all callers through a domain command or transition authority. |
| Side effect runs before state commit. | Rollback can create ghost emails, payments, events, or shipments. | Persist transition and outbox event in one transaction; execute effect downstream. |
| In-progress state has no timeout. | Records get stuck until manual database edits. | Add timeout trigger, failed state, recovery transition, and operator/runbook path. |
| New state value has no migration. | Existing records, reports, consumers, or old code cannot interpret lifecycle. | Define expand/contract, bridge, data mapping, validation query, and rollback behavior. |
| Project memory copied from a similar object. | Different actors, persistence, events, or rules make the copied graph unsafe. | Confirm current source, owners, events, tests, and migration context before reuse. |
