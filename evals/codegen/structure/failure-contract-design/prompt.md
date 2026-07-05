# Benchmark Prompt

## Task

Repair a payment capture flow where adapter, repository, service, controller, and message consumer errors are mixed together.

## Context

The starter repository catches exceptions, returns generic 500 responses, retries every failure, logs raw provider messages, and silently falls back to pending status when a partial capture fails.

## Requirements

- Define a failure contract across adapter, repository, service, controller, job, and message consumer boundaries.
- Distinguish retryable, terminal, validation, permission, conflict, timeout, cancellation, dependency, and partial failure states.
- Translate raw SDK and database errors at the boundary.
- Define fallback, degraded response, compensation, rollback, retry/backoff, DLQ, and poison-message behavior.
- Add negative tests and safe log, metric, and trace fields.

## Constraints

- Do not swallow errors without typed fallback and observability.
- Do not leak raw database, SDK, secret, or PII values to users.
- Do not retry validation, permission, or terminal failures.
- Do not leave partial failure without compensation, rollback, DLQ, or explicit acceptance.

## Deliverables

- Failure Contract.
- Error taxonomy and boundary translation map.
- Retryability and fallback/degradation plan.
- Negative-path tests and observability fields.

## Completion Evidence

- API responses are safe and typed.
- Internal logs preserve diagnostic cause without secrets.
- Message failures have retry, DLQ, and poison-message behavior.
