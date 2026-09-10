# Task DAG Checklist

- Identify prerequisite decisions and missing information.
- Place contract and schema compatibility work before consumers.
- Order migration, backfill, code path, and cleanup where real compatibility or data dependencies require it.
- Create independent slices where parallel work is safe.
- Attach acceptance criteria and tests to each task.
- Add observability or documentation tasks only when they independently satisfy acceptance or reduce a named risk.
- Add feature flag, rollout, and rollback tasks only when the change triggers them.
- Verify no cyclic dependency exists.
- Keep each task reviewable on its own.
- Add independent review only when explicitly requested or justified by a concrete semantic question; task count does not require it.
- If review is needed, state its question, actual scope, source evidence, and the consumer that depends on the answer.
- Record topological-sort or acyclicity proof, critical path, collision scan, validation artifact, freshness, plan-execution consistency, and residual risk owner.
