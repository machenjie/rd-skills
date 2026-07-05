# Language Testing Runtime Tooling

Use this reference when a language test plan needs concrete command families, CI lane shape, or tool-choice calibration. Prefer the matching `<lang>-professional-usage` capability for project-specific versions and package manager conventions.

## Command Families

| Runtime | Fast feedback | Boundary / contract | Runtime safety | Deeper confidence |
| --- | --- | --- | --- | --- |
| Python | `pytest -q`, `pytest -k <risk>` | pydantic/marshmallow invalid fixtures, schemathesis, Pact | `pytest-asyncio` cancellation, `faulthandler`, dependency import smoke | Hypothesis, mutmut/cosmic-ray, coverage.py with branch coverage |
| TypeScript / JavaScript | `npm test`, `vitest run`, `jest --runInBand` when needed | zod/valibot invalid fixtures, OpenAPI/Pact, Playwright API tests | fake timers, abort/cancellation tests, unhandled rejection fail-fast | fast-check, Stryker, c8/nyc branch coverage |
| Go | `go test ./...`, table tests | contract fixtures, `go test -run <boundary>` | `go test -race -count=N`, context cancellation tests | `go test -fuzz`, coverage profiles, mutation tools when available |
| Rust | `cargo test`, `cargo test --release` | serde/proptest fixtures, `buf breaking` where proto is used | `loom`, `miri`, panic boundary tests | `cargo fuzz`, `cargo-mutants`, cargo-llvm-cov |
| Java / JVM | Maven/Gradle unit test tasks | Spring Cloud Contract, Pact, Testcontainers, jqwik | jcstress for low-level concurrency, timeout/interruption tests | PIT mutation, JaCoCo, ArchUnit for test boundary enforcement |
| C / C++ | `ctest`, target-level unit tests | parser fixtures, ABI/API compatibility checks | ASan, UBSan, TSan, MSan lanes | libFuzzer/AFL++, gcov/llvm-cov, valgrind where appropriate |
| SQL / migrations | migration dry run on real engine | forward/rollback fixtures, schema diff | lock/timeout and transaction isolation checks | pgTAP/dbt tests, representative query plans, data-shape assertions |
| Shell / CLI | shellcheck, bats-core | CLI contract fixtures, stdout/stderr/exit-code tests | `set -euo pipefail` behavior, dry-run/destructive guard tests | shfmt, integration tests against temp dirs and fake commands |

## CI Lane Selection

- Keep a fast deterministic lane for every change: unit or focused integration command that can fail for the changed path.
- Add a risk lane only when the runtime needs it: race, sanitizer, fuzz, mutation, generated-client compile, contract replay, or visual/a11y browser check.
- Pin tool versions through the project package manager or CI image; do not prescribe global installs unless the repository already uses them.
- Store reports under the project convention and name the artifact path in the handoff.

## Evidence Notes

- A command family is not evidence until it is run with current source, reports an exit code, and maps to the changed path.
- Coverage is supporting evidence only; pair it with behavior, mutation, contract, or runtime-safety evidence for material risks.
- If a tool is unavailable locally, record the exact CI lane or owner needed and mark the evidence as not run instead of treating the plan as proof.
