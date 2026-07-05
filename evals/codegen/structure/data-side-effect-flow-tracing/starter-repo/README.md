# Starter Repo

## Stack

Python order service with mapper, repository, cache, event bus, fraud API adapter, and response view.

## Initial State

`OrderStatusMapper.to_response` writes the database, invalidates cache, emits `OrderStatusChanged`, and calls the fraud API. A property getter also updates last-seen time.

## Files

- `orders/service.py`
- `orders/mapper.py`
- `orders/repository.py`
- `orders/cache.py`
- `orders/events.py`
- `tests/test_order_side_effects.py`

## Constraints

The starting point intentionally hides side effects in mapper and getter code. The benchmark expects explicit flow tracing, transaction ordering, and visible side-effect boundaries.
