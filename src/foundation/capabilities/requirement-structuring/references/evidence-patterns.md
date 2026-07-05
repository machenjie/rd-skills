# Requirement Structuring Evidence Patterns

Use this reference when a structured brief can hand off only if repository evidence, project memory, repository graph, execution trajectory, validation freshness, forbidden-artifact checks, tool boundary, or proof limits are explicit. Keep this file as an evidence map, not a second requirement-structuring tutorial.

## Brief Fact Evidence Map

| Brief claim | Minimum evidence | What it proves | What it does not prove |
| --- | --- | --- | --- |
| Current behavior | Source path, test, docs, generated contract, report, screenshot, query, or owner record inspected after the latest relevant edit. | The named boundary currently behaves or is specified as claimed. | Uninspected actors, environments, consumers, production data, or hidden jobs match the claim. |
| Desired behavior | Requirement authority, ticket, spec, owner decision, or accepted stakeholder source with scope and date. | The named outcome is authorized for the stated actor/surface. | Implementation approach, adjacent behavior, or future version scope is approved. |
| Actor and trigger | Route/job/event/UI/API/integration evidence or owner-approved actor statement. | The behavior has an initiator and stimulus that downstream scenarios can test. | Authorization, permission, or abuse paths are complete. |
| In-scope surface | Current source/docs/tests/graph show the surface exists or is intentionally added. | Downstream planning may consider that surface part of the change. | All consumers or side effects are known. |
| Non-goal | Behavior-bound exclusion plus forbidden artifact or not-present check. | Implementers have a reviewable boundary against scope creep. | Future work remains excluded after this handoff. |
| Constraint | Threshold, standard, environment, owner, and validation method. | The constraint can block completion or route to a specialist gate. | Production performance, compliance, or security is proven without the named validation. |
| Dependency | Owner, contract/version, readiness signal, feature flag, migration, rollout, or external service state. | Implementation planning can order or block work around the dependency. | The dependency will remain available or compatible. |
| Acceptance signal | Scenario, test/review artifact, query, dashboard, audit, manual review, or sign-off owner. | The requirement has a falsifiable done signal. | Tests are already implemented or exhaustive. |

## Evidence Classification

Classify every reused fact as one of:

- `FACT`: current source, owner record, generated contract, test, report, or command output supports the claim for the named boundary and freshness window.
- `INFERENCE`: current evidence implies the claim but does not prove it directly; name the missing proof.
- `ASSUMPTION`: accepted for a bounded slice because it is reversible, conventional, testable, and has a follow-up owner.
- `MEMORY_SIGNAL`: prior decision, old plan, old validation, or recurring issue used as a lead only.
- `STALE`: evidence predates relevant source, registry, generated artifact, report, validation, or owner-decision changes.
- `OPEN_QUESTION`: authority or evidence gap that can change behavior, contract, data, permission, rollout, or compliance.

Do not let `MEMORY_SIGNAL`, `STALE`, or `OPEN_QUESTION` close a requirement item. They must become a current `FACT`, a bounded `ASSUMPTION`, or a residual risk with owner.

## Graph, Memory, And Execution Reconciliation

| Evidence source | Accept when | Reject or downgrade when |
| --- | --- | --- |
| Repository graph | Current routes, imports, generated artifacts, tests, docs, config, jobs, contracts, and consumers are inspected or explicitly bounded. | Graph proximity is treated as source-of-truth behavior or product intent. |
| Project memory | Memory has date, owner, scope, and current-source confirmation or is carried as advisory only. | Memory predates source/contract/registry/report changes, lacks owner, or conflicts with current artifacts. |
| Execution trajectory | Commands, reviews, repairs, and validation freshness are recorded after the final relevant edit. | Evidence predates final edits or omits a repair/re-review loop. |
| Stakeholder source | Authority, date, scope, decision shape, and downstream gate are named. | Chat summary or generated summary is used as binding approval without owner. |
| Generated artifact | Artifact is generated from current source and inspected alongside source boundary. | Artifact is treated as product intent or compatibility proof without generator/source freshness. |

## Forbidden-Artifact Checks

Use not-present checks when a non-goal, deferred decision, compatibility promise, or partial proceed boundary appears in the brief.

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

## Tool Permission Boundary

| Action | Boundary record |
| --- | --- |
| Local source, registry, report, and graph inspection | Read-only local shell; cite paths/slices and avoid full output dumps. |
| Local validators, evals, build, install checks | Local-write to reports, caches, dist, or build artifacts; cite command, exit code, log path, and freshness. |
| Connector, telemetry, owner record, or production-data lookup | Data-scoped external action; record account, data boundary, redaction, retention, and unavailable evidence. |
| Cleanup, migration, deploy, destructive filesystem, or external write | High-risk action; require owner approval, dry-run where available, rollback/compensation path, and stop condition. |

## Closure Shape

```yaml
structured_change_brief_evidence_closure:
  inspected_boundaries:
    - boundary: ""
      source_or_report: ""
      finding: ""
      freshness: ""
  classified_facts:
    - claim: ""
      class: FACT|INFERENCE|ASSUMPTION|MEMORY_SIGNAL|STALE|OPEN_QUESTION
      evidence: ""
      owner: ""
  graph_memory_execution:
    repository_graph:
      accepted: []
      rejected_or_bounded: []
    project_memory:
      accepted: []
      rejected_or_stale: []
    execution_trajectory:
      validation_after_final_edit: ""
      stale_or_skipped: []
  traceability_map:
    - requirement_or_boundary: ""
      downstream_owner: ""
      validation_or_review_artifact: ""
      proves: ""
      does_not_prove: ""
  forbidden_artifact_checks:
    - artifact: ""
      check: ""
      outcome: ""
  tool_permission_boundary:
    action_class: ""
    sandbox: ""
    state_mutation: ""
    redaction: ""
  evidence_limits:
    - limit: ""
      residual_risk: ""
      owner: ""
      next_gate: ""
```

## Handoff Closure Rules

- Hand off only when every requirement, non-goal, constraint, dependency, and assumption has evidence, an owner, a validation/review artifact, or an explicit residual risk.
- Mark validation stale after edits to requirements, source, tests, generated artifacts, reports, registries, docs, build/install outputs, or owner decisions.
- State what the brief authorizes and what it does not authorize: implementation choices, scope expansion, unresolved authority decisions, stale memory, unverified graph edges, and unrun validation.
- If evidence is unavailable, name the blocked owner or the minimum safe slice; do not silently convert the gap into an assumption.
