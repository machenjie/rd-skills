# Task DAG Decomposition Checklist

- Select mode: plan handoff, multi-surface DAG, safety sequencing, parallelization review, or execution recovery.
- Record boundaries inspected: current source, callers/callees, tests, configs, docs, registry/generated artifacts, graph slice, memory signals, prior trajectory, and skipped boundaries.
- Define task goal, owner surface, inputs, files to inspect, allowed files, output, review gate, and repair route for each node.
- Record dependency edges with type and reason; run or describe cycle check/topological order.
- Identify parallelizable tasks only after shared files, generated outputs, configs, fixtures, data stores, queues, API contracts, and feature flags are checked for collisions.
- Place safety, compatibility, migration, secret-rotation, feature-flag, and rollout prerequisites before dependents.
- Attach validation command, expected output, completion evidence, and review evidence to each behavior-changing task.
- Add rollback or recovery notes, approval owner, and irreversibility flag for runtime or data changes.
- Record `graph_memory_trajectory_judgment`: accepted, rejected, stale, or not verified claims and how they affect nodes, edges, validation, or residual risk.
- Map each node, edge, safety flag, parallelism decision, skipped scope, and repair route to validation, review, owner response, or residual risk.
- Define critical path, integration checkpoints, handoff points, and first unblocked next task.
- Confirm no task depends on hidden context, stale memory, stale graph, stale validation, or unreviewed repair.
- Reconcile accepted DAG with actual changed files, validation freshness, skipped work, and residual risk before final handoff.
