# Extensibility Evidence Patterns

Use this reference when extensibility closure depends on repository graph, project memory, execution output, validation freshness, tool permission boundaries, compatibility claims, or evidence limits. Keep it as an evidence map, not a second extensibility tutorial.

## Extension-To-Validation Map

| Extension claim | Minimum evidence | What it proves | What it does not prove |
| --- | --- | --- | --- |
| Variation is real | Current implementer/caller graph, source paths, docs/tests, generated artifacts, or dated roadmap owner. | The inspected variation exists now or has a named committed owner/date. | Future adoption, hidden external consumers, or uninspected branches will need the same interface. |
| Contract is narrow and versioned | Interface/schema/payload diff, public/private boundary, compatibility class, version/deprecation rule. | The inspected contract has stable inputs, outputs, errors, lifecycle, and change policy. | External implementers not in the graph are compatible. |
| Core invariants remain core-owned | Invariant list, read-only view or command/result boundary, bypass denial test or review artifact. | Inspected extensions cannot directly bypass named core rules. | All future invariants or uninspected privileged paths are covered. |
| Extension input is bounded | Schema, allowlist, sanitization, SSRF/injection denial, redaction rule, and malformed input test. | Inspected extension data has a validation boundary before use. | Every parser, template, SQL, shell, queue, or outbound request path is safe if uninspected. |
| Sandbox is commensurate with privilege | In-process/out-of-process/webhook/config boundary, network/FS/DB/API policy, and owner approval. | The selected isolation class matches inspected extension privileges. | Runtime platform enforcement or production tenant behavior is proven without execution evidence. |
| Compatibility change is controlled | Old/new implementer test, migration/deprecation note, consumer inventory, release/rollback handoff. | Inspected consumers have a planned compatibility path. | Unknown consumers, stale generated clients, or later contract edits remain safe. |
| Observability is sufficient | Trace/log/metric fields per extension ID/version/tenant/result/error/duration with redaction. | Inspected failures can be attributed to extension and owner. | Production dashboards, alert thresholds, or incident runbooks are complete unless inspected. |
| Cleanup is safe | Caller search, telemetry or not-present evidence, docs/generated artifact scan, rollback/removal owner. | Inspected references no longer depend on the extension point. | Private forks, manual integrations, or dormant external users are absent. |
| Validation is fresh | Command, validator, exit code, output summary, artifact/report path, and final-edit timestamp. | Evidence was produced after the inspected source/config/generated changes. | Later edits, environment drift, or unrun validators are covered. |

## Graph, Memory, And Execution Reconciliation

- Treat repository graph, project memory, old roadmap notes, generated docs, previous validation reports, and execution traces as discovery inputs until current source confirms them.
- Accept prior "future provider", "plugin user", "tenant variation", "callback contract", or "feature flag is still used" claims only when current callers, implementers, config, tests, generated artifacts, or owner records still match.
- Reject or downgrade memory when it is undated, lacks owner, conflicts with current graph, names no implementer, or predates contract/schema/generated changes.
- Mark evidence stale after edits to extension interfaces, config schemas, generated artifacts, registry entries, docs, tests, release flags, sandbox policy, validators, or build/install outputs.
- Map every final extension-safety claim to a command, test, validator, report, diff, review artifact, owner approval, or explicit not-run residual risk.

## Tool Permission Boundary

| Action | Boundary record |
| --- | --- |
| Local source reads, graph search, report inspection, markdown validation | Read-only local shell action; cite searched paths and avoid full output dumps. |
| Local validators, tests, builds, content-size checks, and install validation | State-mutating only for generated reports/dist/build artifacts; cite log path, command, and exit code. |
| Local code generation, fixture generation, or contract regeneration | State-mutating development action; record source-of-truth input, generated output owner, cleanup, and diff review. |
| Sandbox, webhook, network, secret, cloud, deploy, migration, or rollback command | High-risk action; require permission, dry-run/rendered diff when available, rollback/forward-fix path, redaction rule, and stop condition. |
| Telemetry, dashboard, audit, or connector export | Read-only or connector-scoped; redact tenant/user/secret-bearing values and state retention limits. |

## Handoff Evidence Shape

```yaml
extensibility_evidence_closure:
  inspected_paths:
    - path: ""
      finding: ""
  accepted_prior_claims:
    - claim: ""
      current_evidence: ""
  rejected_or_stale_claims:
    - claim: ""
      reason: ""
  extension_to_validation_map:
    - extension_point: ""
      variation_proof: ""
      compatibility_validator: ""
      invariant_or_security_validator: ""
      failure_or_performance_validator: ""
      command: ""
      exit_code: ""
      artifact_or_report: ""
      proves: ""
      does_not_prove: ""
      owner: ""
      next_gate: ""
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
