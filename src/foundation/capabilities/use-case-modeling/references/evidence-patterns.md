# Use Case Modeling Evidence Patterns

Use this reference when use-case closure depends on current repository graph, project memory, execution trajectory, stakeholder-owned docs, tests, validation freshness, or tool permission boundaries. Keep it as an evidence map, not a second use-case tutorial.

## Use-Case Claim-To-Evidence Map

| Use-case claim | Minimum evidence | What it proves | What it does not prove |
| --- | --- | --- | --- |
| Actor-goal boundary is current | Current source, docs, tests, route/job/webhook entry point, actor role, goal statement, rejected combined goals, and owner | The inspected behavior has one primary actor and one goal | Other actors, UI navigation, or downstream scenarios are fully modeled |
| Preconditions are enforced gates | Enforcement point, permission or lifecycle guard, fixture or test path, and denied/prerequisite outcome | The inspected use case cannot start unless the listed gates hold | Every caller, client, job, or external integration enforces the same gates |
| Main path matches current behavior | Source/test/doc path, sequence of observable domain steps, durable state/event side effect, and validation command or report | The described path matches the inspected current implementation or accepted design source | Production-only behavior, unavailable stakeholder decisions, or future implementation work is correct |
| Alternate path has defined outcome | Alternate trigger, preserved data, retry/continue rule, postcondition, and acceptance or test trace | The alternate path does not end in vague UI-only behavior | Exhaustive scenario coverage or state-machine legality is complete |
| Failure path has minimal guarantee | Failure trigger, terminal or recoverable state, compensation/retry owner, support/audit visibility, and validation or residual-risk owner | The system promise when the actor goal fails is explicit | Recovery automation, live provider behavior, or operational runbook execution is proven |
| External/system actor is modeled | Actor identity, authentication/trust boundary, idempotency or duplicate rule, timeout/replay behavior, and terminal outcome | The background trigger is visible as actor-facing product behavior | Full integration reliability, provider SLA, or security review is complete |
| Business rule and acceptance trace are linked | Rule id/source, use-case path step, acceptance criterion id, test/validator/report path, and owner | The use case can drive acceptance or implementation handoff | All rule variants, UI states, or downstream consumers are covered |
| Memory/graph/execution claim is current | Prior claim source/date, current source/test/doc reread, graph delta, accepted/rejected mismatch, command, exit code, and report path | The accepted prior evidence still matches the inspected use case boundary | Future edits, dynamic callers, or uninspected production data remain safe |

## Graph, Memory, And Execution Reconciliation

- Treat repository graph, project memory, old requirements, generated summaries, prior acceptance traces, and execution trajectory as selectors until current source, tests, docs, registry entries, or stakeholder-owned artifacts confirm them.
- Accept a prior "use case exists", "precondition already enforced", "alternate path covered", "failure path is handled", or "acceptance trace is complete" claim only when current paths and fresh validation still match.
- Mark evidence stale after edits to requirements, source, tests, docs, policy files, schemas, generated clients, route/job/webhook entry points, fixtures, reports, validation commands, or acceptance traces.
- Record inspected and skipped boundaries: primary actor, secondary actors, UI entry point, API route, service method, job, webhook, durable state, emitted event, side effect, business rule source, acceptance criteria, tests, docs, and registry.
- Map every final use-case confidence claim to a current command, source path, test path, doc section, rule id, report artifact, owner review, or explicit not-verified residual risk.

## Tool Permission Boundary

| Action | Boundary record |
| --- | --- |
| Local source/doc/test reads, graph search, report inspection, and markdown validation | Read-only local shell action; cite paths and searched patterns, avoid full output dumps |
| Local validators, acceptance/test commands, build checks, and generated report refresh | State-mutating only for reports, caches, temp files, dist/build artifacts, or local fixtures; cite command, exit code, artifact path, sandbox, and cleanup |
| Stakeholder document export, production behavior sample, telemetry query, or connector read | High-risk or external data-reading action; require owner, bounded scope, redaction, timestamp, and evidence-limit disclosure |
| Requirement, acceptance, API contract, policy, or workflow source update | State-mutating product-design action; record owner, diff, rollback/revert path, validation map, and downstream handoff |

## Handoff Evidence Shape

```yaml
use_case_modeling_evidence_closure:
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
  use_case_to_validation_map:
    - use_case_or_path: ""
      actor_goal_boundary: ""
      source_path_or_artifact: ""
      acceptance_or_test_trace: ""
      command_or_report: ""
      exit_code_or_status: ""
      proves: ""
      does_not_prove: ""
      owner: ""
  tool_permission_boundary:
    action_class: ""
    sandbox: ""
    state_mutation: ""
    redaction: ""
  residual_use_case_risk:
    - risk: ""
      owner: ""
      next_gate: ""
```

## Blocking Conditions

Block closure when actor and goal are merged across multiple use cases, preconditions are not enforced gates, postconditions are UI-only, alternate or failure paths lack durable outcomes, external/system actors are implicit, memory or graph evidence is reused without current-source confirmation, validation predates the final use-case edit, or state-mutating validation lacks permission/sandbox and rollback disclosure.
