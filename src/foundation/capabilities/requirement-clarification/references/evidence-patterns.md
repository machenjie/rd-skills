# Requirement Clarification Evidence Patterns

Use this reference when clarification closure depends on current-source proof, repository graph, project memory, execution trajectory, validation freshness, forbidden-artifact scans, tool permission boundaries, or evidence limits. Keep it as an evidence map, not a second clarification tutorial.

## Clarification-To-Evidence Map

| Clarification claim | Minimum evidence | What it proves | What it does not prove |
| --- | --- | --- | --- |
| Current behavior is known | Source path, doc/test/generated artifact, report, command output, or owner record inspected after the latest relevant edit. | The inspected boundary currently behaves or is specified as claimed. | Production-only data, unknown consumers, or uninspected routes match the claim. |
| Stakeholder claim is usable | Source, owner, scope, date/trigger, verification needed, and downstream gate recorded. | The claim can be carried as an explicit stakeholder assumption. | The claim is verified fact or safe for authority-owned behavior. |
| Blocking decision is valid | Question category, owner, decision shape, affected surface, and why answer can change contract/data/permission/release behavior. | Implementation would otherwise make an authority decision. | The owner will answer or the answer will be compatible. |
| Non-blocking decision is safe | Safe default, isolation method, not-present check, follow-up owner, expiry or trigger, and residual risk. | Work can proceed inside the named safe slice. | Adjacent work, public behavior, or later implementation will stay inside the slice without review. |
| Graph or memory claim is accepted | Current source, registry/config/docs, tests, generated artifacts, or report confirms the graph/memory lead. | The lead is current enough for this clarification boundary. | Memory alone proves product intent or all runtime callers. |
| Partial proceed is bounded | Can-implement-now list, must-wait list, forbidden assumptions/artifacts, owner response path, and review gate. | The approved safe slice is separated from blocked work. | The final implementation cannot drift into blocked work without a not-present scan. |
| Validation map is fresh | Each question, assumption, evidence claim, safe default, and forbidden artifact maps to a command, review check, owner answer, or residual risk. | Closure evidence matches the final clarification record. | Later edits, unrun validators, or unavailable telemetry are covered. |

## Graph, Memory, And Execution Reconciliation

- Treat repository graph, project memory, old ticket comments, previous validations, generated artifacts, and execution trajectory as leads until current source confirms them.
- Accept a prior "requirement already decided", "route exists", "consumer does not depend on it", "permission is admin-only", or "data shape is clean" claim only when current source, owner records, reports, tests, generated artifacts, or telemetry still match.
- Reject or downgrade memory when it is undated, lacks owner, conflicts with current source, predates schema/generated/report changes, or names no validation path.
- Record execution trajectory when an agent already attempted diagnosis, asked questions, skipped a gate, or validated before the final clarification edit.
- Mark validation stale after edits to requirements, source files, tests, generated artifacts, reports, registries, docs, build/install outputs, or owner decisions.

## Forbidden-Artifact Checks

Use a not-present scan when partial proceed is allowed:

| Forbidden artifact | Example check |
| --- | --- |
| Public contract change | API/schema/generated client diff, export surface search, route table search. |
| Data or migration behavior | Migration directory search, model/schema diff, data-retention owner note. |
| Permission or tenant behavior | Auth policy search, denied-case acceptance, security gate handoff. |
| Release or rollout behavior | Flag/config/deploy script search, release gate handoff. |
| Hidden implementation of blocked work | Changed-path review, task diff, tests/docs scan for blocked term. |

## Tool Permission Boundary

| Action | Boundary record |
| --- | --- |
| Local source, report, graph, and registry inspection | Read-only local shell; cite inspected paths and avoid full output dumps. |
| Local validators, report generation, build, and install checks | Local-write only to reports, caches, dist, or build artifacts; cite command, exit code, log path, and freshness. |
| Owner record, ticket, telemetry, connector, or production-data lookup | Connector or data-scoped action; record account/data boundary, redaction rule, retention, and unavailable evidence. |
| Cleanup, migration, deploy, or external write | High-risk action; require owner approval, dry-run when available, rollback or compensation path, and stop condition. |

## Closure Shape

```yaml
requirement_clarification_evidence_closure:
  inspected_boundaries:
    - boundary: ""
      current_source_or_report: ""
      finding: ""
  accepted_prior_claims:
    - claim: ""
      current_evidence: ""
  rejected_or_stale_claims:
    - claim: ""
      reason: ""
  clarification_to_validation_map:
    - item: ""
      evidence_or_validator: ""
      exit_code_or_status: ""
      proves: ""
      does_not_prove: ""
      owner: ""
      freshness: ""
  forbidden_artifact_checks:
    - artifact: ""
      check: ""
      outcome: ""
  tool_permission_boundary:
    action_class: ""
    sandbox: ""
    state_mutation: ""
    redaction: ""
  residual_risk:
    - risk: ""
      owner: ""
      next_gate: ""
```
