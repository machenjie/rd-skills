# CI/CD Evidence Patterns

Use this reference when CI/CD closure depends on changed-pipeline validation, repository inspection, prior task evidence, observable action sequence, generated reports, dist output, validation freshness, or tool permission boundaries. Keep it as an evidence map, not a second pipeline tutorial.

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

## Current Evidence And Freshness

- Treat prior green builds, task evidence, inspection output, generated reports, dist output, and agent summaries as selectors until current workflows, registry entries, validation scripts, and fresh command output confirm them.
- Accept a prior CI claim only while current workflow, configuration, report paths, and validators still match. Examples include "CI is green", "checks block", "artifact is signed", "rollback hook exists", "affected tests are correct", and "no secrets in pipeline".
- Reject or downgrade memory that lacks date, owner, changed-path scope, command, exit code/status, artifact/report path, provider boundary, or residual-risk owner.
- Mark evidence stale after edits to workflow files, lockfiles, test selection, cache keys, generated inputs, artifact rules, permissions, registry paths, reports, dist output, build scripts, or validation commands.
- Map each final CI/CD claim for the changed pipeline or delivery scope to current evidence. Evidence may include a source path, generated report, dist artifact, validator command, exit code or status, owner approval, or explicit unverified residual risk.

- If CI dry run, secret scan, SBOM/provenance generation, rendered manifest diff, or IaC/Helm plan, record input scope, redaction rule, generated artifact owner, diff review, and cleanup.
- Pipeline dispatch, deployment, publishing, package release, cloud or IAM changes, secret rotation, IaC apply, Helm or Kubernetes upgrade, and rollback commands require explicit permission and bounded scope. They also require a stop condition, rollback or forward-fix path, and secret redaction. A dry run or rendered diff is included when available.
