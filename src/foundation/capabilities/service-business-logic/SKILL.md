---
name: service-business-logic
description: Defines application service orchestration for use cases, transactions, repositories, policies, and domain operations while avoiding pass-through and god services.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "38"
changeforge_version: 0.1.0
---

# Mission

**Design and implement application services that orchestrate meaningful use cases** — coordinating authorization policy checks, transaction boundaries, domain model operations, repository interactions, event emission, and external effect sequencing — without becoming pass-through wrappers that add no value, or god services that accumulate unrelated workflow responsibility and create hidden coupling between domain areas.

# When To Use

Use this capability when: a change adds or substantially modifies an application service or use-case handler; the business logic requires orchestrating multiple repositories, a domain aggregate, a policy check, and an external effect in a defined transaction scope; a service is growing into a god service and needs to be decomposed by use case or domain boundary; or a service currently lives in a controller, a repository, or a domain entity and needs to be extracted to the correct architectural layer.

# Do Not Use When

Do not use this capability to: design or implement domain invariants that belong in a domain model or domain service (use `domain-logic-implementation`); design the API/transport layer mapping between HTTP and application layer (use `controller-api-implementation`); design repository access patterns and persistence contracts (use `repository-persistence`); design transaction coordination across distributed services (use `idempotency-retry-design` and `async-job-design`).

# Non-Negotiable Rules

- **Each service must represent a single coherent use case or workflow responsibility.** A service named `OrderService` that contains `placeOrder`, `cancelOrder`, `shipOrder`, `returnOrder`, `updateOrderMetadata`, `applyPromoCode`, and `generateInvoice` is a god service. Each of these is a distinct use case with different actors, different authorization requirements, different transaction boundaries, and different external effects. They must be separated into cohesive services or use-case handlers (e.g., `PlaceOrderService`, `CancelOrderService`, `ReturnOrderService`).
- **Authorization policy checks occur at the service layer, before any domain or repository operation.** A service method must not read data from the repository and then check if the caller is authorized to see it. The authorization check must happen first: if the caller is not authorized, the service returns 403 before touching the database. This prevents timing side channels and unauthorized data reads that are then discarded.
- **Transaction boundaries must be explicit and represent a single consistency unit.** Every service method must declare its transaction scope: which operations are in the same database transaction, which operations are outside the transaction (external HTTP calls, event emission, cache invalidation), and what the rollback behavior is if the transaction fails after an external call has already been made. "I'll figure out the transaction boundary at implementation time" is not a design decision.
- **External effects outside the transaction scope require explicit compensation design.** A service that calls an external payment gateway inside a database transaction creates a distributed consistency problem: if the database transaction rolls back after the payment API call succeeded, the user was charged but no order exists. External calls must be placed outside the transaction, with a compensating action defined for failure. Pattern: begin transaction → validate → commit → external call → on external call failure → compensating action (e.g., refund request, retry with idempotency key).
- **Domain invariants must not be duplicated in services.** A domain invariant like "an order can only be cancelled if it is in PENDING or PROCESSING status" belongs in the domain model or domain service, not in the application service. If the service checks this condition itself (e.g., `if order.status !== 'PENDING' throw new Error`), it diverges from the domain model over time as business rules evolve. Services must delegate invariant enforcement to the domain, and trust the domain to throw when invariants are violated.
- **Pass-through services must not exist without an architectural boundary justification.** A service method that does nothing except call one repository method and return the result adds no orchestration value and adds a layer of indirection with no benefit. It is acceptable only when the service creates an architectural boundary (e.g., between the application layer and a bounded context that will be extracted) and that boundary is explicitly documented.

# Industry Benchmarks

Anchor against: **Domain-Driven Design (Evans)** — Application Service layer: thin orchestrator; coordinates domain objects; does not contain business logic; manages transaction boundaries. **Clean Architecture (Martin)** — Use Case Interactor: represents one business use case; depends on entity / domain layer; must not depend on framework-specific types. **Patterns of Enterprise Application Architecture (Fowler)** — Transaction Script: appropriate for simple workflows; Application Service pattern: appropriate for complex domain coordination. **Command Query Responsibility Segregation (CQRS)** — separate command handlers (write-side use cases) from query handlers (read-side use cases); command handlers modify state; query handlers return data without side effects. **Hexagonal Architecture (Alistair Cockburn / "Ports and Adapters")** — application core is independent of frameworks, databases, and external services; services are part of the application core; adapters implement ports. **Spring @Service / NestJS @Injectable / Django service layer** — framework conventions for service lifecycle management; singleton scope; constructor injection of dependencies. **Google SRE — Service-Level Objectives** — a service that initiates external effects (payment, email, webhook) must have an SLO for the operation and a defined behavior when the SLO is not met.

### Service Responsibility Classification Matrix

| Service Type | Example | Responsibility | What It Must NOT Do |
| --- | --- | --- | --- |
| Command use-case handler | `PlaceOrderService` | Auth check → validate → domain op → persist → emit event | Contain domain invariants; call multiple external systems in one transaction |
| Query use-case handler | `GetOrderDetailsService` | Auth check → fetch → transform → return | Modify state; emit events; execute transactions |
| Workflow orchestrator | `OrderFulfillmentService` | Coordinate multi-step async workflow; manage compensation | Run long-running sync work inside a transaction |
| Policy enforcement service | `PricingPolicyService` | Apply pricing rules from domain policy; return result | Persist state; emit events |
| Anti-corruption layer service | `LegacyOrderAdapter` | Translate legacy model to bounded context model | Contain business logic; call domain operations directly |
| Pass-through (justified boundary only) | `TenantConfigService` | Facade over config service for bounded context isolation | Exist without documented boundary justification |

### Service Method Template (TypeScript)

```typescript
// PlaceOrderService — single use case, explicit transaction and effect boundaries
class PlaceOrderService {
  constructor(
    private readonly authPolicy: OrderAuthorizationPolicy,
    private readonly orderRepository: OrderRepository,
    private readonly inventoryService: InventoryService,
    private readonly paymentGateway: PaymentGateway,
    private readonly eventBus: EventBus,
    private readonly db: TransactionManager,
  ) {}

  async execute(command: PlaceOrderCommand): Promise<PlaceOrderResult> {
    // 1. Authorization first — before any data access
    await this.authPolicy.assertCanPlaceOrder(command.customerId);

    // 2. Validate inputs at application boundary
    const validated = PlaceOrderCommand.validate(command); // throws on invalid

    // 3. Transaction scope: domain operations + persistence only
    const { order, reservationId } = await this.db.runInTransaction(async (tx) => {
      const inventory = await this.inventoryService.reserveItems(validated.items, tx);
      const order = Order.place(validated, inventory.reservationId); // domain throws on invariant violation
      await this.orderRepository.save(order, tx);
      return { order, reservationId: inventory.reservationId };
    });
    // Transaction committed. Order exists. Inventory reserved.

    // 4. External effect OUTSIDE transaction — with compensation on failure
    let paymentResult;
    try {
      paymentResult = await this.paymentGateway.charge({
        idempotencyKey: order.id,         // prevents duplicate charge on retry
        amount: order.total,
        customerId: order.customerId,
      });
    } catch (paymentError) {
      // Compensating action: cancel order and release inventory reservation
      await this.orderRepository.cancel(order.id, 'PAYMENT_FAILED');
      await this.inventoryService.releaseReservation(reservationId);
      throw new PaymentFailedException(paymentError);
    }

    // 5. Confirm payment on order domain object
    await this.db.runInTransaction(async (tx) => {
      const o = await this.orderRepository.findById(order.id, tx);
      o.confirmPayment(paymentResult.transactionId); // domain operation
      await this.orderRepository.save(o, tx);
    });

    // 6. Emit integration event AFTER all state is consistent
    await this.eventBus.publish(new OrderPlacedEvent(order.id, order.customerId));

    return PlaceOrderResult.success(order.id);
  }
}
```

# Selection Rules

Select this capability when **application-layer orchestration — coordinating auth, domain operations, persistence, and external effects — is the primary design concern**. Route elsewhere when: domain invariants and business rules need design (use `domain-logic-implementation`); the transport/HTTP layer mapping needs design (use `controller-api-implementation`); repository and persistence contracts need design (use `repository-persistence`); async workflow orchestration across services needs design (use `async-job-design`); distributed transaction coordination needs design (use `idempotency-retry-design`).

# Risk Escalation Rules

Escalate when: a service method initiates a financial transaction or subscription charge (must have compensation design and idempotency key before implementation begins); a service coordinates writes to multiple independent data stores (distributed consistency problem — requires explicit saga or outbox pattern design); a service makes external API calls inside a database transaction (rollback-after-external-call inconsistency — requires restructuring before implementation); a service has more than 5 unrelated use cases (god service — requires decomposition before adding new use cases); or a service accesses resources it creates authorization decisions for (potential privilege escalation — requires `authentication-authorization` review).

# Critical Details

- **Authorization order is non-negotiable: check before read.** A service that fetches an order by ID and then checks whether the caller owns the order has read a record from the database before establishing that the caller is allowed to know it exists. For sensitive resources, this is an information disclosure risk. The authorization check must happen before the query: check that the caller has access to order IDs in this scope, then fetch.
- **Event emission sequence matters for consistency.** Emitting an integration event before the database transaction commits creates a race condition: a consumer receives the event and acts on it before the order record exists. Events must be emitted after the transaction commits. For strict at-least-once delivery guarantees, use the Transactional Outbox pattern (event record written inside the same transaction; separate publisher reads and emits from the outbox).
- **CQRS command/query separation prevents read-side services from acquiring write-side dependencies.** A read service that also calls a write repository "just to update a view counter" has crossed the CQRS boundary and created a hidden write dependency in a read path. Read-side services must be side-effect-free. Updates triggered by reads must be handled via events or background jobs.
- **Service tests must not require the web framework to run.** A service whose tests start a full HTTP server or require a Spring/NestJS application context to initialize violates the Clean Architecture dependency rule: the application layer must be testable independently of the framework. Services must be instantiable with constructor-injected mock dependencies and tested in pure unit or narrow integration tests.

### Anti-examples

| Anti-pattern | Problem | Fix |
| --- | --- | --- |
| `OrderService` with 8 unrelated methods | God service; cross-cutting changes; merge conflicts; shared state between unrelated workflows | Decompose: `PlaceOrderService`, `CancelOrderService`, `ShipOrderService` per use case |
| Repository call before authorization check | Reads data from DB before establishing caller has access; timing side channel; information disclosure | Auth check first: `await policy.assertCanAccess(resource, caller)` before any query |
| `paymentGateway.charge()` inside `db.runInTransaction()` | Payment succeeds; DB transaction rolls back; user charged with no order | External call outside transaction; compensating action (cancel + release) on payment failure |
| Domain invariant duplicated in service: `if (order.status !== 'PENDING') throw` | Service and domain drift over time; new state added to domain breaks service silently | Delegate to domain: `order.cancel()` throws `OrderNotCancellableError` internally |
| Integration event published before transaction commit | Consumer receives event before DB record exists; 404 on lookup; inconsistent state | Emit after commit; use Transactional Outbox for at-least-once delivery |
| Service test requires HTTP server startup | Application layer coupled to framework; slow test; cannot test in isolation | Constructor injection of all dependencies; mock in unit test; no framework required |

# Failure Modes

- God service with 12 methods; developer adds a 13th for unrelated workflow; one team's change breaks another team's unrelated workflow in the same file.
- Payment gateway called inside transaction; 0.1% of transactions roll back after successful charge; users charged but order not created; requires manual refund investigation.
- Authorization check occurs after repository fetch; attacker guesses resource ID; even though they cannot act, the timing difference reveals resource existence.
- Domain invariant duplicated in service; 6 months later domain adds new valid state; service continues to reject the new state; production regression.
- Integration event emitted before commit; consumer processes event; source record does not exist yet; consumer error rate spikes.
- Service test requires full Spring context; 45-second startup per test run; developers skip service tests to save time; service layer has no coverage.

# Output Contract

Return a service logic plan with:

- `use_case_name` (specific use case being orchestrated)
- `service_responsibility` (what this service coordinates; what it must not do)
- `inputs` (command object or query object with validation rules)
- `authorization_checks` (policy/permission checks; must precede all data access)
- `transaction_boundary` (which operations are in the transaction; which are outside)
- `domain_operations` (which domain methods are called; expected domain exceptions)
- `repository_operations` (which repositories are used; read vs. write; within/outside transaction)
- `external_effects` (external calls; idempotency keys; compensation design on failure)
- `emitted_events` (event name, timing: after-commit, transport: eventbus/outbox)
- `failure_handling` (per failure type: compensation, retry, error propagation)
- `idempotency_requirements` (can this command be safely retried?)
- `service_level_tests` (unit tests with mock dependencies; narrow integration tests)

# Quality Gate

The service design is complete only when:

1. Each service represents exactly one coherent use case or workflow.
2. Authorization check precedes all data access.
3. Transaction boundary is explicit (in vs. outside transaction).
4. External effects are outside the transaction with compensation design.
5. Domain invariants are delegated to domain model; not duplicated in service.
6. Pass-through services have documented boundary justification.
7. Integration events are emitted after transaction commit.
8. Service tests do not require web framework initialization.
9. Idempotency is designed for all commands that trigger external effects.
10. No god service accumulates more than one distinct use-case responsibility.

# Used By

- backend-change-builder
- domain-impact-modeler

# Handoff

Hand off to `domain-logic-implementation` for invariant placement; `repository-persistence` for data access patterns; `authentication-authorization` for authorization policy design; `idempotency-retry-design` for retry and compensation patterns; `async-job-design` for long-running or distributed workflow design.

# Completion Criteria

The capability is complete when **each service represents a bounded use case with correct authorization-first ordering, explicit transaction scope, external effects outside the transaction with compensation design, domain invariants delegated to the domain layer, and tests that run without the web framework**.
