# Configuration Runtime Policy Evidence Patterns

Use this reference when configuration closure depends on validation freshness, prior source or task evidence claims, security-sensitive defaults, tool permission boundaries, or proof limits. Keep it as an evidence map, not a second configuration taxonomy.

## Config-Claim-To-Validation Map

| Config claim | Minimum evidence | What it proves | What it does not prove |
| --- | --- | --- | --- |
| Config has typed source of truth | Key, type, allowed/rejected values, owner, default, precedence, and read boundary | The inspected behavior has a governed config contract | All downstream consumers document the same contract |
| Default is safe | Production/test default, fail-open/fail-closed posture, invariant impact, and specialist review when sensitive | Obvious unsafe default risk was considered | All deployment environments are currently correct |
| Validation happens before use | Build/deploy/startup/load/apply validation point, invalid/missing/conflict cases, and exit status | Bad values are caught at the inspected boundary | Every dynamic remote update or operator path is proven |
| Flag lifecycle is governed | Flag type, owner, reason, expiry/removal condition, cleanup issue, telemetry, and old/new path tests | Temporary behavior has a closure path | Cleanup will happen without follow-up ownership |
| Graph variant is bounded | Mode/kind/provider enum, variant matrix, config-driven edges, startup fail-fast, and tests | Config-driven construction has known variants | Uninspected dynamic plugins or external providers are impossible |
| Rollout and rollback are concrete | Rollout stage, kill-switch state, rollback value/procedure, audit, alert, and runbook | Operators have a named recovery path | Production rollback has been exercised under every failure |
| Prior task or source evidence claim is fresh | Current source/config/docs/tests/telemetry, accepted/rejected memory, observable action sequence order, and validator timestamp | Reused config facts match current inspected state | prior task evidence or graph is complete source of truth |
| Tool output is safe to retain | Action class, permission state, redaction rule, artifact path, retention owner, and rollback or cleanup path | Evidence collection avoids obvious secret/PII leakage | Every future config export or connector output is safe |

## Current Evidence And Freshness

- Treat repository inspection, prior task evidence, prior incidents, flag dashboards, telemetry, generated reports, and validation output as selectors until current source, config registry, docs, tests, and owner evidence confirm them.
- Accept a prior runtime-policy claim only while current configuration schema, read path, graph variant, telemetry, cleanup state, and validation still match. Examples include "flag is temporary", "default is safe", "mode is bounded", "config covered", and "rollout complete".
- Mark config evidence stale after edits to config keys, defaults, validation timing, flags, targeting, mode/kind/provider values, dependency wiring, rollout plans, docs, tests, generated artifacts, dashboards, or build outputs.
- For each changed configuration element, cite fresh evidence or an explicit not-run disclosure. Name production-only variants and residual risks outside the exercised scope.

- If staging flag/config change, remote config dry run, canary rollout, dashboard export, record environment, data class, owner, stop condition, rollback, and redaction.
- If production config, live flag, operator console, secret manager, or connector write, require owner approval, blast-radius limit, rollback or kill-switch path, and redaction rule.
