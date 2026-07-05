# Test Suite

## Required Checks

Run the benchmark harness and, during candidate evaluation, the optional
complexity assertion script.

## Fixtures

The protected fixture is the public billing rule behavior plus review artifacts
containing the Complexity Delete List.

## Expected Commands

- `bash ../test-suite/run.sh`
- `CHANGEFORGE_CODEGEN_EVALUATE=1 bash ../test-suite/run.sh` for candidate assertions.

## Regression Cases

- Billing behavior remains covered by a public regression test or review evidence.
- Wrapper-only delegation is rejected.
- One-implementation interface, factory, or strategy for future proofing is rejected.
- Delete findings include caller search and regression evidence.
