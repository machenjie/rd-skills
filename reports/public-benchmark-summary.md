# Public Benchmark Summary

This generated summary reports local deterministic ChangeForge evidence. Skill efficacy, activation precision, and executor adapter fixtures are structural/local evidence, not live runtime telemetry, live pass-rate, or empirical before/after agent-performance proof. It does not claim external popularity, marketplace availability, or market adoption.

## Repository

- Repository: `machenjie/rd-skills`
- Version: `0.1.0`
- Source commit: `provided by release artifact / CI metadata`

## Status Counts

- `pass`: 18
- `partial`: 3
- `fail`: 0
- `unknown`: 0
- `not_collected`: 4

## Evidence Levels

| Evidence | Status | Meaning |
| --- | --- | --- |
| live pass-rate | `not_collected` | Measured real-task success rate. |
| live runtime telemetry sample | `not_collected` | Sanitized bounded facts from an actual hook runtime execution. |
| local_codex_cli_live_benchmark | `pass` | Opt-in local Codex CLI benchmark run with sanitized bounded artifacts. |
| promoted golden case | `pass` | Human-reviewed case admitted to regression coverage. |
| runtime telemetry fixture sample | `pass` | Deterministic executor-adapter fixture-derived bounded facts; not live runtime telemetry. |
| structural fixture | `pass` | Local deterministic structure sample passed; not evidence of live task success. |
| token overhead | `not_collected` | Measured additional token cost. |
| turn overhead | `not_collected` | Measured additional turn cost. |

## Evidence

| Area | Status | Evidence Level | Source | Detail | Refresh Command |
| --- | --- | --- | --- | --- | --- |
| Registry source counts | `pass` | structural fixture | src/registry/*.yaml | {"domain_extensions": 7, "foundation_capabilities": 127, "professional_skills": 21} | `python3 scripts/validate-registry.py` |
| Profile build reproducibility | `pass` | structural fixture | dist/universal/skills/*/.changeforge-build-manifest.json | {"dev": {"detail": "dev top-level count is 155", "manifest": "dist/universal/skills/dev/.changeforge-build-manifest.json", "status": "pass"}, "full": {"detail": "full top-level count is 28", "manifest": "dist/universal/skills/full/.changeforge-build-manifest.json", "status": "pass"}, "recommended": {"detail": "recommended top-level count is 21", "manifest": "dist/universal/skills/recommended/.changeforge-build-manifest.json", "status": "pass"}} | `python3 scripts/build.py --profile recommended && python3 scripts/build.py --profile full && python3 scripts/build.py --profile dev` |
| Routing coverage | `pass` | structural fixture | reports/professionalism-release-readiness.json | {"cases_checked": 118, "cases_without_forbidden": 0, "hidden_risks_checked": 91, "hidden_risks_needing_manual_review": 0, "hidden_risks_strongly_covered": 87, "l1_anti_over_routing_count": 9} | `python3 scripts/validate-professional-routing-coverage.py` |
| Professional skill coverage | `partial` | structural fixture | reports/professionalism-release-readiness.json | {"count": 21, "statuses": {"sample-grade": 21}} | `python3 scripts/eval-skill-professionalism.py` |
| Foundation capability coverage | `partial` | structural fixture | reports/professionalism-release-readiness.json | {"count": 40, "statuses": {"acceptable": 29, "needs-review": 10, "sample-grade": 1}} | `python3 scripts/eval-skill-professionalism.py --coverage-matrix` |
| Professional benchmarks | `pass` | structural fixture | reports/professionalism-release-readiness.json | {"cases_checked": 30, "comparison_cases_checked": 30, "empty_baseline_cases": 0, "quality_failures": 0} | `python3 scripts/eval-professional-benchmarks.py` |
| Professionalism regression | `pass` | structural fixture | reports/professionalism-release-readiness.json | strict_regression_status: pass | `python3 scripts/validate-professionalism-regression.py --strict` |
| Promoted agent samples | `pass` | promoted golden case | reports/professionalism-release-readiness.json | promoted_agent_samples_strict_status: pass | `python3 scripts/eval-professional-agent-samples.py --promoted-only --strict` |
| Skill efficacy structural fixtures | `pass` | structural fixture | evals/skill-efficacy and scripts/validate-skill-efficacy-benchmarks.py | {"candidate_fixtures_ignored": 0, "evidence_boundary": "structural/local fixtures only; no empirical before/after agent performance", "evidence_levels": {"live pass-rate": "not_collected", "live runtime telemetry sample": "not_collected", "promoted golden case": "not_collected", "runtime telemetry fixture sample": "not_collected", "structural fixture": 3, "token overhead": "not_collected", "turn overhead": "not_collected"}, "fixtures": 3, "live_pass_rate": "not_collected", "token_overhead": "not_collected", "turn_overhead": "not_collected", "verdicts": {"structural_pass": 3}} | `python3 scripts/validate-skill-efficacy-benchmarks.py` |
| Runtime governance structural fixtures | `pass` | structural fixture | evals/executor-adapters, evals/repository-intelligence, evals/project-memory, evals/validation-broker, evals/trajectory | {"candidate_fixtures_ignored": 0, "evidence_boundary": "structural/local fixtures only; no live empirical pass-rate or runtime overhead evidence", "evidence_levels": {"live pass-rate": "not_collected", "live runtime telemetry sample": "not_collected", "promoted golden case": "not_collected", "runtime telemetry fixture sample": "not_collected", "structural fixture": 15, "token overhead": "not_collected", "turn overhead": "not_collected"}, "suites": {"executor-adapters": {"candidate_fixtures_ignored": 0, "fixtures": 3, "required_capability": "executor-adapter-protocol", "required_capability_hits": 3}, "project-memory": {"candidate_fixtures_ignored": 0, "fixtures": 3, "required_capability": "project-memory-governance", "required_capability_hits": 3}, "repository-intelligence": {"candidate_fixtures_ignored": 0, "fixtures": 3, "required_capability": "repository-graph-analysis", "required_capability_hits": 3}, "trajectory": {"candidate_fixtures_ignored": 0, "fixtures": 3, "required_capability": "execution-trajectory-analysis", "required_capability_hits": 3}, "validation-broker": {"candidate_fixtures_ignored": 0, "fixtures": 3, "required_capability": "validation-broker", "required_capability_hits": 3}}, "total_fixtures": 15} | `python3 scripts/validate-professional-routing-coverage.py` |
| Executor adapter structural fixtures | `pass` | structural fixture | evals/executor-adapter and reports/executor-adapter-eval.json | {"case_count": 20, "coverage_targets": ["closure_verdict", "command_risk", "degradation", "event_recognition", "path_normalization", "permission_decision", "privacy_redaction", "tool_category", "validation_freshness_after_edits", "validation_outcome"], "evidence_boundary": "deterministic local fixtures only; no live runtime pass-rate or overhead measurement", "failed": 0, "live_pass_rate": "not_collected", "passed": 20, "pressure_cases": ["absolute_user_path", "claude_post_tool_failure", "codex_destructive_permission_request", "copilot_unsupported_pre_tool", "edit_after_validation", "failed_validation", "full_command_output_field", "large_path_list_cap", "ready_after_rereview", "ready_closure", "repair_without_rereview", "required_unsupported_check_degraded_ready", "review_finding_without_repair", "secret_like_payload_field", "targeted_test_reported_as_full", "unknown_event", "unsupported_runtime_event", "validation_pass_then_file_changed"], "token_overhead": "not_collected", "turn_overhead": "not_collected"} | `python3 scripts/eval-executor-adapters.py` |
| Activation precision benchmark | `pass` | structural fixture | evals/activation and reports/activation-precision.json | {"error_count": 0, "generated_by": "scripts/eval-activation-precision.py", "summary": {"capability_precision": 1.0, "capability_recall": 1.0, "case_count": 24, "failed": 0, "language_fn_rate": 0.0, "language_fp_rate": 0.0, "metric_definitions": {"language_fn_rate": "Share of cases with at least one missing expected language surface.", "language_fp_rate": "Share of cases with at least one unexpected language surface.", "overroute_rate": "Share of cases with any unexpected exact-set value or any forbidden *_not_contains value.", "precision_recall": "Set precision/recall aggregate true positives, false positives, and false negatives across exact-set cases.", "risk_surface_fn_rate": "Share of cases with at least one missing expected risk surface.", "risk_surface_fp_rate": "Share of cases with at least one unexpected risk surface."}, "overroute_rate": 0.0, "passed": 24, "reference_precision": 1.0, "reference_recall": 1.0, "risk_surface_fn_rate": 0.0, "risk_surface_fp_rate": 0.0, "skill_precision": 1.0, "skill_recall": 1.0, "stage_accuracy": 1.0}} | `python3 scripts/eval-activation-precision.py --mode built --runtime-root dist/codex/project/.codex/hooks` |
| Runtime telemetry fixture sample | `pass` | runtime telemetry fixture sample | reports/runtime-telemetry-sample.json | {"degraded_event_count": 4, "event_count": 20, "evidence_level": "runtime telemetry fixture sample", "privacy_redaction_count": 9, "runtime": "mixed-fixture-runtime-sample", "sample_kind": "runtime_telemetry_fixture_sample", "source": "deterministic-fixture-bounded-facts", "token_overhead": "not_collected", "turn_overhead": "not_collected"} | `python3 scripts/eval-executor-adapters.py` |
| Live runtime telemetry sample | `not_collected` | live runtime telemetry sample | reports/live-runtime-telemetry-sample.json | reports/live-runtime-telemetry-sample.json missing or invalid | `manual live runtime collection with sanitized bounded facts` |
| Executor adapter live pass-rate | `not_collected` | live pass-rate | reports/executor-adapter-eval.json | deterministic local fixtures do not measure real-task success rate | `python3 scripts/eval-executor-adapters.py` |
| Executor adapter token overhead | `not_collected` | token overhead | reports/executor-adapter-eval.json | deterministic local fixture run does not measure token overhead | `python3 scripts/eval-executor-adapters.py` |
| Executor adapter turn overhead | `not_collected` | turn overhead | reports/executor-adapter-eval.json | deterministic local fixture run does not measure turn overhead | `python3 scripts/eval-executor-adapters.py` |
| Codex CLI live pass-rate benchmark | `pass` | local_codex_cli_live_benchmark | reports/codex-live-benchmark-summary.json | mode=ablation; scope=multi_case_ablation_3_run; ready=True; cases=11/11; results=99/99; runs=baseline_clean:3, skills_only_clean:3, skills_with_hooks_clean:3; variants=baseline_clean, skills_only_clean, skills_with_hooks_clean; skills_with_hooks_clean.pass_rate=1.0; effect=neutral/neutral; token_overhead=input +234.06%, output +45.63%; command_delta=22.61; limitations=Local Codex CLI runs depend on the installed CLI, configured model, account access, and local machine state.; Parsed telemetry excludes raw command bodies and assistant/user message content.; Pass rates include only benchmark_eligible assertion-backed results; telemetry-only cases are counted separately. | `python3 scripts/validate-codex-live-benchmark-reports.py --summary reports/codex-live-benchmark-summary.json` |
| Codex CLI live capability coverage | `pass` | local_codex_cli_live_benchmark | reports/codex-live-benchmark-summary.json | mode=ablation; scope=multi_case_ablation_3_run; ready=True; cases=11/11; results=99/99; runs=baseline_clean:3, skills_only_clean:3, skills_with_hooks_clean:3; variants=baseline_clean, skills_only_clean, skills_with_hooks_clean; skills_with_hooks_clean.pass_rate=1.0; effect=neutral/neutral; token_overhead=input +234.06%, output +45.63%; command_delta=22.61; limitations=Local Codex CLI runs depend on the installed CLI, configured model, account access, and local machine state.; Parsed telemetry excludes raw command bodies and assistant/user message content.; Pass rates include only benchmark_eligible assertion-backed results; telemetry-only cases are counted separately. | `python3 scripts/validate-codex-live-benchmark-reports.py --summary reports/codex-live-benchmark-summary.json` |
| Example coverage | `pass` | structural fixture | examples/ and scripts/validate-examples.py | showcase examples validate | `python3 scripts/validate-examples.py` |
| Productization assets | `pass` | structural fixture | docs/productization assets, schemas, and scripts | required productization assets present | `python3 scripts/validate-productization-assets.py` |
| Marketplace index validation | `pass` | structural fixture | scripts/validate-marketplace-index.py | recommended, full, and dev marketplace indexes validate | `python3 scripts/validate-marketplace-index.py --profile recommended && python3 scripts/validate-marketplace-index.py --profile full && python3 scripts/validate-marketplace-index.py --profile dev` |
| Open-source readiness | `partial` | structural fixture | config/open-source-release.yaml, docs/LICENSE_DECISION.md, docs/OPEN_SOURCE_READINESS.md, pyproject.toml, CONTRIBUTING.md, SECURITY.md, LICENSE | config_present=True, selected_license_non_null=False, selected_license_allowed=True, license_file=False, pyproject_license_not_proprietary=False, contribution_licensing_confirmed=False, contribution_licensing_evidence=False, security_contact_confirmed=False, security_contact_evidence=False, dist_release_policy_explicit=True, dist_release_policy_valid=True | `python3 scripts/validate-open-source-readiness.py` |
| Hook safety | `pass` | structural fixture | reports/hook-validation.json | {"error_count": 0, "generated_by": "scripts/validate-hooks.py", "summary": {"claude_templates": 2, "codex_templates": 2, "copilot_templates": 2, "error_count": 0, "hook_runtime_root": "src/hook-runtime", "required_hook_scripts": 29, "required_hook_scripts_present": true}} | `python3 scripts/validate-hooks.py --json-out reports/hook-validation.json --out reports/hook-validation.md` |
| Installation validation | `pass` | structural fixture | reports/installation-validation.json | {"error_count": 0, "generated_by": "scripts/validate-installation.py", "summary": {"built_skill_directories": 2040, "dist_exists": true, "error_count": 0, "required_hook_runtime_files": 396, "runtime_roots": 10, "zip_count": 204}} | `python3 scripts/validate-installation.py --json-out reports/installation-validation.json --out reports/installation-validation.md` |

## Quality Improvement

- baseline pass rate: `1.0`
- skills_only pass rate: `1.0`
- skills_with_hooks pass rate: `1.0`
- skills_only vs baseline delta: `0.0`
- skills_with_hooks vs skills_only delta: `0.0`
- skills_with_hooks vs baseline delta: `0.0`
- no_quality_regression: `True`
- large_quality_improvement_claim: `False`

## Capability Coverage

| Capability | Linked Cases | Evidence | Status |
| --- | --- | --- | --- |
| professional_injection_activation | injection/professional-route-manifest-activation | run/pass | `pass` |
| staged_injection_precision | injection/stage-specific-reference-loading | run/pass | `pass` |
| repository_graph_context_pack | repo-intel/caller-callee-test-impact-map | run/pass | `pass` |
| project_memory_governance | memory/repeated-failure-fragile-file | run/pass | `pass` |
| validation_broker_freshness | process/full-pdd-ddd-sdd-tdd-review-repair, validation/stale-validation-after-edit | run/pass | `pass` |
| pdd_ddd_sdd_tdd_review_flow | process/full-pdd-ddd-sdd-tdd-review-repair | run/pass | `pass` |
| minimal_correct_implementation_ladder | devex/minimal-correct-native-reuse | run/pass | `pass` |
| pua_or_pressure_resistance | pressure/professional-boundary-under-user-pressure | run/pass | `pass` |
| execution_trajectory_review | process/full-pdd-ddd-sdd-tdd-review-repair, review/repair-rereview-required | run/pass | `pass` |
| professional_logging_decision | logging/redacted-structured-log-design | run/pass | `pass` |
| context_compaction_retention | compact/context-retention-after-compaction | run/pass | `pass` |

## Context Compaction Retention

- run_status: `run`
- pre_compact_snapshot_count: `3`
- post_compact_reinject_count: `3`
- session_compact_reinject_count: `3`
- compact_runtime_evidence_count: `3`
- restored_required_context_fields: `['active_skill_context', 'changed_paths', 'current_stage', 'ddd_invariants', 'last_material_edit_index', 'last_validation_command_index', 'memory_references', 'pdd_summary', 'read_paths', 'repair_events', 'repo_graph_references', 'required_quality_gates', 'rereview_events', 'residual_risk', 'review_findings', 'route_id', 'sdd_decisions', 'selected_capabilities', 'selected_skills', 'tdd_validation_plan', 'validation_freshness', 'validation_results']`
- missing_required_context_fields: `[]`
- redacted_required_context_fields: `[]`
- context_unusable_fields: `[]`
- privacy_redaction_status: `pass`
- context_usable_status: `pass`
- context_retention_status: `pass`
- compact_after_repair_continuation_status: `pass`
- candidate_context_status: `pass`

## Process Compliance

- process_trace_count: `99`
- pdd_present_rate: `1.0`
- ddd_present_rate: `1.0`
- sdd_present_rate: `1.0`
- tdd_present_rate: `1.0`
- review_present_rate: `1.0`
- repair_present_rate: `0.3131`
- rereview_present_rate: `0.303`
- required_field_fallback_rate: `0.0`

## Case-Level Result

- improved_cases: none
- no_improvement_cases: compact/context-retention-after-compaction, devex/minimal-correct-native-reuse, injection/professional-route-manifest-activation, injection/stage-specific-reference-loading, logging/redacted-structured-log-design, memory/repeated-failure-fragile-file, pressure/professional-boundary-under-user-pressure, process/full-pdd-ddd-sdd-tdd-review-repair, repo-intel/caller-callee-test-impact-map, review/repair-rereview-required, validation/stale-validation-after-edit
- regressed_cases: none
- reliability_no_improvement_visible: `True`
- known_unresolved_reliability_cases: reliability/redis-cache-stampede-protection

## Cost Telemetry

- cost is telemetry only in this phase
- quality-first benchmark does not gate on cost
- no cost reduction or efficiency improvement claim is made
- input_tokens: `not_collected`
- output_tokens: `not_collected`
- reasoning_output_tokens: `not_collected`

## Known Unknowns / Not Collected

- Live runtime telemetry sample
- Live pass-rate
- Token overhead
- Turn overhead

## Refresh Commands

```bash
python3 scripts/eval-routing.py
python3 scripts/eval-skill-professionalism.py
python3 scripts/eval-skill-professionalism.py --coverage-matrix
python3 scripts/eval-professional-benchmarks.py
python3 scripts/validate-skill-efficacy-benchmarks.py
python3 scripts/eval-executor-adapters.py
python3 scripts/eval-activation-precision.py --mode built --runtime-root dist/codex/project/.codex/hooks
python3 scripts/run-codex-live-benchmarks.py --list
python3 scripts/run-codex-live-benchmarks.py --benchmark-mode ablation --auth-policy borrow-current --benchmark security/ssrf-url-allowlist --dry-run --out /tmp/changeforge-codex-live-ablation-dry-run
python3 scripts/validate-codex-live-benchmark-reports.py --run-dir /tmp/changeforge-codex-live-ablation-dry-run
python3 scripts/validate-report-consistency.py
python3 scripts/validate-professionalism-regression.py --strict
python3 scripts/validate-professional-routing-coverage.py
python3 scripts/validate-hooks.py --json-out reports/hook-validation.json --out reports/hook-validation.md
python3 scripts/build.py --profile recommended
python3 scripts/build.py --profile full
python3 scripts/build.py --profile dev
python3 scripts/validate-runtime-reference-links.py
python3 scripts/validate-installation.py --json-out reports/installation-validation.json --out reports/installation-validation.md
python3 scripts/validate-marketplace-index.py --profile recommended
python3 scripts/validate-marketplace-index.py --profile full
python3 scripts/validate-marketplace-index.py --profile dev
python3 scripts/generate-public-benchmark-summary.py --out reports/public-benchmark-summary.md --json-out reports/public-benchmark-summary.json
```
