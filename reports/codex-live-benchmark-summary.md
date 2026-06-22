# Codex CLI Live Benchmark Summary

- Status: `partial`
- Evidence level: `local_codex_cli_live_benchmark`
- Evidence scope: `multi_case_ablation_3_run`
- Evidence scope ready: `True`
- Evidence scope reason: ablation evidence includes the required assertion-backed case count and repeated runs
- Evidence status: `partial`
- Effect verdict: `mixed`
- Effect status: `mixed`
- Effect reason: some case-level movement exists, but the aggregate effect is not clearly positive
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
- Run id: `ablation-5cases-3runs-20260622-125546`
- Assertion-backed cases: `5`
- Telemetry-only cases: `0`
- Results: `45`
- Benchmark eligible results: `43`
- Telemetry-only results: `0`
- Contaminated results: `0`

## Variants

### baseline_clean

- Results: `15`
- Runs: `3`
- Cases: `5`
- Eligible results: `15`
- Pass rate: `0.2667`
- Security pass rate: `0.8`
- Dominant setup failure reason: `none`
- Dominant setup failure subreason: `none`
- Unknown setup failure rate: `0.0`
- Average input tokens: `333157.33`
- Median input tokens: `288397.0`
- Average output tokens: `9280.33`
- Average command executions: `56.8`
- Average file changes: `5.73`

### skills_only_clean

- Results: `15`
- Runs: `3`
- Cases: `5`
- Eligible results: `15`
- Pass rate: `0.4667`
- Security pass rate: `0.8667`
- Dominant setup failure reason: `none`
- Dominant setup failure subreason: `none`
- Unknown setup failure rate: `0.0`
- Average input tokens: `1039912.2`
- Median input tokens: `829529.0`
- Average output tokens: `11376.53`
- Average command executions: `82.53`
- Average file changes: `5.07`

### skills_with_hooks_clean

- Results: `15`
- Runs: `3`
- Cases: `5`
- Eligible results: `13`
- Pass rate: `0.4615`
- Security pass rate: `0.7692`
- Dominant setup failure reason: `none`
- Dominant setup failure subreason: `none`
- Unknown setup failure rate: `0.0`
- Average input tokens: `714897.87`
- Median input tokens: `744578.0`
- Average output tokens: `8714.73`
- Average command executions: `63.07`
- Average file changes: `4.53`

## Cases

### backend/service-method-vs-new-helper

- Grading mode: `assertion`
- baseline_clean: runs `3`, pass rate `1.0`
- skills_only_clean: runs `3`, pass rate `1.0`
- skills_with_hooks_clean: runs `3`, pass rate `1.0`

### devex/helper-reuse-search

- Grading mode: `assertion`
- baseline_clean: runs `3`, pass rate `0.3333`
- skills_only_clean: runs `3`, pass rate `1.0`
- skills_with_hooks_clean: runs `3`, pass rate `1.0`

### reliability/redis-cache-stampede-protection

- Grading mode: `assertion`
- baseline_clean: runs `3`, pass rate `0.0`
- skills_only_clean: runs `3`, pass rate `0.0`
- skills_with_hooks_clean: runs `3`, pass rate `0.0`

### security/ssrf-url-allowlist

- Grading mode: `assertion`
- baseline_clean: runs `3`, pass rate `0.0`
- skills_only_clean: runs `3`, pass rate `0.3333`
- skills_with_hooks_clean: runs `3`, pass rate `0.0`

### structure/object-method-encapsulation-placement

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
