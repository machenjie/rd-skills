# Context Control Plane Evals

These fixtures make `context-control-plane` measurable without running live
Codex. They validate structural route selection, context budget shape,
selected/skipped reference counts, JIT context-pack boundaries, tool-output
redaction, compaction snapshot v2 continuity, branch route-repair summaries,
and overhead evidence policy.

Each YAML fixture states:

- input scenario and optional router/runtime resolver source;
- expected selected skills and capabilities;
- context budget mode and selected/skipped reference counts;
- skipped-reference reasons;
- safety and closure result;
- forbidden raw fields that must not appear in artifact, state, or telemetry
  records.

The evaluator emits `reports/context-control-plane-eval.json` and
`reports/context-control-plane-eval.md`.

```bash
python3 scripts/eval-context-control-plane.py
```

This suite is structural. It may read
`reports/codex-live-benchmark-summary.json` only as an existing bounded summary
to compute the conservative `context_control_overhead` row. It does not run live
Codex benchmarks; those remain explicit opt-in commands.
