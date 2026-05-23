# Test Suite

## Required Checks

- Buffer ownership is explicit across allocation, transfer, and release.
- Use after free is eliminated under address sanitizer.
- FFI callers receive a stable release contract.
- Regression tests cover normal parse, error parse, and double release denial.

## Fixtures

- Fixture data for memory ownership.
- Fixture data for use after free prevention.
- Fixture data for sanitizer testing.
- At least one denied or failure fixture that proves the implementation does not take a forbidden shortcut.

## Expected Commands

- `bash ../test-suite/run.sh`

## Regression Cases

- Reject shortcut: Returning pointers to freed or stack allocated memory.
- Reject shortcut: Disabling sanitizer checks to pass the benchmark.
- Existing successful behavior remains available after the new guard or compatibility path is added.
