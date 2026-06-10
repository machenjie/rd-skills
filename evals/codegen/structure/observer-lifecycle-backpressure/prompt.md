# Benchmark Prompt

## Task

Add order event subscribers for notification, audit, and search indexing while
choosing whether observer or pub/sub is appropriate.

## Context

The order service currently publishes one committed order event. A proposed
patch adds an in-memory observer list that calls notification, audit, and search
indexing directly inside the transaction with no unsubscribe, no bounds, and no
subscriber error isolation.

## Requirements

- Produce a Design Pattern Decision Record for observer/pub/sub versus direct
  service calls or async jobs.
- If observer or pub/sub is used, define subscribe, unsubscribe, lifecycle
  ownership, shutdown cleanup, bounded fan-out, backpressure, timeout, and
  subscriber error isolation.
- Keep subscriber failures from breaking the main order transaction.
- Add metrics or logs for subscriber failure, queue depth, lag, and drops.
- Add tests for unsubscribe, subscriber error, overload, and normal delivery.

## Constraints

- Do not use unbounded observers or unbounded queues.
- Do not omit unsubscribe or lifecycle cleanup.
- Do not let observer exceptions break the main transaction.
- Do not ship without metrics or logs for subscriber health.

## Deliverables

- Event fan-out implementation or explicit direct-call rejection.
- Tests for lifecycle, failure isolation, and backpressure.
- Design Pattern Decision Record and reliability evidence.

## Completion Evidence

- Subscriber exception tests prove the main order commit is not broken.
- Overload tests or design notes prove fan-out is bounded.
- Review evidence identifies unsubscribe and shutdown cleanup.
