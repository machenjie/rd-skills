---
name: cpp-professional-usage
description: Use when C/C++ code, native extensions, embedded modules, ABI/FFI, parsers, atomics, CMake/toolchain, or performance-sensitive native work needs RAII, undefined-behavior, ownership, sanitizer, thread-safety, portability, resource-safety, graph/memory freshness, or validation-evidence review.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "94"
changeforge_version: 0.1.0
---

# Mission

Enforce professional C / C++ usage for systems, native libraries, embedded, performance-critical, and interoperability code: RAII-based resource ownership, elimination of undefined behavior, smart-pointer ownership, stable ABI policy, sanitizer + static-analysis coverage, documented thread safety, consistent error model, and portable build. Treat C/C++ as code that can fail silently and catastrophically; demand discipline that prevents the failure rather than detects it after the fact.

# Pinned Tooling Baseline (C / C++)

For C/C++, treat pinned versions as minimum review baselines. If a compiler, standard, sanitizer, or package pin is EOL, superseded, unsupported, or conflicts with the target project's platform policy, record the platform rule and update this capability before using the pin for new work.

- **Language standard**: **C++20** as the floor for new code; **C++23** where the toolchain supports it (`std::expected`, `std::print`, `std::flat_map`, deducing-this). C++17 acceptable only with documented reason. C++14 and below for legacy maintenance only. For C: **C17 / C23** where supported.
- **Compilers**: GCC ≥ 13, Clang ≥ 17, MSVC ≥ 17.10 (VS 2022 17.10). All build with `-Wall -Wextra -Wpedantic -Werror` (GCC/Clang) or `/W4 /WX` (MSVC) plus project-specific additions (`-Wconversion`, `-Wshadow`, `-Wnon-virtual-dtor`).
- **Build system**: CMake ≥ 3.27 (with presets) preferred; Bazel for monorepos; package manager: `vcpkg` or `Conan 2`.
- **Formatter**: `clang-format` ≥ 18 with project `.clang-format`; CI enforces.
- **Static analysis**: `clang-tidy` ≥ 18 with at minimum `cppcoreguidelines-*`, `bugprone-*`, `cert-*`, `modernize-*`, `performance-*`, `readability-*`. **Include-what-you-use** (`IWYU`) to control include hygiene.
- **Sanitizers in CI** (separate lanes; cannot combine TSan with ASan):
  - **ASan** (AddressSanitizer) — use-after-free, heap-buffer-overflow, leaks (with LeakSanitizer).
  - **UBSan** (UndefinedBehaviorSanitizer) — signed overflow, null deref, alignment, vptr.
  - **TSan** (ThreadSanitizer) — data races.
  - **MSan** (MemorySanitizer, Clang only) — uninitialized reads; requires building all deps with MSan.
- **Fuzzing**: libFuzzer (Clang) + OSS-Fuzz integration for OSS; AFL++ for binary targets.
- **Test framework**: GoogleTest + GoogleMock, or Catch2 v3, or doctest. **GoogleBenchmark** for microbenchmarks.
- **Vulnerability scan**: `osv-scanner` against vcpkg / Conan manifests; **CVE Binary Tool** for built artifacts.
- **Reference**: `abseil` (Google) for C++ fundamentals (string utilities, time, status) where the stdlib gap is real; `fmt` until `std::format` adoption is universal.

# When To Use

Use when C or C++ code, native extensions (Python C ext / Node N-API / JNI), embedded modules, performance code, ABI boundaries, FFI, platform-specific builds, or sanitizer coverage is part of the change. Trigger this capability when raw pointers, `new` / `delete`, threading primitives, atomic ops, alignment, exported headers, parser buffers, generated bindings, or undefined-behavior surfaces appear. Route by the specific boundary and risk: ownership, UB, ABI, concurrency, portability, dependency, or evidence freshness.

# Do Not Use When

Do not use to teach C/C++ syntax. Do not use to bless manual `new`/`delete` patterns where smart pointers (or Rust) would prevent the bug.

# Stage Fit

Use during C/C++ implementation planning, coding, bug-fix, code-review, refactoring, testing, and sanitizer evidence review. Per-stage focus:

- **coding**: RAII/ownership, bounds, integer overflow, const-correctness, deterministic resource cleanup.
- **debugging-diagnosis**: undefined behavior, use-after-free, data race, leak under ASan/UBSan/TSan/Valgrind.
- **code-review**: raw `new`/`delete`, missing rule-of-five, aliasing, unchecked buffer.
- **refactoring**: header/ABI boundary, ownership-transfer clarity, RAII wrapper extraction.
- **testing**: sanitizer builds, parser fuzzing, deterministic teardown.

# Mode Matrix
| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities | Skip by default |
| --- | --- | --- | --- | --- | --- |
| Ownership and lifetime review | Raw pointer, `new`/`delete`, custom deleter, iterator/reference reuse, resource handle. | Make ownership transfer, destruction order, and moved-from state explicit. | Owner map, RAII wrapper, delete/free boundary, ASan or leak-check result. | `low-level-systems-extension`, `code-review` | Style-only guidance. |
| UB and bounds review | Cast, arithmetic, buffer, alignment, strict aliasing, parser/deserializer, C API. | Remove exploitable UB before optimizing or packaging. | UBSan/ASan command, fuzz or boundary test, rejected unsafe shortcut. | `security-privacy-gate`, `quality-test-gate` | Happy-path unit-only proof. |
| ABI and FFI review | Exported header, shared library, `extern "C"`, JNI/N-API/Python extension, symbol layout. | Preserve binary/source compatibility and translate errors safely. | ABI policy, symbol visibility, versioning decision, exception translation proof. | `data-api-contract-changer`, `contract-testing` | Treating internal tests as ABI proof. |
| Concurrency and atomics review | Mutex, lock-free structure, `std::atomic`, thread pool, cancellation, memory order. | Prove synchronization, lock order, and lifetime across threads. | Thread-safety contract, memory-order rationale, TSan/stress result. | `concurrency-control`, `reliability-observability-gate` | Sequential-only tests. |
| Toolchain and portability review | CMake/presets, compiler flags, package manager, sanitizer lane, cross-build. | Keep builds reproducible across target compilers and platforms. | Build matrix, warning policy, static-analysis report, dependency scan. | `package-dependency-management`, `validation-broker` | Single local compiler as release proof. |

# Non-Negotiable Rules

- **RAII is mandatory.** Every resource (memory, file handle, socket, lock, GPU buffer, DB connection) is owned by an object whose destructor releases it. No raw owning pointers (`new T` without an immediate smart-pointer adoption is rejected). Prefer stack allocation; then `std::unique_ptr<T>`; then `std::shared_ptr<T>` only when shared ownership is genuine.
- **No raw `new` / `delete` in new code.** Use `std::make_unique<T>(...)` / `std::make_shared<T>(...)`. Custom containers / `placement new` requires explicit review.
- **Undefined behavior is a correctness bug.** Signed overflow, null deref, type punning via reinterpret_cast, strict-aliasing violation, data race, use-after-free are blockers. UBSan + ASan + TSan run in CI on every PR for critical native code.
- **ABI boundaries have an explicit compatibility policy.** `extern "C"` interfaces are POD / C-layout; semver discipline for shared libraries; symbol visibility controlled (`-fvisibility=hidden` default, explicit `__attribute__((visibility("default")))` for exports).
- **Thread safety documented.** Each type's thread-safety contract stated (immutable / thread-compatible / thread-safe / thread-hostile). Memory-ordering decisions cited (`std::memory_order_*`) with reasoning, not defaults-by-habit.
- **Exception policy is consistent at module / library boundary.** Either exceptions or error codes — not both. Exceptions never cross FFI / ABI boundaries (caught and translated). For codes: `std::expected<T, E>` (C++23) or `std::optional<T>` + sentinel `enum class Error`.
- **`const` correctness** and **`constexpr`** where applicable. Inputs `const&` by default; outputs by value or out-param. `[[nodiscard]]` on functions where ignoring the result is a bug.
- **No raw arrays / C-string manipulation in new C++ code.** `std::span` / `std::string_view` / `std::array` / `std::string`.
- **Integer arithmetic**: use sized types (`int32_t`, `uint64_t`, `size_t`). Signed-overflow UB is a real bug; use `__builtin_add_overflow` or saturated arithmetic where overflow is possible.
- **No global mutable state** without `std::once_flag` initialization or a clearly documented lifetime; no static initialization order fiasco.
- **Modern alternatives preferred**: `std::ranges` (C++20), `std::span`, `std::filesystem`, `std::format` (C++20 / `fmt::format`), `std::expected` (C++23), `std::jthread` with stop tokens.

# Industry Benchmarks

- **C++ Core Guidelines** (Stroustrup, Sutter) — the single authoritative reference.
- **Effective Modern C++** (Meyers, C++14) and **C++ Best Practices** (Lefticus).
- **CERT C / C++ Secure Coding Standards** and **MISRA C / C++** (for embedded / safety-critical).
- **NIST SP 800-218 (SSDF)** for secure development; **OWASP** C/C++ guidance for native services.
- **CWE Top 25** with focus on CWE-119 (buffer ops), CWE-416 (use-after-free), CWE-476 (null deref), CWE-787 (out-of-bounds write), CWE-190 (integer overflow), CWE-362 (race).
- **C++ memory model** (since C++11) and **Hans-J. Boehm**'s atomics guidance.
- **Google C++ Style Guide** + **LLVM Coding Standards** for stylistic floor.
- **Compiler Explorer (godbolt)** + `objdump` / `nm` for ABI inspection and codegen validation.

# Selection Rules

Select when C / C++ / native / ABI / FFI / embedded / memory-ownership / sanitizer / low-level performance concerns appear. Pair with `low-level-systems-extension` (deep ABI / kernel / hardware), `language-performance-safety` (hot paths), `concurrency-control` (atomics / memory model), `quality-test-gate` (sanitizer / fuzz evidence), `package-dependency-management` (vcpkg / Conan deps), and `validation-broker` when commands or reports must be mapped to changed paths. Skip only for formatter-only, comment-only, or generated-output refreshes with no native behavior, contract, or toolchain change.

# Proactive Professional Triggers
- **Signal:** raw pointer, `new`/`delete`, borrowed reference, iterator, file descriptor, socket, lock, or GPU/native handle crosses a function or thread boundary without an owner. **Hidden risk:** use-after-free, double free, leaked descriptor, or dangling reference survives ordinary tests. **Required professional action:** require an ownership map and RAII wrapper or a documented non-owning lifetime. **Route to:** `low-level-systems-extension`, `code-review`. **Evidence required:** owner/deleter boundary, rejected raw-owning alternative, ASan or leak-check command and exit code.
- **Signal:** exported header, shared-library type, virtual class, `extern "C"` function, JNI/N-API/Python extension, or generated binding changes without ABI policy. **Hidden risk:** downstream binary or foreign caller breakage appears after release. **Required professional action:** classify source/API/binary compatibility and translate exceptions/errors at the boundary. **Route to:** `contract-testing`, `data-api-contract-changer`. **Evidence required:** symbol/layout diff, versioning decision, FFI error translation test, and residual consumer risk.
- **Signal:** parser, deserializer, packet/file decoder, C-string path, size calculation, or `reinterpret_cast` touches untrusted or variable-length input. **Hidden risk:** buffer overflow, strict-aliasing UB, integer overflow, or information disclosure. **Required professional action:** add bounds/overflow proof and fuzz or boundary coverage before acceptance. **Route to:** `security-privacy-gate`, `quality-test-gate`. **Evidence required:** ASan/UBSan command, fuzz artifact or boundary test output, and what evidence does not prove.
- **Signal:** `std::atomic`, lock-free structure, mutex ordering, thread pool, callback lifetime, cancellation, or `memory_order_relaxed` appears without a thread-safety contract. **Hidden risk:** data race, deadlock, stale read, or lifetime race only reproduces under load. **Required professional action:** document synchronization ownership and run race/stress evidence. **Route to:** `concurrency-control`, `reliability-observability-gate`. **Evidence required:** memory-order rationale, lock-order statement, TSan/stress report, and residual platform risk.
- **Signal:** build, sanitizer, static-analysis, package-manager, or cross-platform evidence predates the final source edit or runs on only one local compiler. **Hidden risk:** stale validation or platform skew hides UB and ABI defects. **Required professional action:** map changed paths to fresh validators and disclose skipped targets. **Route to:** `validation-broker`, `quality-test-gate`. **Evidence required:** command, exit code, covered files, stale/not-run targets, and owner.
- **Signal:** repository graph, project memory, prior agent output, or old incident note says a native path is safe, unused, or already covered without current source confirmation. **Hidden risk:** stale context misses generated bindings, hidden consumers, or platform-specific build paths. **Required professional action:** confirm graph/memory claims against current headers, build files, tests, generated artifacts, and reports. **Route to:** `repository-graph-analysis`, `project-memory-governance`, `agent-execution-discipline`. **Evidence required:** inspected paths, accepted/rejected memory, current-source proof, and remaining unknowns.

# Risk Escalation Rules

- Escalate to `low-level-systems-extension` for ABI, FFI, kernel, driver, embedded, SIMD, allocator, lock-free data structure.
- Escalate to `language-performance-safety` for hot paths, allocation profile, cache locality, false sharing.
- Escalate to `quality-test-gate` for sanitizer / fuzz / stress evidence.
- Escalate to `concurrency-control` for memory-ordering and atomics design.
- Escalate to `security-privacy-gate` for buffer-handling on untrusted input, deserialization, integer-overflow in size calculations.
- Escalate to `package-dependency-management` for vcpkg / Conan dependency changes, CVE responses.
- Escalate to `agent-tool-permission-sandbox` when sanitizer, fuzz, build, package-manager, or generated-binding commands can write artifacts, access broad paths, or expose secret-bearing output.

# Critical Details

- **Owning raw pointer is the most common C++ bug class.** `T* p = new T()` without immediate ownership transfer to a smart pointer is rejected. Any function that allocates and returns a raw pointer must document the ownership contract (callee owns? caller frees? library frees via `freeXxx`?).
- **Rule of zero / three / five**: prefer compiler-generated special members (rule of zero) by composing RAII types. If you write one of destructor / copy-ctor / copy-assign / move-ctor / move-assign, write all five (or `= default` / `= delete` them).
- **Move semantics**: an object in a moved-from state is valid but unspecified — only destructible / assignable. Don't use a moved-from value.
- **`std::shared_ptr` cycles leak.** Use `std::weak_ptr` to break cycles (parent owns child via `shared_ptr`; child references parent via `weak_ptr`).
- **`std::vector` invalidation**: any operation that may reallocate (push_back beyond capacity, resize, insert) invalidates iterators and references. Hot-loop bug source.
- **Static initialization order fiasco**: globals across translation units have unspecified initialization order. Use Meyers singletons (`static T& get() { static T t; return t; }`) for lazy init.
- **Strict aliasing**: accessing memory through an incompatible type is UB (except `char*` / `std::byte*` / `unsigned char*`). Use `std::memcpy` for type punning; `std::bit_cast` (C++20) for constant-evaluable cases.
- **Data race UB**: two threads accessing the same memory with at least one writer, without synchronization, is UB. `std::atomic<T>` for shared scalars; `std::mutex` for shared structures.
- **`std::memory_order_relaxed`** is for counters where only atomicity (not ordering) matters; `acquire`/`release` for handoff; `seq_cst` (default) when in doubt and cost is acceptable.
- **False sharing**: two threads writing different fields of the same cache line serialize at the cache-coherence layer. `alignas(std::hardware_destructive_interference_size)` for hot per-thread fields.
- **Exception safety levels** (Abrahams): no-throw (`noexcept`), strong (rollback on throw), basic (no leaks, valid state), no guarantee. Document the level each function provides.
- **`std::filesystem`** for paths — no manual string parsing. Watch for OS-specific encoding (UTF-8 on Linux, UTF-16 on Windows native APIs).
- **`std::format` / `fmt::format`** instead of `printf` / `iostream` for new code (type-safe, faster).
- **CMake hygiene**: target-based commands (`target_link_libraries(...)` with `PUBLIC` / `PRIVATE` / `INTERFACE` discipline); no global `include_directories`; use presets (`CMakePresets.json`).
- **Header guards / `#pragma once`** at the top of every header; include-what-you-use (IWYU) to prevent transitive-include rot.
- **ABI stability**: changing class layout, virtual table, exception types, or symbol mangling breaks ABI for binary consumers. Document the ABI level (header-only / source-compatible / binary-compatible) and version accordingly.

# Failure Modes

- **Use-after-free** — Symptom: heisenbug, sporadic crash. Cause: dangling pointer, lifetime mismatch. Detection: ASan; ownership audit; smart-pointer enforcement. Impact: corruption, security (CVE-class).
- **Buffer overflow** — Symptom: crash or corruption on input near boundary. Cause: missing bounds check on C-string / raw buffer. Detection: ASan + `std::span`/`std::string_view` migration. Impact: CWE-119 / CWE-787.
- **Race condition** — Symptom: intermittent wrong result under load. Cause: shared mutable state without sync. Detection: TSan in CI. Impact: data corruption.
- **UB on signed overflow** — Symptom: optimizer assumes overflow impossible; "impossible" branch removed. Cause: signed integer overflow. Detection: UBSan; `-fsanitize=signed-integer-overflow`. Impact: silent wrong result.
- **Static init order fiasco** — Symptom: crash before `main`, intermittent across builds. Cause: cross-TU global dependency. Detection: Meyers singleton pattern. Impact: startup instability.
- **Shared_ptr cycle leak** — Symptom: memory grows, never released. Cause: parent and child both `shared_ptr` to each other. Detection: ownership review; `weak_ptr` for back-refs. Impact: memory leak.
- **ABI break** — Symptom: consumer crashes after lib upgrade. Cause: layout / vtable change without major bump. Detection: ABI checker (libabigail); semver discipline. Impact: ecosystem breakage.
- **Strict aliasing violation** — Symptom: wrong value under `-O2`, correct under `-O0`. Cause: type-punned read via incompatible pointer. Detection: UBSan; `memcpy` / `bit_cast` migration. Impact: silent wrong result with optimization.
- **False sharing** — Symptom: scaling collapses past N threads. Cause: per-thread fields on same cache line. Detection: perf c2c; align with `hardware_destructive_interference_size`. Impact: scalability cliff.
- **Exception across FFI** — Symptom: undefined behavior in C caller. Cause: C++ exception escaped `extern "C"`. Detection: `try/catch` at boundary; sanitizer / review. Impact: UB in foreign code.

# Reference Loading Policy

Load [references/checklist.md](references/checklist.md) when C/C++ changes touch raw pointers, ownership/lifetime, bounds, undefined behavior, concurrency, atomics, ABI/API layout, FFI, sanitizers, static analysis, or exported headers. Use [examples/example-output.md](examples/example-output.md) only when the expected review shape is unclear. Do not load references for formatter-only or comment-only changes.

# Output Contract
Return a **C / C++ Usage Review** containing:
- **Mode selected**: ownership/lifetime, UB/bounds, ABI/FFI, concurrency/atomics, or toolchain/portability, with trigger signal.
- **Boundaries inspected**: source/header files, generated bindings, build files, tests, package manifests, exported symbols, ABI/FFI callers, and skipped boundaries with reason.
- **Language standard** in use (C17 / C++20 / C++23 etc.); compiler versions per target
- **Tooling pins**: build system, formatter, clang-tidy checks enabled, sanitizer CI lanes, fuzz harness coverage
- **Ownership model**: smart-pointer usage; raw owning-pointer audit; rule-of-zero/five compliance
- **UB risk inventory**: signed overflow, aliasing, alignment, integer narrowing, vptr; UBSan status
- **ABI policy**: header-only / source-compat / binary-compat; visibility flags; symbol export; semver stance
- **Error / exception model**: which boundary uses exceptions vs codes vs `std::expected`; FFI boundary handling
- **Thread safety**: per-type contract; memory-ordering decisions; TSan status
- **Sanitizer + static analysis status**: ASan / UBSan / TSan / MSan lane results; clang-tidy / spotbugs-equivalent verdicts
- **Build portability**: target matrix; cross-compile considerations; CMake presets
- **Dependencies**: vcpkg / Conan manifest; CVE / OSV scan status
- **Tests**: unit + integration + fuzz (libFuzzer / AFL) + benchmark (gbench) coverage
- **Graph/memory/execution coupling**: repository graph and project-memory claims accepted, rejected, stale, or not verified; prior validation freshness after final edit
- **Validation evidence**: literal command, exit code, validator/report/artifact path, and what the output proves or does not prove
- **Tool permission boundary**: build/fuzz/package/generated-artifact command class, sandbox/approval state, write scope, and secret-output redaction rule
- **Accepted C/C++ deviations** with owner, scope, expiration, and cleanup trigger

# Evidence Contract
A C/C++ change is professionally complete only when the output includes:

- **Ownership model**: stack/heap ownership, RAII wrapper, smart pointer choice, and delete/free boundary.
- **Lifetime and aliasing**: pointer/reference validity, iterator invalidation, object lifetime, and aliasing assumptions.
- **Bounds and UB**: array/vector bounds, integer overflow, signed/unsigned conversion, undefined behavior risk.
- **Concurrency**: lock ownership, atomics, memory ordering, and data race risk.
- **ABI/API boundary**: struct layout, header compatibility, exported symbols, and FFI boundary.
- **Validation evidence**: unit test, sanitizer, valgrind, static analyzer, fuzz, benchmark, validator, or not-verified disclosure with command, exit code, output summary, and report/artifact path.
- **What evidence proves**: the inspected native safety and ABI risk is covered.
- **What evidence does not prove**: all platforms, production workload, compiler-specific UB exposure, or downstream binary compatibility.
- **Graph and memory freshness**: current source, generated artifacts, build files, and prior project-memory claims confirmed or rejected before closure.
- **Native residual risk**: untested platform/compiler/runtime path, owner, and next gate.

# Quality Gate

1. Compiles clean at `-Wall -Wextra -Wpedantic -Werror` (or MSVC `/W4 /WX`).
2. clang-tidy with `cppcoreguidelines-*` + `bugprone-*` + `cert-*` clean or each finding justified.
3. ASan + UBSan green; TSan green for concurrent code; MSan where dep-availability permits.
4. No raw `new` / `delete` in new code; smart-pointer ownership audited.
5. Rule of zero / five respected; move-semantics correctness reviewed.
6. ABI policy stated; visibility flags set; semver discipline matches public API change.
7. Thread-safety contract documented per type; memory-ordering decisions cited.
8. Parsers / deserializers / network-input code have fuzz harness.
9. Hot paths have gbench numbers; allocation / cache / false-sharing reviewed if perf-claimed.
10. Build matrix covers all deploy targets; CMake hygiene (no globals; target-based).
11. Validation report maps each changed C/C++ path to command, exit code, covered risk, stale/not-run targets, and residual owner.
12. Tool permission/sandbox record exists for build, fuzz, package-manager, generated-binding, or artifact-writing commands.

# Used By

low-level-systems-extension, reliability-observability-gate, quality-test-gate, ai-code-review-refactor, language-runtime-selection

# Handoff

- **`low-level-systems-extension`** for ABI, FFI, kernel, driver, embedded, SIMD, allocator.
- **`language-performance-safety`** for hot-path allocation, cache locality, false sharing.
- **`concurrency-control`** for atomics, memory ordering, lock-free design.
- **`package-dependency-management`** for vcpkg / Conan dep additions, CVE response.
- **`security-privacy-gate`** for untrusted-input buffer handling, deserialization, integer overflow in size calculations.
- **`quality-test-gate`** for sanitizer / fuzz evidence.

# Completion Criteria

Review is complete when: code compiles clean at maximum warnings; clang-tidy + sanitizer + fuzz lanes are green with commands and exit codes recorded; ownership is RAII; UB risks are eliminated or sanitized; ABI policy is stated and matches version bump; graph/memory claims are current-source confirmed; thread-safety contracts are documented; performance claims have benchmark evidence; and any accepted exception has owner, scope, and expiration.
