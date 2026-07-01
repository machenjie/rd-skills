# Language Runtime Evidence Patterns

Use this reference when a runtime decision depends on current repository graph, project memory, execution trajectory, validation freshness, support-policy evidence, tool permission boundaries, or residual-risk wording. Keep it as an evidence map, not a language comparison guide.

## Runtime Decision-To-Evidence Map

| Decision claim | Minimum evidence | What it proves | What it does not prove |
| --- | --- | --- | --- |
| Existing runtime is sufficient | Runtime inventory, package managers, build lanes, deploy artifacts, supported versions, owner, and current workload constraints | The current stack can satisfy the named decision scope | Future workload growth, all consumers, or every platform target is covered |
| New runtime is justified | Rejected existing-runtime option, workload axis, hard constraint, operational tax, owner acceptance, build/deploy lane diff, and exit path | The added runtime has a concrete product or engineering reason | Team fluency, long-term hiring, or all incident tooling is solved |
| Project memory still applies | Prior ADR or benchmark source, date, owner, workload match, graph delta, support policy status, and accepted/rejected assumptions | A historical decision remains usable for the inspected scope | Future roadmap, changed traffic mix, or stale generated summaries are safe |
| Lifecycle horizon is acceptable | Official support policy source and date, LTS/EOL/MSRV/vendor horizon, exception owner, migration trigger, and retirement date if needed | The runtime can be supported for the declared horizon | Ecosystem packages, container base images, or transitive tooling remain supported |
| Workload fit is validated | Dominant and secondary workload axes, SLOs, benchmark/profile/load plan, runtime behavior table, and selected validation command | The candidate is tested or testable against the named workload | Production p99, all dependency latency, or all tenant mixes are proven |
| Supply-chain posture is acceptable | Package manager integrity model, dependency scan, lockfile policy, license posture, OpenSSF/SLSA/Scorecard or equivalent, and install-script side-effect review | The ecosystem risk was inspected for the selected runtime | Every transitive package or future release remains safe |
| Cross-language boundary is safe | Boundary inventory, schema/runtime validation location, generated-client source, contract test command, consumer impact, and rollback path | Runtime choice preserves the named boundary contract | Every downstream consumer or manual integration is validated |

## Graph, Memory, And Execution Reconciliation

- Treat old ADRs, project memory, generated summaries, benchmark posts, and survey data as leads until current source, repository graph, official support policy, and fresh validation confirm them.
- Mark runtime evidence stale after changes to build lanes, package managers, generated clients, deploy artifacts, container/serverless shape, workload SLOs, benchmark harnesses, support-policy dates, or validation commands.
- Record inspected and skipped boundaries: runtime versions, package managers, toolchains, build/deploy files, generated clients, cross-language APIs, ownership docs, ADRs, CI evidence, and release gates.
- Map each accepted runtime claim to a source path, command/report, official policy source/date, owner approval, or explicit not-verified residual risk.

## Tool Permission Boundary

| Action | Boundary record |
| --- | --- |
| Local source reads, registry search, ADR/doc inspection, and report review | Read-only local shell action; cite searched paths and avoid full output dumps |
| Local build, test, typecheck, benchmark, dependency scan, or container build | State-mutating only for caches, reports, lockfiles, generated output, build artifacts, or container layers; cite command, exit code, artifact path, sandbox, write scope, and rollback |
| External support-policy, ecosystem, hiring, package registry, or vulnerability lookup | Network data-reading action; cite source, retrieval date, freshness limit, and any unavailable source |
| Production telemetry, profile, incident log, or package registry credential use | High-risk data-reading action; require owner, bounded scope, redaction, retention, and not-production-equivalent residual risk |

## Handoff Evidence Shape

```yaml
language_runtime_evidence_closure:
  runtime_decision_scope: ""
  inspected_boundaries: []
  accepted_prior_claims: []
  rejected_or_stale_claims: []
  decision_to_validation_map: []
  support_policy_sources: []
  tool_permission_boundary:
    action_class: ""
    sandbox: ""
    state_mutation: ""
    redaction: ""
  what_remains_unproved: []
  residual_runtime_risk: []
  next_gate: ""
```

## Blocking Conditions

Block completion when a runtime is selected from preference without workload evidence, a new language lacks owner and deploy/build lane proof, project memory is reused without current graph confirmation, lifecycle support lacks official source/date, supply-chain posture lacks scan or integrity evidence, cross-language boundaries lack contract validation, or artifact-writing commands lack write-scope and rollback disclosure.
