# Test Strategy Evidence Patterns

Use this reference when closure depends on repository graph, project memory, execution trajectory, validation freshness, command output, report artifacts, affected-test selection, or a changed-code-to-test map. Keep it as an evidence map, not a second testing tutorial.

## Changed-Code-To-Test Map

| Claim | Minimum evidence | What it proves | What it does not prove |
| --- | --- | --- | --- |
| Changed behavior is covered | Changed path, public behavior, acceptance/risk ID, test level, command, and owner. | The named behavior has a runnable proof obligation. | Untouched consumers, hidden branches, or production-only conditions are safe. |
| Negative path is covered | Denied/invalid/conflict/timeout/retry/rollback/partial-failure case and expected result. | The inspected failure state is distinguished from success. | Every failure taxonomy or provider-specific error is covered. |
| Contract compatibility is covered | Consumer inventory, schema/API/event/SDK diff, generated-client check, old/new fixture. | Inspected consumers have compatibility evidence. | Unknown external consumers or stale generated clients are safe. |
| Migration/data integrity is covered | Forward command, rollback command, representative data shape, integrity assertion, artifact. | Inspected data path can move forward and recover in test. | Production volume, lock duration, backup/restore RTO, or all data skew is safe. |
| Affected-test selection is credible | Repository graph, changed paths, direct/transitive dependents, generated inputs, cache key inputs. | Selected commands match inspected graph and changed inputs. | Full-suite parity or unseen dynamic imports are proven unless separately checked. |
| Validation is fresh | Command, working directory, exit code, output summary, report/artifact path, final-edit freshness. | Evidence was produced after the final material edit for the mapped risk. | Later source/config/fixture/generated/report edits are covered. |
| Omitted level is justified | Technical reason, compensating evidence, release consequence, owner, and reopen trigger. | The omission is explicit and owned. | The omitted level would add no future value if risk changes. |

## Graph, Memory, And Execution Reconciliation

- Treat repository graph, project memory, old coverage notes, prior CI results, generated reports, and execution trajectory as discovery inputs until current source confirms them.
- Accept prior "covered by integration", "E2E sufficient", "no consumer", "full suite passed", or "affected tests selected correctly" claims only when current changed paths, tests, generated inputs, CI config, and reports still match.
- Reject or downgrade memory when it lacks date, owner, command, changed-path scope, generated-input freshness, or coverage alignment.
- Mark evidence stale after edits to source, tests, fixtures, generated artifacts, schemas, migrations, lockfiles, CI config, reports, build outputs, or validation-broker mappings.
- Map every final test confidence claim to a command, test, validator, report, diff, review artifact, owner approval, or explicit not-run residual risk.

## Tool Permission Boundary

| Action | Boundary record |
| --- | --- |
| Local source reads, graph search, report inspection, markdown validation | Read-only local shell action; cite searched paths and avoid full output dumps. |
| Local unit/integration/contract/E2E validators and builds | State-mutating only for reports, caches, temp files, dist/build artifacts, or test databases; cite log path, command, exit code, and cleanup. |
| Fixture, generated-client, migration, or test-data regeneration | State-mutating development action; record source-of-truth input, generated output owner, diff review, and rollback/revert path. |
| External sandbox, live provider, cloud, deploy, migration, backup, restore, or rollback command | High-risk action; require permission, dry-run/sandbox proof when available, rollback/forward-fix path, redaction rule, and stop condition. |
| Dashboard, telemetry, audit, or connector export | Read-only or connector-scoped; redact tenant/user/secret-bearing values and state retention limits. |

## Handoff Evidence Shape

```yaml
test_strategy_evidence_closure:
  inspected_paths:
    - path: ""
      finding: ""
  accepted_prior_claims:
    - claim: ""
      current_evidence: ""
  rejected_or_stale_claims:
    - claim: ""
      reason: ""
  changed_code_to_test_map:
    - changed_path_or_contract: ""
      behavior_or_risk: ""
      test_level: ""
      command: ""
      exit_code: ""
      artifact_or_report: ""
      proves: ""
      does_not_prove: ""
      owner: ""
      freshness: ""
  omitted_levels:
    - level: ""
      rationale: ""
      compensating_evidence: ""
      residual_risk_owner: ""
      release_consequence: ""
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
