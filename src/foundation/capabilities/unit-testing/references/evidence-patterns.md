# Unit Testing Evidence Patterns

Use this reference when unit-testing closure depends on repository graph, project memory, execution trajectory, validation freshness, fixture ownership, mock boundaries, command output, report artifacts, or a changed-code-to-unit-test map. Keep it as an evidence map, not a second unit testing tutorial.

## Changed-Code-To-Unit-Test Map

| Unit-test claim | Minimum evidence | What it proves | What it does not prove |
| --- | --- | --- | --- |
| Changed rule is covered | Current source path, observable behavior, unit boundary, case matrix row, test path, command, and owner | The inspected rule has a runnable local behavior proof | Alternate entry points, integration wiring, or production configuration are covered |
| Boundary and invalid cases are covered | Exact lower/upper/just-around boundary values, malformed/missing/invalid inputs, expected output or error, and assertion path | The inspected equivalence classes fail loudly when the rule boundary changes | Every input generator, locale, serialization, or UI/API translation is safe |
| Regression trigger is locked | Defect reference or captured input/state, red-before-fix output or justified limitation, final green command, and changed-path scope | The historical local failure has a narrow recurrence guard | Related defects, broader workflow behavior, or integration side effects are covered |
| Determinism is controlled | Clock/timezone/random/UUID/env/global/scheduler source, control mechanism, setup/teardown, replay command, and flake residual risk | The inspected unit test is repeatable under the declared local inputs | CI load, test sharding, or future global-state leaks cannot reintroduce flake |
| Mock or fake does not hide the risk | Mocked collaborator, real collaborator rejected, behavior asserted, limitation statement, and next integration or contract gate when needed | The inspected double isolates nondeterminism without replacing the rule under test | Real database constraints, auth filters, provider payloads, queues, or generated clients behave correctly |
| Fixture or generated input is owned | Fixture/factory/golden/generated source, fields used by assertions, owner, reset/update path, and changed-input command | The inspected test data supports the named behavior and has a maintenance owner | All production data distributions, schema drift, or unrelated fixture consumers are covered |
| Assertion proves behavior | Observable return/state/error/event, rejected private/choreography/snapshot-only assertion, and mutation-style branch that would fail | The inspected assertion fails when the named behavior is inverted or removed | Full mutation score, unrelated branches, or integration behavior are proven |
| Memory or graph coverage claim is current | Prior claim source, current source/test/fixture reread, changed-path-to-test map, final command/report path, and freshness verdict | The accepted memory or graph still matches the inspected unit boundary | Future edits, dynamic imports, skipped tests, or production runtime behavior are covered |

## Graph, Memory, And Execution Reconciliation

- Treat repository graph, project memory, old coverage notes, prior CI results, generated reports, and execution trajectory as discovery inputs until current source and fresh validators confirm them.
- Accept a prior "unit test already covers this", "factory default exercises the branch", "mock is safe", "coverage is sufficient", or "full suite passed" claim only when current source, tests, fixtures, doubles, generated inputs, configs, and command outputs still match.
- Mark evidence stale after edits to production source, unit tests, fixtures, factories, mocks, fakes, snapshots, generated inputs, test config, lockfiles, reports, build outputs, or validation-broker mappings.
- Record inspected and skipped boundaries: public/module function, class method, state guard, parser, mapper, validator, policy, fixture/factory/golden source, mock/fake seam, generated input, command selection, and report artifact.
- Map every final unit-test confidence claim to a current command, test path, case row, fixture source, report artifact, owner review, or explicit not-verified residual unit-test risk.

## Tool Permission Boundary

| Action | Boundary record |
| --- | --- |
| Local source reads, graph search, report inspection, and markdown validation | Read-only local shell action; cite searched paths and avoid full output dumps |
| Local unit tests, targeted validators, mutation/property runs, and builds | State-mutating only for reports, caches, temp files, dist/build artifacts, snapshots, or local fixtures; cite command, exit code, artifact path, sandbox, and cleanup |
| Fixture, snapshot, golden, generated input, or test-data regeneration | State-mutating development action; record source-of-truth input, generated output owner, diff review, rollback path, and stale validation scope |
| External provider, shared database, telemetry, production sample, or connector export | Not unit-test evidence by itself; require owner, bounded dataset, redaction, and integration/contract/security handoff |

## Handoff Evidence Shape

```yaml
unit_testing_evidence_closure:
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
  changed_code_to_unit_test_map:
    - changed_rule_or_branch: ""
      source_path_or_artifact: ""
      test_path_or_case: ""
      command_or_gate: ""
      exit_code_or_status: ""
      proves: ""
      does_not_prove: ""
      owner: ""
  tool_permission_boundary:
    action_class: ""
    sandbox: ""
    state_mutation: ""
    redaction: ""
  residual_unit_test_risk:
    - risk: ""
      owner: ""
      next_gate: ""
```
