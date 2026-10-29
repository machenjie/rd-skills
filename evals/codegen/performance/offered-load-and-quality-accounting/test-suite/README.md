# Test Suite

## Required Checks

Intended versus actual arrivals, queue delay, planned and service latency, terminal outcomes, pending work, explicit policies, and hosted versus self-hosted inputs.

## Fixtures

`fixtures/passing/subject.py` is the positive control. The faulty control changes only the unsent count to zero. The runnable starter is incomplete.

## Expected Commands

- `bash ../test-suite/run.sh`

## Regression Cases

Discarding unsent arrivals or measuring latency only after actual start. Approving higher throughput despite violated quality, tail-latency, or cost constraints. The real assertion runner executes candidate functions; smoke alone proves neither passing behavior nor production validity.
