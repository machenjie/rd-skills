# Task DAG Planner Reference Index

Use this index to load only the local reference needed for the selected planning risk. Record skipped-reference rationale when a plausible reference is not loaded.

| Reference | Load When | Do Not Load When | Depends On | Conflicts With | Max Level | Output Fragment |
| --- | --- | --- | --- | --- | --- | --- |
| `../examples/example-output.md` | A compact example helps explain simple dependency ordering, evidence, and release sequencing. | The body output contract is enough or the DAG must be source-specific. | Candidate nodes, dependencies, and evidence type. | Treating example tasks as source evidence or accepted plan nodes. | L1 | Tiny task order example. |
| `references/checklist.md` | A bounded review needs a quick DAG readiness and closure checklist. | Detailed evidence map or executable node contract is required. | Prerequisite decisions, migration/contract order, parallel slices, tests, rollout, rollback, and acyclicity proof. | Checklist completion replacing topological proof, collision scan, or plan-execution consistency. | L2 | Task DAG checklist. |
| `references/task-contract-patterns.md` | Nodes must be executable by a fresh agent or placeholder tasks need replacement. | L1/L2 handoff already has exact files, command, and residual risk. | Scope, inputs, mutation boundary, reuse, validation, rollback, review, and handoff. | Forcing JSON/internal schemas into ordinary Markdown plans. | L3 | Agent-executable node contract and visible plan shape. |
| `references/planning-evidence-patterns.md` | Closing graph validity, new-hypothesis, parallelization, rollback, or plan-execution consistency. | Only task field shape is needed. | Repository context, node/edge list, topological proof, collision scan, verification gates, rollback, and final diff comparison. | Green validation treated as closure without graph and diff freshness. | L4 | Planning evidence map and closure rules. |
