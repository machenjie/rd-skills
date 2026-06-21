# Codex CLI Live Benchmark Summary

- Status: `collected`
- Evidence level: `local_codex_cli_live_benchmark`
- Benchmark mode: `clean-paired`
- Auth policy: `borrow-current`
- Environment policy: `auth_borrowed_clean`
- Strict benchmark eligible: `True`
- Run id: `clean-auth-borrowed-20260621-172911`
- Assertion-backed cases: `1`
- Telemetry-only cases: `0`
- Results: `2`
- Benchmark eligible results: `1`
- Telemetry-only results: `0`
- Contaminated results: `1`

## Variants

### baseline_clean

- Results: `1`
- Eligible results: `0`
- Pass rate: `not_collected`
- Security pass rate: `not_collected`
- Average input tokens: `675059.0`
- Average output tokens: `12616.0`
- Average command executions: `84.0`
- Average file changes: `6.0`

### skills_with_hooks_clean

- Results: `1`
- Eligible results: `1`
- Pass rate: `1.0`
- Security pass rate: `1.0`
- Average input tokens: `929999.0`
- Average output tokens: `10400.0`
- Average command executions: `68.0`
- Average file changes: `6.0`

## Limitations

- Local Codex CLI runs depend on the installed CLI, configured model, account access, and local machine state.
- Parsed telemetry excludes raw command bodies and assistant/user message content.
- Pass rates include only benchmark_eligible assertion-backed results; telemetry-only cases are counted separately.
- Strict comparative claims may borrow Codex authentication only; user skills, hooks, config, and rules are not loaded.
- Baseline contamination blocks publishing, and pass rates include assertion-backed eligible results only.
