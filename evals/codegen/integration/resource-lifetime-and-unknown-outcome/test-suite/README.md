# Test Suite

## Required Checks

Read, cancel, normal completion, error cleanup, repeated effect cleanup, cache identity, outcome reconciliation, persistent migration, and host message identity.

## Fixtures

`fixtures/passing/subject.py` is the positive control. The faulty control adds one premature resource close before each yielded chunk. The runnable starter is incomplete.

## Expected Commands

- `bash ../test-suite/run.sh`

## Regression Cases

Closing the resource before the stream consumer finishes. Repeating a completed operation after timeout or sharing cached values across tenants. The real assertion runner executes candidate functions; smoke alone proves neither passing behavior nor production validity.
