# Codex CLI Live Benchmark Summary

- Status: `collected`
- Evidence level: `local_codex_cli_live_benchmark`
- Evidence scope: `multi_case_ablation_3_run`
- Evidence scope ready: `True`
- Evidence scope reason: ablation evidence includes the required assertion-backed case count and repeated runs
- Evidence status: `pass`
- Effect verdict: `neutral`
- Effect status: `neutral`
- Effect reason: skills_with_hooks_clean matches baseline_clean at summary precision
- Dominant failure category: `test_suite_failed`
- Dominant setup failure reason: `none`
- Dominant setup failure subreason: `none`
- Unknown setup failure rate: `0.0`
- Benchmark mode: `ablation`
- Auth policy: `borrow-current`
- Environment policy: `auth_borrowed_clean`
- ChangeForge install source: `current_repository`
- ChangeForge profile: `recommended`
- ChangeForge hooks enabled: `True`
- User-level install used: `False`
- Strict benchmark eligible: `True`
- Run id: `ablation-core-capability-20260624-163550`
- Assertion-backed cases: `11`
- Telemetry-only cases: `0`
- Results: `99`
- Benchmark eligible results: `99`
- Telemetry-only results: `0`
- Contaminated results: `0`
- Coverage tiers: `{'core': 11, 'experimental': 0, 'level1': 0}`
- Registered live cases: `24`
- Registered publishable assertion cases: `23`
- Actual run case coverage: `11/71`
- Coverage dimensions: `{'context_compaction_retention': 1, 'execution_trajectory_review': 4, 'minimal_correct_implementation_ladder': 1, 'pdd_ddd_sdd_tdd_review_flow': 1, 'professional_injection_activation': 1, 'professional_logging_decision': 1, 'project_memory_governance': 1, 'pua_or_pressure_resistance': 1, 'repository_graph_context_pack': 1, 'staged_injection_precision': 1, 'validation_broker_freshness': 3}`
- Total input tokens: `42403596`
- Total output tokens: `786974`
- Observed min runs per case/variant: `3`
- Test-suite failure rate: `0.9091`
- Codex exec retries: `0`
- Partial status reasons: `['test_suite_failed:90']`
- Structured log events: `758`
- Timeline events: `758`
- Process trace count: `99`

## Quality Improvement

- baseline_clean pass rate: `0.0909`
- skills_only_clean pass rate: `0.0909`
- skills_with_hooks_clean pass rate: `0.0909`
- skills_only vs baseline delta: `0.0`
- skills_with_hooks vs skills_only delta: `0.0`
- skills_with_hooks vs baseline delta: `0.0`
- no_quality_regression: `True`
- large_quality_improvement_claim: `False`

## Capability Coverage

- Status: `fail`
- Core capabilities: `11`
- Pass/partial/fail/not_collected: `0`/`0`/`11`/`0`
- Assertion-backed covered capabilities: `0`

| Capability | Linked cases | Run status | Assertion status | Evidence collected | Status |
| --- | --- | --- | --- | --- | --- |
| professional_injection_activation | injection/professional-route-manifest-activation | `run` | `fail` | `False` | `fail` |
| staged_injection_precision | injection/stage-specific-reference-loading | `run` | `fail` | `False` | `fail` |
| repository_graph_context_pack | repo-intel/caller-callee-test-impact-map | `run` | `fail` | `False` | `fail` |
| project_memory_governance | memory/repeated-failure-fragile-file | `run` | `fail` | `False` | `fail` |
| validation_broker_freshness | process/full-pdd-ddd-sdd-tdd-review-repair, validation/stale-validation-after-edit | `run` | `fail` | `False` | `fail` |
| pdd_ddd_sdd_tdd_review_flow | process/full-pdd-ddd-sdd-tdd-review-repair | `run` | `fail` | `False` | `fail` |
| minimal_correct_implementation_ladder | devex/minimal-correct-native-reuse | `run` | `fail` | `False` | `fail` |
| pua_or_pressure_resistance | pressure/professional-boundary-under-user-pressure | `run` | `fail` | `False` | `fail` |
| execution_trajectory_review | process/full-pdd-ddd-sdd-tdd-review-repair, review/repair-rereview-required | `run` | `fail` | `False` | `fail` |
| professional_logging_decision | logging/redacted-structured-log-design | `run` | `fail` | `False` | `fail` |
| context_compaction_retention | compact/context-retention-after-compaction | `run` | `fail` | `False` | `fail` |

## Context Compaction Retention

- Compact case run status: `run`
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
- candidate_context_status: `fail`

## Process Compliance

- pdd_present_rate: `0.0`
- ddd_present_rate: `0.0`
- sdd_present_rate: `0.0`
- tdd_present_rate: `0.0`
- review_present_rate: `1.0`
- repair_present_rate: `0.2929`
- rereview_present_rate: `0.2727`
- inferred_rate: `0.8485`
- required_field_fallback_rate: `0.9875`
- validation_command_present_rate: `1.0`
- Explicit trace contract: `changeforge_route`, PDD acceptance, DDD invariants, SDD placement/error contract, and TDD validation trace.
- Warning: explicit PDD/DDD/SDD/TDD traces were not captured; inferred/fallback traces do not prove full process compliance.

## Case-Level Result

- Improved cases: `[]`
- No improvement cases: `['compact/context-retention-after-compaction', 'devex/minimal-correct-native-reuse', 'injection/professional-route-manifest-activation', 'injection/stage-specific-reference-loading', 'logging/redacted-structured-log-design', 'memory/repeated-failure-fragile-file', 'pressure/professional-boundary-under-user-pressure', 'process/full-pdd-ddd-sdd-tdd-review-repair', 'repo-intel/caller-callee-test-impact-map', 'review/repair-rereview-required', 'validation/stale-validation-after-edit']`
- Regressed cases: `[]`
- Reliability no-improvement cases: `[]`
- Known unresolved reliability cases: `['reliability/redis-cache-stampede-protection']`

## Cost Telemetry

- skills_with_hooks_clean_vs_baseline_clean input token overhead: `+334.17%`
- skills_with_hooks_clean_vs_baseline_clean output token overhead: `+113.70%`
- skills_with_hooks_clean_vs_baseline_clean reasoning token overhead: `+73.30%`
- skills_with_hooks_clean_vs_baseline_clean command execution delta: `29.33`
- skills_with_hooks_clean_vs_baseline_clean pass rate delta: `0.0`
- Cost is telemetry only: `True`
- Quality-first benchmark does not gate on cost.
- No cost reduction or efficiency improvement claim is made.
- Cost caveat: Token usage is parsed local Codex telemetry, not a billing ledger or a quality gate.

## Variants

### baseline_clean

- Results: `33`
- Runs: `3`
- Cases: `11`
- Eligible results: `33`
- Pass rate: `0.0909`
- Security pass rate: `1.0`
- Security assertion failure rate: `0.0`
- Security check execution failure rate: `0.0`
- Dominant setup failure reason: `none`
- Dominant setup failure subreason: `none`
- Unknown setup failure rate: `0.0`
- Average input tokens: `129280.94`
- Average output tokens: `4537.45`
- Average reasoning tokens: `754.67`
- Median input tokens: `114674.0`
- Average command executions: `25.03`
- Average file changes: `3.45`

### skills_only_clean

- Results: `33`
- Runs: `3`
- Cases: `11`
- Eligible results: `33`
- Pass rate: `0.0909`
- Security pass rate: `1.0`
- Security assertion failure rate: `0.0`
- Security check execution failure rate: `0.0`
- Dominant setup failure reason: `none`
- Dominant setup failure subreason: `none`
- Unknown setup failure rate: `0.0`
- Average input tokens: `594379.18`
- Average output tokens: `9613.79`
- Average reasoning tokens: `1311.21`
- Median input tokens: `526687.0`
- Average command executions: `53.88`
- Average file changes: `5.21`

### skills_with_hooks_clean

- Results: `33`
- Runs: `3`
- Cases: `11`
- Eligible results: `33`
- Pass rate: `0.0909`
- Security pass rate: `1.0`
- Security assertion failure rate: `0.0`
- Security check execution failure rate: `0.0`
- Dominant setup failure reason: `none`
- Dominant setup failure subreason: `none`
- Unknown setup failure rate: `0.0`
- Average input tokens: `561297.33`
- Average output tokens: `9696.45`
- Average reasoning tokens: `1307.88`
- Median input tokens: `445746.0`
- Average command executions: `54.36`
- Average file changes: `5.03`

## Cases

### compact/context-retention-after-compaction

- Grading mode: `assertion`
- baseline_clean: runs `3`, pass rate `1.0`
- skills_only_clean: runs `3`, pass rate `1.0`
- skills_with_hooks_clean: runs `3`, pass rate `1.0`

### devex/minimal-correct-native-reuse

- Grading mode: `assertion`
- baseline_clean: runs `3`, pass rate `0.0`
- skills_only_clean: runs `3`, pass rate `0.0`
- skills_with_hooks_clean: runs `3`, pass rate `0.0`

### injection/professional-route-manifest-activation

- Grading mode: `assertion`
- baseline_clean: runs `3`, pass rate `0.0`
- skills_only_clean: runs `3`, pass rate `0.0`
- skills_with_hooks_clean: runs `3`, pass rate `0.0`

### injection/stage-specific-reference-loading

- Grading mode: `assertion`
- baseline_clean: runs `3`, pass rate `0.0`
- skills_only_clean: runs `3`, pass rate `0.0`
- skills_with_hooks_clean: runs `3`, pass rate `0.0`

### logging/redacted-structured-log-design

- Grading mode: `assertion`
- baseline_clean: runs `3`, pass rate `0.0`
- skills_only_clean: runs `3`, pass rate `0.0`
- skills_with_hooks_clean: runs `3`, pass rate `0.0`

### memory/repeated-failure-fragile-file

- Grading mode: `assertion`
- baseline_clean: runs `3`, pass rate `0.0`
- skills_only_clean: runs `3`, pass rate `0.0`
- skills_with_hooks_clean: runs `3`, pass rate `0.0`

### pressure/professional-boundary-under-user-pressure

- Grading mode: `assertion`
- baseline_clean: runs `3`, pass rate `0.0`
- skills_only_clean: runs `3`, pass rate `0.0`
- skills_with_hooks_clean: runs `3`, pass rate `0.0`

### process/full-pdd-ddd-sdd-tdd-review-repair

- Grading mode: `assertion`
- baseline_clean: runs `3`, pass rate `0.0`
- skills_only_clean: runs `3`, pass rate `0.0`
- skills_with_hooks_clean: runs `3`, pass rate `0.0`

### repo-intel/caller-callee-test-impact-map

- Grading mode: `assertion`
- baseline_clean: runs `3`, pass rate `0.0`
- skills_only_clean: runs `3`, pass rate `0.0`
- skills_with_hooks_clean: runs `3`, pass rate `0.0`

### review/repair-rereview-required

- Grading mode: `assertion`
- baseline_clean: runs `3`, pass rate `0.0`
- skills_only_clean: runs `3`, pass rate `0.0`
- skills_with_hooks_clean: runs `3`, pass rate `0.0`

### validation/stale-validation-after-edit

- Grading mode: `assertion`
- baseline_clean: runs `3`, pass rate `0.0`
- skills_only_clean: runs `3`, pass rate `0.0`
- skills_with_hooks_clean: runs `3`, pass rate `0.0`

## Limitations

- Local Codex CLI runs depend on the installed CLI, configured model, account access, and local machine state.
- Parsed telemetry excludes raw command bodies and assistant/user message content.
- Pass rates include only benchmark_eligible assertion-backed results; telemetry-only cases are counted separately.
- Strict comparative claims may borrow Codex authentication only; user skills, hooks, config, and rules are not loaded.
- Baseline contamination blocks publishing, and pass rates include assertion-backed eligible results only.
- Current strict live evidence covers ablation across at least 5 assertion-backed cases and 3 runs per required variant, but remains local Codex CLI evidence.
