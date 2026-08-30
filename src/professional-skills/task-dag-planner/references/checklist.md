# Task DAG Checklist

- Identify prerequisite decisions and missing information.
- Place contract and schema compatibility work before consumers.
- Separate migration, backfill, code path, and cleanup tasks.
- Create independent slices where parallel work is safe.
- Attach acceptance criteria and tests to each task.
- Add observability or documentation tasks only when they independently satisfy acceptance or reduce a named risk.
- Add feature flag, rollout, and rollback tasks only when the change triggers them.
- Verify no cyclic dependency exists.
- Keep each task reviewable on its own.
- Assign every task one complete review contract: strategy, scope, evidence, and boundary.
- For combined review, name the accountable owner, covered task IDs, final changed scope, and any risk-specific independent reviews.
- Record topological-sort or acyclicity proof, critical path, collision scan, validation artifact, freshness, plan-execution consistency, and residual risk owner.
