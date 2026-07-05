# Starter Repo

## Stack

Python worker service with HTTP, database, queue, retry timer, and cache dependencies.

## Initial State

The worker constructs HTTP and DB clients inside `handle_message`, reaches into a global locator, and never closes the retry timer or queue subscription.

## Files

- `invoice_sync/app.py`
- `invoice_sync/worker.py`
- `invoice_sync/clients.py`
- `invoice_sync/locator.py`
- `tests/test_worker_wiring.py`

## Constraints

The starting point intentionally has per-operation client construction and missing shutdown cleanup. The benchmark expects composition root ownership and lifecycle scope evidence.
