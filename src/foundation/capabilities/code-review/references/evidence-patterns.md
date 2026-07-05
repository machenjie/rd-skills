# Code Review Evidence Patterns

Use this reference when code-review closure depends on finding-to-fix traceability, explicit non-findings, stale validation, repository graph, project memory, API hallucination proof, accepted finding accountability, or re-review evidence. Keep it as an evidence map, not a second review taxonomy.

## Review Claim To Evidence Map

| Review claim | Minimum evidence | What it proves | What it does not prove |
| --- | --- | --- | --- |
| Spec compliance passed | Requirement/non-goal/plan excerpt, inspected diff boundary, changed behavior map, old-behavior preservation note, and fresh validation status | The review checked the named requested behavior before code-quality approval | Unstated product expectations, downstream consumers, or later edits are covered |
| Finding is valid | Finding id, severity, file/line or logical unit, evidence excerpt, impact, reproduction or reasoning, required remediation, and test gap | The defect is actionable and severity-calibrated for the inspected change | All similar defects in the repo were found unless same-pattern scan is listed |
| High-risk surface has no finding | Surface name, inspected files/callers/config, checklist or review method, validation command or manual result, and evidence limits | The named surface was checked and no issue was found in the inspected scope | Uninspected routes, generated code, runtime config, or future edits are safe |
| AI/API/dependency call is real | Source or lockfile search, dependency version, local docs or type/build result, generated-client status, and unresolved scope | The inspected API/config/key/flag exists for the current project dependency graph | Runtime provider behavior, undocumented feature semantics, or future version drift is proven |
| Finding was repaired | Finding id, fix diff path, re-review scope, validation command, exit code/status, and residual risk | The named finding was addressed and re-reviewed after the fix | Other findings or unrelated changed files are approved |
| Finding was accepted | Finding id, severity, owner, ticket/reference, expiration or release consequence, and explicit approval boundary | The risk was consciously accepted with accountability | The accepted defect is safe or no longer needs monitoring |

## Evidence Quality Labels

- **Strong evidence**: current requirement, final diff, source/config/lock/generated files inspected, command or artifact named, exit code or manual status recorded, final-edit freshness stated, and proof limits named.
- **Weak evidence**: old CI output, one-file diff glance, unverified memory, generic checklist statement, typecheck without behavior mapping, or style-only comments on a behavior change.
- **Missing evidence**: no requirement, no changed-code-to-test map, no high-risk non-findings, no validation command/status, no line evidence, no re-review after fix, or no owner for accepted risk.
- **Invalid evidence**: "LGTM", author-only self-review for high-risk change, hallucinated API accepted without source proof, stale validation after final edit, or inaccessible report.

## Handoff Evidence Shape

```yaml
code_review_evidence_closure:
  reviewed_requirement:
    source: ""
    result: pass | fail | partial | not_available
  inspected_boundaries:
    - path_or_surface: ""
      finding_or_non_finding: ""
  findings:
    - finding_id: ""
      severity: critical | high | medium | low
      evidence: ""
      fix_or_acceptance: ""
      re_review_status: open | resolved | accepted_with_ticket | not_run
  validation_map:
    - changed_surface: ""
      command_or_artifact: ""
      exit_code_or_status: ""
      proves: ""
      does_not_prove: ""
      freshness: fresh | stale | partial | not_run
  explicit_non_findings:
    - surface: ""
      evidence: ""
      limits: ""
  residual_risk:
    - risk: ""
      owner: ""
      next_gate: ""
```
