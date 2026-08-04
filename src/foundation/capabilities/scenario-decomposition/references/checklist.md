# Scenario Decomposition Checklist

- Derive applicable categories from task-local behavior, decision, failure, boundary,
  trust, recovery, and operational triggers.
- Exclude universal scenario-matrix completion.
- Define a normal scenario only when the changed behavior has a reachable success path.
- Define failure scenarios only for task-local validation, permission, dependency,
  timeout, conflict, or partial-completion mechanisms that are reachable or material.
- Define edge scenarios only where the affected contract distinguishes a boundary,
  empty or maximum input, stale data, or unusual lifecycle state.
- Define abuse scenarios only where a changed trust boundary makes intentional misuse,
  privilege probing, replay, or hostile input material.
- Define recovery scenarios only where a triggered failure can require retry,
  cancellation, cleanup, rollback, or manual correction.
- Define operational scenarios only where the change creates monitoring, support,
  audit, backfill, or incident-handling consequences.
- Attach actor, trigger, precondition, and expected outcome to each scenario.
- Mark release-critical scenarios.
- Map each scenario to verification evidence.
- For each applicable, triggered category, retain its scenarios or record a
  source-backed omission rationale; omit categories with no task-local trigger.
- Preserve non-goals to prevent scenario-driven scope expansion.
- For release-critical scenarios or those reused from prior evidence, record the current evidence source, freshness, validation or not-verified status, owner, and residual risk. Include repository or action-sequence detail when it materially supports the scenario.
