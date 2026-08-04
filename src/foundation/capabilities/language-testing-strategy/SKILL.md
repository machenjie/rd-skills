---
name: language-testing-strategy
description: "`analysis-agent`/`task-agent`/`review-agent`: use when test results depend on runner, concurrency, timeout, cache, or isolation semantics; skip test-portfolio work."
---

# language-testing-strategy

## Registry Trigger

**Use when**

- Test evidence depends on runner discovery, process/thread/event-loop behavior, parallelism, deadlines, caching, instrumentation, or fixture lifecycle.
- An accepted test boundary needs language/runtime-specific harness behavior before its result is comparable locally and in CI.

**Do not use when**

- The open decision is the failure-to-test-level portfolio, oracle, or omission; use `test-strategy` and the relevant test-level capability.
- The runner and runtime behavior are fixed and no affected cache, isolation, concurrency, timeout, or tooling decision remains.

## Skill Role

Define test-runner and runtime execution semantics through discovery, scheduling, deadlines, async completion, isolation, cache freshness, instrumentation, and reproducible failures. Exclude proof-portfolio and case selection.

## High-Value Rules

- Verify runner version, configuration, discovery filters, shards, environment, and local/CI invocation from current repository sources before comparing results.
- Match test concurrency to the affected runtime model; shared module, class, process, database, port, or global state has an isolation owner, and a serial pass is not concurrency proof.
- Distinguish a runner timeout from the system deadline under test; cancellation reaches the subject, owned work terminates, and cleanup becomes observable before the harness exits.
- Await or join owned async work and surface background panics, rejected promises, task exceptions, and subprocess failures instead of letting the test finish first.
- Invalidate watch, incremental, test-result, transform, coverage, and build caches when their source, config, environment, generated input, or instrumentation key changes.
- Define fixture ownership for temporary paths, ports, environment, clock, randomness, locale, timezone, processes, and containers, including parallel isolation and cleanup on failure.
- Select failure-mechanism-specific test modes with reproducible first-failure evidence and repository-authorized limits.
- Return the language-test execution decision with inspected harness evidence, proof limits, and specialist routes even when no Reference loads.

## Anti-Patterns

- A command catalog selects a runner or flag without checking the repository version and configuration.
- A cached, watched, serial, or filtered pass is reported as evidence for a different CI shard or runtime mode.
- A runner timeout or retry converts a hang, leak, deadlock, or flake into a passing result.
- Coverage or instrumentation changes scheduling, module loading, or emitted code while the result is treated as equivalent.

## Stop Conditions

- Route risk portfolios to `test-strategy` and case design to `unit-testing`, `integration-testing`, `contract-testing`, `e2e-testing`, or `frontend-testing`.
- Route runner dependencies to `package-dependency-management`, lanes and cache keys to `build-tool-professional-usage`, and final freshness or sufficiency to `quality-test-gate`.

## Output Contract

- language-test execution decision with runner discovery scheduling deadline cancellation async completion isolation cache instrumentation failure artifact proof limits and specialist routes

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [runtime tooling](references/runtime-tooling.md) | targeted | Test evidence depends on runner discovery concurrency deadline cancellation cache isolation or instrumentation semantics | Repository and CI use one established runner mode with no affected runtime-sensitive harness behavior | analysis-agent, task-agent, review-agent | validation-plan, proof-limit |
