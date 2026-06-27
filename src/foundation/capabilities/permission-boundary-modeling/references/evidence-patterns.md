# Permission Boundary Evidence Patterns

Use this reference when permission-boundary closure depends on repository graph, project memory, execution trajectory, generated contracts, validation freshness, same-pattern scans, tool permission boundaries, or production evidence limits. Keep it as an evidence map, not a second authorization tutorial.

# Permission Change-To-Evidence Map

| Permission claim | Minimum evidence | What it proves | What it does not prove |
| --- | --- | --- | --- |
| Object read is tenant/owner scoped | Current route, service method, repository query or policy point, server-derived subject/tenant source, and wrong-tenant/wrong-owner denial test | The inspected read cannot bypass object-level scope through that path | Alternate routes, jobs, reports, caches, or direct SQL paths are covered |
| Mutation is backend-enforced | Service/controller enforcement point, object ownership source, lifecycle condition source, positive case, denied case, and audit assertion when high risk | The inspected mutation checks trusted permission inputs before state change | Every mutation variant, admin override, or retry path is safe |
| List/search/export is source-filtered | Query predicate, pagination/count behavior, export builder, generated contract, and cross-tenant fixture | The inspected collection path restricts visible data before pagination/export | Timing leakage, downstream BI/reporting, or materialized view paths are proven |
| Bulk operation authorizes every object | Bulk request contract, per-object decision loop or all-or-nothing query, partial-failure semantics, and mixed-tenant test | The inspected bulk path cannot mutate/export unauthorized objects silently | Very large batches, async continuation, or replay behavior is fully covered |
| Support/admin access is bounded | Actor role, ticket/purpose binding, time box or step-up/approval rule, diagnostic-vs-mutation split, and audit event | The inspected privileged flow has purpose, scope, and traceable use | Human process compliance or all support tools are covered |
| Service account is least-privilege | Credential owner, resource/action/tenant/run scope, rotation/review owner, policy diff, and job/webhook audit sample | The inspected machine identity is scoped to named work | Credential compromise blast radius is eliminated or every worker path is tested |
| Denial behavior avoids enumeration | 401/403/404 taxonomy, safe client message, internal reason code, response fixture, and log/audit field check | The inspected denial path does not reveal invisible resource existence | All localization, SDK, or gateway transformations preserve the behavior |
| Memory/graph claim is current | Prior claim source/date, current route/policy/test/source reread, generated contract check, validation command, exit code, and report/artifact path | The accepted memory or graph still matches the inspected permission boundary | Future edits, unknown entry points, or production policy state are covered |

# Graph, Memory, And Execution Reconciliation

- Treat repository graph, project memory, audit notes, generated clients, old policy matrices, previous reviews, and compaction summaries as selectors until current source and validation confirm them.
- Accept a prior "permission check exists", "tenant filter is applied", "support is read-only", "service account is scoped", or "denial is safe" claim only when current routes, services, repositories, policies, tests, generated contracts, and audit fields still match.
- Mark evidence stale after edits to routes, resolvers, controllers, services, repositories, policy files, schemas, generated clients, jobs, event consumers, support/admin tools, service account scopes, audit schemas, fixtures, reports, or validation commands.
- Record inspected and skipped boundaries: HTTP/API routes, GraphQL/RPC, CLI/admin/support tools, import/export, search/reporting, background jobs, message consumers, webhooks, repositories, caches, object storage, generated clients, policy-as-code, audit sinks, and tests.
- Map every final authorization confidence claim to a current command, source path, fixture, response sample, audit sample, report artifact, owner review, or explicit not-verified residual risk.

# Tool Permission Boundary

| Action | Boundary record |
| --- | --- |
| Local source reads, registry search, route/policy grep, same-pattern scan, and report inspection | Read-only local shell action; cite paths and searched patterns, avoid dumping secrets or full payloads |
| Local validators, authorization tests, generated-client checks, and synthetic wrong-tenant fixtures | State-mutating only for reports, caches, temp files, or local fixtures; cite command, exit code, artifact/report path, sandbox, and cleanup |
| Production permission probe, audit-log export, telemetry query, or support/admin sample | High-risk data-reading action; require owner, bounded query, redaction, timestamp, dataset, and no-secret disclosure |
| Role grant, service-account change, support override, policy deploy, or rollback | High-risk write/release action; require explicit permission, dry-run where available, rollback/forward-fix path, owner, and redaction rule |

# Handoff Evidence Shape

```yaml
permission_boundary_evidence_closure:
  inspected_boundaries:
    - boundary: ""
      current_source_or_artifact: ""
      finding: ""
  accepted_prior_claims:
    - claim: ""
      current_evidence: ""
      freshness: ""
  rejected_or_stale_claims:
    - claim: ""
      reason: ""
  permission_to_validation_map:
    - permission_decision: ""
      source_path_or_artifact: ""
      command_or_gate: ""
      exit_code_or_status: ""
      proves: ""
      does_not_prove: ""
      owner: ""
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
