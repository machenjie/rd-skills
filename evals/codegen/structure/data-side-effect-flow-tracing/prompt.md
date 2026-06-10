# Benchmark Prompt

## Task

Refactor an order status mapper that writes the database, mutates cache, emits an event, and calls an external fraud API while building a response object.

## Context

The starter repository hides side effects in a mapper and a property getter. Events are published before the transaction commits, cache mutation has no source-of-truth statement, and retries can duplicate external calls.

## Requirements

- Trace input to validation, mapping, policy, mutation, transaction, persistence, event, cache, external I/O, and response.
- Keep pure decision logic separate from side effects.
- Make side effects visible at service, adapter, repository, job, or message-consumer boundaries.
- Publish events after commit or document why pre-commit is safe.
- Define cache source of truth, invalidation, idempotency, compensation, and observability.

## Constraints

- Do not hide DB, cache, event, file, external API, clock, random, or environment side effects in mapper or getter code.
- Do not publish events before commit without explicit safety.
- Do not let logging or metrics change behavior.
- Do not perform external I/O without timeout, cancellation, retry, and cleanup policy.

## Deliverables

- Data and Side-Effect Flow Map.
- Ordering and transaction boundary decision.
- Idempotency and compensation plan.
- Tests for side-effect visibility and ordering.

## Completion Evidence

- Mapper becomes pure or side effects move to visible orchestration boundaries.
- Event publication happens after commit or has explicit safety proof.
- Cache mutation references source of truth and invalidation behavior.
