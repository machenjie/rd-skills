# Java JVM Evidence Patterns

Use this reference when Java/JVM closure depends on repository graph, project memory, execution trajectory, validation freshness, transaction/runtime/dependency proof, tool permission boundaries, or changed-surface-to-validation mapping. Keep it as an evidence map, not a Java tutorial.

## Changed-JVM-Surface-To-Validation Map

| JVM claim | Minimum evidence | What it proves | What it does not prove |
| --- | --- | --- | --- |
| Transaction boundary is correct | Current bean caller/callee path, proxy crossing decision, propagation/isolation/rollback rule, and rollback integration test | The inspected Spring boundary executes through the expected advice and rolls back for the tested failure | Every call path, nested transaction, scheduler/event listener path, or production database behavior is covered |
| Executor or virtual-thread path is bounded | Executor inventory, queue/rejection/shutdown/timeout policy, interruption behavior, and JFR pinning result or not-run owner | The inspected asynchronous path has explicit ownership and bounded failure behavior | All load spikes, carrier-thread interactions, or third-party blocking calls are covered |
| ORM and DTO boundary is safe | Entity/DTO map, fetch plan, query-count output or Testcontainers result, and API/event serialization check | The inspected persistence boundary avoids entity leakage and measured N+1 behavior | All queries, historic payloads, lazy paths, or downstream consumers are proven safe |
| JVM runtime setting matches SLO | JDK/vendor/version, heap/container flags, GC/JFR/async-profiler artifact, allocation or pause summary, and SLO target | The measured path has runtime evidence aligned to the named SLO | Production data shape, peak traffic, kernel/container variance, or all GC phases are covered |
| Dependency or generated boundary is controlled | BOM/lock diff, dependency scan result, generated artifact diff, compatibility note, and accepted-risk owner | The inspected upgrade or generated client has provenance and compatibility evidence | Unknown transitive behavior, unpublished consumers, or future CVEs are covered |
| Security-sensitive JVM idiom is safe | Deserialization/logging/XML/SSRF path, allowlist or disabled feature, dependency status, and negative test or security review | The named trust boundary has a reviewed mitigation | All gadget chains, deployment flags, or third-party service behavior are covered |

## Evidence Quality Labels

- **Strong evidence**: current source/build/config inspected, command or artifact named, exit code or review status recorded, final-edit freshness stated, and proof limits named.
- **Weak evidence**: local unit test for transaction/runtime behavior, old JFR/GC/query output, generic framework guidance, or memory claim without current source.
- **Missing evidence**: no bean path, no rollback test, no executor inventory, no query count, no dependency scan, no runtime artifact, or no owner for not-run validation.
- **Invalid evidence**: annotation presence as transaction proof, compile success as runtime proof, pass-through service layer as design proof, stale generated artifact, or inaccessible report.

## Graph, Memory, And Execution Reconciliation

- Treat repository graph, project memory, incident notes, generated summaries, old validation, and prior agent output as discovery inputs until current source, build files, configs, generated artifacts, and validation confirm them.
- Accept a prior "transaction covered", "executor bounded", "safe ORM boundary", "dependency clean", or "runtime low risk" claim only when the current inspected files still match.
- Mark evidence stale after edits to Spring beans, annotations, build files, dependency locks, generated clients, ORM mappings, DTO/API models, runtime flags, validation fixtures, or reports.
- Map every accepted JVM claim to a current command, artifact/report, inspected path, owner approval, or explicit not-run residual risk.

## Tool Permission Boundary

| Action | Boundary record |
| --- | --- |
| Source reads, graph search, build-file inspection, generated artifact review, and report review | Read-only local shell action; cite searched paths and avoid full output dumps. |
| Maven/Gradle tests, validators, dependency scans, code generation checks, and report refreshes | State-mutating only for caches, reports, build artifacts, generated output, or local fixtures; cite command, exit code, artifact path, and rollback/cleanup if relevant. |
| Testcontainers, local service startup, profiling, JFR/GC capture, and load probes | Local runtime action; record service scope, ports, data fixture, stop condition, cleanup, and secret-output redaction. |
| Staging/production profiling, dependency upgrade, publish, database migration, or cloud credential use | High-risk state-mutating action; require explicit scope, rollback/forward-fix path, redaction, retention limit, and stop condition. |

## Handoff Evidence Shape

```yaml
jvm_evidence_closure:
  inspected_paths:
    - path: ""
      finding: ""
  accepted_prior_claims:
    - claim: ""
      current_evidence: ""
  rejected_or_stale_claims:
    - claim: ""
      reason: ""
  changed_jvm_surface_to_validation_map:
    - surface: ""
      risk: transaction | executor | orm_boundary | runtime | dependency | security
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
