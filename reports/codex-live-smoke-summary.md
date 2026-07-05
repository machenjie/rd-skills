# Codex CLI Live Benchmark Summary

- Status: `collected`
- Evidence level: `local_codex_cli_live_benchmark`
- Evidence scope: `smoke`
- Evidence scope ready: `False`
- Evidence scope reason: strict clean-paired evidence is smoke-scale until ablation covers the required cases and runs
- Evidence status: `pass`
- Effect verdict: `inconclusive`
- Effect status: `inconclusive`
- Effect reason: missing required ablation variants, repeated runs, or eligible assertion-backed results
- Dominant failure category: `none`
- Dominant setup failure reason: `none`
- Dominant setup failure subreason: `none`
- Unknown setup failure rate: `0.0`
- Benchmark mode: `clean-paired`
- Auth policy: `borrow-current`
- Environment policy: `auth_borrowed_clean`
- ChangeForge install source: `current_repository`
- ChangeForge profile: `recommended`
- ChangeForge hooks enabled: `True`
- User-level install used: `False`
- Strict benchmark eligible: `True`
- Run id: `clean-auth-borrowed-20260701-220235`
- Assertion-backed cases: `1`
- Telemetry-only cases: `0`
- Results: `2`
- Benchmark eligible results: `2`
- Telemetry-only results: `0`
- Contaminated results: `0`
- Coverage tiers: `{'core': 1, 'experimental': 0, 'level1': 0}`
- Registered live cases: `24`
- Registered publishable assertion cases: `23`
- Actual run case coverage: `1/79`
- Actual run publishable assertion cases: `1/23`
- Registered-but-not-run publishable assertion cases: `backend/service-method-vs-new-helper, compact/context-retention-after-compaction, data-api/backward-compatible-api-field, data-middleware/kafka-consumer-offset-dlq, devex/bugfix-same-pattern-scan, devex/helper-reuse-search, devex/minimal-correct-native-reuse, frontend/accessible-form-error-state, injection/professional-route-manifest-activation, injection/stage-specific-reference-loading, integration/webhook-hmac-raw-body, logging/redacted-structured-log-design, memory/repeated-failure-fragile-file, performance/event-loop-blocking-async-path, performance/lock-held-across-io, pressure/professional-boundary-under-user-pressure, process/full-pdd-ddd-sdd-tdd-review-repair, reliability/redis-cache-stampede-protection, repo-intel/caller-callee-test-impact-map, review/repair-rereview-required, structure/object-method-encapsulation-placement, validation/stale-validation-after-edit`
- Coverage dimensions: `{'input-validation': 1, 'security-ssrf': 1}`
- Total input tokens: `1120725`
- Total output tokens: `23237`
- Observed min runs per case/variant: `1`
- Test-suite failure rate: `0.0`
- Codex exec retries: `0`
- Partial status reasons: `[]`
- Structured log events: `16`
- Timeline events: `16`
- Process trace count: `2`

## Quality Improvement

- baseline_clean pass rate: `1.0`
- skills_only_clean pass rate: `not_collected`
- skills_with_hooks_clean pass rate: `1.0`
- skills_only vs baseline delta: `not_collected`
- skills_with_hooks vs skills_only delta: `not_collected`
- skills_with_hooks vs baseline delta: `0.0`
- no_quality_regression: `False`
- large_quality_improvement_claim: `False`

## Capability Coverage

- Status: `partial`
- Core capabilities: `11`
- Pass/partial/fail/not_collected: `0`/`11`/`0`/`0`
- Assertion-backed covered capabilities: `0`

| Capability | Linked cases | Run status | Assertion status | Evidence collected | Status |
| --- | --- | --- | --- | --- | --- |
| professional_injection_activation | injection/professional-route-manifest-activation | `not_run` | `partial` | `False` | `partial` |
| staged_injection_precision | injection/stage-specific-reference-loading | `not_run` | `partial` | `False` | `partial` |
| repository_graph_context_pack | repo-intel/caller-callee-test-impact-map | `not_run` | `partial` | `False` | `partial` |
| project_memory_governance | memory/repeated-failure-fragile-file | `not_run` | `partial` | `False` | `partial` |
| validation_broker_freshness | process/full-pdd-ddd-sdd-tdd-review-repair, validation/stale-validation-after-edit | `not_run` | `partial` | `False` | `partial` |
| pdd_ddd_sdd_tdd_review_flow | process/full-pdd-ddd-sdd-tdd-review-repair | `not_run` | `partial` | `False` | `partial` |
| minimal_correct_implementation_ladder | devex/minimal-correct-native-reuse | `not_run` | `partial` | `False` | `partial` |
| pua_or_pressure_resistance | pressure/professional-boundary-under-user-pressure | `not_run` | `partial` | `False` | `partial` |
| execution_trajectory_review | process/full-pdd-ddd-sdd-tdd-review-repair, review/repair-rereview-required | `not_run` | `partial` | `False` | `partial` |
| professional_logging_decision | logging/redacted-structured-log-design | `not_run` | `partial` | `False` | `partial` |
| context_compaction_retention | compact/context-retention-after-compaction | `not_run` | `partial` | `False` | `partial` |

## Context Compaction Retention

- Compact case run status: `not_run`
- pre_compact_snapshot_count: `0`
- post_compact_reinject_count: `0`
- session_compact_reinject_count: `0`
- compact_runtime_evidence_count: `0`
- restored_required_context_fields: `[]`
- missing_required_context_fields: `['route_id', 'selected_skills', 'selected_capabilities', 'required_quality_gates', 'current_stage', 'pdd_summary', 'ddd_invariants', 'sdd_decisions', 'tdd_validation_plan', 'changed_paths', 'read_paths', 'validation_results', 'validation_freshness', 'review_findings', 'repair_events', 'rereview_events', 'residual_risk', 'memory_references', 'repo_graph_references', 'active_skill_context', 'last_material_edit_index', 'last_validation_command_index']`
- redacted_required_context_fields: `[]`
- context_unusable_fields: `[]`
- privacy_redaction_status: `not_collected`
- context_usable_status: `not_collected`
- context_retention_status: `not_collected`
- compact_after_repair_continuation_status: `not_collected`
- candidate_context_status: `not_collected`

## Process Compliance

- pdd_present_rate: `1.0`
- ddd_present_rate: `1.0`
- sdd_present_rate: `1.0`
- tdd_present_rate: `1.0`
- review_present_rate: `1.0`
- repair_present_rate: `0.0`
- rereview_present_rate: `0.0`
- inferred_rate: `0.0`
- required_field_fallback_rate: `0.0`
- validation_command_present_rate: `1.0`
- Explicit trace contract: `changeforge_route`, PDD acceptance, DDD invariants, SDD placement/error contract, and TDD validation trace.

## Case-Level Result

- Improved cases: `[]`
- No improvement cases: `['security/ssrf-url-allowlist']`
- Regressed cases: `[]`
- Reliability no-improvement cases: `[]`
- Known unresolved reliability cases: `['reliability/redis-cache-stampede-protection']`

## Cost Telemetry

- skills_with_hooks_clean_vs_baseline_clean input token overhead: `+184.02%`
- skills_with_hooks_clean_vs_baseline_clean output token overhead: `+10.67%`
- skills_with_hooks_clean_vs_baseline_clean reasoning token overhead: `-6.91%`
- skills_with_hooks_clean_vs_baseline_clean command execution delta: `10.0`
- skills_with_hooks_clean_vs_baseline_clean pass rate delta: `0.0`
- Cost is telemetry only: `True`
- Quality-first benchmark does not gate on cost.
- No cost reduction or efficiency improvement claim is made.
- Cost caveat: Token usage is parsed local Codex telemetry, not a billing ledger or a quality gate.

## Variants

### baseline_clean

- Results: `1`
- Runs: `1`
- Cases: `1`
- Eligible results: `1`
- Pass rate: `1.0`
- Security pass rate: `1.0`
- Security assertion failure rate: `0.0`
- Security check execution failure rate: `0.0`
- Dominant setup failure reason: `none`
- Dominant setup failure subreason: `none`
- Unknown setup failure rate: `0.0`
- Average input tokens: `291840.0`
- Average output tokens: `11030.0`
- Average reasoning tokens: `3025.0`
- Median input tokens: `291840.0`
- Average command executions: `56.0`
- Average file changes: `4.0`

### skills_with_hooks_clean

- Results: `1`
- Runs: `1`
- Cases: `1`
- Eligible results: `1`
- Pass rate: `1.0`
- Security pass rate: `1.0`
- Security assertion failure rate: `0.0`
- Security check execution failure rate: `0.0`
- Dominant setup failure reason: `none`
- Dominant setup failure subreason: `none`
- Unknown setup failure rate: `0.0`
- Average input tokens: `828885.0`
- Average output tokens: `12207.0`
- Average reasoning tokens: `2816.0`
- Median input tokens: `828885.0`
- Average command executions: `66.0`
- Average file changes: `4.0`

## Cases

### security/ssrf-url-allowlist

- Grading mode: `assertion`
- baseline_clean: runs `1`, pass rate `1.0`
- skills_with_hooks_clean: runs `1`, pass rate `1.0`

## Limitations

- Local Codex CLI runs depend on the installed CLI, configured model, account access, and local machine state.
- Parsed telemetry excludes raw command bodies and assistant/user message content.
- Pass rates include only benchmark_eligible assertion-backed results; telemetry-only cases are counted separately.
- Strict comparative claims may borrow Codex authentication only; user skills, hooks, config, and rules are not loaded.
- Baseline contamination blocks publishing, and pass rates include assertion-backed eligible results only.
- Current strict live evidence is a smoke sample only: it supports only the listed case and variants, not a broad rd-skills pass-rate improvement claim. Stronger claims require at least 3-5 assertion-backed cases with 3 runs per variant.
