# Test Strategy Evidence Patterns

Use this reference when closure depends on repository inspection, prior task evidence, observable action sequence, validation freshness, command output, report artifacts, affected-test selection, or a changed-code-to-test map. Keep it as an evidence map, not a second testing tutorial.

## Changed-Code-To-Test Map

| Claim | Minimum evidence | What it proves | What it does not prove |
| --- | --- | --- | --- |
| Changed behavior is covered | Changed path, public behavior, acceptance/risk ID, test level, command, and owner. | The named behavior has a runnable proof obligation. | Untouched consumers, hidden branches, or production-only conditions are safe. |
| Negative path is covered | Denied/invalid/conflict/timeout/retry/rollback/partial-failure case and expected result. | The inspected failure state is distinguished from success. | Every failure taxonomy or provider-specific error is covered. |
| Contract compatibility is covered | Consumer inventory, schema/API/event/SDK diff, generated-client check, old/new fixture. | Inspected consumers have compatibility evidence. | Unknown external consumers or stale generated clients are safe. |
| Migration/data integrity is covered | Forward command, rollback command, representative data shape, integrity assertion, artifact. | Inspected data path can move forward and recover in test. | Production volume, lock duration, backup/restore RTO, or all data skew is safe. |
| Affected-test coverage obligation is bounded | Changed paths, direct/transitive dependents, generated inputs, cache-key inputs, and required observable signals. | The strategy identifies graph surfaces and command-signal requirements for targeted selection. | Exact repository entrypoints, combined coverage, fallbacks, or full-suite parity are selected. |
| Validation is fresh | Command, working directory, exit code, output summary, report/artifact path, final-edit freshness. | Evidence was produced after the final material edit for the mapped risk. | Later source/config/fixture/generated/report edits are covered. |
| Omitted level is justified | Technical reason, compensating evidence, release consequence, owner, and reopen trigger. | The omission is explicit and owned. | The omitted level would add no future value if risk changes. |

## Current Evidence And Freshness

- Treat repository inspection, prior task evidence, old coverage notes, prior CI results, generated reports, and observable action sequence as discovery inputs until current source confirms them.
- Accept prior "covered by integration", "E2E sufficient", "no consumer", "full suite passed", or "affected tests selected correctly" claims only when current changed paths, tests, generated inputs, CI config, and reports still match.
- Reject or downgrade memory when it lacks date, owner, command, changed-path scope, generated-input freshness, or coverage alignment.
- Mark evidence stale after edits to source, tests, fixtures, generated artifacts, schemas, migrations, lockfiles, CI config, reports, build outputs, or targeted-validation-selection mappings.
- When making a final test confidence claim for the selected strategy and inspected scope, map it to a command, test, validator, report, diff, review artifact, owner approval, or explicit not-run residual risk.

- If fixture, generated-client, migration, or test-data regeneration, record source-of-truth input, generated output owner, diff review, and rollback/revert path.
- If external sandbox, live provider, cloud, deploy, migration, backup, restore, or rollback command, require permission, dry-run/sandbox proof when available, rollback/forward-fix path, redaction rule, and stop condition.
- If dashboard, telemetry, audit, or connector export, keep access read-only or approved-connector-scoped, redact tenant/user/secret-bearing values, and state retention limits.
