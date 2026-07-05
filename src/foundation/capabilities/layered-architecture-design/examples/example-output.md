# Example Output

```markdown
## Layer Responsibility Map

Mode selected: Layer responsibility map and transaction/exception boundary.

Layering scope: Subscription cancellation use case in the subscriptions module; excludes public API schema redesign and distributed saga design.

Source evidence: Subscription controller, cancel use-case handler, Subscription aggregate, repository interface, Postgres repository adapter, event outbox adapter, import rule config, and service tests inspected. Project memory about direct ORM use rejected because current repository adapter owns persistence.

Graph/memory/trajectory judgment:
- Accepted: existing subscriptions domain package owns lifecycle invariants.
- Rejected: legacy pattern where controller checked `subscription.status`.
- Not verified: CI execution of the architecture rule and real database adapter test.

Presentation:
- POST /subscriptions/{id}/cancel parses request and maps response.
- Returns stable error codes from the application result.

Application:
- CancelSubscriptionUseCase checks authorization, opens transaction, loads subscription, calls domain cancellation, persists result, emits event.

Domain:
- Subscription.cancel(reason, requested_at) enforces lifecycle and refund eligibility invariants.

Infrastructure:
- SubscriptionRepository maps domain object to storage.
- Event outbox persists SubscriptionCanceled.
- Postgres adapter maps unique/foreign-key errors to application/domain exceptions.

Dependency rule:
- presentation -> application -> domain
- infrastructure -> domain contracts
- domain -> no infrastructure imports

Transaction boundary:
- CancelSubscriptionUseCase opens the unit of work, loads subscription, calls `subscription.cancel`, persists, writes outbox event, and commits.

Layer exception decisions:
- Transaction Script is rejected because cancellation has lifecycle and refund eligibility invariants.
- Active Record is rejected because domain must not import ORM models.

Changed layer to validation map:
- Controller no business conditionals: controller test or code review.
- Domain has no infrastructure imports: import-linter/dependency rule.
- Repository exception mapping: adapter unit/integration test.
- Transaction/outbox boundary: application service test with rollback case.

Handoff boundaries:
- `service-business-logic` owns concrete orchestration details.
- `domain-logic-implementation` owns the cancellation invariant implementation.
- `repository-persistence` owns SQL mapping and adapter tests.

Evidence limits:
- CI architecture rule and real database integration test were not run in this example.
```
