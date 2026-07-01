# Codex CLI Live Benchmark Summary

- Status: `collected`
- Evidence level: `local_codex_cli_live_benchmark`
- Evidence scope: `multi_case_ablation_3_run`
- Evidence scope ready: `True`
- Evidence scope reason: ablation evidence includes the required assertion-backed case count and repeated runs
- Evidence status: `pass`
- Effect verdict: `positive`
- Effect status: `improved`
- Effect reason: skills_with_hooks_clean improves over baseline_clean and is not below skills_only_clean
- Dominant failure category: `none`
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
- Run id: `ablation-core-auth-borrowed-20260701-013224`
- Assertion-backed cases: `16`
- Telemetry-only cases: `0`
- Results: `144`
- Benchmark eligible results: `144`
- Telemetry-only results: `0`
- Contaminated results: `0`
- Coverage tiers: `{'core': 16, 'experimental': 0, 'level1': 0}`
- Registered live cases: `24`
- Registered publishable assertion cases: `23`
- Actual run case coverage: `16/79`
- Coverage dimensions: `{'backend-service-boundary': 1, 'concurrency-control': 1, 'context_compaction_retention': 1, 'devex-reuse': 1, 'execution_trajectory_review': 4, 'implementation-structure': 2, 'input-validation': 1, 'minimal_correct_implementation_ladder': 1, 'object-boundary': 1, 'observability': 1, 'pdd_ddd_sdd_tdd_review_flow': 1, 'professional_injection_activation': 1, 'professional_logging_decision': 1, 'project_memory_governance': 1, 'pua_or_pressure_resistance': 1, 'reliability-cache': 1, 'repository_graph_context_pack': 1, 'security-ssrf': 1, 'staged_injection_precision': 1, 'structure-placement': 1, 'validation_broker_freshness': 3}`
- Total input tokens: `78938559`
- Total output tokens: `1493233`
- Observed min runs per case/variant: `3`
- Test-suite failure rate: `0.0347`
- Codex exec retries: `0`
- Partial status reasons: `['test_suite_failed:5']`
- Structured log events: `1018`
- Timeline events: `1018`
- Process trace count: `144`

## Quality Improvement

- baseline_clean pass rate: `0.9375`
- skills_only_clean pass rate: `0.9792`
- skills_with_hooks_clean pass rate: `0.9792`
- skills_only vs baseline delta: `0.0417`
- skills_with_hooks vs skills_only delta: `0.0`
- skills_with_hooks vs baseline delta: `0.0417`
- no_quality_regression: `False`
- large_quality_improvement_claim: `False`

## Capability Coverage

- Status: `partial`
- Core capabilities: `11`
- Pass/partial/fail/not_collected: `2`/`9`/`0`/`0`
- Assertion-backed covered capabilities: `2`

| Capability | Linked cases | Run status | Assertion status | Evidence collected | Status |
| --- | --- | --- | --- | --- | --- |
| professional_injection_activation | injection/professional-route-manifest-activation | `run` | `partial` | `False` | `partial` |
| staged_injection_precision | injection/stage-specific-reference-loading | `run` | `partial` | `False` | `partial` |
| repository_graph_context_pack | repo-intel/caller-callee-test-impact-map | `run` | `partial` | `False` | `partial` |
| project_memory_governance | memory/repeated-failure-fragile-file | `run` | `pass` | `True` | `pass` |
| validation_broker_freshness | process/full-pdd-ddd-sdd-tdd-review-repair, validation/stale-validation-after-edit | `run` | `partial` | `False` | `partial` |
| pdd_ddd_sdd_tdd_review_flow | process/full-pdd-ddd-sdd-tdd-review-repair | `run` | `partial` | `False` | `partial` |
| minimal_correct_implementation_ladder | devex/minimal-correct-native-reuse | `run` | `partial` | `False` | `partial` |
| pua_or_pressure_resistance | pressure/professional-boundary-under-user-pressure | `run` | `partial` | `False` | `partial` |
| execution_trajectory_review | process/full-pdd-ddd-sdd-tdd-review-repair, review/repair-rereview-required | `run` | `partial` | `False` | `partial` |
| professional_logging_decision | logging/redacted-structured-log-design | `run` | `partial` | `False` | `partial` |
| context_compaction_retention | compact/context-retention-after-compaction | `run` | `pass` | `True` | `pass` |

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
- candidate_context_status: `pass`

## Process Compliance

- pdd_present_rate: `1.0`
- ddd_present_rate: `1.0`
- sdd_present_rate: `0.7847`
- tdd_present_rate: `1.0`
- review_present_rate: `0.9931`
- repair_present_rate: `0.2083`
- rereview_present_rate: `0.2083`
- inferred_rate: `0.0`
- required_field_fallback_rate: `0.0`
- validation_command_present_rate: `1.0`
- Explicit trace contract: `changeforge_route`, PDD acceptance, DDD invariants, SDD placement/error contract, and TDD validation trace.

## Case-Level Result

- Improved cases: `['reliability/redis-cache-stampede-protection', 'structure/object-method-encapsulation-placement']`
- No improvement cases: `['backend/service-method-vs-new-helper', 'compact/context-retention-after-compaction', 'devex/helper-reuse-search', 'devex/minimal-correct-native-reuse', 'injection/professional-route-manifest-activation', 'injection/stage-specific-reference-loading', 'logging/redacted-structured-log-design', 'memory/repeated-failure-fragile-file', 'pressure/professional-boundary-under-user-pressure', 'process/full-pdd-ddd-sdd-tdd-review-repair', 'repo-intel/caller-callee-test-impact-map', 'review/repair-rereview-required', 'security/ssrf-url-allowlist', 'validation/stale-validation-after-edit']`
- Regressed cases: `[]`
- Reliability no-improvement cases: `[]`
- Known unresolved reliability cases: `[]`

## Cost Telemetry

- skills_with_hooks_clean_vs_baseline_clean input token overhead: `+228.79%`
- skills_with_hooks_clean_vs_baseline_clean output token overhead: `+35.56%`
- skills_with_hooks_clean_vs_baseline_clean reasoning token overhead: `+44.55%`
- skills_with_hooks_clean_vs_baseline_clean command execution delta: `19.91`
- skills_with_hooks_clean_vs_baseline_clean pass rate delta: `0.0417`
- Cost is telemetry only: `True`
- Quality-first benchmark does not gate on cost.
- No cost reduction or efficiency improvement claim is made.
- Cost caveat: Token usage is parsed local Codex telemetry, not a billing ledger or a quality gate.

## Variants

### baseline_clean

- Results: `48`
- Runs: `3`
- Cases: `16`
- Eligible results: `48`
- Pass rate: `0.9375`
- Security pass rate: `1.0`
- Security assertion failure rate: `0.0`
- Security check execution failure rate: `0.0`
- Dominant setup failure reason: `none`
- Dominant setup failure subreason: `none`
- Unknown setup failure rate: `0.0`
- Average input tokens: `222075.4`
- Average output tokens: `8404.15`
- Average reasoning tokens: `1255.21`
- Median input tokens: `185076.5`
- Average command executions: `38.17`
- Average file changes: `4.79`

### skills_only_clean

- Results: `48`
- Runs: `3`
- Cases: `16`
- Eligible results: `48`
- Pass rate: `0.9792`
- Security pass rate: `1.0`
- Security assertion failure rate: `0.0`
- Security check execution failure rate: `0.0`
- Dominant setup failure reason: `none`
- Dominant setup failure subreason: `none`
- Unknown setup failure rate: `0.0`
- Average input tokens: `692307.4`
- Average output tokens: `11312.08`
- Average reasoning tokens: `1746.4`
- Median input tokens: `578457.0`
- Average command executions: `59.08`
- Average file changes: `5.38`

### skills_with_hooks_clean

- Results: `48`
- Runs: `3`
- Cases: `16`
- Eligible results: `48`
- Pass rate: `0.9792`
- Security pass rate: `1.0`
- Security assertion failure rate: `0.0`
- Security check execution failure rate: `0.0`
- Dominant setup failure reason: `none`
- Dominant setup failure subreason: `none`
- Unknown setup failure rate: `0.0`
- Average input tokens: `730170.52`
- Average output tokens: `11392.79`
- Average reasoning tokens: `1814.4`
- Median input tokens: `627271.0`
- Average command executions: `58.08`
- Average file changes: `5.79`

## Cases

### backend/service-method-vs-new-helper

- Grading mode: `assertion`
- baseline_clean: runs `3`, pass rate `1.0`
- skills_only_clean: runs `3`, pass rate `0.6667`
- skills_with_hooks_clean: runs `3`, pass rate `1.0`

### compact/context-retention-after-compaction

- Grading mode: `assertion`
- baseline_clean: runs `3`, pass rate `1.0`
- skills_only_clean: runs `3`, pass rate `1.0`
- skills_with_hooks_clean: runs `3`, pass rate `1.0`

### devex/helper-reuse-search

- Grading mode: `assertion`
- baseline_clean: runs `3`, pass rate `1.0`
- skills_only_clean: runs `3`, pass rate `1.0`
- skills_with_hooks_clean: runs `3`, pass rate `1.0`

### devex/minimal-correct-native-reuse

- Grading mode: `assertion`
- baseline_clean: runs `3`, pass rate `1.0`
- skills_only_clean: runs `3`, pass rate `1.0`
- skills_with_hooks_clean: runs `3`, pass rate `1.0`

### injection/professional-route-manifest-activation

- Grading mode: `assertion`
- baseline_clean: runs `3`, pass rate `1.0`
- skills_only_clean: runs `3`, pass rate `1.0`
- skills_with_hooks_clean: runs `3`, pass rate `1.0`

### injection/stage-specific-reference-loading

- Grading mode: `assertion`
- baseline_clean: runs `3`, pass rate `1.0`
- skills_only_clean: runs `3`, pass rate `1.0`
- skills_with_hooks_clean: runs `3`, pass rate `1.0`

### logging/redacted-structured-log-design

- Grading mode: `assertion`
- baseline_clean: runs `3`, pass rate `1.0`
- skills_only_clean: runs `3`, pass rate `1.0`
- skills_with_hooks_clean: runs `3`, pass rate `1.0`

### memory/repeated-failure-fragile-file

- Grading mode: `assertion`
- baseline_clean: runs `3`, pass rate `1.0`
- skills_only_clean: runs `3`, pass rate `1.0`
- skills_with_hooks_clean: runs `3`, pass rate `1.0`

### pressure/professional-boundary-under-user-pressure

- Grading mode: `assertion`
- baseline_clean: runs `3`, pass rate `1.0`
- skills_only_clean: runs `3`, pass rate `1.0`
- skills_with_hooks_clean: runs `3`, pass rate `1.0`

### process/full-pdd-ddd-sdd-tdd-review-repair

- Grading mode: `assertion`
- baseline_clean: runs `3`, pass rate `1.0`
- skills_only_clean: runs `3`, pass rate `1.0`
- skills_with_hooks_clean: runs `3`, pass rate `1.0`

### reliability/redis-cache-stampede-protection

- Grading mode: `assertion`
- baseline_clean: runs `3`, pass rate `0.6667`
- skills_only_clean: runs `3`, pass rate `1.0`
- skills_with_hooks_clean: runs `3`, pass rate `1.0`

### repo-intel/caller-callee-test-impact-map

- Grading mode: `assertion`
- baseline_clean: runs `3`, pass rate `1.0`
- skills_only_clean: runs `3`, pass rate `1.0`
- skills_with_hooks_clean: runs `3`, pass rate `1.0`

### review/repair-rereview-required

- Grading mode: `assertion`
- baseline_clean: runs `3`, pass rate `1.0`
- skills_only_clean: runs `3`, pass rate `1.0`
- skills_with_hooks_clean: runs `3`, pass rate `1.0`

### security/ssrf-url-allowlist

- Grading mode: `assertion`
- baseline_clean: runs `3`, pass rate `1.0`
- skills_only_clean: runs `3`, pass rate `1.0`
- skills_with_hooks_clean: runs `3`, pass rate `1.0`

### structure/object-method-encapsulation-placement

- Grading mode: `assertion`
- baseline_clean: runs `3`, pass rate `0.3333`
- skills_only_clean: runs `3`, pass rate `1.0`
- skills_with_hooks_clean: runs `3`, pass rate `0.6667`

### validation/stale-validation-after-edit

- Grading mode: `assertion`
- baseline_clean: runs `3`, pass rate `1.0`
- skills_only_clean: runs `3`, pass rate `1.0`
- skills_with_hooks_clean: runs `3`, pass rate `1.0`

## Limitations

- Local Codex CLI runs depend on the installed CLI, configured model, account access, and local machine state.
- Parsed telemetry excludes raw command bodies and assistant/user message content.
- Pass rates include only benchmark_eligible assertion-backed results; telemetry-only cases are counted separately.
- Strict comparative claims may borrow Codex authentication only; user skills, hooks, config, and rules are not loaded.
- Baseline contamination blocks publishing, and pass rates include assertion-backed eligible results only.
- Current strict live evidence covers ablation across at least 5 assertion-backed cases and 3 runs per required variant, but remains local Codex CLI evidence.
