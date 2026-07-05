# Rust Evidence Patterns

Use this reference when Rust closure depends on repository graph, project memory, execution trajectory, validation freshness, unsafe/runtime/dependency proof, tool permission boundaries, or changed-surface-to-validation mapping. Keep it as an evidence map, not a Rust tutorial.

## Changed-Rust-Surface-To-Validation Map

| Rust claim | Minimum evidence | What it proves | What it does not prove |
| --- | --- | --- | --- |
| Ownership boundary is sound | Current module/API path, ownership map, borrow/clone decision, mutation boundary, and targeted unit/property test | The inspected path has intentional ownership and mutation behavior | All future call sites, data sizes, or allocator behavior are covered |
| Recoverable error path is typed | Error enum or conversion map, panic/unwrap scan, caller-visible negative test, and public API note | The inspected recoverable boundary exposes typed failure behavior | Every downstream caller handles the error correctly |
| Unsafe or FFI boundary is controlled | `// SAFETY:` contract, safe wrapper, layout/aliasing/panic rules, Miri/fuzz/geiger result or not-run owner | The named unsafe surface has documented invariants and unsafe-specific validation | All undefined behavior paths, target architectures, or C caller behavior are covered |
| Async or concurrency path is scheduler-safe | Runtime map, lock/await scan, `Send`/`Sync` boundary, cancellation behavior, loom/stress/clippy result | The inspected async path has a reviewed runtime and synchronization model | Every scheduling interleaving or production load pattern is covered |
| Trait/API or crate boundary is compatible | Impl inventory, rejected concrete alternative, semver-checks result, feature audit, and consumer impact note | The inspected abstraction or public API has compatibility evidence | Unknown consumers, future feature unification, or behavioral compatibility is proven |
| Dependency or generated binding is controlled | `Cargo.lock`/workspace diff, `cargo tree -e features`, audit/deny result, generated binding diff, and accepted-risk owner | The inspected dependency or generated artifact has provenance and feature evidence | Future advisories, unpublished platform targets, or all transitive behavior are covered |

## Evidence Quality Labels

- **Strong evidence**: current source/Cargo/toolchain inspected, command or artifact named, exit code or review status recorded, final-edit freshness stated, and proof limits named.
- **Weak evidence**: compile success for unsafe/runtime behavior, local unit-only concurrency test, old audit report, generic Rust guidance, or memory claim without current Cargo/source.
- **Missing evidence**: no ownership map, no panic/unwrap scan, no `// SAFETY:` contract, no Miri/fuzz/loom/audit/deny/semver result when relevant, or no owner for not-run validation.
- **Invalid evidence**: undocumented `unsafe` as proof, `unwrap()` in recoverable library path, `cargo build` as compatibility proof, stale generated binding, or inaccessible report.

## Graph, Memory, And Execution Reconciliation

- Treat repository graph, project memory, generated binding summaries, old validation, Cargo lock reports, and prior agent output as discovery inputs until current source, Cargo files, toolchain config, generated artifacts, and validation confirm them.
- Accept a prior "safe", "race-free", "no unsafe", "dependency clean", "runtime singular", or "API compatible" claim only when current source and Cargo metadata still match.
- Mark evidence stale after edits to unsafe blocks, FFI bindings, async runtime entrypoints, Cargo manifests, lockfiles, feature flags, public traits/types, generated bindings, validation fixtures, or reports.
- Map every accepted Rust claim to a current command, artifact/report, inspected path, owner approval, or explicit not-run residual risk.

## Tool Permission Boundary

| Action | Boundary record |
| --- | --- |
| Source reads, graph search, Cargo metadata inspection, generated binding review, and report review | Read-only local shell action; cite searched paths and avoid full output dumps. |
| `cargo fmt`, `cargo clippy`, `cargo test`, `cargo doc`, audit/deny/semver checks, and report refreshes | State-mutating only for caches, reports, build artifacts, or local fixtures; cite command, exit code, artifact path, and rollback/cleanup if relevant. |
| Miri, loom, fuzzing, criterion, sanitizer, profiler, local service startup, or generated binding refresh | Local runtime or generated-artifact action; record toolchain, data fixture, stop condition, output path, and secret-output redaction. |
| Dependency upgrade, publishing, staging/production profiling, FFI system library install, or credential-backed registry access | High-risk state-mutating action; require explicit scope, rollback/forward-fix path, redaction, retention limit, and stop condition. |

## Handoff Evidence Shape

```yaml
rust_evidence_closure:
  inspected_paths:
    - path: ""
      finding: ""
  accepted_prior_claims:
    - claim: ""
      current_evidence: ""
  rejected_or_stale_claims:
    - claim: ""
      reason: ""
  changed_rust_surface_to_validation_map:
    - surface: ""
      risk: ownership | error | unsafe_ffi | async_concurrency | trait_api | dependency
      command_or_artifact: ""
      exit_code_or_status: ""
      proves: ""
      does_not_prove: ""
      freshness: fresh | stale | partial | not_run
      owner: ""
  tool_permission_boundary:
    action_class: ""
    sandbox: ""
    state_mutation: ""
    redaction: ""
  residual_risk:
    - risk: ""
      owner: ""
      next_gate: ""
```
