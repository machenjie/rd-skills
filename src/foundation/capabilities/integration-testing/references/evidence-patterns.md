# Integration Testing Evidence Patterns

Use this reference when integration-testing closure depends on repository graph, project memory, execution trajectory, validation freshness, real-boundary proof, fixture/fake/emulator calibration, tool permission boundaries, or changed-surface-to-validation mapping. Keep it as an evidence map, not a second tooling guide.

## Changed-Integration-Surface-To-Validation Map

| Integration claim | Minimum evidence | What it proves | What it does not prove |
| --- | --- | --- | --- |
| Real boundary is exercised | Current source/test/config paths, components included, real dependency or calibrated substitute, and why a unit test cannot prove the seam | The inspected test crosses the named seam that carries the risk | Full user journeys, unrelated services, or production-scale behavior are covered |
| Data and side effects are isolated | Fixture owner, namespace/schema/topic/cache key, cleanup command or rollback strategy, and parallel-safety note | The inspected integration case owns and cleans the state it mutates | Shared staging state, hidden provider state, or future parallel suite behavior is fully safe |
| Failure path is covered | Injected constraint/timeout/error/denial, expected final durable state, retry/DLQ/rollback assertion, and command result | The selected seam handles the named failure without the inspected partial-state bug | Every failure mode, scheduler interleaving, or production recovery path is covered |
| Stub/fake/emulator is calibrated | Stub/fake/emulator source, contract or captured fixture version, request/response verification, and recalibration command or owner | The substitute matches the named contract for the inspected behavior | All provider behavior, undocumented fields, or future contract drift is proven |
| Auth and tenant scope are realistic | Principal/role/scope fixture, tenant/object predicate, denied-case identity, and no-state-change assertion | The inspected real auth path covers allowed and denied access for the named scope | All roles, policy combinations, or external identity provider behavior are covered |
| Prior integration evidence is fresh | Current changed-path map, fixture/generated artifact version, command/report path, exit code/status, and final-edit freshness | The prior run still covers the current wiring and fixture graph | Later source/config/migration/schema/container changes remain covered |

## Evidence Quality Labels

- **Strong evidence**: current source/test/config/fixture inspected, real boundary or calibrated substitute named, command or artifact recorded, exit code/status captured, final-edit freshness stated, and proof limits named.
- **Weak evidence**: happy-path smoke only, mock-only test for a real seam, old CI output, uncalibrated fake, shared staging success, or memory claim without current source.
- **Missing evidence**: no boundary map, no cleanup/isolation, no failure path, no auth denied case when auth matters, no command/status, or no owner for not-run validation.
- **Invalid evidence**: mocked primary seam presented as integration proof, catch-all HTTP stub, shared uncontrolled production/staging dependency, stale generated fixture, or inaccessible report.

## Tool Permission Boundary

| Action | Boundary record |
| --- | --- |
| Source reads, config/fixture inspection, graph search, report review, and dry-run plan review | Read-only local action; cite searched paths and avoid full output dumps. |
| Testcontainers/local emulator run, integration suite, fixture generation, report refresh, and local sandbox cleanup | State-mutating only for local containers, temp files, fixtures, reports, or isolated test databases; cite command, exit code, artifact path, data scope, and cleanup. |
| Shared sandbox, cloud emulator, connector, credential-backed provider, staging dependency, destructive cleanup, or migration-backed integration run | Higher-risk action; require explicit scope, redaction, rollback/cleanup, stop condition, and retained-output boundary. |

## Handoff Evidence Shape

```yaml
integration_testing_evidence_closure:
  boundary_under_test:
    components: []
    real_dependency_or_substitute: ""
    unit_test_gap: ""
  changed_surface_to_validation_map:
    - surface: ""
      risk: real_boundary | isolation | failure_path | calibrated_substitute | auth_scope | freshness
      command_or_artifact: ""
      exit_code_or_status: ""
      proves: ""
      does_not_prove: ""
      freshness: fresh | stale | partial | not_run
      owner: ""
  fixture_and_side_effects:
    owner: ""
    cleanup: ""
    parallel_safety: ""
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
