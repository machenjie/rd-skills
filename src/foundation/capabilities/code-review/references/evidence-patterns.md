# Code Review Evidence Patterns

Use this reference when code-review closure depends on finding-to-fix traceability, explicit non-findings, stale validation, repository inspection, prior task evidence, API hallucination proof, accepted finding accountability, or re-review evidence. Keep it as an evidence map, not a second review taxonomy.

## Review Claim To Evidence Map

| Review claim | Minimum evidence | What it proves | What it does not prove |
| --- | --- | --- | --- |
| Spec compliance passed | Requirement/non-goal/plan excerpt, inspected diff boundary, changed behavior map, old-behavior preservation note, and fresh validation status | The review checked the named requested behavior before code-quality approval | Unstated product expectations, downstream consumers, or later edits are covered |
| Finding is valid | Finding description and location, severity, file/line or logical unit, evidence excerpt, impact, reproduction or reasoning, required remediation, and test gap | The defect is actionable and severity-calibrated for the inspected change | All similar defects in the repo were found unless same-pattern scan is listed |
| High-risk surface has no finding | Surface name, inspected files/callers/config, checklist or review method, validation command or manual result, and evidence limits | The named surface was checked and no issue was found in the inspected scope | Uninspected routes, generated code, runtime config, or future edits are safe |
| AI/API/dependency call is real | Source or lockfile search, dependency version, local docs or type/build result, generated-client status, and unresolved scope | The inspected API/config/key/flag exists for the current project dependency graph | Runtime provider behavior, undocumented feature semantics, or future version drift is proven |
| Finding was repaired | Finding description and location, fix diff path, re-review scope, validation command, exit code/status, and residual risk | The named finding was addressed and re-reviewed after the fix | Other findings or unrelated changed files are approved |
| Finding was accepted | Finding description and location, severity, owner, ticket/reference, expiration or release consequence, and explicit approval boundary | The risk was consciously accepted with accountability | The accepted defect is safe or no longer needs monitoring |

## Evidence Quality Labels

- **Strong evidence**: current requirement, final diff, source/config/lock/generated files inspected, command or artifact named, exit code or manual status recorded, final-edit freshness stated, and proof limits named.
- **Weak evidence**: old CI output, one-file diff glance, unverified memory, generic checklist statement, typecheck without behavior mapping, or style-only comments on a behavior change.
- **Missing evidence**: no requirement, no changed-code-to-test map, no high-risk non-findings, no validation command/status, no line evidence, no re-review after fix, or no owner for accepted risk.
- **Invalid evidence**: "LGTM", author-only self-review for high-risk change, hallucinated API accepted without source proof, stale validation after final edit, or inaccessible report.

## Handoff Evidence Shape

Use a natural-language Markdown review handoff:

```markdown
## Result

## Reviewed and Unreviewed Scope

## Findings

### <Severity>: <short finding title>

Location:
Evidence and impact:
Required action:
Repair / re-review status:

## Validation Results and Proof Limits

## Explicit High-Risk Non-findings

## Residual Risk and Recommended Next Step
```
