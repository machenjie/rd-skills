# Example Output

```markdown
## Layer Responsibility Map

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

Dependency rule:
- presentation -> application -> domain
- infrastructure -> domain contracts
- domain -> no infrastructure imports
```
