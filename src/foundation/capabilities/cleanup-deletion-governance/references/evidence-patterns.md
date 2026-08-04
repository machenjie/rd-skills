# Cleanup Deletion Evidence Patterns

Use this reference when closure depends on repository inspection, prior task evidence, observable action sequence, validation freshness, command output, generated reports, or a deletion-to-validation map. Keep it as an evidence map, not a second cleanup tutorial.

## Deletion Claim To Evidence Map

| Deletion claim | Minimum evidence | What it proves | What it does not prove |
| --- | --- | --- | --- |
| Artifact has no callers | Static search scope, generated/reference search, runtime registration/reflection search, config/script/docs search, and skipped-search rationale. | The inspected caller classes did not reference the artifact. | Unknown dynamic consumers, external users, or unsearched runtime paths are absent. |
| Public contract can be removed | Consumer inventory, usage threshold/window, compatibility/deprecation rule, migration docs, release note, rollback path. | Inspected consumers have a migration and removal basis. | Unknown external consumers or stale generated clients are safe. |
| Flag or fallback is obsolete | Owner, rollout or incident state, telemetry window, old/new branch behavior, re-enable or replacement path, tests. | The inspected temporary path is no longer needed or has a bounded replacement. | Future incident recovery or unobserved cohorts are safe. |
| Expand/contract path can contract | Migration phase, backfill/data integrity result, old-version usage, old-path telemetry, rollback/data-loss limit, contract tests. | The inspected old data or compatibility path is safe to remove under the stated condition. | Production volume, mixed-version deploys, or undiscovered old producers are covered. |
| Generated/runtime artifact can be removed | Generator source, rebuild command, registration search, package/install impact, generated diff. | The generated/runtime path is tied to source and validated after regeneration. | Other generated outputs or runtime plugins are unaffected. |
| Shortcut can be closed | Bounded shortcut note, ceiling, owner, review date, upgrade/deletion trigger, validation command, closure evidence. | The accepted shortcut has an accountable conversion or deletion path. | Similar shortcuts or future scope expansion are governed. |
| Validation is fresh | Command, working directory, exit code, output summary, report/artifact path, covered paths, final-edit order. | Evidence was produced after the final material edit for the mapped deletion risk. | Later source/config/generated/report edits or untested consumers are covered. |

## Current Evidence And Freshness

- Treat repository inspection, prior task evidence, old cleanup notes, generated reports, prior validation, and observable action sequence as selectors until current source confirms them.
- Accept prior "unused", "no consumer", "flag complete", "fallback obsolete", or "generated artifact safe" claims only when current source, generated inputs, telemetry/report paths, and validator mappings still match.
- Reject or downgrade memory that lacks date, owner, inspected path scope, command/report artifact, validation freshness, or residual-risk owner.
- Mark evidence stale after edits to source, registries, config, generated artifacts, docs, reports, tests, validators, package/install outputs, or cleanup records.
- For each final deletion-safety claim, cite current source, graph or search evidence, telemetry or report, validator output, owner approval, or explicit not-run residual risk. The handoff also names unsearched dynamic or external consumers.

- If generated rebuild, package/install validation, or cleanup fixture regeneration, record source-of-truth input, generated output owner, diff review, and revert path.
- If destructive deletion, live config removal, deploy, publish, migration, backup, restore, or rollback command, require explicit permission, dry-run or rendered diff when available, stop condition, rollback or forward-fix path, and secret/output redaction.
