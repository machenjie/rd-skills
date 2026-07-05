# Starter Repo

## Stack

Backend order service with transaction, event, and cache collaborators.

## Initial State

The service publishes an event and updates cache before the transaction commits.

## Files

- `src/order_service.py`
- `tests/test_order_service.py`

## Constraints

Do not introduce generic helper placement or duplicate event publication.

