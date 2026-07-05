# Technology Stack Evidence Patterns

Use this reference when a stack decision depends on current repository graph, project memory, execution trajectory, official support policy, validation freshness, tool permission boundaries, or residual-risk wording. Keep it as an evidence map, not a technology catalog.

## Stack Decision-To-Evidence Map

| Decision claim | Minimum evidence | What it proves | What it does not prove |
| --- | --- | --- | --- |
| Existing stack is sufficient | approved-stack inventory, repository graph, owner, current constraints, cost comparison, and rejected novelty path | The known stack can satisfy the inspected scope | Future growth, every consumer, or all deployment targets are covered |
| New stack is justified | hard constraint, rejected existing option, TCO estimate, owner acceptance, support policy, validation map, and exit path | The new stack has a concrete reason and owned risk | Long-term hiring, all incidents, or every transitive dependency is solved |
| Project memory or ADR still applies | source/date/owner, current graph delta, workload match, support policy status, accepted/rejected assumptions | A historical decision remains usable for the inspected scope | Roadmap, price, EOL, workload, or generated summaries stay current |
| Performance or scale claim is valid | workload axis, data volume, traffic shape, benchmark/load plan or report, target SLO, and residual risk | The claim was tested or can be tested against the named workload | Production p99, all tenants, or future volume are proven |
| Supply-chain posture is acceptable | dependency/license scan, package manager integrity, maintainer/vendor status, CVE process, OpenSSF/SLSA/Scorecard or equivalent | Ecosystem risk was inspected for selected candidates | Every future release or transitive package remains safe |
| Reversibility is acceptable | class, exit estimate, migration/coexistence plan, rollback trigger, owner, and re-evaluation date | The team understands exit cost and trigger | Exit will be cheap or incident-free |

## Graph, Memory, And Execution Reconciliation

- Treat approved-stack inventory, repository graph, old ADRs, generated summaries, templates, benchmark posts, and project memory as leads until current source, official support policy, owner acceptance, and validation evidence confirm them.
- Mark stack evidence stale after changes to workload, support policy, package manager, generated clients, build/deploy lanes, container base, cloud quota, pricing, data volume, or validation command order.
- Record inspected and skipped boundaries: source paths, runtime versions, package managers, build/deploy files, generated artifacts, ADRs, ownership docs, support policy, CI evidence, and release gates.
- Map each accepted stack claim to a source path, command/report, owner approval, official policy source/date, or explicit not-verified residual risk.

## Tool Permission Boundary

| Action | Boundary record |
| --- | --- |
| Local repository, registry, ADR, or report reads | Read-only local shell; cite searched paths and avoid full output dumps. |
| Local build, test, benchmark, dependency scan, or generated report | State-mutating only for caches, reports, dist, generated output, or lockfiles; cite command, exit code, artifact path, sandbox, and rollback. |
| External support-policy, package registry, hiring-market, vulnerability, or pricing lookup | Network data-read; cite source, retrieval date, freshness limit, and unavailable sources. |
| Production telemetry, incident logs, cloud accounts, package credentials, or customer data | High-risk data-read or write; require owner, bounded scope, redaction, retention, and not-production-equivalent residual risk. |

## Handoff Evidence Shape

```yaml
technology_stack_evidence_closure:
  decision_scope: ""
  inspected_boundaries: []
  selected_option: ""
  rejected_options: []
  accepted_prior_claims: []
  rejected_or_stale_claims: []
  stack_to_validation_map: []
  support_policy_sources: []
  reversibility:
    class: ""
    exit_estimate: ""
    rollback_or_migration_trigger: ""
  tool_permission_boundary:
    action_class: ""
    sandbox: ""
    state_mutation: ""
    redaction: ""
  what_remains_unproved: []
  residual_stack_risk: []
  next_gate: ""
```

## Blocking Conditions

Block approval when a stack is selected from preference without current constraints, an existing approved stack was not compared, project memory is reused without graph confirmation, ownership is missing, support policy lacks source/date, TCO excludes operational tax, supply-chain posture lacks scan or integrity review, reversibility is unknown, or artifact-writing commands lack write-scope and rollback disclosure.
