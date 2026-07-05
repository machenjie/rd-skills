# Example Output

```markdown
## Domain Implementation Contract

Domain owner:
- Subscription aggregate.

Invariant authority:
- A subscription can be canceled only when status is active or past_due.
- A canceled subscription cannot be reactivated through the cancel operation.
- Cancellation reason is required for administrator-initiated cancellation.

Operation:
- Subscription.cancel(actorType, reason, requestedAt)

Failure outcomes:
- AlreadyCanceled
- InvalidCancellationReason
- TerminalStateTransitionDenied

Layer rule:
- Controller and service may precheck status for UX, but Subscription.cancel enforces the invariant.

Tests:
- Active subscription cancels.
- Canceled subscription is rejected.
- Administrator cancel without reason is rejected.
```
