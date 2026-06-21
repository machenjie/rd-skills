# Codex CLI Live Benchmark Summary

- Status: `collected`
- Evidence level: `local_codex_cli_live_benchmark`
- Benchmark mode: `clean-paired`
- Auth policy: `borrow-current`
- Environment policy: `auth_borrowed_clean`
- Strict benchmark eligible: `True`
- Run id: `clean-auth-borrowed-20260621-174453`
- Assertion-backed cases: `1`
- Telemetry-only cases: `0`
- Results: `2`
- Benchmark eligible results: `2`
- Telemetry-only results: `0`
- Contaminated results: `0`

## Variants

### baseline_clean

- Results: `1`
- Eligible results: `1`
- Pass rate: `1.0`
- Security pass rate: `1.0`
- Average input tokens: `555261.0`
- Average output tokens: `9694.0`
- Average command executions: `72.0`
- Average file changes: `8.0`

### skills_with_hooks_clean

- Results: `1`
- Eligible results: `1`
- Pass rate: `1.0`
- Security pass rate: `1.0`
- Average input tokens: `1386510.0`
- Average output tokens: `11662.0`
- Average command executions: `98.0`
- Average file changes: `6.0`

## Limitations

- Local Codex CLI runs depend on the installed CLI, configured model, account access, and local machine state.
- Parsed telemetry excludes raw command bodies and assistant/user message content.
- Pass rates include only benchmark_eligible assertion-backed results; telemetry-only cases are counted separately.
- Strict comparative claims may borrow Codex authentication only; user skills, hooks, config, and rules are not loaded.
- Baseline contamination blocks publishing, and pass rates include assertion-backed eligible results only.
