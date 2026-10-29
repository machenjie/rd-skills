# Test Suite

## Required Checks

Invoke all three candidate functions. Assert rational timestamps, seek bounds, cleanup, fixed-step conservation, replay identity, and device ordering and cache identity.

## Fixtures

`passing` implements the bounded contracts. Four faulty candidates each change one mechanism: timestamp precision, pause handling, completed host dependency, or full artifact identity. The starter is incomplete.

## Expected Commands

- `bash ../test-suite/run.sh`

## Regression Cases

Reject success-only evidence, paused-time stepping, reads before completion, and stale artifact reuse. Starter smoke alone is not positive candidate evidence.
