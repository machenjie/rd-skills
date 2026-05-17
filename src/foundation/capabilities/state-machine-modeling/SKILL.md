---
name: state-machine-modeling
description: Models lifecycle states, allowed transitions, illegal transitions, guards, and side effects for orders, payments, subscriptions, approvals, assets, jobs, and workflows.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "14"
changeforge_version: 0.1.0
---

# Mission

**Model every domain object with meaningful lifecycle as an explicit finite state machine** — enumerating all states, all allowed transitions, all illegal transitions, every transition's guard conditions, side effects, emitted events, and audit impact — so that lifecycle behavior is enforceable in the authoritative domain layer, untestable implicit status logic is eliminated, and impossible states become structurally unrepresentable rather than defended by scattered conditional checks.

# When To Use

Use this capability when: a domain object (order, payment, subscription, job, document, approval, asset, request, ticket) has more than one meaningful lifecycle state and the allowed transitions between states carry business rules, side effects, authorization constraints, or audit obligations; a change adds a new state, new transition, or new guard to an existing lifecycle; a production incident was caused by an illegal transition or unexpected state (e.g., double-charging, duplicate fulfillment, stuck job); or a multi-step workflow requires recovery, cancellation, and timeout to be explicitly designed as first-class transitions rather than discovered in production.

# Do Not Use When

Do not use this capability for: simple display-only status labels that control no behavior, no persistence, no authorization, no events, and no side effects (a color badge on a card is not a state machine); UI-only loading/error/empty states that are local to a single component and map to no domain concept (use `interaction-state-modeling`); domain event consumers that react to transitions but do not own the transition logic (use `domain-event-modeling`).

# Non-Negotiable Rules

- **States must be mutually exclusive and exhaustive for the lifecycle.** A domain object must be in exactly one state at any point in time. Overlapping states ("PROCESSING and also PENDING"), implicit states ("no status field means PENDING"), and undeclared states discovered by reading boolean flags in combination are design defects. The state machine must enumerate all states including terminal states (from which no transition is possible) and error/failed states.
- **Allowed transitions must be explicit, and all unlisted transitions are illegal by default.** Enforcement means: any code path that attempts to transition a domain object from state A to state B must be validated against the allowed transition table. Any attempt to perform an unlisted transition must throw a domain exception (e.g., `IllegalStateTransitionException`), not silently fail or succeed. "State B can only be reached from state A and state C — all other origins are illegal" must be enforced at the authoritative domain layer.
- **Every transition must name its actor or trigger, guard conditions, side effects, emitted events, and audit record.** A transition row without a guard is a transition that anyone can trigger under any conditions — which is almost never correct. A transition without a side effect specification enables developers to add external calls to transition handlers with no review. A transition without an audit record is an untracked business event.
- **Side effects must be tied to committed transitions, not attempted transitions.** If a transition side effect is "send confirmation email," the email must be sent only after the state transition has durably committed to the source of truth. An email sent before the commit means the user can receive a confirmation for a transaction that ultimately fails. Pattern: transition and persist → commit → emit event → downstream handles side effect asynchronously.
- **Retry and idempotency must be designed for every transition that triggers an external effect.** If the transition "PENDING → PROCESSING" initiates a payment charge, a retry of this transition (due to timeout, network error, or at-least-once delivery) must not cause a double charge. Idempotency key design for the external call must be part of the transition specification.
- **Recovery, cancellation, and timeout must be first-class transitions, not afterthoughts.** A state machine that has `PROCESSING` but no `FAILED`, `TIMED_OUT`, `CANCELLED`, or recovery transition will produce stuck records in production. Every state that represents in-progress work must have an explicit exit to a failure or recovery state, with the trigger (timeout after N minutes, manual operator action, system event) and the side effects of that recovery transition.

# Industry Benchmarks

Anchor against: **UML State Machine Diagrams (ISO/IEC 19501)** — formal notation for states, transitions, guards `[condition]`, actions `/effect`, entry/exit actions; composite states for nested behaviors. **Harel Statecharts (David Harel, 1987)** — hierarchical state machines; parallel states; history states for resuming after interruption. **XState (JavaScript)** — modern implementation of Statecharts; guards (`cond`), actions, services for async transitions; strict transition validation at runtime. **Martin Fowler — State Pattern** (Patterns of Enterprise Application Architecture) — encapsulating state-specific behavior in objects; preventing `if status === X` branching scattered through domain code. **Event Sourcing (Greg Young, CQRS pattern)** — each state transition is a domain event; state is derived by replaying events; transition history is the audit log. **BPMN 2.0** — business process modeling notation for workflow states including parallel paths, interrupting events, error boundaries. **DORA Research** — change failure rate metric; a significant proportion of production incidents are caused by invalid state transitions or missing failure/recovery states. **IEEE Std 830 / ISTQB** — state transition testing: all-states coverage, all-transitions coverage, invalid-transition coverage.

### State Transition Table Template

```
Object: Order
States: DRAFT | PENDING | PROCESSING | CONFIRMED | SHIPPED | DELIVERED | CANCELLED | FAILED | REFUNDING | REFUNDED
Terminal states: DELIVERED | CANCELLED | REFUNDED

Transition Table:
From         | To           | Trigger                  | Actor            | Guard                              | Side Effect                         | Emitted Event            | Audit Record
-------------|--------------|--------------------------|------------------|------------------------------------|-------------------------------------|--------------------------|----------------------------
DRAFT        | PENDING      | Customer submits order   | Customer         | Items in cart ≥ 1; payment method  | Reserve inventory                   | order.submitted          | orderId, customerId, items
PENDING      | PROCESSING   | Payment initiated        | Payment system   | All items in-stock; payment method | Charge payment (idempotency: orderId)| order.payment.initiated  | orderId, amount, gateway
PROCESSING   | CONFIRMED    | Payment gateway callback | Payment webhook  | payment.status = SUCCESS           | Release inventory hold; notify user | order.confirmed          | orderId, transactionId
PROCESSING   | FAILED       | Payment gateway callback | Payment webhook  | payment.status = FAILED            | Release inventory; refund if charged| order.payment.failed     | orderId, failureReason
PROCESSING   | FAILED       | Timeout (15 min)         | Scheduler        | PROCESSING for > 15 min with no CB | Release inventory; alert support    | order.timed.out          | orderId, elapsedMs
CONFIRMED    | SHIPPED      | Warehouse ships order    | Warehouse system | Tracking number provided           | Notify customer; update ETA         | order.shipped            | orderId, trackingId
SHIPPED      | DELIVERED    | Delivery confirmed       | Courier system   | Delivery scan received             | Close order; trigger review prompt  | order.delivered          | orderId, deliveryTimestamp
CONFIRMED    | CANCELLED    | Customer cancels         | Customer         | < 1 hour since CONFIRMED           | Initiate refund; release inventory  | order.cancelled          | orderId, reason, refundId
FAILED       | CANCELLED    | Manual support action    | Support operator | —                                  | Notify customer                     | order.cancelled          | orderId, operatorId

Illegal Transitions (must throw IllegalStateTransitionException):
- DELIVERED → any state (terminal)
- CANCELLED → any state (terminal)
- SHIPPED → CANCELLED (cannot cancel after shipping)
- PROCESSING → CONFIRMED (must go through payment webhook, not direct)
```

### State Machine Guard Validation Pattern

```typescript
// Enforced at domain layer — not in controller or service
class Order {
  private state: OrderState;

  transition(targetState: OrderState, trigger: OrderTrigger): void {
    const allowed = ALLOWED_TRANSITIONS[this.state];
    if (!allowed?.includes(targetState)) {
      throw new IllegalStateTransitionException(
        `Cannot transition from ${this.state} to ${targetState} via ${trigger}`
      );
    }
    const guard = TRANSITION_GUARDS[`${this.state}->${targetState}`];
    if (guard && !guard(this, trigger)) {
      throw new TransitionGuardFailedException(
        `Guard failed for ${this.state}->${targetState}`
      );
    }
    this.state = targetState;
    this.recordTransition(targetState, trigger); // audit trail
  }
}
```

# Selection Rules

Select this capability when **state transitions carry business rules, authorization constraints, external side effects, or audit obligations**. Route elsewhere when: UI loading/empty/error states are the primary concern (use `interaction-state-modeling`); domain events consumed by downstream handlers are the primary concern (use `domain-event-modeling`); business rule guards need detailed extraction from existing code (use `business-rule-extraction`); the implementation of state transition enforcement needs design (use `domain-logic-implementation`).

# Risk Escalation Rules

Escalate immediately when: an illegal transition can cause a double charge, duplicate fulfillment, duplicate shipment, or inventory corruption (financial or operational impact — MUST-HANDLE); a transition can be triggered by an actor who should not have authority (authorization constraint on transitions must be reviewed with `authentication-authorization`); a state has no recovery/failure exit (stuck records risk — must add timeout or manual recovery transition); a transition involves a GDPR-relevant action (data deletion, export — must verify audit record requirement); or a state machine change would require a data migration for existing records in states that no longer exist.

# Critical Details

- **The most dangerous state machine defect is a missing failure/recovery exit.** A `PROCESSING` state with no `FAILED` or `TIMED_OUT` exit will produce permanently stuck records when the external dependency fails. These stuck records require manual operator intervention with no runbook, cause customer support escalations, and violate SLA commitments. Every in-progress state must have a timeout trigger and a failure state.
- **Guard evaluation order matters for concurrent transitions.** If two concurrent actors (customer and support operator) can both trigger a cancellation transition, and the guard is evaluated before the row-level lock, a race condition can cause double execution of the side effects (two refunds, two inventory releases). Guard evaluation must happen after acquiring the row-level lock, or transitions must use optimistic concurrency control (version column check).
- **Terminal states require irreversibility enforcement at the infrastructure layer, not just in guards.** A domain object in `DELIVERED` or `CANCELLED` state must not be modifiable by any actor. This means: the application layer enforces the terminal state check; but as a defense-in-depth measure, the database row should also be protected by an update trigger or soft-lock pattern that alerts on unauthorized state modification.
- **State machine diagrams and transition tables must be versioned alongside the domain code.** A state machine that evolves without updating the table makes future maintainers guess at the intended behavior, reopening the risk of illegal transitions. The transition table is the authoritative specification — it is a living document, not a one-time artifact.

### Anti-examples

| Anti-pattern | Problem | Fix |
| --- | --- | --- |
| `if order.status == 'PENDING' or order.status == 'PROCESSING': allow_cancel()` scattered in 6 files | Inconsistent cancellation rules; one file updated, others not; illegal cancel allowed | Single domain method `order.cancel()` enforces the guard; all callers delegate |
| `PROCESSING` state with no `FAILED` or `TIMED_OUT` exit | Stuck records when payment gateway times out; manual DB surgery required | Add `FAILED` state; add scheduler timeout trigger (15 min); add support recovery transition |
| Side effect (send email) called before transaction commit | Email sent; DB rollback; user receives confirmation email for failed order | Emit domain event after commit; downstream email service handles asynchronously |
| Transition `SHIPPED → DELIVERED` has no guard or audit record | Delivery can be confirmed by any actor with any data; no audit trail | Guard: `courier_scan_code verified`; audit: `deliveredAt`, `courierId`, `scanCode` |
| Payment charged again on retry because idempotency key not set | Double charge; customer dispute; financial loss | Idempotency key = `orderId` in payment gateway call; charge is deduplicated on retry |
| State machine stored as integer (0=PENDING, 1=PROCESSING...) | Magic numbers; no domain meaning; collision when states reordered | Named enum with string values; enforced by domain layer; DB stores string |

# Failure Modes

- Double charge: `PENDING → PROCESSING` transition retried without idempotency key; payment charged twice.
- Stuck order: `PROCESSING` has no timeout exit; payment gateway down for 2 hours; 847 orders stuck; manual intervention required.
- Illegal cancel: `SHIPPED → CANCELLED` not in illegal-transitions list; support tool allows cancellation after shipment; refund and delivery both complete.
- Race condition: two goroutines read order as `CONFIRMED`; both apply `CONFIRMED → CANCELLED` guard successfully without lock; two refunds initiated.
- Silent failure: illegal transition attempt swallows exception; order remains in `PROCESSING` indefinitely with no audit record.
- Missing state in data migration: new state `REFUNDING` added; 200 existing records have no migration path from `FAILED → REFUNDING`; migration script not written.

# Output Contract

Return a state machine model with:

- `states` (all states: name, meaning, terminal/non-terminal)
- `transition_table` (per transition: from, to, trigger, actor, guard, side effects, emitted event, audit record)
- `illegal_transitions` (explicitly listed; enforcement method)
- `timeout_triggers` (per in-progress state: duration, actor, resulting state, side effects)
- `recovery_transitions` (per failure/stuck state: trigger, actor, resulting state)
- `idempotency_design` (per transition with external effect: idempotency key, deduplication method)
- `concurrency_controls` (row-level lock vs. optimistic concurrency; where applied)
- `state_machine_diagram` (textual notation or Mermaid stateDiagram-v2)
- `test_coverage` (all-states, all-transitions, all-invalid-transitions, timeout, recovery)

# Quality Gate

The state machine model is complete only when:

1. All states are enumerated including terminal and failure/recovery states.
2. Transition table has actor, guard, side effect, event, and audit record for every transition.
3. All illegal transitions are explicitly listed with enforcement mechanism.
4. Every in-progress state has at least one timeout/failure exit.
5. Every transition with an external effect has an idempotency key design.
6. Side effects are tied to committed transitions (post-commit, not pre-commit).
7. Concurrency control is specified for states that multiple actors can transition concurrently.
8. Transition table is versioned alongside the domain code.
9. Test plan covers: all states, all valid transitions, all invalid transitions, timeout paths, recovery paths.
10. Data migration plan exists if new states are added to objects with existing production records.

# Used By

- domain-impact-modeler
- backend-change-builder
- quality-test-gate

# Handoff

Hand off to `business-rule-extraction` for guard condition detail; `domain-event-modeling` for downstream event consumption design; `domain-logic-implementation` for enforcement implementation; `idempotency-retry-design` for retry safety; `backend-change-builder` for implementation.

# Completion Criteria

The capability is complete when **every state, legal transition, illegal transition, guard, side effect, audit record, timeout exit, recovery transition, and idempotency design is explicit — and lifecycle behavior can be implemented and tested without scattered conditional status checks**.
