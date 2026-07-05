# Benchmark Prompt

## Task

Refactor an order cancellation policy so pure business decisions are separated from database writes, payment API calls, event emission, logging, and cache updates.

## Context

The starter repository has `OrderPolicy.canCancel()` returning a boolean while also updating order status, writing an audit row, calling a payment API, invalidating a cache key, and emitting `OrderCancelled`.

## Requirements

- Extract a pure cancellation decision that can be tested without mocks for infrastructure.
- Keep state mutation, persistence, payment calls, cache invalidation, event emission, and logging in an orchestrating service or adapter boundary.
- Return a structured result that states allowed, denied reason, partial/failure state, and retryability when applicable.
- Preserve existing public behavior.
- Add tests for pure decision outcomes and service orchestration side effects at the public boundary.

## Constraints

- Do not leave policy code writing the database or calling external APIs.
- Do not hide side effects inside generic helpers.
- Do not return magic booleans or nulls for denied and failure states.
- Do not mock private helper calls.

## Deliverables

- Implementation Structure Plan with side-effect boundary classification.
- Code Clarity Maintainability Review for the main cancellation flow.
- Tests for pure decisions and public orchestration behavior.
- Evidence that old behavior is preserved.

## Completion Evidence

- Unit tests for pure policy decisions pass without infrastructure mocks.
- Service-level tests prove persistence, payment, event, cache, and logging coordination.
- Review note names rejected side-effect placement alternatives.
