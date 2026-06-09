# Security Checks

## Threat Surface

Cancellation changes touch authorization-adjacent state mutation and external payment behavior.

## Required Checks

- Policy decisions do not trust caller-supplied authority fields.
- Service orchestration performs authorization before mutation or external side effects.
- Logs omit sensitive customer and payment data.

## Rejection Cases

- Side effects occur before permission or cancellation eligibility is checked.
- Denied cancellation still emits an event or mutates cache.
- Error response leaks payment provider internals.
