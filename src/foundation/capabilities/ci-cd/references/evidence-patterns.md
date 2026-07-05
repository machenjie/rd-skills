# CI/CD Evidence Patterns

Use this reference when CI/CD closure depends on changed-pipeline validation, repository graph, project memory, execution trajectory, generated reports, dist output, validation freshness, or tool permission boundaries. Keep it as an evidence map, not a second pipeline tutorial.

## Pipeline Claim To Evidence Map

| Pipeline claim | Minimum evidence | What it proves | What it does not prove |
| --- | --- | --- | --- |
| Required checks block unsafe merge | Workflow path, branch policy, check names, failure action, override rule, owner, and validator/report path | The inspected pipeline declares blocking checks for the named scope | CI provider enforcement, branch protection state, or every repository rule is active unless inspected live |
| Artifact is immutable and promotable | Commit SHA, artifact digest, registry path, SBOM/provenance artifact, promotion path, and rollback target | The inspected release artifact can be traced and promoted without rebuild | Runtime image contents, registry retention, or production deploy state is current |
| Secrets and deploy permissions are bounded | Workflow permissions block, OIDC/vault source, runner trust boundary, redaction rule, secret scan, and environment role scope | The inspected workflow avoids obvious long-lived secret and broad-permission patterns | Cloud IAM effective permissions, vault policy, or hidden provider logs are safe |
| IaC, Helm, or GitOps mutation is gated | Plan/rendered diff, policy result, state lock, IAM/cost/destructive review, reviewer, and rollback scope | The inspected mutation path requires review before changing state | Live apply behavior, drift in the provider, or all CRD/cloud side effects are reversible |
| Affected-test and cache selection is credible | Changed paths, module graph, generated inputs, lockfiles, cache-key inputs, selected tests, and full-suite fallback rule | The inspected selection uses current graph and invalidation inputs | Dynamic imports, hidden generated files, or full-suite parity are proven |
| Pipeline evidence is fresh | Final edited paths, command, exit code/status, report/artifact path, generated report/dist freshness, and rerun timestamp | Validation was produced after the final material edit for the mapped pipeline claim | Later workflow, registry, report, dist, or provider-state changes are covered |
| Prior green build or memory is reusable | Prior claim source, date, scope, unchanged workflow/config/report paths, current-source comparison, and accepted/rejected verdict | Old evidence still matches the inspected pipeline shape | Live provider state, credentials, runners, or production deployment remains unchanged |

## Graph, Memory, And Execution Reconciliation

- Treat previous green builds, project memory, repository graph output, generated reports, dist output, and prior agent summaries as selectors until current workflow files, registry entries, validation scripts, and fresh command output confirm them.
- Accept a prior "CI is green", "checks block", "artifact is signed", "rollback hook exists", "affected tests are correct", or "no secrets in pipeline" claim only when current workflow/config/report paths and validators still match.
- Reject or downgrade memory that lacks date, owner, changed-path scope, command, exit code/status, artifact/report path, provider boundary, or residual-risk owner.
- Mark evidence stale after edits to workflow files, lockfiles, test selection, cache keys, generated inputs, artifact rules, permissions, registry paths, reports, dist output, build scripts, or validation commands.
- Map every final CI/CD confidence claim to a current source path, generated report, dist artifact, validator command, exit code/status, owner approval, or explicit not-verified residual risk.

## Tool Permission Boundary

| Action | Boundary record |
| --- | --- |
| Local source reads, registry search, graph search, report inspection, and markdown validation | Read-only local shell action; cite searched paths and avoid full output dumps. |
| Local validators, tests, builds, report refresh, and dist generation | State-mutating only for reports, caches, temp files, dist/build artifacts, or local fixtures; cite log path, command, exit code, and rollback path. |
| CI dry run, secret scan, SBOM/provenance generation, rendered manifest diff, or IaC/Helm plan | Development or sandbox action; record input scope, redaction rule, generated artifact owner, diff review, and cleanup. |
| Pipeline dispatch, deploy, publish, package release, cloud/IAM change, secret rotation, IaC apply, Helm/Kubernetes upgrade, or rollback command | High-risk external or production action; require explicit permission, bounded scope, dry-run/rendered diff when available, stop condition, rollback/forward-fix path, and secret redaction. |

## Handoff Evidence Shape

```yaml
ci_cd_evidence_closure:
  inspected_pipeline_surfaces:
    - surface: ""
      current_source_or_artifact: ""
      finding: ""
  accepted_prior_claims:
    - claim: ""
      current_evidence: ""
      freshness: ""
  rejected_or_stale_claims:
    - claim: ""
      reason: ""
  changed_pipeline_to_validation_map:
    - pipeline_surface: ""
      source_or_config_path: ""
      validation_command_or_artifact: ""
      exit_code_or_status: ""
      proves: ""
      does_not_prove: ""
      owner: ""
      freshness: ""
  tool_permission_boundary:
    action_class: ""
    sandbox: ""
    state_mutation: ""
    redaction: ""
  residual_risks:
    - risk: ""
      owner: ""
      next_gate: ""
```
