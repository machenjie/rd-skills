# Security Checks

## Threat Surface

This benchmark touches affected test selection, module graph accuracy, build cache safety, CI fallback. A flawed implementation can expose data, weaken integrity, hide operational failure, or ship a release path that cannot be safely reviewed.

## Required Checks

- Verify that module graph edges include generated and runtime dependencies.
- Verify that tests cover direct, transitive, lockfile, generated, and unknown path cases.
- Verify that cache keys include dependency graph and tool version inputs.
- Verify that periodic full suite fallback is documented.

## Rejection Cases

- Reject any solution that uses selecting tests only from direct file path prefixes.
- Reject any solution that uses ignoring lockfile or generated contract changes in cache keys.
- Reject any solution that uses skipping all tests for unknown paths.
- Reject implementations that pass happy path checks while skipping denial, rollback, or failure-mode evidence.
