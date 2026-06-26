# Graph Memory Trajectory Validator Map

Use this reference when validation scope depends on repository graph edges, project memory signals, or execution trajectory order. Keep it out of `SKILL.md` unless the broker needs concrete coupling fields.

## Coupling Inputs

| Input | What It Can Prove | What It Cannot Prove | Validator Effect |
| --- | --- | --- | --- |
| Repository graph direct test edge | A changed path has an adjacent test, eval, build, or install check candidate. | Behavior correctness without running the mapped command. | Prefer narrow or module validation when risk is local and graph freshness is current. |
| Repository graph missing test edge | No direct validator was found in the searched scope. | That no dynamic, generated, or owner-specific test exists. | Escalate to broader validation or record missing-edge residual risk. |
| Source/generated graph edge | A generated artifact maps to a source file and generator command. | Generated freshness unless the generator ran after final source edit. | Require source validator plus generator/build command. |
| Project memory prior validation gap | A prior run, fragile file, or repeated failure affects confidence. | Current behavior or source truth by itself. | Increase depth or require direct source and graph confirmation. |
| Execution trajectory later edit | A command result predates a material edit. | That the old command still covers the final diff. | Mark stale and rerun or downgrade closure. |
| Review repair trajectory | A repair happened after review approval. | That repaired files were reviewed. | Require targeted re-review plus mapped validator. |

## Decision Rules

1. Treat graph and memory as validator selectors, not pass evidence.
2. Let trajectory order override older green results when final edits changed covered paths or inputs.
3. Choose the cheapest validator that covers the accepted graph/memory/trajectory risk; escalate when any accepted signal crosses module, generated, install, package, release, security, or hook runtime boundaries.
4. If graph, memory, and trajectory disagree, preserve the disagreement in `graph_memory_trajectory_coupling` and close as partial, stale, not-verified, or residual risk until reconciled.
5. If a memory signal is rejected as stale, name the direct source or graph evidence that replaced it.

## Coupling Output Fields

- `graph_edges`: direct, indirect, missing, generated, report, package, install, or unknown.
- `memory_signals`: accepted, rejected, stale, privacy-excluded, or not-verified.
- `trajectory_order`: after_final_edit, before_final_edit, repair_without_rereview, repeated_failure, or unknown.
- `validator_effect`: keep_narrow, escalate_module, escalate_full, rerun_stale, record_residual_risk, or block_closure.
- `evidence_limit`: exact claim the selected command can and cannot support.

## Examples

| Scenario | Broker Decision |
| --- | --- |
| Foundation capability `SKILL.md` and its references changed; graph finds no direct unit test. | Run capability validators, content/link/audit checks, professionalism eval, then full AGENTS suite if route behavior changed. |
| Report file changed after eval output, but source did not change. | Require source generator command or mark report freshness unsupported. |
| Memory marks a file fragile and trajectory shows prior failed command. | Re-read source, inspect graph/test edge, rerun the failed scope or explain owner/deferred risk. |
