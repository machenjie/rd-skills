# Project Initialization Evidence Patterns

Use this reference when closure depends on proving repository initialization decisions, current graph/template claims, generated-artifact policy, secret safety, package-manager entrypoint and dependency-policy handoff, or clean-checkout validation. Keep `SKILL.md` for routing and output shape; load this file only for concrete evidence mapping.

## Claim To Evidence Map

| Claim | Strong evidence | Weak or invalid evidence | Residual risk if absent |
| --- | --- | --- | --- |
| Folder layout has architectural purpose | Folder map, owner/boundary notes, source/test/docs/scripts/config/build separation | Template folder list only | Boundaryless `utils`, `misc`, or scaffold drift |
| Clean checkout works | Bootstrap/setup command, validation command, exit code, and toolchain version from fresh workspace | README command not run | Onboarding and CI setup fail after handoff |
| Secrets are excluded | `.gitignore`, placeholder `.env.example`, secret-scan command/report, and no real fixture credentials | Manual "no secrets" review only | Credentials or environment-specific values enter git |
| Generated artifacts are governed | Gitignore or committed-generated policy, build command, drift check, source-of-truth path | Generated folder exists with no policy | Runtime/source drift and noisy reviews |
| Package entrypoint and dependency-policy handoff are explicit | Package-manager identity, manifest and lockfile paths, bootstrap command, lockfile owner, accepted `package-dependency-management` evidence or unresolved handoff, and separate `dependency-vulnerability-scanning` status when applicable | License policy or scanner presence treated as initialization acceptance | Bootstrap may work while package or vulnerability policy remains unaccepted |
| Template or memory is current | Template source/date, accepted/rejected assumptions, current graph/convention scan | Prior repo copied by memory | Unsupported stale conventions become project defaults |
| Initialization maps to validation | Scaffold decision to setup/build/lint/test/secret/docs command or residual risk | Checklist marked complete | Handoff overclaims readiness without executable proof |

## Initialization To Validation Map

For each folder, config surface, command, generated policy, package-manager entrypoint, dependency-policy handoff, docs target, local-dev tool, and monorepo decision, record:

```yaml
initialization_validation_map:
  decision: ""
  source_or_doc_path: ""
  owner: ""
  validation:
    command: ""
    exit_code: null
    artifact_or_report: ""
    proves: ""
    does_not_prove: ""
  residual_risk:
    owner: ""
    reason: ""
```

## Closure Checks

- Reject closure when setup/build/test commands are documented but not run or explicitly marked not verified.
- Reject closure when `.env.example`, fixtures, or bootstrap scripts are added without placeholder and secret-scan evidence.
- Reject initialization closure that claims dependency policy ready without accepted `package-dependency-management` evidence; retain the unresolved handoff and owner instead.
- Route vulnerability, malicious-package, provenance, or license-exception acceptance to `dependency-vulnerability-scanning`; scanner presence is not an initialization decision.
- Downgrade template, memory, and prior-repository claims unless current source and graph evidence confirm them.
- Do not treat initialization proof as production deployment, full compliance, or future module-boundary approval.
