# Documentation Output And Gates

Use this reference when reader-task organization or artifact-specific closure needs more detail than the root contract. Apply only the affected rows and checks; a small edit needs no matrix or additional approval process.

## Reader Task

- For action, organize by the reader's steps and expected results, with prerequisites and recovery where needed.
- For understanding, organize by causal relationships, constraints, and consequences.
- For lookup, use stable names, fields, units, and version boundaries so readers can find an exact value or rule.

## Artifact Decision Matrix

| Artifact | Load when | Required closure |
| --- | --- | --- |
| README or developer guide | Creating or editing setup, local workflow, feature usage, dependency, or command guidance. | Source path and applicable command/example freshness; before/after behavior only for a behavior change. |
| API or schema docs | Creating or maintaining endpoint, event, SDK, CLI, error, config, or generated contract guidance. | Source/spec path and documented fields; compatibility, migration, and consumer impact when affected. |
| Migration guide | Upgrade, schema migration, deprecation, rollout, rollback, or compatibility branch changes. | Who is affected, pre/post-upgrade actions, rollback or validated alternative recovery with rollback limits, and deadline. |
| Runbook or troubleshooting | Creating or maintaining operational guidance for alerts, SLOs, dependencies, support flows, or failure modes. | Trigger, impact, triage steps, expected output, escalation, and validation evidence for the affected procedure. |
| ADR | Recording or updating an accepted architecture decision; unresolved decisions stay with the architecture owner. | Status, context, decision, rejected alternatives, consequences, owner, and supersession rule. |
| Changelog or release notes | External or operator-visible behavior changes before release. | Audience-specific category, user impact, migration link if needed, and release owner. |
| Incident or compliance packet | Customer impact, control evidence, exception, security posture, or audit trail changes. | Timeline, control objective, evidence owner, approval source, freshness, and retention. |

## No-Docs Decision Pattern

```yaml
no_docs_decision:
  changed_surface: ""
  inspected_artifacts:
    - {path: "", audience: "", reason_not_affected: ""}
  behavior_delta: none | internal_only | already_documented
  evidence: {command_or_review: "", exit_code_or_status: ""}
  residual_risk: ""
  owner: ""
```

## Documentation Matrix Pattern

```yaml
documentation_matrix:
  - {artifact: "", audience: "", status: updated | not_required | outstanding,
     rationale: "", validation: "", owner: "", release_blocking: false}
```

## Gate-Specific Checks

- **API docs**: when an API or schema documentation surface is affected, reconcile its public shape and error model with final source and contract tests. Also reconcile examples, applicable rate limits, generated-client impact, and deprecation policy. List unverified dimensions or consumers.
- **Migration docs**: document the executable recovery path available to the named audience—rollback, restore, forward repair, or containment—with commands or steps and expected outcomes; a bare "run migration" instruction is insufficient.
- **Runbooks**: each operational step needs an observation or action, expected result, and escalation when the result differs; preserve these when editing the procedure.
- **ADRs**: record alternatives before implementation when possible, with evidence limits stated for any retroactive ADR.
- **Release notes**: write in audience language, group by `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, or `Security`, and avoid commit-log dumps.
- **Compliance evidence**: record control owner, evidence owner, exception owner, freshness date, approval source, retention period, and storage path.
## Anti-Patterns To Reject

- Public docs expose internal service names, IPs, tokens, provider error bodies, or tenant-sensitive detail.
- Migration docs omit compatibility windows or the applicable recovery evidence above.
- Runbook says "check logs" without query, dashboard, expected signal, or escalation.
- Changelog says "miscellaneous fixes" for behavior that affects users or API consumers.
- No-docs decision cites "internal refactor" without inspecting audiences and docs, or dismisses an explicit documentation request because runtime behavior is unchanged.
## Handoff Closure
Close with changed artifacts, source mapping, validation evidence and limits. Include outstanding affected docs, audience owners, release blocks, disclosure review, or next steps when the task actually needs them.
