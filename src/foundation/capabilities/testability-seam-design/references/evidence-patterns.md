# Testability Seam Evidence Patterns

Use this reference when closure depends on current repository graph, project memory, execution trajectory, validation freshness, tool permission boundary, or changed-path-to-seam mapping.

## Changed-Path-To-Seam Map

| Seam claim | Minimum evidence | What it proves | What it does not prove |
| --- | --- | --- | --- |
| Public boundary is testable | Current source path, public entry point, observable output/side effect, test path, command, and owner | The inspected behavior can be verified without private-helper export | All callers, integrations, or UI/API translations are covered |
| Private helper remains private | Rejected export or visibility change, replacement public-boundary assertion, and placement rationale | Encapsulation was preserved for the inspected behavior | Future tests will not request the same shortcut |
| Double fidelity is sufficient | Real contract source, fake/stub/mock/spy choice, calibration command or explicit limitation, and next gate | The double is adequate for the named risk at the chosen layer | The real provider is fully verified unless contract/integration evidence ran |
| Determinism is controlled | Clock/random/UUID/env/scheduler/IO source, override mechanism, reset/cleanup path, replay command, and flake risk | The test can repeat under declared inputs | CI load, future globals, or external services cannot introduce flake |
| Fixture ownership is bounded | Fixture/factory/golden/generated source, asserted fields, owner, update/delete path, and privacy status | The test data supports the named behavior with a maintenance boundary | Production distributions or unrelated fixture consumers are covered |
| Characterization is fresh | Behavior boundary, pre-move command, post-move command, report path, exit code, and preserved-bug decision | The refactor preserved the characterized observable behavior | Uncharacterized branches or hidden side effects are safe |
| Memory or graph claim is current | Prior claim source, current graph/source/test reread, accepted/rejected claims, final validator, and freshness verdict | Old seam evidence still matches current source | Future edits, dynamic imports, skipped suites, or generated artifacts remain safe |

## Graph, Memory, And Execution Reconciliation

- Treat repository graph, project memory, old coverage reports, prior CI logs, generated summaries, and agent notes as discovery inputs until current source and fresh validators confirm them.
- Accept a prior "public behavior already covered", "mock is safe", "fixture is owned", "fake matches provider", or "full validation passed" claim only when current source, tests, fixtures, doubles, generated inputs, configs, and command outputs still match.
- Mark evidence stale after edits to production source, tests, fixtures, factories, mocks, fakes, snapshots, golden files, generated inputs, config, lockfiles, reports, build outputs, or validation-broker mappings.
- Record inspected and skipped boundaries: public entry point, private helper, collaborator, external provider, dependency graph, fixture/golden source, generated input, command selection, and report artifact.
- Map every final seam confidence claim to a command, test path, report artifact, fixture source, owner review, or explicit not-verified residual seam risk.

## Tool Permission Boundary

| Action | Boundary record |
| --- | --- |
| Local source reads, graph search, report inspection, and markdown validation | Read-only local shell action; cite searched paths and avoid full output dumps |
| Local validators, unit/integration/contract tests, mutation/property runs, and builds | State-mutating only for reports, caches, temp files, dist/build artifacts, snapshots, fixtures, or local test data; cite command, exit code, artifact path, sandbox, and cleanup |
| Fixture, snapshot, golden, generated input, or test-data regeneration | State-mutating development action; record source input, generated output owner, diff review, rollback path, and stale validation scope |
| External provider, shared database, telemetry, production sample, or connector export | Not seam evidence by itself; require owner, bounded dataset, redaction, and integration/contract/security handoff |

## Handoff Evidence Shape

```yaml
testability_seam_evidence_closure:
  inspected_boundaries:
    - boundary: ""
      current_source_or_artifact: ""
      finding: ""
  accepted_prior_claims:
    - claim: ""
      current_evidence: ""
      freshness: ""
  rejected_or_stale_claims:
    - claim: ""
      reason: ""
  changed_path_to_seam_map:
    - changed_path_or_behavior: ""
      public_boundary: ""
      seam_or_double: ""
      test_or_validator: ""
      report_path: ""
      exit_code_or_status: ""
      proves: ""
      does_not_prove: ""
      owner: ""
  tool_permission_boundary:
    action_class: ""
    sandbox: ""
    state_mutation: ""
    redaction: ""
  residual_seam_risk:
    - risk: ""
      owner: ""
      next_gate: ""
```

## Blocking Conditions

Block closure when private-helper export is accepted without a public-boundary attempt, a double represents a real provider with no fidelity evidence or limitation, nondeterministic inputs remain uncontrolled, fixture ownership is unknown, characterization runs after movement, old graph/memory/validation claims are reused without current-source confirmation, or state-mutating validation lacks permission/sandbox and rollback disclosure.
