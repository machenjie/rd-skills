# Planning Evidence Patterns

Use this reference when closing a DAG, repair, parallelization decision, or plan-execution consistency check. Evidence must show why the graph is safe to execute, not just that tasks are listed.

## Evidence Map
- **Repository context:** owning surface, caller/callee path, sibling conventions, tests, configs, docs, generated artifacts, and rejected placement locations.
- **Graph validity:** node list, edge list, topological-sort result or manual acyclicity proof, dependency order, and blocked/unblocked parallel groups.
- **Collision analysis:** shared files, tables, generated artifacts, config, fixtures, external resources, owners, and the reason parallel nodes cannot conflict.
- **Validation boundaries:** command, validator, expected output, evidence artifact, exit code/status, freshness, downstream unblock rule, and not-run residual risk.
- **Rollback and stop conditions:** rollback node, revert note, maximum retry path, repeated-failure trigger, owner, and release or deployment consequence.
- **Plan-execution consistency:** accepted nodes compared with final changed files, skipped work, stale evidence, unplanned behavior, and residual risk.

## Duration And Parallel Completion

- A timing claim needs nonnegative task-duration weights in a common unit. Record their sources, assumptions, and uncertainty intervals.
- In an acyclic graph, sum task durations along each dependency path, including single-node paths. The largest sum is the critical-path duration lower bound; retain tied paths and alternatives allowed by uncertain estimates.
- A dependency lower bound is not a feasible completion schedule. Slot limits, shared resources, scheduling, context transfer, and integration can increase elapsed time.
- Compare serial and feasible parallel completion for the same accepted scope and assumptions.
- For that same-scope comparison, include applicable overhead in each estimate before claiming a time saving.
- Without sufficient duration or overhead evidence, report dependency order, safe parallel opportunities, and timing unknown. Do not invent a benefit from node count or dependency depth.

For example, let A precede B, each taking one hour, with independent C taking ten hours. The duration critical path is C, not the deeper A-to-B path. Serial completion takes twelve hours; two slots with no overhead finish in ten. Three additional hours of parallel-only integration make that schedule take thirteen hours. Scheduling does not shorten the graph's ten-hour dependency lower bound.

## Closure Rules
- Do not close a DAG when any node still says TBD, TODO, similar to above, handle edge cases, write tests, or cleanup without named files and behavior.
- Do not claim parallelism without a shared-resource scan and owner decision.
- Do not treat green validation as plan closure unless it is fresh against the final task graph and final changed files.
