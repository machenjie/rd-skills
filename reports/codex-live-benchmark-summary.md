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
- Run id: `ablation-5cases-3runs-20260622-positive`
- Assertion-backed cases: `5`
- Telemetry-only cases: `0`
- Results: `45`
- Benchmark eligible results: `45`
- Telemetry-only results: `0`
- Contaminated results: `0`
- Coverage tiers: `{'core': 5, 'experimental': 0, 'level1': 0}`
- Registered live cases: `23`
- Registered publishable assertion cases: `22`
- Actual run case coverage: `5/70`
- Coverage dimensions: `{'backend-service-boundary': 1, 'concurrency-control': 1, 'devex-reuse': 1, 'implementation-structure': 2, 'input-validation': 1, 'object-boundary': 1, 'observability': 1, 'reliability-cache': 1, 'security-ssrf': 1, 'structure-placement': 1}`
- Total input tokens: `38616339.0`
- Total output tokens: `515302.95`
- Observed min runs per case/variant: `3`
- Test-suite failure rate: `0.3333`
- Codex exec retries: `0`
- Partial status reasons: `[]`
- Structured log events: `0`
- Timeline events: `0`
- Process trace count: `not_collected`

## Quality Improvement

- baseline_clean pass rate: `0.4`
- skills_only_clean pass rate: `0.7333`
- skills_with_hooks_clean pass rate: `0.8667`
- skills_only vs baseline delta: `0.3333`
- skills_with_hooks vs skills_only delta: `0.1334`
- skills_with_hooks vs baseline delta: `0.4667`
- no_quality_regression: `True`
- large_quality_improvement_claim: `False`

## Capability Coverage

- Status: `partial`
- Core capabilities: `10`
- Pass/partial/fail/not_collected: `0`/`10`/`0`/`0`
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

## Process Compliance

- pdd_present_rate: `not_collected`
- ddd_present_rate: `not_collected`
- sdd_present_rate: `not_collected`
- tdd_present_rate: `not_collected`
- review_present_rate: `not_collected`
- repair_present_rate: `not_collected`
- rereview_present_rate: `not_collected`
- inferred_rate: `not_collected`
- required_field_fallback_rate: `not_collected`
- validation_command_present_rate: `not_collected`
- Explicit trace contract: `changeforge_route`, PDD acceptance, DDD invariants, SDD placement/error contract, and TDD validation trace.
- Warning: process evidence not collected; inferred/fallback traces do not prove full process compliance.

## Case-Level Result

- Improved cases: `['devex/helper-reuse-search', 'security/ssrf-url-allowlist', 'structure/object-method-encapsulation-placement']`
- No improvement cases: `['backend/service-method-vs-new-helper', 'reliability/redis-cache-stampede-protection']`
- Regressed cases: `[]`
- Reliability no-improvement cases: `['reliability/redis-cache-stampede-protection']`

## Cost Telemetry

- skills_with_hooks_clean_vs_baseline_clean input token overhead: `+194.52%`
- skills_with_hooks_clean_vs_baseline_clean output token overhead: `+31.70%`
- skills_with_hooks_clean_vs_baseline_clean reasoning token overhead: `+41.02%`
- skills_with_hooks_clean_vs_baseline_clean command execution delta: `29.47`
- skills_with_hooks_clean_vs_baseline_clean pass rate delta: `0.4667`
- Cost is telemetry only: `True`
- Quality-first benchmark does not gate on cost.
- No cost reduction or efficiency improvement claim is made.
- Cost caveat: Cost is telemetry only in this phase; quality-first benchmark does not gate on token, command, or file-change overhead, and no cost reduction or efficiency improvement claim is made.

## Variants

### baseline_clean

- Results: `15`
- Runs: `3`
- Cases: `5`
- Eligible results: `15`
- Pass rate: `0.4`
- Security pass rate: `0.8`
- Security assertion failure rate: `0.2`
- Security check execution failure rate: `not_collected`
- Dominant setup failure reason: `none`
- Dominant setup failure subreason: `none`
- Unknown setup failure rate: `0.0`
- Average input tokens: `395344.8`
- Average output tokens: `9843.87`
- Average reasoning tokens: `1621.13`
- Median input tokens: `335189.0`
- Average command executions: `61.33`
- Average file changes: `6.4`

### skills_only_clean

- Results: `15`
- Runs: `3`
- Cases: `5`
- Eligible results: `15`
- Pass rate: `0.7333`
- Security pass rate: `0.9333`
- Security assertion failure rate: `0.0667`
- Security check execution failure rate: `not_collected`
- Dominant setup failure reason: `none`
- Dominant setup failure subreason: `none`
- Unknown setup failure rate: `0.0`
- Average input tokens: `1014727.73`
- Average output tokens: `11545.53`
- Average reasoning tokens: `2106.27`
- Median input tokens: `1035639.0`
- Average command executions: `79.47`
- Average file changes: `7.33`

### skills_with_hooks_clean

- Results: `15`
- Runs: `3`
- Cases: `5`
- Eligible results: `15`
- Pass rate: `0.8667`
- Security pass rate: `1.0`
- Security assertion failure rate: `0.0`
- Security check execution failure rate: `not_collected`
- Dominant setup failure reason: `none`
- Dominant setup failure subreason: `none`
- Unknown setup failure rate: `0.0`
- Average input tokens: `1164350.07`
- Average output tokens: `12964.13`
- Average reasoning tokens: `2286.13`
- Median input tokens: `1133683.0`
- Average command executions: `90.8`
- Average file changes: `7.2`

## Cases

### backend/service-method-vs-new-helper

- Grading mode: `assertion`
- baseline_clean: runs `3`, pass rate `1.0`
- skills_only_clean: runs `3`, pass rate `1.0`
- skills_with_hooks_clean: runs `3`, pass rate `1.0`

### devex/helper-reuse-search

- Grading mode: `assertion`
- baseline_clean: runs `3`, pass rate `0.6667`
- skills_only_clean: runs `3`, pass rate `1.0`
- skills_with_hooks_clean: runs `3`, pass rate `1.0`

### reliability/redis-cache-stampede-protection

- Grading mode: `assertion`
- baseline_clean: runs `3`, pass rate `0.3333`
- skills_only_clean: runs `3`, pass rate `0.3333`
- skills_with_hooks_clean: runs `3`, pass rate `0.3333`

### security/ssrf-url-allowlist

- Grading mode: `assertion`
- baseline_clean: runs `3`, pass rate `0.0`
- skills_only_clean: runs `3`, pass rate `0.6667`
- skills_with_hooks_clean: runs `3`, pass rate `1.0`

### structure/object-method-encapsulation-placement

- Grading mode: `assertion`
- baseline_clean: runs `3`, pass rate `0.0`
- skills_only_clean: runs `3`, pass rate `0.6667`
- skills_with_hooks_clean: runs `3`, pass rate `1.0`

## Limitations

- Local Codex CLI runs depend on the installed CLI, configured model, account access, and local machine state.
- Parsed telemetry excludes raw command bodies and assistant/user message content.
- Pass rates include only benchmark_eligible assertion-backed results; telemetry-only cases are counted separately.
- Strict comparative claims may borrow Codex authentication only; user skills, hooks, config, and rules are not loaded.
- Baseline contamination blocks publishing, and pass rates include assertion-backed eligible results only.
- Current strict live evidence covers ablation across at least 5 assertion-backed cases and 3 runs per required variant, but remains local Codex CLI evidence.
