# Security Checks

## Threat Surface

Cancellation touches authorization and refund-adjacent decisions. The structure
risk is that method movement hides authorization or payment side effects inside
the wrong object.

## Required Checks

- Authorization remains visible before cancellation mutation.
- Domain/value objects do not import payment provider, repository, cache, queue,
  framework, or UI dependencies.
- Private helpers are not exported as test-only public API.

## Rejection Cases

- Reject implementations that let a domain object call payment infrastructure.
- Reject helper exports created only for tests.
- Reject object movement that hides authorization or refund side effects.
