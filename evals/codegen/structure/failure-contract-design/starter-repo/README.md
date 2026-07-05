# Starter Repo

## Stack

Python API, service, repository, payment provider adapter, and queue consumer.

## Initial State

The flow catches broad exceptions, maps all failures to a generic error, retries terminal cases, exposes provider text, and has no DLQ or compensation for partial capture.

## Files

- `payments/controller.py`
- `payments/service.py`
- `payments/repository.py`
- `payments/provider_adapter.py`
- `payments/consumer.py`
- `tests/test_payment_failures.py`

## Constraints

The starting point intentionally mixes failure semantics. The benchmark expects typed boundary failure contracts and negative-path evidence.
