# Task DAG Decomposition Checklist

- Define task goal, boundaries, inputs, and output for each node.
- Record dependencies and explain why they block.
- Identify parallelizable tasks and merge-conflict risks.
- Place safety, compatibility, and migration prerequisites early.
- Attach tests and review evidence to each behavior-changing task.
- Add rollback or recovery notes for runtime changes.
- Define integration checkpoints and handoff points.
- Confirm no task depends on hidden or stale context.
