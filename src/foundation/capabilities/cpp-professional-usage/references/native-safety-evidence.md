# Cpp Native Safety Evidence

Use this reference when C/C++ review closure depends on ownership maps, sanitizer freshness, fuzz or stress evidence, repository graph, project memory, generated bindings, or tool permission boundaries. Keep it as an evidence map, not a second C++ tutorial.

## Native Risk To Evidence Map

| Native risk | Minimum evidence | What it proves | What it does not prove |
| --- | --- | --- | --- |
| Ownership transfer | Allocation/acquisition site, RAII owner, move/copy policy, deleter, and release path on success and error | The inspected resource has a single cleanup owner | Every alias, callback, or generated binding keeps lifetime safe |
| Borrowed lifetime | Caller/callee lifetime contract, reference/iterator invalidation points, moved-from use search, and negative or sanitizer case | The inspected borrow cannot outlive its owner through the named path | All optimization levels, threads, or foreign callers preserve the lifetime |
| Bounds and UB | Input size clamp, overflow check, aliasing/alignment decision, ASan/UBSan command, and boundary/fuzz case | Representative unsafe inputs fail closed or are handled safely | Full exploit coverage, all parser states, or all compilers are proven |
| Concurrency | Shared-state owner, lock order, atomic memory order, cancellation/lifetime boundary, and TSan or stress report | The inspected synchronization path has a stated invariant and evidence | All schedules, platforms, or production contention patterns are proven |
| Resource cleanup | File descriptor/socket/handle/thread ownership, `O_CLOEXEC` or platform equivalent, cleanup-on-error path, and leak report | The inspected error paths release acquired resources | Every external dependency or process boundary is leak-free |
| Generated binding | Source schema/header, generator version, generated diff, exception/error translation, and compatibility check | The inspected native/foreign boundary matches current generated artifacts | Unknown consumers or unreleased generated clients remain compatible |
| Graph or memory claim | Prior claim source/date, current header/source/build/test reread, graph search, validation command, and rejected stale assumptions | Accepted memory or graph still matches current source | Future edits, hidden entry points, or platform-specific builds are covered |
| Tool permission boundary | Build/fuzz/package action class, sandbox, artifact write path, timeout, redaction rule, and cleanup/rollback note | The evidence-producing command is bounded and auditable | The command is safe for production data or every workstation setup |

## Validation Freshness Rules

- Re-run or disclose stale evidence after edits to headers, exported symbols, generated bindings, build files, compiler flags, sanitizer config, package manifests, test fixtures, fuzz corpora, or benchmark inputs.
- Treat ASan/UBSan/TSan/MSan as different lanes; one green sanitizer does not prove the others.
- Treat static analysis as a defect finder, not behavior proof; map each accepted finding suppression to owner, reason, and expiration.
- Treat fuzz coverage as corpus-specific; state seed corpus, dictionary, timeout, sanitizer lane, crash artifact path, and not-covered grammar branches.
- Treat repository graph and project memory as selectors until current source and command output confirm them.

## Handoff Evidence Shape

```yaml
cpp_native_safety_evidence:
  inspected_boundaries:
    - boundary: ownership | borrow | ub_bounds | concurrency | resource_cleanup | generated_binding
      source_or_artifact: ""
      finding: ""
  graph_memory_execution:
    accepted_claims:
      - claim: ""
        current_evidence: ""
    rejected_or_stale_claims:
      - claim: ""
        reason: ""
  validation_map:
    - risk: ""
      command_or_artifact: ""
      exit_code_or_status: ""
      proves: ""
      does_not_prove: ""
      owner: ""
      freshness: fresh | stale | partial | not_run
  tool_permission_boundary:
    action_class: ""
    sandbox: ""
    write_scope: ""
    redaction: ""
  residual_risk:
    - risk: ""
      owner: ""
      next_gate: ""
```
