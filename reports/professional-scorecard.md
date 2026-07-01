# Professional Scorecard

This scorecard is generated from local registry, build, and report evidence. Missing machine-readable evidence is shown as `not_collected` or `unknown`, not as pass.

## Summary

- `pass`: 17
- `partial`: 5
- `fail`: 0
- `unknown`: 0
- `not_collected`: 4

## Evidence Levels

| Evidence | Status | Meaning |
| --- | --- | --- |
| structural fixture | `pass` | Local deterministic structure sample passed; not evidence of live task success. |
| runtime telemetry fixture sample | `pass` | Deterministic executor-adapter fixture-derived bounded facts; not live runtime telemetry. |
| live runtime telemetry sample | `not_collected` | Sanitized bounded facts from an actual hook runtime execution. |
| promoted golden case | `pass` | Human-reviewed case admitted to regression coverage. |
| live pass-rate | `not_collected` | Measured real-task success rate. |
| token overhead | `not_collected` | Measured additional token cost. |
| turn overhead | `not_collected` | Measured additional turn cost. |
| local_codex_cli_live_benchmark | `partial` | Opt-in local Codex CLI benchmark run with sanitized bounded artifacts. |

## Dimensions

| Dimension | Status | Source | Verification |
| --- | --- | --- | --- |
| Registry source counts | `pass` | src/registry/*.yaml | `python3 scripts/validate-registry.py` |
| Profile build reproducibility | `pass` | dist/universal/skills/*/.changeforge-build-manifest.json | `python3 scripts/build.py --profile recommended && python3 scripts/build.py --profile full && python3 scripts/build.py --profile dev` |
| Routing coverage | `pass` | reports/professionalism-release-readiness.json | `python3 scripts/validate-professional-routing-coverage.py` |
| Professional skill coverage | `partial` | reports/professionalism-release-readiness.json | `python3 scripts/eval-skill-professionalism.py` |
| Foundation capability coverage | `partial` | reports/professionalism-release-readiness.json | `python3 scripts/eval-skill-professionalism.py --coverage-matrix` |
| Professional benchmarks | `pass` | reports/professionalism-release-readiness.json | `python3 scripts/eval-professional-benchmarks.py` |
| Professionalism regression | `pass` | reports/professionalism-release-readiness.json | `python3 scripts/validate-professionalism-regression.py --strict` |
| Promoted agent samples | `pass` | reports/professionalism-release-readiness.json | `python3 scripts/eval-professional-agent-samples.py --promoted-only --strict` |
| Skill efficacy structural fixtures | `pass` | evals/skill-efficacy and scripts/validate-skill-efficacy-benchmarks.py | `python3 scripts/validate-skill-efficacy-benchmarks.py` |
| Runtime governance structural fixtures | `pass` | evals/executor-adapters, evals/repository-intelligence, evals/project-memory, evals/validation-broker, evals/trajectory | `python3 scripts/validate-professional-routing-coverage.py` |
| context_control_overhead | `partial` | reports/context-control-plane-eval.json | `python3 scripts/eval-context-control-plane.py` |
| Executor adapter structural fixtures | `pass` | evals/executor-adapter and reports/executor-adapter-eval.json | `python3 scripts/eval-executor-adapters.py` |
| Activation precision benchmark | `pass` | evals/activation and reports/activation-precision.json | `python3 scripts/eval-activation-precision.py --mode built --runtime-root dist/codex/project/.codex/hooks` |
| Runtime telemetry fixture sample | `pass` | reports/runtime-telemetry-sample.json | `python3 scripts/eval-executor-adapters.py` |
| Live runtime telemetry sample | `not_collected` | reports/live-runtime-telemetry-sample.json | `manual live runtime collection with sanitized bounded facts` |
| Executor adapter live pass-rate | `not_collected` | reports/executor-adapter-eval.json | `python3 scripts/eval-executor-adapters.py` |
| Executor adapter token overhead | `not_collected` | reports/executor-adapter-eval.json | `python3 scripts/eval-executor-adapters.py` |
| Executor adapter turn overhead | `not_collected` | reports/executor-adapter-eval.json | `python3 scripts/eval-executor-adapters.py` |
| Codex CLI live pass-rate benchmark | `pass` | reports/codex-live-benchmark-summary.json | `python3 scripts/validate-codex-live-benchmark-reports.py --summary reports/codex-live-benchmark-summary.json` |
| Codex CLI live capability coverage | `partial` | reports/codex-live-benchmark-summary.json and evals/codex-live/capability-matrix.yaml | `python3 scripts/validate-codex-live-benchmark-reports.py --summary reports/codex-live-benchmark-summary.json` |
| Example coverage | `pass` | examples/ and scripts/validate-examples.py | `python3 scripts/validate-examples.py` |
| Productization assets | `pass` | docs/productization assets, schemas, and scripts | `python3 scripts/validate-productization-assets.py` |
| Marketplace index validation | `pass` | scripts/validate-marketplace-index.py | `python3 scripts/validate-marketplace-index.py --profile recommended && python3 scripts/validate-marketplace-index.py --profile full && python3 scripts/validate-marketplace-index.py --profile dev` |
| Open-source readiness | `partial` | config/open-source-release.yaml, docs/LICENSE_DECISION.md, docs/OPEN_SOURCE_READINESS.md, pyproject.toml, CONTRIBUTING.md, SECURITY.md, LICENSE | `python3 scripts/validate-open-source-readiness.py` |
| Hook safety | `pass` | reports/hook-validation.json | `python3 scripts/validate-hooks.py --json-out reports/hook-validation.json --out reports/hook-validation.md` |
| Installation validation | `pass` | reports/installation-validation.json | `python3 scripts/validate-installation.py --json-out reports/installation-validation.json --out reports/installation-validation.md` |

## Context Control Overhead

- eval_status: `partial`
- fixture_status: `pass`
- structural_fixture_status: `pass`
- overhead_status: `partial`
- release_status: `partial`
- status: `partial`
- quality_improvement_claim_allowed: `False`
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

## Codex CLI Live Benchmark

### Codex CLI live pass-rate benchmark
- run_id: `ablation-core-auth-borrowed-20260701-013224`
- effect_verdict: `positive`
- evidence_status: `pass`
- benchmark_passed_result_count: `139`
- benchmark_eligible_result_count: `144`
- skills_with_hooks_clean.pass_rate: `0.9792`

### Codex CLI live capability coverage
- run_id: `ablation-core-auth-borrowed-20260701-013224`
- effect_verdict: `positive`
- evidence_status: `partial`
- benchmark_passed_result_count: `139`
- benchmark_eligible_result_count: `144`
- skills_with_hooks_clean.pass_rate: `0.9792`


## Profile Counts

- `recommended`: `pass` - recommended top-level count is 21
- `full`: `pass` - full top-level count is 28
- `dev`: `pass` - dev top-level count is 164

## Repair Hints

- Professional skill coverage: Repair weak professional skill sections without keyword stuffing.
- Foundation capability coverage: Improve selected capability evidence contracts and references.
- context_control_overhead: Repair context-control fixtures or collect lower-overhead live evidence before claiming context-control quality improvement.
- Live runtime telemetry sample: Collect a real hook-runtime sample before changing this status from not_collected; do not use executor adapter fixtures for this dimension.
- Executor adapter live pass-rate: Collect a real measured run before changing this status from not_collected.
- Executor adapter token overhead: Collect a real measured run before changing this status from not_collected.
- Executor adapter turn overhead: Collect a real measured run before changing this status from not_collected.
- Codex CLI live capability coverage: skills_only_clean: strict process trace validation failed; skills_with_hooks_clean: strict process trace validation failed; register every core capability linked case; run linked cases in baseline_clean, skills_only_clean, and skills_with_hooks_clean; keep linked cases assertion-backed and publishable_for_strict=true; collect explicit process-trace evidence instead of inferred/fallback fields; rerun reports after capability cases pass
- Open-source readiness: Owner must select an OSI license, update package metadata, confirm contribution licensing, and configure private vulnerability reporting before open-source publication.
