# Test Suite

## Required Checks

- Blocking call on event loop is rejected by static or runtime review.
- CPU-bound work on event loop is rejected and must move to worker or executor.
- Promise.all or gather unbounded is rejected.
- Timeout and cancellation behavior is tested.

## Fixtures

- Large report fixture.
- Slow file or SDK fixture.
- Downstream notification list exceeding the concurrency limit.

## Expected Commands

Run `bash ../test-suite/run.sh` from the starter repo.

## Regression Cases

- Blocking call on event loop must fail.
- Promise.all or gather unbounded must fail.
- No timeout or cancellation must fail.
- Event-loop lag measurement or profile plan must be present.
