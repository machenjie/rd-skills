# Cleanup Deletion Evidence Patterns

Use this reference when closure depends on repository graph, project memory, execution trajectory, validation freshness, command output, generated reports, or a deletion-to-validation map. Keep it as an evidence map, not a second cleanup tutorial.

## Deletion Claim To Evidence Map

| Deletion claim | Minimum evidence | What it proves | What it does not prove |
| --- | --- | --- | --- |
| Artifact has no callers | Static search scope, generated/reference search, runtime registration/reflection search, config/script/docs search, and skipped-search rationale. | The inspected caller classes did not reference the artifact. | Unknown dynamic consumers, external users, or unsearched runtime paths are absent. |
| Public contract can be removed | Consumer inventory, usage threshold/window, compatibility/deprecation rule, migration docs, release note, rollback path. | Inspected consumers have a migration and removal basis. | Unknown external consumers or stale generated clients are safe. |
| Flag or fallback is obsolete | Owner, rollout or incident state, telemetry window, old/new branch behavior, re-enable or replacement path, tests. | The inspected temporary path is no longer needed or has a bounded replacement. | Future incident recovery or unobserved cohorts are safe. |
| Expand/contract path can contract | Migration phase, backfill/data integrity result, old-version usage, old-path telemetry, rollback/data-loss limit, contract tests. | The inspected old data or compatibility path is safe to remove under the stated condition. | Production volume, mixed-version deploys, or undiscovered old producers are covered. |
| Generated/runtime artifact can be removed | Generator source, rebuild command, registration search, package/install impact, generated diff. | The generated/runtime path is tied to source and validated after regeneration. | Other generated outputs or runtime plugins are unaffected. |
| Shortcut can be closed | Ledger entry, ceiling, owner, review date, upgrade/deletion trigger, validation command, closure evidence. | The accepted shortcut has an accountable conversion or deletion path. | Similar shortcuts or future scope expansion are governed. |
| Validation is fresh | Command, working directory, exit code, output summary, report/artifact path, covered paths, final-edit order. | Evidence was produced after the final material edit for the mapped deletion risk. | Later source/config/generated/report edits or untested consumers are covered. |

## Graph, Memory, And Execution Reconciliation

- Treat repository graph, project memory, old cleanup notes, generated reports, prior validation, and execution trajectory as selectors until current source confirms them.
- Accept prior "unused", "no consumer", "flag complete", "fallback obsolete", or "generated artifact safe" claims only when current source, generated inputs, telemetry/report paths, and validator mappings still match.
- Reject or downgrade memory that lacks date, owner, inspected path scope, command/report artifact, validation freshness, or residual-risk owner.
- Mark evidence stale after edits to source, registries, config, generated artifacts, docs, reports, tests, validators, package/install outputs, or cleanup ledgers.
- Map every final deletion-safety claim to a source path, graph slice, search command, telemetry/report artifact, validator command, owner approval, or explicit not-run residual risk.

## Tool Permission Boundary

| Action | Boundary record |
| --- | --- |
| Local source reads, graph search, report inspection, and markdown validation | Read-only local shell action; cite searched paths and avoid full output dumps. |
| Local validators, builds, report refresh, and dist generation | State-mutating only for reports, caches, temp files, dist/build artifacts, or local fixtures; cite log path, command, exit code, and rollback path. |
| Generated rebuild, package/install validation, or cleanup fixture regeneration | Development write action; record source-of-truth input, generated output owner, diff review, and revert path. |
| Destructive deletion, live config removal, deploy, publish, migration, backup, restore, or rollback command | High-risk action; require explicit permission, dry-run or rendered diff when available, stop condition, rollback or forward-fix path, and secret/output redaction. |

## Handoff Evidence Shape

```yaml
cleanup_deletion_evidence_closure:
  inspected_surfaces:
    - surface: ""
      finding: ""
  accepted_prior_claims:
    - claim: ""
      current_evidence: ""
      freshness: ""
  rejected_or_stale_claims:
    - claim: ""
      reason: ""
  deletion_to_validation_map:
    - target_artifact: ""
      deletion_mode: ""
      evidence_source: ""
      validation_command_or_artifact: ""
      exit_code_or_status: ""
      proves: ""
      does_not_prove: ""
      owner: ""
      freshness: ""
  tool_permission_boundary:
    action_class: ""
    sandbox: ""
    state_mutation: ""
    redaction: ""
  residual_risks:
    - risk: ""
      owner: ""
      next_gate: ""
```
