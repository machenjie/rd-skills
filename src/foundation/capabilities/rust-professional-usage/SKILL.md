---
name: rust-professional-usage
description: Use when writing or reviewing professional Rust for systems, services, CLIs, WASM, or performance-sensitive modules with focus on ownership, lifetimes, Result modeling, traits, async runtime, unsafe invariants, concurrency safety, and zero-cost abstraction.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "93"
changeforge_version: 0.1.0
---

# Mission

Enforce professional Rust usage for systems, services, CLIs, WASM, and performance-sensitive modules: ownership and lifetime discipline, `Result`-based error modeling, justified trait abstractions, explicit async-runtime choice, documented `unsafe` invariants, concurrency safety, and zero-cost abstractions backed by measurement. Reject `Box<dyn Trait>` hierarchies that mimic Java; reject `unwrap()` in library code; reject `unsafe` without a written safety contract.

# Pinned Tooling Baseline (Rust)

Pinned versions are review baselines, not permanent recommendations. If a pinned baseline is EOL, superseded, unsupported, or conflicts with the target project's approved platform policy, update this capability before relying on it for new product work.

- **Toolchain**: stable Rust on a 6-week cadence. Pin via `rust-toolchain.toml` (`channel = "1.81"` or similar). Edition **2021** (2024 edition stabilizing in 1.85 — plan migration). Declare an **MSRV (Minimum Supported Rust Version)** in `Cargo.toml` (`rust-version = "..."`) for libraries.
- **Format**: `rustfmt` with project `rustfmt.toml` (or defaults); CI runs `cargo fmt -- --check`.
- **Lint**: `cargo clippy --all-targets --all-features -- -D warnings` in CI, with `clippy::pedantic` enabled for new code (`#![warn(clippy::pedantic)]`) and selective allows justified inline.
- **Vulnerability scan**: `cargo audit` in CI; `cargo deny check` for license + bans + advisories.
- **Documentation lint**: `RUSTDOCFLAGS="-D warnings" cargo doc --no-deps`; `#![warn(missing_docs)]` on public APIs of libraries.
- **`unsafe` audit**: `cargo geiger` to surface unsafe usage; `miri` (`cargo +nightly miri test`) for unsafe / FFI test coverage.
- **Test framework**: stdlib `#[test]` + `cargo test --all-features`; `proptest` or `quickcheck` for property tests; `cargo-fuzz` (libFuzzer) or `afl.rs` for fuzz harnesses on parsers / deserializers; `criterion` for benchmarks.
- **Concurrency model checking**: `loom` for testing concurrent primitives across schedule permutations.
- **Async runtime**: `tokio` ≥ 1.38 is the default for services (broadest ecosystem). `async-std` and `smol` only with explicit justification. Mixing runtimes is rejected.
- **Error handling**: `thiserror` for library error enums; `anyhow` for binaries / application code. **Not** both in the same crate without a clear boundary.
- **CI**: `cargo build --locked`, `cargo test --locked`, `cargo clippy --locked`, `cargo audit`, `cargo deny check`.

# When To Use

Use when Rust code is added, reviewed, refactored, or selected for a system / service / CLI / WASM / embedded / performance-sensitive component. Use whenever `unsafe`, `async`, FFI (`extern "C"`), a new trait, or a major Cargo dependency change is introduced.

# Do Not Use When

Do not use to teach Rust syntax. Do not use to introduce Rust solely because of safety appeal — require named team ownership, hiring plan, and ecosystem fit for the target domain.

# Stage Fit

Launched in coding, bug-fix, code-review, refactoring, and testing. Per-stage focus:

- **coding**: ownership/borrowing, `Result`/`?` error model, justified `unsafe` boundary, trait design, async runtime choice.
- **debugging-diagnosis**: lifetime/borrow errors, `panic`/`unwrap` paths, async deadlock, `Send`/`Sync` violation.
- **code-review**: unjustified `unsafe`, `clone()` overuse, premature trait abstraction, error-type erosion.
- **refactoring**: module/visibility boundary, public trait/type compatibility, lifetime simplification.
- **testing**: unit and `#[should_panic]`, property tests, `miri` or sanitizer for `unsafe`.

# Non-Negotiable Rules

- **`unsafe` requires a `// SAFETY:` comment** documenting every invariant the caller (or the surrounding code) must uphold. Reviewed by ≥ 2 engineers including one fluent in unsafe Rust. Covered by `miri` tests where feasible.
- **No `unwrap()` / `expect()` / `panic!()` in library code** (`lib.rs` and its modules). Acceptable: tests, `main()`, and clearly documented `expect("static invariant")` for compile-time-known cases.
- **Error model**: libraries return typed `Result<T, E>` with `E` implementing `std::error::Error` (via `thiserror::Error`). Binaries can use `anyhow::Result<T>` for top-level. Mixing requires explicit conversion boundary.
- **Lifetimes model ownership; cloning is not the default.** `.clone()` on every shared value is rejected; use `&T`, `Arc<T>`, `Cow<'_, T>` deliberately. Profile when clone vs borrow vs Arc is unclear.
- **Trait abstractions justified by ≥ 2 implementations or a clear extension contract.** Single-impl traits are rejected unless they document the planned second implementation or serve as a test/mock boundary.
- **Async runtime is explicit and singular per process.** `tokio` (default) or `async-std`, never both. `tokio::main` / `#[tokio::test]` at entry points; `block_on` only outside async context.
- **Clippy + fmt + tests + audit + deny green in CI** — no `#[allow(clippy::...)]` without inline justification + owner.
- **Public API of libraries follows semver**: breaking change = major bump. Verified with `cargo semver-checks`.
- **Concurrency primitives**: prefer message passing (`tokio::sync::mpsc`) over shared `Arc<Mutex<T>>`. When `Arc<Mutex<T>>` is necessary, lock scope is minimal; never hold a lock across `.await`.
- **`Sync` / `Send` bounds** documented for types crossing thread boundaries.

# Industry Benchmarks

- **The Rust Programming Language ("the book")** and **Rust API Guidelines** (`rust-lang.github.io/api-guidelines`).
- **Rustonomicon** for unsafe.
- **Tokio docs / tokio-console** for async runtime patterns and diagnostics.
- **Rust Performance Book** (Nicholas Nethercote) for allocation, profiling, build-time tuning.
- **Programming Rust** (Blandy / Orendorff / Tindall) and **Rust for Rustaceans** (Gjengset) as professional references.
- **CWE Top 25** — idiomatic Rust fixes: parameterized SQL via `sqlx::query!` macro; command injection — `std::process::Command::arg` (never shell); path traversal — `std::path::Path::canonicalize` + base check.
- **RustSec advisory DB** and **OSV-Scanner** for vulnerability detection.
- **`cargo semver-checks`** for library compatibility.

# Selection Rules

Select when Rust / Cargo / ownership / lifetimes / `unsafe` / traits / async runtime / WASM / FFI / systems performance is part of the request. Pair with `low-level-systems-extension` (unsafe, FFI, embedded), `language-performance-safety` (hot paths), `concurrency-control` (synchronization), `package-dependency-management` (Cargo deps), and `quality-test-gate` (fuzz / property evidence).

# Risk Escalation Rules

- Escalate to `low-level-systems-extension` for `unsafe`, FFI, `extern "C"`, embedded / `#![no_std]`, custom allocator, SIMD, or lock-free primitives.
- Escalate to `language-performance-safety` for hot paths, allocation profiling, async runtime diagnostics.
- Escalate to `quality-test-gate` for fuzz / property / `miri` / `loom` evidence.
- Escalate to `concurrency-control` for `Mutex` / channel / atomics / memory-ordering design.
- Escalate to `package-dependency-management` for Cargo dep additions, `cargo audit` / `cargo deny` advisories, license review.
- Escalate to `security-privacy-gate` for `unsafe` exposed to untrusted input, deserialization (serde with `deny_unknown_fields`), command/SQL injection.

# Critical Details

- **Borrow checker errors are design feedback.** Fighting the borrow checker with `Rc<RefCell<T>>` everywhere is usually a sign the data model is wrong; redesign data flow.
- **`.clone()` cost varies enormously**: cloning a `String` allocates; cloning an `Arc<T>` is an atomic increment; cloning a `&str` is free. Be explicit about which.
- **`async` is contagious.** Once a function is async, all callers must be async or use `block_on`. Async runtime selection is therefore a load-bearing decision.
- **Holding a lock across `.await`** — if the future is cancelled or moved to a different runtime thread, the lock may not release as expected; use `tokio::sync::Mutex` (async-aware) and minimize critical section, or restructure to release before await.
- **`tokio::spawn` requires `'static`** — spawned futures cannot borrow stack data; use `Arc` / `Clone` for shared state.
- **`Send` / `Sync` are auto-traits** — a type containing `Rc` is `!Send`; a type with interior mutability via `RefCell` is `!Sync`. Use `Arc` + `Mutex` for cross-thread.
- **`Pin<T>`** required for self-referential futures; almost always handled by `tokio::spawn` / async machinery; manual `Pin` work indicates designing a future / stream and requires `Pin` correctness review.
- **`unsafe` invariants** must specify: lifetime/aliasing rules (no overlapping mutable references), alignment, validity (no `&T` to invalid bits), thread-safety, panic safety (no panic across FFI boundary without `catch_unwind`).
- **FFI**: `extern "C"` boundary requires `#[repr(C)]` on shared types; never let Rust panic propagate across FFI (use `std::panic::catch_unwind` at the boundary).
- **`Vec::with_capacity` / `String::with_capacity`** when size is known — avoids reallocation in tight loops.
- **Iterator chains often compile to optimal code** — prefer them over manual indexing; verify with `cargo asm` / godbolt when claims matter.
- **`#[non_exhaustive]` on public enums / structs** for forward-compat in libraries.
- **`serde` with `#[serde(deny_unknown_fields)]`** at trust boundaries to prevent silent field drift / injection.
- **Cargo features unification surprise**: a transitive crate enabling a feature you don't want. Audit with `cargo tree -e features -f "{p} {f}"`.

# Failure Modes

- **Undocumented `unsafe`** — Symptom: invariant violation under refactor; UB. Cause: missing `// SAFETY:` block; assumed invariants not documented. Detection: `cargo geiger`, code review. Impact: memory safety lost, security exposure.
- **`unwrap()` in library** — Symptom: library panics in consumer code path. Cause: error handling shortcut. Detection: clippy `unwrap_used` lint. Impact: consumer outage.
- **Lock held across `.await`** — Symptom: deadlock / cancellation hang. Cause: `let g = mutex.lock().unwrap(); some_async().await;`. Detection: clippy `await_holding_lock`. Impact: deadlock.
- **Async runtime mixing** — Symptom: panic about "no reactor running" or undefined behavior. Cause: tokio future polled by async-std executor. Detection: review + runtime-aware tests. Impact: production crash.
- **`.clone()` everywhere** — Symptom: allocator hot in profile; latency high. Cause: avoiding borrow checker via clone. Detection: profile + review. Impact: allocator pressure, GC-like cost.
- **Single-impl trait** — Symptom: `trait Foo` with one `impl Foo for Concrete`; tests box-dyn-mock. Cause: Java-style abstraction. Detection: review. Impact: complexity tax with no abstraction value.
- **`Box<dyn Error>` everywhere** — Symptom: lost type information; `match` impossible. Cause: error model not designed. Detection: review for `thiserror` enum at library boundaries. Impact: poor error handling at consumer.
- **FFI panic propagation** — Symptom: undefined behavior in C caller after Rust panic. Cause: panic crossed `extern "C"`. Detection: `catch_unwind` at FFI boundary mandatory; tests for panic paths. Impact: UB in C ABI.
- **`Vec` growth in hot path** — Symptom: profile shows `realloc` hot. Cause: `Vec::push` without `with_capacity`. Detection: profile. Impact: latency.
- **Cargo feature explosion** — Symptom: build pulls unexpected heavy deps. Cause: transitive feature unification. Detection: `cargo tree -e features`. Impact: bloat, build time.

# Output Contract

Return a **Rust Usage Review** containing:
- **Toolchain pin** (`rust-toolchain.toml`), **edition**, **MSRV**
- **Tooling pins**: clippy lint set, rustfmt config, cargo-audit / cargo-deny / cargo-semver-checks status
- **Ownership / borrowing model**: clone audit; `Arc` / `Cow` / lifetime choices justified
- **Error model**: `thiserror` vs `anyhow` boundary; `Result<T, E>` discipline; panic boundaries
- **`unsafe` blocks**: each with `// SAFETY:` doc, reviewer names, miri coverage
- **Async runtime**: declared (tokio / async-std); singular per process; `tokio-console` available
- **Concurrency**: lock scope; no `.await` while holding sync lock; channel vs Arc<Mutex> choice; `Send`/`Sync` bounds documented
- **Trait audit**: each trait has ≥ 2 impls or documented extension contract
- **Dependencies**: `cargo audit` / `cargo deny` results; feature audit (`cargo tree -e features`)
- **Public API compat** (libraries): `cargo semver-checks` verdict
- **Tests**: unit + property (proptest / quickcheck) + fuzz (cargo-fuzz) + loom (concurrency) + miri (unsafe) coverage
- **Performance**: criterion benchmarks for hot paths; allocation profile
- **Accepted exceptions** with owner / scope / expiration

# Quality Gate

1. `cargo fmt --check` + `cargo clippy --all-targets -- -D warnings` + `cargo test --locked` + `cargo audit` + `cargo deny check` all green.
2. Every `unsafe` block has a `// SAFETY:` comment; miri tests where feasible; ≥ 2 reviewers including unsafe-fluent.
3. No `unwrap()` / `expect()` / `panic!()` in library code without justification.
4. Async runtime declared and singular; no `await_holding_lock`.
5. Traits justified (≥ 2 impls or documented extension contract).
6. Public library API: `cargo semver-checks` verdict matches version bump.
7. Hot paths have criterion benchmarks; allocation profile reviewed if claims involve performance.
8. Parsers / deserializers / FFI boundaries have fuzz harness or property tests.
9. `cargo geiger` reviewed; unsafe surface area minimized.
10. Cargo features audited; no transitive feature surprises.

# Used By

low-level-systems-extension, backend-change-builder, reliability-observability-gate, quality-test-gate, ai-code-review-refactor, language-runtime-selection

# Handoff

- **`low-level-systems-extension`** for unsafe, ABI, FFI, embedded, allocator, lock-free primitives.
- **`language-performance-safety`** for hot-path allocation, async runtime profile.
- **`concurrency-control`** for atomics, memory ordering, channel design.
- **`package-dependency-management`** for crate adds, audit, license.
- **`quality-test-gate`** for fuzz / property / miri / loom evidence.
- **`security-privacy-gate`** for unsafe-on-untrusted-input, serde boundaries, injection.

# Completion Criteria

Review is complete when: toolchain + clippy + audit + deny + miri (where applicable) + tests are green; every `unsafe` is documented and reviewed; error model is consistent; async runtime is singular; traits are justified; lock scope is minimal; public API compat is verified; and any accepted exception has owner, scope, and expiration.
