# Benchmark Prompt

## Task

Implement a focused change to make monorepo affected test selection include dependency graph, lockfile, generated inputs, and fallback rules.

## Context

The starter repo represents a CI job skips tests by selecting packages affected by changed files. In its initial state, the starter behavior only maps direct source file paths and misses shared generated contracts. The implementation should be small enough to review but complete enough to prove the professional quality target.

## Requirements

- Changed shared packages select downstream test suites.
- Lockfile and generated contract changes invalidate affected test caches.
- Unknown paths fall back to a broader safe test set.
- CI output explains selected and skipped tests.

## Constraints

- Module graph edges include generated and runtime dependencies.
- Tests cover direct, transitive, lockfile, generated, and unknown path cases.
- Cache keys include dependency graph and tool version inputs.
- Preserve the existing public contract unless the prompt explicitly asks for a compatible addition.
- Do not replace the benchmark with documentation-only output.

## Deliverables

- Source changes in the starter repo that implement the requested behavior.
- Tests or executable checks that prove the required behavior and denial paths.
- A short implementation note describing important tradeoffs and residual risk.

## Completion Evidence

- `bash setup.sh`
- `bash ../test-suite/run.sh`
- `bash ../security-checks/run.sh`
- Review evidence that no automatic failure condition applies.
