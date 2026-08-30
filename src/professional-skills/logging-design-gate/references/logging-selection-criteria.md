# Logging Selection Criteria

Load when purpose, placement, level, fields, redaction, correlation, or signal choice is unresolved; Task implements and Review inspects without repair.

## Root-Relocated Decision Rules

- Log only for a named diagnostic, audit, security, or operational question; prefer another signal or no new signal when it answers better.
- Place one event at the boundary owning the outcome; do not duplicate intermediate retries, wrappers, and terminal failures.
- Select level and stable schema from current logger policy, event meaning, and reachable failure states.
- Allow only purpose-required fields; omit or transform secrets, credentials, sensitive payloads, and unnecessary personal data under current policy.
- Preserve only the correlation needed across affected request, trace, message, or job boundaries without exposing raw identity.
- Bound material rate, value-space, retention, access, sink, cost, cardinality, and audit risk with measured/platform evidence and an owner.

## Root-Relocated Failure Warnings

- Raw payload logging creates a durable privacy incident.
- Intermediate retry errors can create false incidents before the terminal outcome is known.
- High-cardinality fields, hot-path events, or an error without useful context can make the signal unusable.

## Selection Criteria And Limits

- Match operation/dependency/worker failure signals to safe category, attempt, duration, fallback and correlation fields; exclude unbounded per-item detail.
- Give governed actions and security outcomes an accepted audit/security owner; a diagnostic log cannot become the protected record or business ledger.
- Bind business, process, config, migration and readiness signals to their owning outcome boundary.
- Pending outcome proof, keep intermediate success provisional.
- Place entry identity at entry, application outcome in its owner, dependency detail in its adapter and job state in its worker; pure domain code returns facts.
- Choose severity from final consequence and policy; allowlist fields, transform classified data and keep raw URLs, bodies, credentials, identity/free text out of labels.
- Task proves changed emission with final-edit tests/capture; Review returns verdict/scope. Neither proves production sinks, redaction, sampling, retention, access, cardinality or audit immutability.

Error mechanics, telemetry design, secret handling, and release approval remain separate capability boundaries; record their decision owners when triggered.
