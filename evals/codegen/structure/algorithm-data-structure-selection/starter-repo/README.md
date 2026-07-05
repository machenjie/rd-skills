# Starter Repo

## Stack

Python batch reconciliation job with iterable ledger and provider row sources.

## Initial State

The job loads all 10M ledger rows and provider rows into lists, performs nested scans, sorts large intermediates, and computes top-K unmatched results without memory or complexity evidence.

## Files

- `reconcile/job.py`
- `reconcile/sources.py`
- `reconcile/topk.py`
- `tests/test_reconcile.py`

## Constraints

The starting point intentionally uses O(n squared) and load-all behavior. The benchmark expects input scale, complexity, memory, and streaming evidence.
