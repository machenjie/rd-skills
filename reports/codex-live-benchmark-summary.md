# Codex CLI Live Benchmark Summary

- Status: `collected`
- Evidence level: `local_codex_cli_live_benchmark`
- Evidence scope: `multi_case_ablation_3_run`
- Evidence scope ready: `True`
- Evidence scope reason: ablation evidence includes the required assertion-backed case count and repeated runs
- Evidence status: `pass`
- Effect verdict: `negative`
- Effect status: `regression`
- Effect reason: skills_with_hooks_clean pass rate is below baseline_clean
- Benchmark mode: `ablation`
- Auth policy: `borrow-current`
- Environment policy: `auth_borrowed_clean`
- Strict benchmark eligible: `True`
- Run id: `ablation-auth-borrowed-20260621-213019`
- Assertion-backed cases: `5`
- Telemetry-only cases: `1`
- Results: `54`
- Benchmark eligible results: `45`
- Telemetry-only results: `9`
- Contaminated results: `0`

## Variants

### baseline_clean

- Results: `18`
- Runs: `3`
- Cases: `6`
- Eligible results: `15`
- Pass rate: `0.2`
- Security pass rate: `0.2`
- Average input tokens: `418332.78`
- Median input tokens: `367045.5`
- Average output tokens: `9534.5`
- Average command executions: `66.0`
- Average file changes: `5.78`

### skills_only_clean

- Results: `18`
- Runs: `3`
- Cases: `6`
- Eligible results: `15`
- Pass rate: `0.0667`
- Security pass rate: `0.0667`
- Average input tokens: `972824.94`
- Median input tokens: `952899.0`
- Average output tokens: `9982.72`
- Average command executions: `73.78`
- Average file changes: `5.67`

### skills_with_hooks_clean

- Results: `18`
- Runs: `3`
- Cases: `6`
- Eligible results: `15`
- Pass rate: `0.0667`
- Security pass rate: `0.0667`
- Average input tokens: `894470.44`
- Median input tokens: `891559.0`
- Average output tokens: `9141.44`
- Average command executions: `68.89`
- Average file changes: `4.44`

## Cases

### backend/service-method-vs-new-helper

- Grading mode: `assertion`
- baseline_clean: runs `3`, pass rate `0.0`
- skills_only_clean: runs `3`, pass rate `0.0`
- skills_with_hooks_clean: runs `3`, pass rate `0.0`

### devex/helper-reuse-search

- Grading mode: `assertion`
- baseline_clean: runs `3`, pass rate `0.0`
- skills_only_clean: runs `3`, pass rate `0.0`
- skills_with_hooks_clean: runs `3`, pass rate `0.0`

### devex/minimal-correct-implementation-ladder

- Grading mode: `telemetry_only`
- baseline_clean: runs `3`, pass rate `not_collected`
- skills_only_clean: runs `3`, pass rate `not_collected`
- skills_with_hooks_clean: runs `3`, pass rate `not_collected`

### reliability/redis-cache-stampede-protection

- Grading mode: `assertion`
- baseline_clean: runs `3`, pass rate `0.0`
- skills_only_clean: runs `3`, pass rate `0.0`
- skills_with_hooks_clean: runs `3`, pass rate `0.0`

### security/ssrf-url-allowlist

- Grading mode: `assertion`
- baseline_clean: runs `3`, pass rate `0.6667`
- skills_only_clean: runs `3`, pass rate `0.3333`
- skills_with_hooks_clean: runs `3`, pass rate `0.3333`

### structure/object-method-encapsulation-placement

- Grading mode: `assertion`
- baseline_clean: runs `3`, pass rate `0.3333`
- skills_only_clean: runs `3`, pass rate `0.0`
- skills_with_hooks_clean: runs `3`, pass rate `0.0`

## Limitations

- Local Codex CLI runs depend on the installed CLI, configured model, account access, and local machine state.
- Parsed telemetry excludes raw command bodies and assistant/user message content.
- Pass rates include only benchmark_eligible assertion-backed results; telemetry-only cases are counted separately.
- Strict comparative claims may borrow Codex authentication only; user skills, hooks, config, and rules are not loaded.
- Baseline contamination blocks publishing, and pass rates include assertion-backed eligible results only.
- Current strict live evidence covers ablation across at least 5 assertion-backed cases and 3 runs per required variant, but remains local Codex CLI evidence.
