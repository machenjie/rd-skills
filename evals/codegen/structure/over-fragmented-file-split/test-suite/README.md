# Test Suite

## Required Checks

- Public behavior test for standard cancellation.
- Public behavior test for premium grace cancellation.
- Public behavior test for disputed cancellation with refund hold.
- Public behavior test for denied authorization.
- Static review or structure evidence rejects one-function file and micro-file
  sprawl.

## Fixtures

Order fixtures live under the orders test boundary and describe behavior states:
standard cancellable order, premium grace order, disputed order, denied actor,
and deadline-expired order. Fixtures must not import private helper predicates.

## Expected Commands

- `bash ../test-suite/run.sh`

## Regression Cases

- Existing deadline denial remains unchanged.
- Existing refund-hold behavior remains unchanged for non-disputed orders.
- A future maintainer can place the next adjacent cancellation rule in an
  obvious owner file without broad search.
- Review fails any implementation that splits tiny cohesive helpers into
  separate files.
