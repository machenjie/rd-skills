# Regression Testing Evidence Patterns

Use this reference when closure depends on current repository graph, project memory, execution trajectory, validation freshness, command output, report artifacts, tool permission boundaries, or a changed-defect-to-test map. Keep it as an evidence map, not a second testing tutorial.

## Defect-To-Regression Evidence Map

| Regression claim | Minimum evidence | What it proves | What it does not prove |
| --- | --- | --- | --- |
| Defect is reproduced | Defect/incident/review reference, exact trigger input/state/role/timing/dependency, test path, command, and matching failure output | The test exercises the named historical failure mode | Adjacent variants, production-only dependencies, or unreported causes are covered |
| Red-before-fix is credible | Pre-fix commit/branch/revert state, command, exit code, failure output, and why the failure matches the original defect | The guard would have caught the defect before repair | The whole fix is correct or every recurrence path is covered |
| Green-after-fix is fresh | Final source/test/fixture state, command, exit code, report/artifact path, and final-edit timestamp or freshness statement | The same guard passes after the final material change | Later edits, skipped tests, flaky shards, or uninspected clients remain safe |
| Test level is narrow enough | Defect boundary, rejected broader/narrower levels, unit/integration/E2E rationale, and next gate when a double hides risk | The selected level should catch recurrence with reasonable signal and cost | Lower layers, real infrastructure, browser behavior, or external provider behavior are proven when not tested |
| Fixture mirrors trigger | Original payload/data shape, minimized-equivalent rationale, fixture owner, reset/update path, and sensitive-data redaction status | The inspected fixture represents the recurrence condition | Production distribution, future schema drift, or every tenant/object case is covered |
| Security regression is safe | Abuse vector, denied/non-leak assertion, same-pattern scan, non-production target, and security review or residual-risk owner | The inspected vulnerability path has a bounded non-regression guard | Live attack safety, full exploit coverage, or all authorization boundaries are proven |
| Untestable decision is justified | Rejected replay/fake/stub/contract/chaos options, infeasibility reason, residual risk, compensating control, owner, and expiry | Automated regression is currently infeasible for the named defect | Recurrence is impossible or monitoring will catch every failure |
| Existing coverage claim is current | Prior claim source/date, current source/test/fixture reread, graph delta, final command/report, and accepted/rejected freshness verdict | Old evidence still matches the inspected defect boundary | Future edits, dynamic callers, or skipped suites remain covered |

## Graph, Memory, And Execution Reconciliation

- Treat repository graph, project memory, bug trackers, old CI output, previous agent reports, and incident notes as discovery inputs until current source, fixtures, generated inputs, and fresh validators confirm them.
- Accept a prior "regression already covered", "this test failed before", "fixture matches production", or "security path is denied" claim only when the current defect boundary, test path, fixture, and command output still match.
- Mark evidence stale after edits to source, test code, fixtures, factories, generated inputs, mocks/fakes, provider stubs, schemas, feature flags, test config, reports, build outputs, or validation commands.
- Record inspected and skipped boundaries: changed source, existing tests, fixtures, generated inputs, bug report, incident notes, same-pattern paths, CI gate, and old claims.
- Map every final regression confidence claim to a command, test path, failure output, report artifact, fixture source, owner review, or explicit not-verified residual risk.

## Tool Permission Boundary

| Action | Boundary record |
| --- | --- |
| Source reads, graph search, report inspection, and markdown validation | Read-only local shell action; cite searched paths and avoid full output dumps |
| Local unit, integration, E2E, mutation, property, or targeted validator command | State-mutating only for reports, caches, temp files, snapshots, fixtures, build artifacts, or local test data; cite command, exit code, artifact path, sandbox, write scope, and cleanup |
| Pre-fix replay through checkout, revert, stash, or branch switch | State-mutating git action; record branch/commit, dirty-worktree protection, rollback path, and whether the replay was skipped with owner |
| Security exploit replay, production incident data, provider sandbox, or shared database use | High-risk action; require non-production scope, owner approval, redaction, retention, same-pattern scan limit, and residual proof limit |

## Handoff Evidence Shape

```yaml
regression_testing_evidence_closure:
  defect_reference: ""
  inspected_boundaries: []
  accepted_prior_claims: []
  rejected_or_stale_claims: []
  defect_to_test_map: []
  red_green_evidence:
    red_before_fix: ""
    green_after_fix: ""
  tool_permission_boundary:
    action_class: ""
    sandbox: ""
    state_mutation: ""
    redaction: ""
  what_remains_unproved: []
  residual_regression_risk: []
  next_gate: ""
```

## Blocking Conditions

Block completion when a confirmed defect lacks automated reproduction or documented impossibility, the proposed test was never observed red before the fix, the fixture omits the original trigger without equivalence rationale, a security regression lacks denied/abuse coverage or same-pattern scan, old coverage claims are reused without current-source confirmation, or state-mutating replay/test commands lack dirty-worktree protection and rollback disclosure.
