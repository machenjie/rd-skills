# Test Suite

## Required Checks

The pytest assertions scan candidate artifacts for the capability-specific evidence required by Minimal Correct Native Reuse. They check final code or evidence files as well as handoff-oriented artifacts such as `process-trace.json`, `final.md`, and `diff.patch` when present.

## Fixtures

The suite uses the benchmark worktree produced by `starter-repo/setup.sh`. It does not require network access, credentials, or user-specific files.

## Expected Commands

- `./test-suite/run.sh`
- `python -m pytest test-suite/tests`

## Regression Cases

- Missing explicit capability evidence fails the case.
- Telemetry-only evidence does not satisfy assertion-backed requirements.
- Raw prompt, secret, full command output, or local absolute path leakage fails relevant checks.
- Final handoff claims unsupported by validation or residual-risk evidence fail the case.
