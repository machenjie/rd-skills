# Security Checks

## Threat Surface

Cancellation can affect refund holds and payment-adjacent side effects. The
primary risk is that a reckless file merge hides adapter/client side effects,
weakens value object invariants, or obscures policy checks that protect refund
behavior.

## Required Checks

- Payment client side effects remain isolated behind the adapter/client
  boundary.
- Value object invariant checks are not scattered into procedural service code.
- Policy decisions remain visible and testable through public behavior.
- Dependency direction still prevents service internals from depending on
  external protocol details directly.

## Rejection Cases

- Fail any solution that merges the adapter/client into service code.
- Reject any solution that bypasses or weakens the value object invariant.
- Reject any solution that hides policy behavior or side effects to reduce file
  count.
- Reject any solution that removes public behavior test boundaries for policy or
  value object behavior.
