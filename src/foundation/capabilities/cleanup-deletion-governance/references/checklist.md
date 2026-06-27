# Cleanup Deletion Checklist

Use this reference for L3+ cleanup, public/runtime deletion, stale flags, fallbacks, deprecated APIs, generated or reflection references, rollback-sensitive contraction, shortcut ledger review, or validation freshness disputes. Keep it as a closure checklist, not a second capability body.

## Removal Readiness

- Name the target artifact, source of truth, owner, deletion mode, and reason removal is proposed.
- State the removal condition: threshold, release state, migration phase, telemetry window, owner confirmation, and evidence expiry.
- Classify public or runtime surface: API, schema, event, SDK, CLI, config key, generated client, runtime registration, docs, metric, alert, or runbook.
- Identify rollback: revert, re-enable flag, restore field, redeploy compatibility branch, regenerate artifact, republish package, or forward fix; include state/data limits.
- Confirm cleanup tracking: issue, owner, review date, trigger condition, validation command, and residual risk.

## Search Coverage

- Search static imports, exports, package manifests, generated references, config values, reflection/registration, templates, scripts, cron, CLI commands, docs, dashboards, alerts, tests, migrations, and install/package paths.
- For public contracts, add consumer inventory, usage threshold/window, compatibility notice, migration docs, and unknown-consumer residual risk.
- For generated artifacts, map generator source, rebuild command, generated output owner, and package/install validator.
- For flags and fallbacks, verify old/new branches, tests, metrics, docs, rollout records, incident state, and re-enable path.

## Closure Gate

- Map deletion to tests for remaining behavior, absence of obsolete path, contract/generation/build/install checks, and release or rollback validators.
- Mark graph, memory, generated reports, and command output as selector evidence until current source and fresh validation confirm them.
- Re-run mapped validators after final material edits or disclose stale, partial, not-run, or not-verified status.
- Handoff with what evidence proves, what it does not prove, rollback note, residual deletion risk, and next owner.
