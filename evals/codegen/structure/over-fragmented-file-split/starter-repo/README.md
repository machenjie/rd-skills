# Starter Repo

## Stack

Python service/use-case code with pytest-style behavior tests and in-memory
order fixtures.

## Initial State

`OrderCancellationService` is cohesive. It owns cancellation authorization,
deadline rules, refund-hold decisions, and orchestration for one use case. The
known gap is a small premium grace and disputed refund-hold rule. The starter
state does not need new public policy, adapter, or module boundaries to express
that rule.

## Files

- `orders/cancellation_service.py`
- `orders/order.py`
- `orders/repository.py`
- `tests/orders/test_cancellation_service.py`

## Constraints

The benchmark expects an anti-fragmentation decision. Implementations should
keep private helpers in the owning file when cohesive, or create at most one new
policy/value-object file when a real boundary is documented. One-function file
splits, trivial helper files, pass-through glue, and navigation cost regression
must be rejected.
