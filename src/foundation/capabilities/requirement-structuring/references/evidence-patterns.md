# Requirement Structuring Evidence Patterns

Use this reference only when a structured requirement needs explicit repository or prior-task evidence, inspection, observable actions, validation freshness, forbidden-artifact checks, tool boundaries, or proof limits. Keep this file as an evidence map, not a second requirement-structuring tutorial.

## Structured Requirement Fact Evidence Map

| Structured requirement claim | Minimum evidence | What it proves | What it does not prove |
| --- | --- | --- | --- |
| Current behavior | Source path, test, docs, generated contract, report, screenshot, query, or owner record inspected after the latest relevant edit. | The named boundary currently behaves or is specified as claimed. | Uninspected actors, environments, consumers, production data, or hidden jobs match the claim. |
| Desired behavior | Requirement authority, ticket, spec, owner decision, or accepted stakeholder source with scope and date. | The named outcome is authorized for the stated actor/surface. | Implementation approach, adjacent behavior, or future version scope is approved. |
| Actor and trigger | Route/job/event/UI/API/integration evidence or owner-approved actor statement. | The behavior has an initiator and stimulus that downstream scenarios can test. | Authorization, permission, or abuse paths are complete. |
| In-scope surface | Current source/docs/tests/graph show the surface exists or is intentionally added. | Downstream planning may consider that surface part of the change. | All consumers or side effects are known. |
| Non-goal | Behavior-bound exclusion plus forbidden artifact or not-present check. | Implementers have a reviewable boundary against scope creep. | Future work remains excluded after this handoff. |
| Constraint | Threshold, standard, environment, owner, and validation method. | The constraint can block completion or route to a specialist gate. | Production performance, compliance, or security is proven without the named validation. |
| Dependency | Owner, contract/version, readiness signal, feature flag, migration, rollout, or external service state. | Implementation planning can order or block work around the dependency. | The dependency will remain available or compatible. |
| Acceptance signal | Scenario, test/review artifact, query, dashboard, audit, manual review, or sign-off owner. | The requirement has a falsifiable done signal. | Tests are already implemented or exhaustive. |

## Current Evidence And Freshness

| Evidence source | Accept when | Reject or downgrade when |
| --- | --- | --- |
| repository inspection | Current routes, imports, generated artifacts, tests, docs, config, jobs, contracts, and consumers are inspected or explicitly bounded. | Graph proximity is treated as source-of-truth behavior or product intent. |
| prior task evidence | Memory has date, owner, scope, and current-source confirmation or is carried as advisory only. | Memory predates source/contract/registry/report changes, lacks owner, or conflicts with current artifacts. |
| Observable action sequence | Commands, reviews, repairs, and validation freshness are recorded after the final relevant edit. | Evidence predates final edits or omits a repair/re-review loop. |
| Stakeholder source | Authority, date, scope, decision shape, and downstream Skill or owner are named. | Chat summary or generated summary is used as binding approval without owner. |
| Generated artifact | Artifact is generated from current source and inspected alongside source boundary. | Artifact is treated as product intent or compatibility proof without generator/source freshness. |

## Forbidden-Artifact Checks

Use not-present checks when a non-goal, deferred decision, compatibility promise, or partial proceed boundary appears in the structured requirement.

| Forbidden artifact | Example check |
| --- | --- |
| Public route, operation, or endpoint | Route table, OpenAPI diff, generated client diff, contract test. |
| Response field, enum, event, or SDK surface | Schema diff, DTO test, generated artifact review, consumer-impact note. |
| Data migration, table, column, backfill, or retention rule | Migration directory review, schema snapshot, data owner note. |
| Permission, role, policy, tenant predicate, or audit requirement | Policy/role registry search, denied-case acceptance, security gate handoff. |
| UI action, navigation, form field, or hidden control | Component/route review, accessibility query by role/name, screenshot/manual check. |
| Job, queue topic, cron, webhook, or external call | Job registry, topic/event contract, integration route search. |
| Release flag, config default, rollback script, or deploy artifact | Config/flag scan, release gate review, rollback plan note. |
| Docs, support macro, runbook, or release note that promises excluded behavior | Docs diff, support path review, changelog/release-note check. |

- If connector, telemetry, owner record, or production-data lookup, record account, data boundary, redaction, retention, and unavailable evidence.
- If cleanup, migration, deploy, destructive filesystem, or external write, require owner approval, dry-run where available, rollback/compensation path, and stop condition.
