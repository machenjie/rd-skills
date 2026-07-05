---
name: low-level-systems-extension
description: "Use this domain extension when a selected professional skill handles professional product rules for OS, kernel, driver, native performance, networking, embedded C and C++, Rust systems, and low-level runtime changes requiring explicit memory safety, concurrency, ABI, platform behavior, syscalls, and resource cleanup. Do not use it for keyword-only, documentation-only, or UI-only mentions without domain behavior, data, risk, validation, or release impact."
license: MIT
changeforge_kind: domain-extension
changeforge_version: 0.1.0
metadata:
  changeforge.profile: full
  changeforge.skill_type: domain-extension
  changeforge.domain: low-level-systems
---

## Domain Scope
Extend ChangeForge product and code change analysis with low-level systems engineering discipline for memory safety, concurrency correctness, ABI stability, syscall security boundaries, undefined behavior elimination, performance profiling, and resource lifecycle management — ensuring that systems-level changes cannot introduce exploitable memory corruption, concurrency data races, or silent undefined behavior that manifests only under specific conditions in production.

## Mission
Own the low-level systems domain addendum for a selected professional owner skill: memory, concurrency, ABI, syscall, resource, unsafe/FFI, and profiling-risk decisions. Non-owned implementation, security, release, and test decisions remain with the primary owner or gate. Expected output is a systems decision addendum that prevents exploitable memory corruption, data races, ABI breaks, privilege escalation, resource leaks, and optimization without proof.

## When To Use
Use when a strong low-level systems signal can change a product, code, validation, release, or residual-risk decision. Treat strong signals as compiled-code behavior, ownership/lifetime, unsafe/FFI, kernel/driver, syscall, ABI, concurrency, or profiling evidence, not as keywords. Skip keyword-only, docs-only, fixture-only, or managed-language mentions unless systems behavior, data, validation, release, or security posture can change.

## Strong Domain Signals
- Any change to C or C++ source code in production systems (kernel modules, drivers, networking stacks, runtime libraries, native plugins).
- Rust systems code with unsafe blocks, FFI (Foreign Function Interface), or raw pointer manipulation.
- OS kernel module additions or modifications.
- Device driver changes: DMA configuration, interrupt handling, memory-mapped I/O.
- Memory allocator changes: custom allocators, arena allocators, slab allocators, memory pool modifications.
- Thread management changes: thread pool sizing, mutex introduction or removal, lock order changes, lock-free data structure additions.
- ABI-affecting changes: struct layout changes, function signature changes in shared libraries, calling convention changes.
- Syscall boundary changes: new `seccomp` filter rules, capability set modifications, namespace configuration.
- Network stack changes: socket options, TCP congestion control, buffer sizing, packet processing paths.
- Performance-critical path changes requiring profiling evidence (< 1ms latency budget, > 1M ops/sec throughput).

## Weak Signals That Are Not Enough

Do not load this extension only because a path, label, button, fixture, variable, title, or documentation paragraph contains a domain word. Do not load it for copy, styling, formatting, or generic refactors unless domain behavior, domain data, domain risk, validation, release evidence, or compliance posture can change.

## Do Not Use When
- The change is pure Python, JavaScript, Go, Java, or other managed-memory language with no FFI, no native extensions, and no OS-level system call manipulation.
- The change is a configuration file or build script change with no compiled code.

## Required Professional Owner Skill

This extension must compose with one primary professional owner skill; it never replaces that owner or closes engineering work alone unless the user requested domain-only analysis.

- security-privacy-gate
- reliability-observability-gate
- quality-test-gate
- ai-code-review-refactor
- backend-change-builder

## Selection Rules
- If ownership/lifetime, unsafe/FFI, lock order, ABI, syscall, descriptor, allocator, or performance-critical behavior can change, require a systems domain addendum before approval.
- When sanitizer, fuzz, concurrency, ABI compatibility, resource-cleanup, or benchmark evidence is missing, treat systems approval as a blocking pass decision and route validation to `quality-test-gate`.
- When syscall surface, memory corruption, privilege boundary, untrusted input parsing, or sandbox behavior changes, escalate to `security-privacy-gate`.
- Skip this extension when the primary owner confirms no compiled/native, unsafe/FFI, OS, ABI, syscall, resource-lifecycle, or performance-critical boundary can change.

## Tradeoff Priorities
- Memory safety before micro-optimization.
- ABI compatibility before internal layout convenience.
- Deterministic resource cleanup before short control flow.
- Measured performance before speculative tuning.

## Domain-Specific Non-Negotiable Rules
- **Memory ownership must be explicit and unambiguous**: every heap allocation must have a single, identified owner responsible for deallocation — in C, use RAII-equivalent patterns or `__attribute__((cleanup))`; in Rust, ownership and borrow checker enforce this at compile time; in C++, use smart pointers (`unique_ptr`, `shared_ptr`) not raw owning pointers.
- **All `unsafe` blocks in Rust must have a documented safety invariant**: an `unsafe` block without a comment explaining why it is safe and what invariants the author is relying on is a maintenance time bomb — document the invariants explicitly.
- **Lock order must be documented and enforced globally**: two mutexes that can be held simultaneously must have a total order — acquiring them in any order is a deadlock — document the lock order hierarchy; enforce it with lock-order checking tools (Helgrind, TSAN).
- **Undefined behavior in C/C++ is not a latent bug, it is an exploit surface**: UB (null pointer dereference, signed integer overflow, out-of-bounds array access, use after free) can be exploited by a motivated attacker because compilers optimize based on the assumption that UB does not occur — eliminate UB, do not assume it is benign.
- **ABI-breaking changes in shared libraries require version bumps**: changing a struct's field layout or a function's signature in a shared library without a version bump silently breaks all existing callers — increment the SONAME; use symbol versioning (`__attribute__((symver))`).
- **Syscall surface must be minimized with `seccomp`**: a process that does not filter its syscall surface has access to the full Linux syscall table — use `seccomp-bpf` to restrict to the minimal set of required syscalls; this limits exploit escalation.
- **Integer arithmetic on security-sensitive paths must be checked for overflow**: signed integer overflow in C is UB; unsigned integer overflow wraps (defined but often incorrect for size calculations) — use `__builtin_add_overflow`, `__builtin_mul_overflow`, or `safeint` for security-critical arithmetic.
- **Profiling must precede optimization**: optimization without profiling data is guessing — use `perf`, `gprof`, `Valgrind`, or eBPF-based profiling to identify the actual bottleneck before modifying code; document baseline and post-optimization measurements.

## Domain Risk Escalation

- Escalate to `security-privacy-gate` for custody, secrets, PII, permissions, abuse, prompt/security, device safety, or privileged access risk.
- Escalate to `data-api-contract-changer` for domain DTOs, events, schemas, SDKs, public APIs, or compatibility changes.
- Escalate to `reliability-observability-gate` for retries, replay, reconciliation, freshness, fallback, SLO, or incident visibility.
- Escalate to `delivery-release-gate` for rollout, rollback, migration, compliance evidence, irreversible production change, or operational readiness.
- Escalate to `quality-test-gate` when domain golden cases, regression proof, or validation evidence is missing.

## Domain Reference Loading Policy

Do not load all domain references by default. Load `references/checklist.md` only after a primary professional owner is selected and a strong domain signal proves the checklist can change a domain rule, validation requirement, release decision, or residual-risk addendum. Do not load domain references for keyword-only mentions, display-only copy, or unrelated refactors.

## Industry Benchmarks
- **MISRA C:2012**: 143 rules for safety-critical C programming. Mandatory/required/advisory classification. Prohibits dynamic allocation, recursion, goto, implicit conversions, and uninitialized variables in safety-critical code.
- **CERT C Coding Standard (SEI Carnegie Mellon)**: 99 rules for secure C covering memory (MEM), integers (INT), characters (STR), file I/O (FIO), concurrency (CON), and signals (SIG). Maps to CWE vulnerabilities for each rule.
- **Google C++ Style Guide**: Naming, memory management, RAII, `absl::Status` for error handling, thread safety annotations (`GUARDED_BY`, `EXCLUSIVE_LOCKS_REQUIRED`), disallowing raw owning pointers in new code.
- **Rust Unsafe Code Guidelines (UCG)**: Formal model for what `unsafe` Rust may and may not do, including pointer aliasing rules, uninitialized memory, and memory layout guarantees. Required reading before writing any `unsafe` block.
- **Brendan Gregg — Systems Performance (2nd ed.)**: Methodology for performance analysis using USE Method, flame graphs, BPF tools, `perf`, `strace`, `tcpdump`, `netstat`. Defines profiling-first discipline.
- **The Art of Writing Efficient Programs (Pikus)**: CPU cache effects, branch prediction, SIMD vectorization, memory bandwidth limits, lock-free vs. lock-based trade-offs. Required for high-throughput systems code.
- **Linux Kernel Coding Style**: `checkpatch.pl` compliance, error handling patterns (`goto err_cleanup`), locking annotations (`__must_hold`, `__acquires`, `__releases`), memory barrier documentation (`smp_mb()`).
- **CWE Top 25 (2023)**: CWE-119 (buffer overflow), CWE-416 (use-after-free), CWE-476 (null pointer dereference), CWE-362 (concurrent race condition), CWE-190 (integer overflow). Systems code has the highest density of these vulnerabilities.

### Memory Safety Tool Selection Matrix

| Language | Tool | What It Detects |
|---|---|---|
| C/C++ | AddressSanitizer (ASan) | Heap overflow, stack overflow, use-after-free, double-free, out-of-bounds |
| C/C++ | UndefinedBehaviorSanitizer (UBSan) | Signed overflow, null dereference, invalid shift, misaligned access |
| C/C++ | ThreadSanitizer (TSan) | Data races, lock order violations, mutex misuse |
| C/C++ | Valgrind Memcheck | Memory leaks, use of uninitialized memory, invalid heap operations |
| C/C++ | Coverity / CodeChecker | Static analysis: null deref, resource leaks, integer overflow |
| Rust | Miri | Undefined behavior in unsafe code; pointer aliasing violations |
| Rust | cargo-geiger | Count of unsafe code blocks; dependency unsafe surface |
| All | `perf record` + flamegraph | CPU hotspots; cache miss rate; branch misprediction rate |

## Domain Risk Model
- **Use-after-free enables arbitrary code execution**: a pointer is used after the object it points to has been freed — the memory may have been reallocated to an attacker-controlled object; writing to it overwrites attacker-controlled data in the new allocation.
- **Data race produces non-deterministic corruption**: two threads read-modify-write a shared variable without synchronization — the behavior depends on scheduling; the bug manifests intermittently and only under load.
- **ABI break silently corrupts struct layout**: a struct gains a new field in a shared library; the caller was compiled against the old struct layout; it reads fields at the wrong offset — silent data corruption with no crash.
- **Deadlock from lock order violation**: Thread A holds lock M1 and waits for M2; Thread B holds lock M2 and waits for M1 — both block indefinitely; the system hangs.
- **Signed integer overflow is UB exploited by optimizer**: a bounds check uses `if (offset + length < 0)` to detect overflow — the C compiler eliminates this check because signed overflow is UB and the optimizer assumes it cannot happen; the buffer overflow proceeds unchecked.
- **Syscall escalation via unrestricted syscall surface**: an exploited process has access to `ptrace`, `clone`, `mount`, `mknod` — these are used to escape the process boundary and escalate to host privilege.
- **Memory leak in long-running daemon**: a server process leaks 4KB per request — at 10 RPS, it consumes 2.4GB/hour; the process is killed by OOM after 3 hours; the leak was invisible without profiling.
- **Uninitialized memory read leaks sensitive data**: stack memory from a previous function call contains credential data — a new buffer read of uninitialized memory returns that stale credential; an attacker-controlled read exfiltrates it.

## Linked Foundation Capabilities
- threat-modeling
- authentication-security
- test-strategy
- regression-testing
- observability
- logging-error-handling
- concurrency-control
- performance-budgeting
- profiling
- error-code-design

## Critical Details
- **Thread safety annotation is documentation and enforcement**: Clang thread safety analysis (`GUARDED_BY`, `REQUIRES`, `EXCLUDES`) checks lock correctness at compile time — it is free static analysis that prevents a class of runtime crashes.
- **Memory ordering on atomic operations is not optional**: `std::memory_order_relaxed` is often incorrect for multi-producer/multi-consumer patterns — use `acquire`/`release` semantics for synchronization; document the memory ordering choice with the invariant it protects.
- **`mmap` with `MAP_FIXED` can silently overwrite existing mappings**: using `MAP_FIXED` without careful address space management will overwrite the stack, heap, or existing shared libraries — always validate the target address range or use `MAP_FIXED_NOREPLACE` (Linux 4.17+).
- **Copy-on-Write page fault overhead is significant at fork scale**: a process that forks with large heap/stack sizes incurs high CoW page fault overhead in the child — profile fork overhead or prefer `posix_spawn` for performance-sensitive child process creation.
- **`O_CLOEXEC` must be set on all file descriptors opened by a server process**: a file descriptor without `O_CLOEXEC` is inherited by child processes after `fork+exec` — this leaks file handles to untrusted processes.
- **Futex contention dominates lock performance at scale**: a mutex implemented on a contended futex degrades linearly with thread count — use lock-free structures for hot paths, or shard the lock by key/hash to reduce contention.

### Anti-Examples

| Systems Pattern | Problem | Corrected Approach |
|---|---|---|
| `free(ptr); use(ptr->field)` | Use-after-free; exploitable memory corruption | Null the pointer after free: `free(ptr); ptr = NULL;`; use ASan in CI |
| `int total = a + b; if (total < 0)` overflow check | Signed integer overflow is UB; check is optimized away | Use `__builtin_add_overflow(a, b, &total)` and check the return value |
| Mutex M1 acquired in Thread A, M2 in Thread B in different orders | Deadlock | Document and enforce total lock order; use lock-order checker (Helgrind) |
| `struct Config { int field1; }` in shared library → add `int field2` without version bump | ABI break silently corrupts callers | Bump SONAME; use opaque pointer idiom or versioned symbols |
| `char buf[64]; read(fd, buf, 256)` | Buffer overflow on stack | `read(fd, buf, sizeof(buf) - 1)` with bounds check |

## Failure Modes
Report each failure mode with condition, consequence, detection, prevention or repair, and evidence; narrative risk alone is not enough for domain closure.

- **Use-after-free exploited in production**: a memory management refactor frees an object while a worker thread still holds a reference; the freed memory is reallocated; the worker writes to the new allocation — arbitrary code execution.
- **Data race produces silent financial corruption**: two threads increment a counter without synchronization — the counter silently drops increments; financial totals are understated; auditing discovers the discrepancy weeks later.
- **ABI break causes silent data corruption**: a shared library struct layout change is deployed without a version bump — existing callers read fields at wrong offsets; application behavior becomes non-deterministic.
- **Deadlock in production hangs service**: lock order violation introduced by a refactoring — two threads deadlock under a specific concurrent request pattern; discovered only under production load.
- **Memory leak causes nightly daemon restart**: a connection handler leaks a small buffer per connection — the daemon is restarted each night as a workaround; root cause not diagnosed for 6 months.
- **Unrestricted syscall allows privilege escalation**: an exploited process uses `ptrace` (not filtered by seccomp) to inject code into a higher-privilege process — privilege escalation from exploited network service to root.

## Domain Output Addendum
Return systems-level change assessment with:
- **Selected mode and professional decision**: selected owner skill, systems addendum mode, approved/blocked/not-verified decision, and the native/system behavior under review.
- **Inspected boundaries**: ownership/lifetime, unsafe/FFI, lock order, ABI, syscall, descriptor, allocator, error cleanup, and performance boundaries read or explicitly skipped.
- **Evidence collected / validation status**: sanitizer, `miri`, fuzz/property, thread-safety, ABI, seccomp, leak, and benchmark evidence with current pass/fail/not-run status.
- **Evidence limits, residual risk, and next gate**: untested architectures, compilers, kernels, data races, descriptor leaks, owner, and next gate.
- **Memory safety analysis**: ownership clarity, sanitizer CI requirements, use-after-free/double-free risk.
- **Concurrency review**: lock order documentation, data race risk, atomic operation memory ordering.
- **ABI stability check**: struct layout changes, symbol version requirements, calling convention compatibility.
- **Undefined behavior inventory**: signed overflow, null dereference, uninitialized read, out-of-bounds access.
- **Syscall surface review**: required syscalls, seccomp filter configuration, capability set.
- **Performance profile**: profiling baseline, bottleneck identification, optimization measurement.
- **Resource lifecycle audit**: all allocations paired with deallocation, file descriptors with `O_CLOEXEC`, all resources cleaned up on error paths.
- **Block/pass decision** with required conditions for approval.

## Evidence Contract
Close a systems-level change only when all five canonical answers are concrete (answer schema: `agent-execution-discipline`), because the loss path is memory corruption and privilege escalation:
- **Basis**: the memory-safety rule, ABI/FFI contract, or memory-ordering guarantee the change rests on.
- **Files and boundaries inspected**: the ownership and lifetime of each allocation, the lock order, and the syscall surface read, with the ABI boundary and the unsafe/FFI boundary confirmed.
- **Placement rationale**: why each ownership transfer, atomic ordering, and resource-cleanup path is shaped as it is, with the rejected lock-free or shared-state alternative.
- **Validation commands**: the ASan/UBSan/TSan or `miri` build, the fuzz/property test, and the reproducible benchmark run, each with its outcome.
- **Residual risk**: the UB, descriptor-leak, signal-safety, or cross-platform-build path that remains, with the named owner.
- **What evidence proves**: only the tested compiler, target platform, sanitizer configuration, ABI boundary, workload, and syscall/resource path meet the stated gate.
- **What evidence does not prove**: untested architectures, kernel versions, compiler optimizations, rare interleavings, signal-safety paths, or production-only workload shape.
- **Behavior preservation**: existing ABI compatibility, ownership transfer, cleanup behavior, syscall restrictions, concurrency invariants, and latency/throughput targets are preserved or explicitly changed.
- **Next gate**: unresolved sanitizer, ABI, concurrency, security, performance, or cross-platform gaps route to the named owner before release.

## Domain Quality Gate
1. All C/C++ changes run AddressSanitizer and UndefinedBehaviorSanitizer in CI with zero violations.
2. All Rust `unsafe` blocks have documented safety invariants; `cargo-geiger` baseline is not exceeded.
3. Lock order is documented; ThreadSanitizer or Helgrind shows no lock order violations.
4. All ABI-affecting changes have SONAME version bumps or use versioned symbols.
5. All security-critical integer arithmetic uses overflow-checked operations.
6. Syscall surface is minimized with `seccomp-bpf` filter; filter is tested.
7. All file descriptors are opened with `O_CLOEXEC`.
8. Performance changes have profiling baseline and post-change measurements.
9. All heap allocations have a documented owner; memory leak check (Valgrind) passes.
10. Error paths free all acquired resources; no resource leak under error conditions.

## Handoff
Return this domain addendum to the primary professional owner; do not approve systems-level work from this extension alone. Hand off exploit-surface blockers to `security-privacy-gate`, sanitizer/fuzz/concurrency gaps to `quality-test-gate`, performance/operability gaps to `reliability-observability-gate`, and AI-generated code risk to `ai-code-review-refactor` with the residual-risk owner and next evidence gate.

## Return / Escalate
- **security-privacy-gate** — for CWE-level vulnerability assessment, syscall surface, and exploit surface analysis.
- **quality-test-gate** — for sanitizer CI requirements, fuzzing obligations, and concurrency test scenarios.
- **reliability-observability-gate** — for memory usage SLI, latency profiling baseline, and resource leak monitoring.
- **ai-code-review-refactor** — for automated detection of memory management patterns, concurrency anti-patterns, and UB-prone constructs.

## Completion Criteria
The systems-level change is approved when memory ownership is explicit, sanitizers run clean in CI, lock order is documented with no detected violations, ABI-affecting changes have version bumps, integer overflow is checked on security-critical paths, syscall surface is minimized with seccomp, file descriptors use `O_CLOEXEC`, performance changes have profiling evidence, and all resources are released on all code paths including error paths.
