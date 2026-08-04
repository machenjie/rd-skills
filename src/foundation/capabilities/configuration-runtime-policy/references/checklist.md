# Configuration Runtime Policy Checklist

- Name each config key, flag, mode, kind, provider, rollout toggle, kill switch, tenant/user/experiment override, or operator setting.
- State source of truth, type, allowed values, rejected values, default, owner, precedence, read boundary, and environments in scope.
- Confirm defaults are production-safe and fail closed for security, privacy, money, data integrity, tenant isolation, and compliance unless explicitly reviewed.
- Validate invalid, missing, stale, conflicting, and representative behavior-changing variant values before use.
- Record feature flag type, reason, owner, expiry or removal condition, cleanup issue, telemetry, and old/new path tests.
- Map mode/kind/provider values to bounded enum semantics, graph variants, rejected strategy drift, and test coverage.
- Define runtime reload or remote config behavior: validate before apply, version publication, last-good rollback, visible current state, audit, and alert.
- Name rollout, rollback, kill-switch, re-enable, cleanup, and operator runbook path.
- Route secrets, credential-bearing values, public frontend exposure, auth, tenant, data visibility, logging redaction, and fail-open defaults to the correct gate.
- Map changed keys and variants to validator commands, reports, artifact paths, exit codes, skipped combinations, freshness, residual risk, and next owner.
