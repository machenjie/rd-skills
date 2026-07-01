# Planning Evidence Patterns

Use this reference when closing a DAG, route repair, parallelization decision, or plan-execution consistency check. Evidence must show why the graph is safe to execute, not just that tasks are listed.

## Evidence Map
- **Repository context:** owning surface, caller/callee path, sibling conventions, tests, configs, docs, generated artifacts, and rejected placement locations.
- **Graph validity:** node list, edge list, topological-sort result or manual acyclicity proof, critical path, and blocked/unblocked parallel groups.
- **Collision analysis:** shared files, tables, generated artifacts, config, fixtures, external resources, owners, and the reason parallel nodes cannot conflict.
- **Verification gates:** command, validator, expected output, evidence artifact, exit code/status, freshness, downstream unblock rule, and not-run residual risk.
- **Rollback and stop conditions:** rollback node, revert note, maximum retry path, route-repair trigger, owner, and release or deployment consequence.
- **Plan-execution consistency:** accepted nodes compared with final changed files, skipped work, stale evidence, unplanned behavior, and residual risk.

## Closure Rules
- Do not close a DAG when any node still says TBD, TODO, similar to above, handle edge cases, write tests, or cleanup without named files and behavior.
- Do not claim parallelism without a shared-resource scan and owner decision.
- Do not treat green validation as plan closure unless it is fresh against the final task graph and final changed files.

