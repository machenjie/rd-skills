# Task DAG Checklist

- Identify prerequisite decisions and missing information.
- Place contract and schema compatibility work before consumers.
- Separate migration, backfill, code path, and cleanup tasks.
- Create independent slices where parallel work is safe.
- Attach acceptance criteria and tests to each task.
- Add observability and documentation tasks.
- Add feature flag, rollout, and rollback tasks where needed.
- Verify no cyclic dependency exists.
- Keep each task reviewable on its own.
