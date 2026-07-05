# Starter Repo

## Stack

Python modular backend code with public facade tests and in-memory adapters.

## Initial State

Cancellation service logic, policies, refund hold behavior, repository calls,
payment adapter calls, DTO mapping, and private helpers are scattered. The
benchmark expects an order cancellation module object cluster, not a directory
tree created by technical type alone.

## Files

- `orders/cancellation/service.py`
- `orders/cancellation/policy.py`
- `orders/cancellation/dto.py`
- `orders/payment_adapter.py`
- `tests/orders/test_cancellation_module.py`

## Constraints

The implementation must preserve repository conventions, keep internals private,
avoid shared/common business logic, and expose only the current public facade.
