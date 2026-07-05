# Starter Repo

## Stack

Node.js or Python async service with endpoint tests.

## Initial State

An async handler performs CPU-bound parsing, synchronous file/network IO, and
unbounded downstream fan-out on the request path.

## Files

- `src/reportHandler.ts` or `app/report_handler.py`
- `src/reportWorker.ts` or `app/report_worker.py`
- `tests/test_report_handler.*`

## Constraints

The benchmark rejects event-loop blocking, unbounded fan-out, and missing
timeout or cancellation behavior.
