# Example Output

```markdown
## Service Logic Plan

Mode selected:
- Command use case.

Use case:
- Cancel subscription.

Service scope:
- `CancelSubscriptionService` owns orchestration for one cancellation request by an authenticated account owner.
- Excluded: HTTP status mapping, lifecycle rule definition, storage query construction, payment-provider retry worker.

Source evidence:
- Current controller delegates cancellation to a service.
- Repository graph shows `SubscriptionRepository`, `Subscription.cancel()`, and outbox publisher are current collaborators.
- Project memory about a prior cancellation retry bug is accepted only as a risk signal; the current retry path was not fully inspected.

Graph/memory/trajectory judgment:
- Accepted: existing outbox pattern in subscription module.
- Rejected: old memory that payment reversal is synchronous; current provider adapter uses async reversal.
- Not verified: production retry dashboard freshness.

Responsibilities:
- Authorize actor for account/subscription scope before protected data access.
- Load subscription through `SubscriptionRepository`.
- Start transaction for domain transition, repository save, and outbox write.
- Call `Subscription.cancel(reason, requestedAt)` for invariant enforcement.
- Persist subscription and write `SubscriptionCanceled` event to outbox.
- Commit transaction, then let outbox publisher notify downstream processors.

Not owned by service:
- HTTP status mapping.
- Lifecycle invariant definitions.
- Storage-specific query construction.
- Provider-specific payment reversal retry policy.

Failure handling:
- Already canceled maps to domain conflict.
- Permission denial happens before state mutation.
- Missing or inaccessible subscription returns non-leaking not-found.
- Outbox write failure rolls back the cancellation transaction.
- Payment reversal failure is handled by async retry worker with idempotency key `subscriptionId:cancellationId`.

Changed service to validation map:
- Authorization-before-read -> denied actor service test with repository not called.
- Domain transition delegation -> domain test for `Subscription.cancel()` denied and allowed states.
- Transaction and outbox atomicity -> integration test for rollback when outbox write fails.
- Retry handoff -> residual risk until payment reversal worker tests are inspected.

Handoff boundaries:
- `domain-logic-implementation` owns lifecycle transition rules.
- `repository-persistence` owns repository not-found/filtered semantics.
- `idempotency-retry-design` owns payment reversal retry worker.
- `quality-test-gate` owns test selection and freshness.

Evidence limits:
- Real payment provider sandbox was not inspected.
- Production retry metrics were not inspected.
- This plan does not prove controller response mapping or repository SQL correctness.
```
