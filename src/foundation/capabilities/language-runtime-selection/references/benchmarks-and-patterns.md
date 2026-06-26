# Language Runtime Benchmarks And Patterns

Use this reference when a runtime decision needs detailed workload matrices, decision rubric, validation mapping, or anti-pattern review. Keep `SKILL.md` focused on routing, evidence, and quality gates.

## Workload To Runtime Fit Matrix

This matrix is a starting point, not a substitute for current repository and workload evidence.

| Workload axis | Strong fits | Risk fits |
| --- | --- | --- |
| CPU-bound numeric or ML | C++20/23, Rust 2021, Go, Java 21 | Python unless C extensions own the hot path |
| IO-bound high-fanout RPC | Go, Rust with Tokio, Java 21 virtual threads, Node.js LTS | Node.js when CPU work mixes into the event loop |
| Latency-sensitive p99 under 10ms | Rust, C++, tuned Go, Java with low-pause GC | Python, Node.js, or default GC settings without evidence |
| Memory-sensitive or embedded | Rust, C++, Zig | GC runtimes with high heap floor |
| Batch or data pipeline | Python, Scala/Java, Go, Rust | Node.js when ETL library depth is weak |
| Interactive web frontend | TypeScript strict | Plain JavaScript for contract-heavy surfaces |
| Contract-heavy SDK or IDL | TypeScript, Rust, Go, Java | Dynamic languages without runtime schema validation |
| Scripts, glue, or CI | Bash with ShellCheck, Python | Compiled languages when startup and maintenance dominate |
| Systems, kernel, or driver | C, C++23, Rust 2021 | GC languages due latency and footprint |
| Edge or cold-start critical | Go, Rust, JS isolate runtimes | JVM or .NET without AOT/native-image evidence |

## Decision Rubric

Apply in order and stop when a candidate fails a hard gate:

1. Classify workload on the dominant and secondary axes.
2. Check whether an existing approved runtime is sufficient; prefer existing unless a hard constraint forces change.
3. Enumerate runtime behavior: GC, concurrency, exceptions, FFI, startup, binary or image size, observability, debugger, package manager, and boundary validation.
4. Name operational owner and on-call debug procedure.
5. Confirm hiring market or in-house upskilling plan with timeline.
6. Confirm lifecycle horizon from official support policy for at least three years or record an exception owner and retirement date.
7. Verify supply-chain posture: package manager integrity, dependency scan, license posture, and OpenSSF/SLSA/Scorecard or equivalent where applicable.
8. Estimate exit cost in engineer-quarters and define rollback or migration trigger.

## Runtime Validation Map

| Decision risk | Required evidence | Typical next gate |
| --- | --- | --- |
| GC pause or allocation risk | GC log, heap profile, allocation benchmark, latency budget comparison | `language-performance-safety` |
| Event-loop or scheduler blocking | event-loop lag, load/stress output, cancellation test, bounded executor proof | `concurrency-control` |
| Boundary validation drift | schema/runtime validator location, hostile input test, contract test | `language-testing-strategy` |
| Package ecosystem risk | dependency scan, package integrity, lockfile policy, license check | `package-dependency-management` |
| New build/deploy lane | CI command, build artifact, container/serverless shape, rollback path | `delivery-release-gate` |
| Unsupported or unfamiliar runtime | owner acceptance, support policy, incident debug procedure, retirement date | `reliability-observability-gate` |
| Unsafe, FFI, native, or embedded surface | safety invariant, sanitizer/race command, ABI or platform matrix | `low-level-systems-extension` |

## Anti-Pattern Review

- Runtime selected because the team prefers it, with no workload axis or rejected alternative.
- Public benchmark cited without matching input size, SLO, deployment topology, or version.
- Type system treated as external input validation.
- Existing runtime inventory skipped before introducing a new production language.
- EOL runtime accepted without owner, exception, retirement date, and migration path.
- One-language prototype used as production-scale proof.
- Runtime decision lacks build/test/security/observability commands.
- Project memory or old ADR treated as current proof after repository graph or workload changed.
