# Test Suite

## Required Checks

- Expired reservations cannot be silently fulfilled by late payment.
- Repeated cancellation preserves inventory and partial returns preserve conservation.
- SaaS entitlement follows the explicit grace, downgrade, refund, seat, and usage policies.
- Shrinking retains reservation preconditions and replays a minimal duplicate-cancellation counterexample.

## Fixtures

`fixtures/passing` supplies an executable accepted candidate. The named faulty fixture changes one mechanism. `starter-repo` remains deliberately incomplete. Assertion oracles do not import candidate helpers or read expected-result flags from input records.

## Expected Commands

- `bash ../test-suite/run.sh`

## Regression Cases

- Seven executable assertion methods cover arithmetic, time, identity, and policy.
- Twenty bounded generated quantity/replay combinations challenge conservation.
- A stored three-event counterexample is minimized and replayed.
- Passing, incomplete starter, and duplicate-release control are run separately.

Default smoke validates starter rejection. The passing fixture and faulty control also require explicit execution through the existing assertion runner.
