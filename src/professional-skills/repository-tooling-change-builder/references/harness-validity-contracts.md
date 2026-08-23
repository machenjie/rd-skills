# Harness Validity Contracts

**Load when:** Test discovery, orchestration, oracle, fixtures, negative controls, benchmark measurement, or harness exit behavior can change the decision.

**Do not load when:** An unchanged existing harness directly proves the accepted behavior and failure mechanism.

**Required by:** `task-agent`

**Required output:** `decision-record`, `validation-plan`, `proof-limit`

Sources accessed 2026-07-26.

## Decision Rules

- Name the changed mechanism, boundary, and smallest representative fixture.
- Define suite roots, filters, tags, shards, exclusions, and empty-selection behavior.
- Fail empty discovery unless emptiness is the accepted result.
- Bind expected output or state to an independent oracle.
- Make the valid case pass and an invalid case fail for the intended reason.
- Control files, environment, time, randomness, network, concurrency, and shared state.
- Distinguish test failure, infrastructure loss, skip, timeout, crash, and malformed output.
- Record flaky, retried, partial, skipped, and unavailable evidence.
- Keep benchmark correctness separate from performance measurement.
- Define benchmark metric, unit, workload, setup exclusion, warmup, repetitions, variance, baseline, and comparison.
- Do not substitute coverage percentage for an asserted regression mechanism.

## Primary Sources

- [Bazel tests](https://bazel.build/reference/test-encyclopedia); [LLVM lit](https://llvm.org/docs/CommandGuide/lit.html); [JUnit](https://docs.junit.org/current/user-guide/); [Go testing](https://pkg.go.dev/testing); [Google Benchmark](https://google.github.io/benchmark/user_guide.html).

## Proof Limits

Sources do not prove repository discovery, fixtures, filters, isolation, controls, benchmark stability, or CI. Local results do not prove production behavior or performance beyond the measured environment.
