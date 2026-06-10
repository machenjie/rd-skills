# Test Suite

## Required Checks

- Composition root constructs app-scoped clients and passes dependencies explicitly.
- Request, job, transaction, and operation scoped dependencies are distinguishable.
- Service locator usage and circular dependency graph are rejected unless framework convention justifies them.
- Shutdown cleanup closes pool, timer, subscription, file, socket, and client resources.

## Fixtures

Wiring fixtures belong under the worker boundary and must name which lifecycle scope they represent.

## Expected Commands

- `bash ../test-suite/run.sh`

## Regression Cases

- Per-request HTTP or DB client construction fails review.
- Test override does not mutate global production wiring.
- Startup validation catches missing typed configuration.
- Shutdown cleanup remains idempotent.
