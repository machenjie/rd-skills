# Codex CLI Live Benchmark Summary

- Status: `collected`
- Evidence level: `local_codex_cli_live_benchmark`
- Evidence scope: `smoke`
- Strong claim ready: `False`
- Evidence scope reason: strict clean-paired evidence is smoke-scale until ablation covers the required cases and runs
- Benchmark mode: `clean-paired`
- Auth policy: `borrow-current`
- Environment policy: `auth_borrowed_clean`
- Strict benchmark eligible: `True`
- Run id: `clean-auth-borrowed-20260621-175817`
- Assertion-backed cases: `1`
- Telemetry-only cases: `0`
- Results: `2`
- Benchmark eligible results: `2`
- Telemetry-only results: `0`
- Contaminated results: `0`

## Variants

### baseline_clean

- Results: `1`
- Runs: `1`
- Cases: `1`
- Eligible results: `1`
- Pass rate: `0.0`
- Security pass rate: `0.0`
- Average input tokens: `564266.0`
- Median input tokens: `564266.0`
- Average output tokens: `10952.0`
- Average command executions: `70.0`
- Average file changes: `14.0`

### skills_with_hooks_clean

- Results: `1`
- Runs: `1`
- Cases: `1`
- Eligible results: `1`
- Pass rate: `1.0`
- Security pass rate: `1.0`
- Average input tokens: `1616056.0`
- Median input tokens: `1616056.0`
- Average output tokens: `13641.0`
- Average command executions: `102.0`
- Average file changes: `8.0`

## Cases

### security/ssrf-url-allowlist

- Grading mode: `assertion`
- baseline_clean: runs `1`, pass rate `0.0`
- skills_with_hooks_clean: runs `1`, pass rate `1.0`

## Limitations

- Local Codex CLI runs depend on the installed CLI, configured model, account access, and local machine state.
- Parsed telemetry excludes raw command bodies and assistant/user message content.
- Pass rates include only benchmark_eligible assertion-backed results; telemetry-only cases are counted separately.
- Strict comparative claims may borrow Codex authentication only; user skills, hooks, config, and rules are not loaded.
- Baseline contamination blocks publishing, and pass rates include assertion-backed eligible results only.
- Current strict live evidence is a smoke sample only: it supports only the listed case and variants, not a broad rd-skills pass-rate improvement claim. Stronger claims require at least 3-5 assertion-backed cases with 3 runs per variant.
