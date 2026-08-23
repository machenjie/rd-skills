# Configuration Runtime Policy Evidence Patterns

Use this evidence-pattern Reference only when configuration closure depends on current effective-state, variant, safety, authority, or proof-limit evidence.

## Evidence Records

| Claim | Minimum current evidence | Explicit limit |
| --- | --- | --- |
| Typed source | Key, type, allowed/rejected values, owner, default, precedence, and read boundary. | Downstream agreement remains unproved. |
| Safe default | Production/test value, fail-open/closed posture, invariant impact, and specialist review when sensitive. | Environment variants not represented by this evidence remain proof limits. |
| Validation before use | Build/deploy/startup/load/apply point, invalid/missing/conflict cases, and status. | Dynamic or operator paths not exercised by this evidence remain proof limits. |
| Governed lifecycle | Flag type, owner, reason, expiry/removal, cleanup issue, telemetry, and old/new tests. | Follow-through remains owner-dependent. |
| Bounded variant | Enum, graph matrix, config-driven edges, startup fail-fast, and tests. | Uninspected plugins/providers remain unproved. |
| Rollout/recovery | Stage, kill-switch state, rollback value/procedure, audit, alert, and runbook. | Production failure modes not exercised by this evidence remain proof limits. |
| Reused evidence | Current schema, read path, graph, telemetry, cleanup, tests, reports, and final-edit freshness. | Later key/default/wiring/rollout changes invalidate it. |
| Safe retained output | Action, permission, redaction, artifact, retention owner, and recovery/cleanup. | Future exports remain unproved. |

## Freshness And Authority

- Treat prior tasks, incidents, dashboards, telemetry, generated reports, and tool output as selectors until current source, registry, docs, tests, and owner evidence confirm them.
- For each changed configuration element, cite current evidence or a not-run disclosure and name production-only variants and residual owners.
- For staging or production config/flag actions, record environment, data class, permission, owner, blast radius, stop, rollback/kill switch, and redaction.
