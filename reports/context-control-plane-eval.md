# Context Control Plane Eval

- status: `partial`
- fixture_status: `pass`
- overhead_status: `partial`
- release_status: `partial`
- structural_fixture_status: `pass`
- cases: `8/8`
- raw_leak_count: `0`
- live_codex_executed: `False`

## Context Control Overhead

- status: `partial`
- input_token_overhead_pct: `228.79`
- output_token_overhead_pct: `35.56`
- turn_overhead: `None`
- command_delta: `19.91`
- pass_rate_delta: `0.0417`
- live_pass_rate: `{"pass_rate_delta": 0.0417, "status": "collected"}`
- token_overhead: `{"input_pct": 228.79, "output_pct": 35.56, "status": "collected"}`
- turn_overhead_detail: `{"status": "not_collected", "turn_overhead": null}`
- runtime_telemetry: `{"command_delta": 19.91, "live_codex_executed": false, "source": "reports/codex-live-benchmark-summary.json", "status": "existing_report"}`
- overhead_policy_verdict: `partial: structural fixtures pass and live overhead is collected, but high token overhead remains an ungoverned P2 risk; do not claim Context Control Plane quality or cost improvement`
- evidence_boundary: `Evidence separates structural fixture pass, live pass-rate, live runtime telemetry, token overhead, and turn overhead. High overhead without pass-rate improvement is not success.`

## Cases

| Case | Status | Budget | Selected refs | Skipped refs |
| --- | --- | --- | --- | --- |
| routing-budget-minimal | `pass` | `minimal` | `2` | `1` |
| routing-budget-broad-audit | `pass` | `staged-plan` | `7` | `2` |
| reference-signal-density | `pass` | `staged-plan` | `5` | `3` |
| jit-context-pack-runtime-budget | `pass` | `staged-plan` | `4` | `2` |
| tool-output-boundary-large-output | `pass` | `single-stage` | `4` | `2` |
| compaction-snapshot-v2 | `pass` | `single-stage` | `6` | `2` |
| branch-route-repair-summary | `pass` | `staged-plan` | `4` | `1` |
| negative-small-typo-no-context-control | `pass` | `minimal` | `1` | `0` |
