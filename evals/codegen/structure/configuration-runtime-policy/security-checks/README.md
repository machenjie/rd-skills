# Security Checks

## Threat Surface

Runtime configuration and feature flags can bypass consent, permissions, rate limits, or secrets handling when untyped or unvalidated.

## Required Checks

- Config changes do not bypass domain or security invariants.
- Secrets are separated from ordinary runtime config and never logged.
- Kill switches fail closed for permission, consent, and privacy-sensitive paths.

## Rejection Cases

- Reject mode or kind switches that disable consent or permission checks.
- Fail when secret config is exposed in logs or telemetry.
- Reject invalid config accepted without fail-fast or safe degradation.
