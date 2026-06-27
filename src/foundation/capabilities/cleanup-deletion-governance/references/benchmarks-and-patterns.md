# Cleanup Deletion Benchmarks And Patterns

Use this reference when a cleanup decision needs benchmark-backed calibration for deletion lifecycle, public contract removal, generated artifacts, rollback, feature flags, fallbacks, expand/contract contraction, or shortcuts. Keep examples decision-focused and avoid tutorial detail.

## Benchmarks

| Benchmark | Cleanup decision it calibrates | Evidence required |
| --- | --- | --- |
| Expand/contract delivery | Remove old schema, alias, upcaster, dual-read, or dual-write path only after old producers/consumers and old data shape are unused. | Migration phase, backfill state, old-path telemetry, rollback/data limit, contract tests. |
| Semantic versioning and deprecation policy | Remove public API, event, SDK, CLI, config, metric, or log field only within an announced compatibility rule. | Consumer inventory, usage window, migration guide, release note, version policy, rollback. |
| Feature flag lifecycle | Delete stale flag and branches after rollout completion rather than leaving permanent conditional architecture. | Flag owner, exposure telemetry, removal trigger, old/new branch tests, config/docs cleanup. |
| Generated artifact provenance | Delete generated output only through its source generator and rebuild path. | Generator source, rebuild command, diff review, package/install validation. |
| Incident and degraded-mode readiness | Remove fallback or kill switch only when replacement, runbook, telemetry, and re-enable/forward-fix path are known. | Incident state, safety analysis, alert/runbook owner, rollback/re-enable path. |
| Shortcut debt governance | Convert or delete shortcuts before their ceiling expires. | `changeforge-shortcut` ledger, owner, review date, upgrade trigger, validation signal. |

## Decision Patterns

- **Delete now:** current source and caller search are clean, runtime/consumer evidence is fresh or explicitly not applicable, validators are mapped, rollback is feasible, and docs/release impact is handled.
- **Keep with owner:** usage is present, telemetry is inconclusive, fallback is still required, compatibility window is active, generated source is unclear, or rollback limits are unacceptable.
- **Convert before delete:** shortcut, temporary scaffold, or compatibility bridge still encodes behavior that must move to a stable owner before removal.
- **Stage the cleanup:** public contracts, migrations, package releases, or config removals need announce/measure/remove phases with release gates.
- **Downgrade evidence:** graph, memory, reports, or prior validation are stale, selector-only, or created before final edits; require current-source confirmation and fresh validation.

## Anti-Patterns

- Removing a public export because no local imports exist while SDK users, docs, or generated clients remain uninspected.
- Deleting a generated file without changing the generator, causing the next build to restore it.
- Removing a fallback after an incident without checking whether the replacement has telemetry and a runbook.
- Closing cleanup because "tests pass" while no absence test, contract test, generated rebuild, or package/install path covers the removed artifact.
- Treating a memory note or old report as current proof that a stale branch is unused.
