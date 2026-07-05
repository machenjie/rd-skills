# Security Checks

## Threat Surface

The cancellation module touches authorization, refund-adjacent decisions, and
payment adapter behavior. Module leaks can bypass authorization or hide side
effects.

## Required Checks

- Public facade enforces authorization before state mutation.
- Internals are not imported by external modules to bypass facade checks.
- Payment side effects remain in adapters and are not hidden inside policies or
  value objects.

## Rejection Cases

- Reject direct external imports of module internals.
- Reject shared/common order cancellation business logic.
- Reject module composition that hides payment or authorization side effects.
