# Security Checks

## Threat Surface

Cancellation, refund, and shipping decisions can affect authorization and money
adjacent state. The structure risk is hidden internal access that bypasses a
policy or lifecycle guard.

## Required Checks

- Authorization or actor checks remain in the public lifecycle path.
- Sibling objects cannot call each other's private methods to bypass guards.
- Shared behavior is explicit and owned.

## Rejection Cases

- Reject implementations where a child mutates parent internals directly.
- Reject sibling internal access that bypasses policy checks.
- Reject shared/common business rules with no owning module.
