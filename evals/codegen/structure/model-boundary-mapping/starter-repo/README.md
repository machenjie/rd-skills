# Starter Repo

## Stack

Python API service with request DTOs, domain profile objects, SQLAlchemy-style persistence models, and event payloads.

## Initial State

One `AccountProfile` class acts as request DTO, domain object, ORM model, event payload, and response view. A mapper mutates eligibility state and drops optional display-name semantics.

## Files

- `accounts/api.py`
- `accounts/models.py`
- `accounts/mapper.py`
- `accounts/events.py`
- `tests/test_account_mapping.py`

## Constraints

The starting point deliberately leaks API and persistence models across boundaries. The benchmark expects a model map and compatibility-preserving tests.
