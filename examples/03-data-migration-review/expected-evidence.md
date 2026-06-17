# Expected Evidence

- read before plan: migration files, model definitions, API serializers, background jobs, analytics queries, rollback policy, and deployment order.
- TDD: migration/rollback test or compatibility fixture proving old and new code can run during the transition.
- validation evidence: migration validation command, schema diff, and mixed-version compatibility assessment.
- independent review: `delivery-release-gate` reviews rollout/rollback; `reliability-observability-gate` reviews telemetry and alerting.
- repair/re-review: unsafe same-release removal routes back to `data-api-contract-changer` for expand-contract repair, then re-review repeats.
- residual risk: unknown downstream reporting queries that read the old column.
- handoff: include route manifest, compatibility table, migration order, rollback result, validation output, residual risk, and owner decision if a breaking change remains.
