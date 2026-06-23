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
- Run id: `ablation-core-20260623-073137`
- Assertion-backed cases: `5`
- Telemetry-only cases: `0`
- Results: `45`
- Benchmark eligible results: `44`
- Telemetry-only results: `0`
- Contaminated results: `0`
- Coverage tiers: `{'core': 5, 'experimental': 0, 'level1': 0}`
- Coverage dimensions: `{'backend-service-boundary': 1, 'concurrency-control': 1, 'devex-reuse': 1, 'implementation-structure': 2, 'input-validation': 1, 'object-boundary': 1, 'observability': 1, 'reliability-cache': 1, 'security-ssrf': 1, 'structure-placement': 1}`
- Total input tokens: `37082375`
- Total output tokens: `468459`
- Observed min runs per case/variant: `3`
- Test-suite failure rate: `0.3556`

## Variants

### baseline_clean

- Results: `15`
- Runs: `3`
- Cases: `5`
- Eligible results: `15`
- Pass rate: `0.3333`
- Security pass rate: `0.8`
- Dominant setup failure reason: `none`
- Dominant setup failure subreason: `none`
- Unknown setup failure rate: `0.0`
- Average input tokens: `340436.07`
- Median input tokens: `322362.0`
- Average output tokens: `8864.93`
- Average command executions: `55.73`
- Average file changes: `4.67`

### skills_only_clean

- Results: `15`
- Runs: `3`
- Cases: `5`
- Eligible results: `15`
- Pass rate: `0.8`
- Security pass rate: `1.0`
- Dominant setup failure reason: `none`
- Dominant setup failure subreason: `none`
- Unknown setup failure rate: `0.0`
- Average input tokens: `1227635.87`
- Median input tokens: `1049362.0`
- Average output tokens: `12157.07`
- Average command executions: `83.07`
- Average file changes: `8.13`

### skills_with_hooks_clean

- Results: `15`
- Runs: `3`
- Cases: `5`
- Eligible results: `14`
- Pass rate: `0.7857`
- Security pass rate: `1.0`
- Dominant setup failure reason: `none`
- Dominant setup failure subreason: `none`
- Unknown setup failure rate: `0.0`
- Average input tokens: `904086.4`
- Median input tokens: `922783.0`
- Average output tokens: `10208.6`
- Average command executions: `72.13`
- Average file changes: `5.47`

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
- baseline_clean: runs `3`, pass rate `0.0`
- skills_only_clean: runs `3`, pass rate `0.0`
- skills_with_hooks_clean: runs `3`, pass rate `0.0`

### security/ssrf-url-allowlist

- Grading mode: `assertion`
- baseline_clean: runs `3`, pass rate `0.0`
- skills_only_clean: runs `3`, pass rate `1.0`
- skills_with_hooks_clean: runs `3`, pass rate `1.0`

### structure/object-method-encapsulation-placement

- Grading mode: `assertion`
- baseline_clean: runs `3`, pass rate `0.0`
- skills_only_clean: runs `3`, pass rate `1.0`
- skills_with_hooks_clean: runs `3`, pass rate `1.0`

## Limitations

- Local Codex CLI runs depend on the installed CLI, configured model, account access, and local machine state.
- Parsed telemetry excludes raw command bodies and assistant/user message content.
- Pass rates include only benchmark_eligible assertion-backed results; telemetry-only cases are counted separately.
- Strict comparative claims may borrow Codex authentication only; user skills, hooks, config, and rules are not loaded.
- Baseline contamination blocks publishing, and pass rates include assertion-backed eligible results only.
- Current strict live evidence covers ablation across at least 5 assertion-backed cases and 3 runs per required variant, but remains local Codex CLI evidence.
