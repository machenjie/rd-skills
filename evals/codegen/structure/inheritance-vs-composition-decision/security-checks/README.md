# Security Checks

## Threat Surface

Payment processing touches money-adjacent provider behavior. Structure mistakes
can hide provider-specific error handling or retry safety.

## Required Checks

- Provider-specific authentication, idempotency, and retry behavior remain
  explicit.
- Shared helper code does not leak provider secrets or collapse distinct error
  handling into unsafe common behavior.
- Contract tests cover security-relevant failure behavior when an interface is
  accepted.

## Rejection Cases

- Reject a base class that swallows provider-specific security failures.
- Reject caller branching that bypasses contract behavior.
- Reject shared helper extraction that logs secrets or removes idempotency
  boundaries.
