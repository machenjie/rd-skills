# Benchmark Prompt

## Task

Implement idempotent payment creation in the starter service. A repeated
request with the same idempotency key and same payload must return the first
payment result without creating a second provider charge.

## Context

The current payment endpoint creates a new payment every time it receives a
POST request. Clients retry when their network connection drops, so duplicate
charges are possible. The service uses a relational database repository and a
provider adapter that can return success, decline, or timeout.

## Requirements

- Require an idempotency key for create requests and persist the first result.
- Treat a repeated key with a different payload as a conflict.
- Keep money values precise and never use floating point arithmetic.
- Store enough provider metadata to support audit and reconciliation.
- Make the payment state machine explicit for pending, succeeded, failed, and
  declined outcomes.
- Add tests for concurrent duplicate requests and provider timeout recovery.

## Constraints

- Do not rely on process memory for idempotency decisions.
- Do not create a provider charge before the database write that reserves the
  idempotency key.
- Keep the public API backward compatible except for the new required
  idempotency key validation error.

## Deliverables

- Updated service, repository, request validation, and tests.
- Migration or schema notes for any new persistence fields.
- Documentation for retry behavior and conflict responses.

## Completion Evidence

- Unit and integration tests showing one charge for repeated and concurrent
  retries.
- Security review notes for key entropy, audit data, and safe error messages.
- Explanation of transaction boundaries and provider retry behavior.