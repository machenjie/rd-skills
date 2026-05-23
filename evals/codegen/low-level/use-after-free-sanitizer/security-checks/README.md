# Security Checks

## Threat Surface

This benchmark touches memory ownership, use after free prevention, sanitizer testing, FFI boundary safety. A flawed implementation can expose data, weaken integrity, hide operational failure, or ship a release path that cannot be safely reviewed.

## Required Checks

- Verify that the API documents who owns every pointer and when it is valid.
- Verify that tests run with sanitizer flags or an equivalent memory safety tool.
- Verify that error paths release resources exactly once.
- Verify that no global mutable ownership workaround hides the bug.

## Rejection Cases

- Reject any solution that uses returning pointers to freed or stack allocated memory.
- Reject any solution that uses disabling sanitizer checks to pass the benchmark.
- Reject any solution that uses leaking buffers to avoid defining ownership.
- Reject implementations that pass happy path checks while skipping denial, rollback, or failure-mode evidence.
