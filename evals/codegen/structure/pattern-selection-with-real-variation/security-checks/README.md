# Security Checks

## Threat Surface

Payment provider boundaries handle money-adjacent requests, provider secrets,
idempotency keys, and retry behavior.

## Required Checks

- Reject provider code that logs secrets or raw provider credentials.
- Verify idempotency keys are preserved across retry mapping.
- Reject hidden network IO without timeout and resource cleanup.

## Rejection Cases

- Reject a provider factory that creates clients per request.
- Reject a base class that swallows provider-specific security or retry errors.
- Reject caller branching that bypasses the provider contract.
