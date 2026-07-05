# Starter Repo

## Stack

Python service/use-case code with pytest-style behavior tests and in-memory
adapters.

## Initial State

`OrderCancellationService` contains helper functions for deadline checks,
refund-hold calculation, premium grace handling, mapping, and a payment
provider call. The benchmark expects object-method organization before any file
or method movement.

## Files

- `orders/cancellation_service.py`
- `orders/order.py`
- `orders/payment_adapter.py`
- `tests/orders/test_cancellation_service.py`

## Constraints

The implementation must not export private helpers for tests, create a
helper-bag object, or move payment provider calls into a domain/value object.
