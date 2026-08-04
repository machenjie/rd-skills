# Documentation Output And Gates

Use this reference when `change-documentation-gate` needs deeper output structure than the main `SKILL.md` should carry. Keep the body focused on routing, mode selection, and evidence; use this file for artifact-specific documentation closure.

## Artifact Decision Matrix

| Artifact | Load when | Required closure |
| --- | --- | --- |
| README or developer guide | Setup, local workflow, feature usage, dependency, or command behavior changes. | Before/after behavior, command or example freshness, owner, and reviewed path. |
| API or schema docs | Endpoint, event, SDK, CLI, error, config, or generated contract changes. | Spec path, changed fields, compatibility stance, migration note, and consumer owner. |
| Migration guide | Upgrade, schema migration, deprecation, rollout, rollback, or compatibility branch changes. | Who is affected, pre-upgrade action, post-upgrade action, rollback, and deadline. |
| Runbook or troubleshooting | Alert, SLO, dashboard, operational dependency, support flow, or failure mode changes. | Trigger, impact, triage steps, expected output, escalation, and validation command. |
| ADR | Architecture decision is hard to reverse or changes team-level constraints. | Status, context, decision, rejected alternatives, consequences, owner, and supersession rule. |
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
  - artifact: ""
    audience: user | operator | api_consumer | developer | auditor | release_owner
    status: updated | not_required | outstanding
    rationale: ""
    validation: ""
    owner: ""
    release_blocking: true
```

## Gate-Specific Checks

- **API docs**: when an API or schema documentation surface is affected, reconcile its public shape and error model with final source and contract tests. Also reconcile examples, applicable rate limits, generated-client impact, and deprecation policy. List unverified dimensions or consumers.
- **Migration docs**: document the executable recovery path available to the named audience—rollback, restore, forward repair, or containment—with commands or steps and expected outcomes; a bare "run migration" instruction is insufficient.
- **Runbooks**: each step needs an observation, command/query/dashboard, expected result, and escalation when the result differs.
- **ADRs**: record alternatives before implementation when possible, with evidence limits stated for any retroactive ADR.
- **Release notes**: write in audience language, group by `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, or `Security`, and avoid commit-log dumps.
- **Compliance evidence**: record control owner, evidence owner, exception owner, freshness date, approval source, retention period, and storage path.
## Anti-Patterns To Reject

- Public docs expose internal service names, IPs, tokens, provider error bodies, or tenant-sensitive detail.
- Migration docs omit rollback, compatibility window, owner, or validation command.
- Runbook says "check logs" without query, dashboard, expected signal, or escalation.
- Changelog says "miscellaneous fixes" for behavior that affects users or API consumers.
- ADR records only the chosen decision and omits rejected alternatives or consequences.
- No-docs decision cites "internal refactor" without inspecting affected audiences and docs.
## Handoff Closure
Close with updated/not-required/outstanding artifacts, audience owners, validation evidence, safe-disclosure review, release-block status, evidence limits, residual risk, and recommended next step.
