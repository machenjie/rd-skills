# Scenario Decomposition Checklist

- Define the normal scenario for the approved behavior.
- Define failure scenarios for validation, permission, dependency, timeout, conflict, and partial completion.
- Define edge scenarios for boundaries, empty input, maximum input, stale data, and unusual lifecycle state.
- Define abuse scenarios for intentional misuse, privilege probing, replay, and hostile input.
- Define recovery scenarios for retry, cancellation, cleanup, rollback, and manual correction.
- Define operational scenarios for monitoring, support diagnosis, audit, backfill, and incident handling.
- Attach actor, trigger, precondition, and expected outcome to each scenario.
- Mark release-critical scenarios.
- Map each scenario to verification evidence.
- Preserve non-goals to prevent scenario-driven scope expansion.
- Map repository graph, accepted/rejected memory, execution trajectory, validator command, report/artifact path, freshness, owner, and residual risk to every scenario that is release-critical or reused from prior evidence.
