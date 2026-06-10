---
name: language-testing-strategy
description: Use when defining or reviewing tests by language and runtime, including unit, integration, contract, concurrency, property, snapshot, visual, fixture, mock, race, sanitizer, and CI execution choices.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "86"
changeforge_version: 0.1.0
---

# Mission

Define a professional test strategy matched to the chosen language and runtime, covering unit / integration / contract / concurrency / property / fuzz / snapshot / visual / accessibility / sanitizer / race tests, fixtures, mocks, and CI execution. The strategy must target the **actual failure modes of the runtime**, not generic test theater. Tests that pass while the system is broken are worse than no tests — they create false confidence.

# When To Use

Use when defining or reviewing the test plan for a change in a chosen language/runtime, when test gaps are unclear, when runtime-specific failure modes are likely (races, GC, async, FFI, native memory, type-erasure), or when CI must prove language-specific safety properties. Use whenever AI-generated tests are merged — they tend to test the mock, not the behavior.

# Do Not Use When

Do not use to generate broad test catalogs unrelated to change risk. Do not use to replace acceptance criteria with framework-specific test mechanics (acceptance criteria live in `acceptance-standard-definition`).

# Non-Negotiable Rules

- **Test strategy must match the runtime's actual failure modes.** Go/Rust/Java need race tests for concurrency changes; C/C++ need sanitizer runs; Python/JS need runtime boundary validation; TS frontend needs behavior + accessibility tests, not just snapshot tests.
- **CI runs the checks that prove the stated risk.** A passing CI without race detector / sanitizer / fuzzer / mutation-testing on relevant code paths is not evidence of safety.
- **Dynamic-language tests must include runtime boundary validation tests.** Type hints are not tests.
- **Concurrent code without race-detector evidence is rejected.** Go `-race`, Rust `loom` / `cargo test --release` with TSAN, Java jcstress for low-level concurrency primitives, C/C++ TSan.
- **Coverage % is a floor, not a goal.** ≥ 80% line coverage is common but meaningless without mutation testing on critical logic (target mutation score ≥ 60% on business-critical modules).
- **Snapshot/golden tests require explicit owner and review discipline.** Auto-accepting snapshot diffs is a known anti-pattern — `git diff` of snapshots must be reviewed line-by-line.
- **External-input tests must include hostile input.** Fuzz / property tests against parsers, deserializers, query builders. CWE-mapped boundary tests for security-relevant inputs.
- **No test relies on production-only resources.** Tests are hermetic; integration tests use ephemeral containers (testcontainers) or recorded fixtures; secrets via test-only credentials.

# Industry Benchmarks

- **Test pyramid** (Cohn) and **test honeycomb** (Spotify) — heavy on fast unit/integration, narrow at end-to-end UI. For backend services, the inverted-trapezoid (unit + integration > E2E) is the modern guidance.
- **DORA — Accelerate**: test automation, deployment automation, trunk-based development are predictors of elite performance.
- **Property-based testing**: Hypothesis (Python), proptest / quickcheck (Rust), jqwik (Java), fast-check (TS), go-quick / gopter (Go).
- **Mutation testing**: mutmut / cosmic-ray (Python), Stryker (TS/JS/.NET), PIT (Java), cargo-mutants (Rust), go-mutesting (Go). Mutation score ≥ 60% on critical logic.
- **Race / sanitizer tooling**: `go test -race`, Rust `loom` + `-Z sanitizer=thread`, Java jcstress, C/C++ TSan/ASan/UBSan/MSan, Python `faulthandler` + `pytest-asyncio` cancellation tests.
- **Fuzzing**: native `go test -fuzz` (Go 1.18+), `cargo fuzz` (libFuzzer), AFL++, OSS-Fuzz integration for OSS, Atheris (Python).
- **Contract testing**: Pact, Spring Cloud Contract, OpenAPI-driven schemathesis, gRPC service-protobuf compatibility checks (buf breaking).
- **Frontend**: Testing Library + Playwright + axe-core for accessibility; Lighthouse CI budgets for performance regressions.
- **Coverage tooling**: pytest-cov / coverage.py (Python), go test -cover + go tool cover, cargo-llvm-cov / tarpaulin (Rust), JaCoCo (Java), c8 / vitest (TS/JS), gcov / llvm-cov (C/C++).

# Selection Rules

Select this capability when language/runtime selection changes the test obligations of a change. Always pair with `quality-test-gate` for release evidence and the matching `<lang>-professional-usage` capability for tool-specific commands and pinned versions.

### Pyramid composition (starting points by language; tune to product)

```
Language / runtime  | Unit | Integration | Contract | E2E / UI | Special required
--------------------|------|-------------|----------|----------|----------------------------
Python 3.11+        | 60%  | 25%         | 10%      | 5%       | Boundary validators (pydantic),
                    |      |             |          |          | asyncio cancellation tests
Go 1.22+            | 60%  | 25%         | 10%      | 5%       | `go test -race` mandatory for
                    |      |             |          |          | concurrent code, table-driven tests
Rust 2021           | 65%  | 20%         | 10%      | 5%       | proptest for parsers, loom for
                    |      |             |          |          | concurrency primitives, miri for unsafe
TypeScript 5.4+     | 50%  | 25%         | 10%      | 15%      | Testing Library + axe (frontend),
                    |      |             |          |          | zod/valibot runtime checks
Java 21 LTS         | 60%  | 25%         | 10%      | 5%       | JUnit 5 + Testcontainers + ArchUnit,
                    |      |             |          |          | jcstress for low-level concurrency
C++20/23            | 60%  | 25%         | 5%       | 10%      | ASan + UBSan + TSan + MSan CI lanes,
                    |      |             |          |          | fuzz harnesses for parsers
SQL (migrations)    | n/a  | 70% (against| 30%      | n/a      | Forward + rollback in CI,
                    |      | real engine)|          |          | data-shape & perf assertion
Shell (Bash 4+)     | 60%  | 30%         | n/a      | 10%      | shellcheck + bats-core + --dry-run path
```

# Risk Escalation Rules

- Escalate to `quality-test-gate` when evidence is missing or coverage of stated risk is incomplete.
- Escalate to `reliability-observability-gate` for load / soak / chaos / stress tests proving production behavior.
- Escalate to `security-privacy-gate` for boundary tests involving hostile input, secrets, deserialization, or authn/authz.
- Escalate to `language-performance-safety` for hot-path, allocation, and concurrency-stress test design.
- Escalate to `concurrency-control` for race-detector and stress-test design for concurrency primitives.
- Escalate to `ai-code-review-refactor` when tests are AI-generated and may be testing mocks rather than behavior.

# Critical Details

- **Tests verify behavior at runtime, not source shape.** Snapshot tests that compare serialized object structure pass while the rendered behavior is broken. Behavior tests (rendered output, side-effect observed, downstream state) catch real defects.
- **Race tests need stress, not single-run pass.** `go test -race -count=100 -timeout=10m`; Rust `loom::model` for permutation coverage of concurrency primitives.
- **Cancellation / timeout / context-deadline propagation requires explicit tests.** A concurrent change without cancellation tests is incomplete.
- **Mocks become liabilities when they drift from the real dependency.** Prefer fakes/in-memory implementations over mocks; pair every mocked external dependency with a contract test against the real one.
- **Test data must include edge cases**: empty collection, single element, max size, unicode (incl. surrogate pairs, RTL, zero-width), null/missing, malformed encoding, timezone boundaries, leap day, DST transition, numeric overflow.
- **Coverage gaming**: 100% line coverage on a getter is worthless; 60% mutation score on a pricing algorithm is meaningful. Direct coverage measurement at critical business logic, not at trivial code.
- **Flaky tests are tickets, not retries.** A test that passes 9/10 runs is broken; CI `retry` flags hide real concurrency / ordering / time-dependence bugs.

# Failure Modes

- **Snapshot pass / behavior broken** — Symptom: tests green, user-facing render is wrong. Cause: snapshot auto-accepted, no behavior assertion. Detection: behavior test added; visual regression run. Impact: defects ship undetected.
- **Race in production not in CI** — Symptom: heisenbug only under load. Cause: race detector not in CI. Detection: `go test -race -count=N` in CI. Impact: data corruption, intermittent failure.
- **Unvalidated dynamic input** — Symptom: Python service crashes on malformed JSON. Cause: type hints assumed; no pydantic/marshmallow validator. Detection: boundary-validation test with malformed fixture. Impact: outage, error-budget burn.
- **Sanitizer-free native code** — Symptom: UB / memory corruption in C++. Cause: no ASan/UBSan/TSan/MSan CI lane. Detection: add sanitizer lane. Impact: silent corruption, security exposure.
- **Contract drift** — Symptom: SDK consumers break on minor bump. Cause: public API change without contract test. Detection: buf breaking / pact / openapi-diff in CI. Impact: ecosystem-wide breakage.
- **Mock-tests-mock** — Symptom: tests pass, integration fails immediately. Cause: mock returns shape that real service never produces. Detection: pair mock with contract test; periodic test against staging. Impact: false confidence.
- **Flaky retry masking** — Symptom: CI `retry: 3` hides 30% flake rate. Cause: time/order/concurrency bug treated as infra noise. Detection: flake-quarantine + root-cause SLA. Impact: real bugs ride flakes into production.
- **Coverage % gamed** — Symptom: 95% line coverage, mutation score 10%. Cause: tests exercise lines without asserting behavior. Detection: mutation testing on critical modules. Impact: hidden defect surface.

# Reference Loading Policy

Read `references/checklist.md` when runtime-specific test obligations are in scope: async/sync boundaries, race detectors, sanitizers, fuzz/property tests, mutation testing, framework selection, fixture lifecycle, or CI language-tool lanes. Do not load it for a language-agnostic test-level decision already covered by `quality-test-gate`.

# Output Contract

Return a **Language Test Plan** containing:
- **Risk areas** for the change, prioritized by impact × likelihood
- **Test types selected** per risk area (unit / integration / contract / property / fuzz / race / sanitizer / E2E / accessibility / load) with rationale
- **Per-language tool pins** (test runner, race detector, sanitizer, fuzzer, mutation-testing, contract-testing, coverage tool) with versions
- **Fixtures / fakes / contract pairings** with ownership
- **CI command list** (exact commands as runnable in CI, with flags `-race`, `-fuzz=`, sanitizer flags, mutation-score floor)
- **Coverage targets** (line floor + mutation-score target on critical modules)
- **Acceptance-evidence mapping** — which acceptance criterion is proved by which test
- **Coverage gaps** explicitly listed with owner and resolution plan
- **Flake protocol** — quarantine path, root-cause SLA

# Evidence Contract

A language testing strategy is complete only when the output includes:

- **Language runtime risk**: async/sync boundary, memory ownership, concurrency model, type/runtime validation, package/build system, or fixture lifecycle.
- **Layer selection**: unit, integration, contract, E2E, property, mutation, snapshot, benchmark, race/concurrency test with rationale.
- **Framework fit**: selected test framework and why it matches the language/runtime.
- **Fixture ownership**: setup/teardown, isolation, parallelism, deterministic data, and cleanup.
- **Language-specific validation**: typecheck, race detector, sanitizer, mutation test, async test harness, or equivalent.
- **What evidence proves**: the language-specific failure mode is covered.
- **What evidence does not prove**: cross-language boundary, production runtime, external dependency, performance behavior, or platform-specific behavior.
- **Residual risk**: untested runtime behavior, owner, and next gate.

# Quality Gate

1. Every material runtime failure mode (concurrency, async, boundary, FFI, GC, native memory) has a corresponding test or documented compensating evidence.
2. Race-detector / sanitizer / fuzz lanes present and passing for languages that require them (Go/Rust/Java concurrency, C/C++ memory, parsers/deserializers fuzzing).
3. Mutation score on critical business modules ≥ 60% (or explicit waiver with owner).
4. Boundary validation tests present for every external input surface; hostile-input tests for security-relevant boundaries.
5. Contract tests present for every public API / SDK / cross-service interface; `buf breaking` / `openapi-diff` in CI for IDL-defined contracts.
6. No CI test-retry / flake-tolerance flag; flakes go to quarantine with root-cause SLA.
7. CI is reproducible: same command, same result, on any machine.

# Used By

quality-test-gate, backend-change-builder, frontend-change-builder, ai-code-review-refactor

# Handoff

- **`quality-test-gate`** for execution and release evidence collection.
- **Matching `<lang>-professional-usage` capability** for tool-specific commands, version pins, and CI templates.
- **`reliability-observability-gate`** for load / soak / chaos tests proving production-shape behavior.
- **`security-privacy-gate`** for hostile-input / authn / authz / deserialization boundary tests.
- **`concurrency-control`** for race-detector and stress design on concurrency primitives.

# Completion Criteria

Test strategy is complete when: every material runtime failure mode has a corresponding test in CI; race / sanitizer / fuzz / mutation tooling is invoked on the code paths that need them; coverage targets (line floor + mutation score on critical modules) are met or waived with owner; contract tests guard public APIs; boundary tests guard external inputs; and tests can be reproduced on any machine with the same command.
