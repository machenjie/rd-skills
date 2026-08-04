# Test Runner Execution Contract

This contract compares language/runtime harness behavior after the task's failure mechanism and test boundary are selected.

## Runner Decision Matrix

| Harness facet | Repository facts to establish | Accident signal |
| --- | --- | --- |
| Discovery and invocation | Runner and plugin versions, config sources, file filters, tags, shards, working directory, environment, and local/CI commands | Local selection exercises different files, config, or environment from the authoritative lane |
| Scheduling model | Process, thread, event-loop, worker, fork, parallelism, ordering, and shared-state rules | A serial or isolated pass hides a race, ordering dependency, leaked global, or port collision |
| Deadline and cancellation | Runner timeout, system deadline under test, cancellation injection, owned-work termination, and cleanup observation | The harness kills the process before the subject handles cancellation or exposes leaked work |
| Async completion | Awaited tasks, goroutines, promises, subprocesses, background exceptions, and failure observation | The test returns green while owned work rejects, panics, blocks, or mutates later |
| Fixture isolation | Temp paths, ports, database/schema/topic namespace, environment, clock, randomness, locale, timezone, and cleanup owner | Parallel or failed cases share mutable state or leave resources for later evidence |
| Cache and watch state | Test-result, transform, build, module, coverage, watch, and incremental cache keys and invalidators | Changed source, config, generated input, or environment reuses a stale result |
| Instrumentation and stress | Coverage, race, sanitizer, fuzz, property, mutation, repetition, and scheduling effects | The evidence mode changes code or timing without that difference being disclosed |
| Failure artifact | First failure, seed, schedule, shard, command, environment, logs, cleanup status, retry containment, and not-run gap | Retry or rerun replaces the original signal and removes reproduction evidence |

## Decision Limits

- Select the repository's fastest deterministic lane that can fail for the accepted mechanism, or a gap-owned broader lane when no such lane exists.
- Treat coverage and instrumentation as supporting evidence whose timing, emission, and cache effects are named beside behavior proof.
- A passing command establishes the exercised runner modes and environment, not omitted shards, production scheduling, hidden consumers, or final release sufficiency.
