# Harness Validity Contracts

**Load when:** Test discovery, orchestration, oracle, fixtures, negative controls, benchmark measurement, or harness exit behavior can change the decision.

**Do not load when:** An unchanged existing harness directly proves the accepted behavior and failure mechanism.

**Required by:** `task-agent`

**Required output:** `decision-record`, `validation-plan`, `proof-limit`

Official sources were accessed on 2026-07-26.

## One Decision

Select one harness contract whose discovery, execution, oracle, and reporting distinguish the target behavior from harness failure.

| Fact to establish | Required decision | Failure signal |
|---|---|---|
| Target mechanism | Name the changed behavior, regression mechanism, boundary, and smallest representative fixture | A broad green run can omit the changed path |
| Discovery | Define suite roots, filters, tags, shards, exclusions, and empty-selection behavior | Zero selected tests return success without an explicit signal |
| Oracle | Bind expected output or state to an independent assertion source | The harness reproduces the implementation's defect in its expected value |
| Controls | Make the valid case pass and a deliberately invalid case fail for the intended reason | Reintroducing the defect leaves the harness green |
| Isolation | Control files, environment, time, randomness, network, concurrency, and shared state | Results depend on run order, workstation state, or prior output |
| Exit and reporting | Separate test failure, infrastructure failure, skip, timeout, crash, and malformed result | Infrastructure loss is reported as passing or ordinary product failure |
| Benchmark measurement | Define metric, unit, workload, setup exclusion, warmup, repetitions, variance, baseline, and comparison rule | Noise, optimization, setup, or host drift dominates the claimed effect |

## Decision Rules

- Require a negative control for a new or materially changed harness path.
- Fail clearly on empty discovery unless emptiness is the accepted result.
- Keep benchmark correctness checks separate from performance measurement.
- Record skipped, flaky, retried, partial, and unavailable evidence.
- Do not use coverage percentage as proof that the regression mechanism was asserted.

## Primary Sources

- [Bazel Test Encyclopedia](https://bazel.build/reference/test-encyclopedia)
- [LLVM Integrated Tester](https://llvm.org/docs/CommandGuide/lit.html)
- [JUnit User Guide](https://docs.junit.org/current/user-guide/)
- [Go testing package](https://pkg.go.dev/testing)
- [Google Benchmark user guide](https://google.github.io/benchmark/user_guide.html)

## Proof Limits

Framework documentation does not prove repository discovery, fixtures, filters, isolation, negative controls, benchmark stability, or CI execution. A local harness result also does not prove production behavior or performance outside the measured environment.
