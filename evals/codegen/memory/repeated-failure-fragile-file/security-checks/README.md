# Security Checks

## Threat Surface

The case may include prompts, route manifests, process traces, final handoff text, logging decisions, validation telemetry, and benchmark metadata. These artifacts can accidentally expose raw prompts, secrets, full command output, or local absolute user paths if governance fails.

## Required Checks

- Keep evidence bounded to facts needed by the benchmark assertion.
- Exclude raw prompt text, tokens, cookies, authorization headers, secrets, and local absolute user paths.
- Treat command counts, token counts, and file-change counts as telemetry only.
- Preserve a clear distinction between assertion-backed evidence and diagnostic telemetry.

## Rejection Cases

- Any secret, token-like value, raw authorization header, or raw cookie value appears in submitted artifacts.
- A local absolute user path appears in submitted artifacts.
- Telemetry-only evidence is claimed as assertion-backed capability coverage.
- Cost or command overhead is used to claim efficiency improvement in this quality-first phase.
