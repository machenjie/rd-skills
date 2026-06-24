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
- Dominant failure category: `test_suite_failed`
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
- Run id: `clean-auth-borrowed-20260624-042529`
- Assertion-backed cases: `1`
- Telemetry-only cases: `0`
- Results: `2`
- Benchmark eligible results: `2`
- Telemetry-only results: `0`
- Contaminated results: `0`
- Coverage tiers: `{'core': 1, 'experimental': 0, 'level1': 0}`
- Registered live cases: `13`
- Registered publishable assertion cases: `12`
- Actual run case coverage: `1/60`
- Coverage dimensions: `{'input-validation': 1, 'security-ssrf': 1}`
- Total input tokens: `1564353`
- Total output tokens: `20867`
- Observed min runs per case/variant: `1`
- Test-suite failure rate: `0.5`
- Codex exec retries: `0`
- Partial status reasons: `['test_suite_failed:1']`
- Structured log events: `16`
- Timeline events: `16`
- Process trace count: `2`
- PDD/DDD/SDD/TDD rates: `0.0`/`0.0`/`0.0`/`0.0`

## Variants

### baseline_clean

- Results: `1`
- Runs: `1`
- Cases: `1`
- Eligible results: `1`
- Pass rate: `0.0`
- Security pass rate: `0.0`
- Dominant setup failure reason: `none`
- Dominant setup failure subreason: `none`
- Unknown setup failure rate: `0.0`
- Average input tokens: `525515.0`
- Median input tokens: `525515.0`
- Average output tokens: `9375.0`
- Average command executions: `62.0`
- Average file changes: `10.0`

### skills_with_hooks_clean

- Results: `1`
- Runs: `1`
- Cases: `1`
- Eligible results: `1`
- Pass rate: `1.0`
- Security pass rate: `1.0`
- Dominant setup failure reason: `none`
- Dominant setup failure subreason: `none`
- Unknown setup failure rate: `0.0`
- Average input tokens: `1038838.0`
- Median input tokens: `1038838.0`
- Average output tokens: `11492.0`
- Average command executions: `80.0`
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
