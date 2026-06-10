# Test Suite

## Required Checks

- Lock held across network or storage IO is rejected.
- Concurrent update test exercises the named invariant.
- Timeout behavior is covered or documented.
- Deadlock analysis and stress or race evidence are required.

## Fixtures

- Slow repository fixture.
- Slow notifier fixture.
- Concurrent account update fixture.

## Expected Commands

Run `bash ../test-suite/run.sh` from the starter repo.

## Regression Cases

- Lock held across network or storage IO must fail review.
- No timeout must fail.
- No deadlock analysis must fail.
- No stress or race evidence must fail.
