---
name: ci-cd
description: Defines CI/CD pipelines with relevant build, test, lint, security checks, artifacts, deployment gates, and failure policy.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "73"
changeforge_version: 0.1.0
---

# Mission

Design CI/CD pipelines that **prove change quality through automated evidence**, produce traceable immutable artifacts, gate deployment according to blast radius and compliance, and preserve rollback capability — so that no unsafe, unverified, or untraceable change can reach production without a named approval decision.

# When To Use

Use this capability when creating or modifying: CI workflows (GitHub Actions, GitLab CI, Jenkins, CircleCI, Buildkite, Azure Pipelines, Tekton, Drone), release pipelines, artifact build and publishing, image build and promotion, environment promotion logic, approval gates, deployment strategies (rolling, blue/green, canary), feature-flag cut-overs, infrastructure-as-code (Terraform, Pulumi, Crossplane) plan/apply pipelines, database-migration pipelines, monorepo affected-test and incremental-build workflows, supply-chain security controls (SBOM, signing, provenance), compliance evidence capture, or failure handling and rollback hooks.

Use this capability for Helm chart pipelines, Helm release promotion, `helm lint`, `helm template`, `helm diff`, chart dependency locking, OCI chart packaging, and rendered manifest validation.

# Do Not Use When

Do not use this capability to bypass local verification (`pre-commit`, unit tests), treat green pipeline as proof of correctness without acceptance evidence, hide flaky checks by retrying silently, or design general deployment architecture — that belongs to `release-rollback` and `containerization`.

# Non-Negotiable Rules

- **Build once, promote everywhere.** The *same binary/image* digest is promoted across dev → staging → production; never rebuild for each environment. Environment differences come from config injection, not from a different build.
- **Artifacts are immutable and content-addressed.** Container images referenced by digest (`sha256:...`), not mutable tags (`latest`, `main`). Binaries carry a build provenance attestation (SLSA).
- **Required checks block promotion.** Failed unit tests, SAST, container scan, or policy checks cannot be bypassed except via a named, audited emergency-override with approver + justification.
- **Secrets never enter pipeline logs, environment variables in build output, artifact layers, or GITHUB_STEP_SUMMARY.** Inject via vault-backed OIDC (GitHub → AWS/GCP/Azure federation), never long-lived static keys committed or stored in CI variables.
- **Least-privilege deployment credentials.** Deploy job has OIDC-federated short-lived credentials scoped to the target environment; no `AdministratorAccess`, no shared deploy key across environments.
- **Flaky checks have owners and SLAs.** A flaky check either gets fixed (SLA: 2 working days for mandatory checks) or is quarantined to a non-blocking track. Silent retry-to-green is not a strategy.
- **Deployment gates are proportional to blast radius:** dev = auto-deploy on merge; staging = auto-deploy + smoke test gate; production = approval + deploy window + progressive rollout + post-deploy health gate.
- **Rollback hook is tested.** Not "we can roll back" but "the rollback job runs in the pipeline and its success/failure is visible"; tested in staging at least quarterly.
- **Pipeline steps are idempotent and deterministic.** The same git SHA produces the same artifact; `go build` / `npm ci --frozen-lockfile` / `pip install --require-hashes` enforce a lockfile; no `latest` dependency pulls.
- **Supply-chain provenance.** SLSA level 2 minimum for new pipelines: signed build provenance (`cosign`, `sigstore`), SBOM generated at build time (`syft`, `cyclonedx-gomod`, `spdx-sbom-generator`), dependency hash pinning.
- **Post-deploy verification gate.** Smoke test, synthetic transaction, or key metric health check within a timeout after deploy; auto-rollback if health check fails within the window.
- **Audit trail.** Every deploy event records: trigger (commit SHA + author), artifact digest, environment, deploy job id, approver(s), start/end time, outcome. Retained per compliance policy.
- **Infrastructure plan changes require impact evidence.** IaC plan/apply pipelines must capture plan diff, destructive resource detection, IAM diff, cost delta, state lock evidence, drift status, and approval before apply.
- **High-cost infrastructure requires an approval gate.** New or modified resources that exceed budget thresholds, reserved commitments, large storage, high-egress paths, or autoscaling spend must block on named budget approval.

# Industry Benchmarks

Anchor against: **DORA four key metrics** (Deployment Frequency, Lead Time for Changes, Change Failure Rate, Failed Deployment Recovery Time) — elite performers deploy on-demand with < 1 h lead time and < 5% change failure rate. **SLSA (Supply-chain Levels for Software Artifacts) v1.0** levels 1–3 for build integrity. **OpenSSF Scorecard** for supply-chain security signals. **Sigstore / Cosign** for keyless signing. **CycloneDX / SPDX** SBOM standards. **NIST SSDF (SP 800-218)** for secure software development lifecycle integration. **OWASP Software Assurance Maturity Model (SAMM) v2** for CI security practices. **GitHub Actions security hardening guide** (pin actions to `sha`, OIDC federation, `permissions: {}` minimal). **GitLab CI/CD security practices**. **Tekton Chains** for supply-chain provenance in Kubernetes-native pipelines. **AWS/GCP/Azure OIDC federation** for keyless cloud credentials. **Google Build / Bazel** hermetic build discipline. **Netflix Spinnaker** progressive delivery patterns. **Argo CD / Flux** (GitOps) — declarative desired state, reconciliation, diff visibility. **Weaveworks/Flux CNCF graduation** as reference for pull-based GitOps. **Semantic Versioning (SemVer 2.0)** for release artifact naming. **Keep a Changelog** format for release notes automation.

### Pipeline Stage Design — Fail-Fast Ordering

Cheap and deterministic checks run first to give fast feedback; expensive or blocking checks run later to avoid wasting time on already-broken builds:

| Stage | Typical checks | Block on failure? | Speed target |
| --- | --- | --- | --- |
| **Pre-merge / PR** | Lint, format, unit tests, secrets scan, PR policy (reviewers, size) | Yes | < 5 min |
| **CI (on merge to trunk)** | Full test suite, SAST (Semgrep/CodeQL), licence check, SBOM generation | Yes | < 15 min |
| **Build / Package** | Reproducible build, artifact signing, container scan (Trivy/Grype/Snyk), provenance attestation | Yes | < 10 min |
| **Deploy to dev/test** | Auto-deploy, integration smoke test | Yes | < 5 min |
| **Deploy to staging** | Auto-deploy, integration + regression suite, performance gate, config drift check | Yes | < 30 min |
| **Deploy to production** | Approval gate, change window, progressive rollout (canary → ≥x%), post-deploy health check | Yes + human gate | Per org policy |
| **Post-deploy** | Synthetic monitors, SLO burn-rate check, auto-rollback trigger | Auto-rollback if fail | < 5 min |

### Deployment Strategy Selection

| Strategy | Traffic shift | Rollback speed | Blast radius | Pick when |
| --- | --- | --- | --- | --- |
| **Recreate** | All at once | Slow (redeploy) | 100% | Dev/test; acceptable downtime |
| **Rolling** | Gradual pods | Moderate (drain + replace) | Partial | Stateless services; default |
| **Blue/Green** | Instant switch | Fastest (flip LB) | 0% until cut | Database-compatible migrations; instant rollback needed |
| **Canary** | % of traffic | Fast (drain canary) | Small % | Production risk reduction; A/B behavior |
| **Shadow / Mirror** | No live impact | N/A (no real traffic) | 0% | New path validation without user impact |
| **Feature flag** | Cohort-based | Instant (flag off) | Per cohort | Decouple deploy from release |

### Decision Tree: Should This Gate Block?

```
Is this a security finding (SAST HIGH+, secrets detected, CVE CRITICAL in runtime image)?
└─ Yes → BLOCK (no bypasses except documented emergency exception with CISO sign-off).

Is this a failing unit / integration / regression test?
├─ Flaky (known) → Quarantine track; still BLOCK on mandatory suite.
└─ New failure → BLOCK. Fix or revert.

Is this a MEDIUM dependency vulnerability in a dev-only package?
└─ Warn only; track in vulnerability backlog; SLA = 30 days.

Is this a build-time lint / format failure?
└─ BLOCK in CI; developer-class fix (< 15 min).

Is this a production deploy to regulated environment?
└─ Require: change-ticket, approval(s), deploy window, rollback plan, post-deploy test.
```

### Supply-Chain Security Hardening

| Control | Implementation | Standard |
| --- | --- | --- |
| Pin third-party actions to commit SHA | `uses: actions/checkout@abc123` not `@v4` | GitHub hardening guide |
| OIDC keyless cloud credentials | `aws-actions/configure-aws-credentials` with `role-to-assume` | AWS OIDC, SLSA |
| Minimal permissions per job | `permissions: contents: read` (no inherited `write-all`) | GitHub hardening guide |
| Image digest pinning | `FROM debian@sha256:...` in Dockerfile | SLSA L2 |
| SBOM at build time | `syft` / `cyclonedx` output to artifact store | CycloneDX, SPDX |
| Build provenance attestation | `cosign attest --predicate provenance.json` | SLSA L2/L3 |
| Container scan | Trivy / Grype / Snyk in CI; block on CRITICAL runtime CVEs | NIST SSDF |
| Dependency lockfile | `package-lock.json`, `Cargo.lock`, `go.sum`, `requirements.txt --require-hashes` | SLSA L1 |
| Secret scanning | `truffleHog`, `gitleaks`, `detect-secrets` pre-commit + CI | OWASP SAMM |

# Selection Rules

Select this capability when **pipeline design, quality gates, artifact lifecycle, or deployment promotion policy** are primary. Adjacent routing:

- Prefer `test-strategy` for selecting which test layers to run and coverage targets.
- Prefer `dependency-vulnerability-scanning` for supply-chain and SCA assessment methodology.
- Prefer `release-rollback` for rollback strategy, feature-flag management, and deployment reversal.
- Prefer `containerization` for image construction, multi-stage builds, and runtime minimization.
- Prefer `secret-configuration-security` for secret injection, rotation, and vault integration design.
- Use **with** `delivery-release-gate` for release readiness review.

# Risk Escalation Rules

Escalate when: deployment is to production with no rollback hook tested, required checks are being bypassed, secrets were detected in logs or artifacts, an emergency override is invoked (requires async CISO/engineering-lead notification within 1 h), the pipeline serves regulated workloads (PCI, HIPAA, SOX ITGC, ISO 27001 A.8.25), a data migration runs inline with the deploy (separate concern), or a deployment fails the post-deploy health check and auto-rollback does not trigger.

# Critical Details

The CI/CD pipeline is both a **quality enforcement mechanism and a supply-chain security boundary**. Key refinements:

- **Trunk-based development reduces merge debt.** Short-lived branches (< 1 day) with feature flags outperform long-lived feature branches for DORA metrics. PR size limits (< 400 lines) are enforceable by policy.
- **Caching must not skip determinism.** Cache keys must hash the dependency manifest (lockfile); cache hits that restore stale packages silently produce different builds. Cache the build *output*, not the package fetch, for artifact reproducibility.
- **CI parallelism with test sharding.** Slow test suites should be sharded (`pytest-split`, `vitest --shard`, `--split-by-timing`) across parallel jobs; fan-out / fan-in pattern; total wall time target < 10 min for pre-merge.
- **Flaky test economics.** A flaky test that causes 1 in 20 builds to fail adds ~5% overhead; at 10 engineers × 8 deploys/day = 4 lost engineer-hours/day. Flakiness is a throughput tax; assign an owner and SLA.
- **Environment parity.** Staging must mirror production topology (same image, same config shape, same external mocks). "Works in staging" is only evidence when parity is documented.
- **GitOps pull model (Argo CD / Flux).** Deploy job pushes a git-reconciled desired-state manifest; cluster controller applies it. Benefits: drift detection, reconciliation loop, `kubectl apply` is never run from CI directly → audit trail is the git history.
- **Progressive delivery telemetry.** Canary requires live SLO baseline; canary must emit the *same metrics* as stable; rollback decision is automated by comparing canary error rate / latency vs stable baseline (Argo Rollouts, Flagger).
- **Infrastructure-as-code pipelines.** `terraform plan` output requires human review in `diff` form; `terraform apply` runs only after plan approval; state lock prevents concurrent runs; drift detection runs nightly.
- **Database migration pipelines.** Migrations must be backwards-compatible with N-1 app version; deploy migration *before* app (expand / contract); never bundle destructive migration with app deploy without explicit gate.
- **SBOM retention.** SBOM attached to each release artifact and retained per compliance policy; enables rapid CVE impact triage (which releases contain `libxyz < 1.2.3`?).
- **Audit log as compliance evidence.** For SOX ITGC / PCI-DSS §6.4: every production deploy must have: change record, test evidence, approval, artifact digest, deploy timestamp. Pipeline must emit structured events to an immutable audit sink.
- **Self-hosted runners security.** Shared self-hosted runners are a lateral-movement risk; use ephemeral (just-in-time provisioned) runners or GitHub-hosted runners; isolate secrets per environment.
- **Notification and visibility.** Failed deploys notify the team in real time (Slack/PagerDuty); deploy-to-production events are visible to all engineers; anomalies (unexpected failure rate, unusual deploy time) alert.
- **Ownership.** Each pipeline has a named owner; the pipeline config is code-reviewed with the same rigor as application code; `CODEOWNERS` or equivalent enforces review.

### Infrastructure-As-Code Governance

IaC pipelines must treat infrastructure diffs as production changes, not as generated text:

- Terraform/Pulumi/Crossplane module interface: required inputs, outputs, version constraints, provider versions, and compatibility contract.
- State backend and state locking required before any apply; lock contention must fail closed.
- Drift detection schedule with owner, notification path, and reconciliation policy.
- Plan file review with immutable plan artifact, reviewer, environment, and commit SHA.
- Destructive resource detection for delete/recreate, replacement, data-loss, or downtime-inducing actions.
- IAM diff review for privilege additions, trust policy changes, wildcard grants, and service account scope changes.
- Cost delta review for compute, storage, egress, reserved commitments, and autoscaling-sensitive resources.
- Budget approval gate for high-cost resources before apply.
- Resource tagging and audit trail for owner, environment, data classification, cost center, and lifecycle.

### Monorepo Build And DevEx

Monorepo pipelines must prove that incremental speed does not hide correctness gaps:

- Module graph is declared and checked for boundary violations.
- Affected test selection maps changed files to modules, dependents, and contract tests.
- Incremental build works with Bazel, Pants, Nx, Turborepo, or equivalent workspace tooling when justified.
- Build cache keys include lockfiles, compiler/tool versions, environment inputs, generated source inputs, and test fixtures.
- Generated file policy states which generated files are committed, ignored, or regenerated in CI.
- Devcontainer or equivalent reproducible local environment keeps onboarding setup time measurable.
- Pre-commit policy runs only fast deterministic checks; CI owns expensive checks.

### Helm Pipeline Gate

Helm release pipelines must include:

- `helm dependency build` with `Chart.lock` committed for dependency reproducibility.
- `helm lint` for chart syntax and common chart errors.
- `helm template` for every environment values file.
- `values.schema.json` validation for required and typed values.
- `kubeconform` or `kubeval` on rendered manifests.
- Policy-as-code checks with OPA/Gatekeeper/Kyverno/Conftest.
- `helm diff upgrade` for human review before production promotion.
- `helm upgrade --install --atomic --wait --timeout` or equivalent GitOps rollback policy.
- OCI chart provenance/signing when charts are published as artifacts.
- Release evidence: chart version, appVersion, values file checksum, rendered manifest digest, reviewer, deployment outcome.

### Anti-examples

| Anti-pattern | Failure |
| --- | --- |
| `FROM python:latest` in Dockerfile, `npm install` without lockfile | Different builds from same git SHA → irreproducible; silent dependency changes |
| Long-lived `DEPLOY_TOKEN` in CI secret | Token theft → unauthorized deploy to prod; never audited |
| `continue-on-error: true` on SAST job | Security findings silently ignored |
| Rebuild image per environment; inject `ENV=prod` at build time | Production runs a different binary than staging tested |
| Flaky test retried 3× silently; green if at least 1 pass | Flakiness hidden; intermittent race conditions ship |
| `terraform apply -auto-approve` in CI with no plan review | Unreviewed infra change destroys production resource |
| Deploy job runs with `AdministratorAccess` | Blast radius = entire AWS account on any pipeline compromise |
| No post-deploy health check; rollback is a manual Slack request | Silent degradation ships; recovery time = detection time |

# Failure Modes

- Image rebuilt per environment; production runs a different binary than staging tested.
- Mutable tag (`latest`) promotes without digest pin; a silent upstream change ships.
- Required SAST or scan check bypassed with `continue-on-error` or admin override; finding ships.
- Long-lived static deploy credentials exposed in logs or leaked in a PR.
- Flaky test silently retried to green; underlying race condition ships to production.
- `terraform apply` runs without plan review; unintended destructive change executes.
- Database migration ships simultaneously with app, breaking N-1 compatibility during rolling deploy.
- Post-deploy health check absent; degraded deploy runs undetected until user reports.
- SBOM not generated; unable to triage which releases contain a newly disclosed CVE.
- Self-hosted runner shared across environments; lateral movement from compromised dev pipeline reaches prod secrets.
- Pipeline has no owner; configuration drifts; checks silently removed or no longer run.
- Canary promoted to 100% with no automated rollback decision; bad canary completes full rollout.
- Approval gate bypassed in emergency; no async notification to security/engineering lead.
- Build cache keyed only on branch name; dependency update not reflected in cached build.

# Output Contract

Return a CI/CD pipeline specification with:

- `triggers` (push, PR, schedule, manual, webhook, release tag — per branch/environment)
- `stages` (ordered; for each stage: purpose, jobs, parallelism, fail-fast policy, speed target)
- `required_checks` (per merge/deploy gate: name, failure action, override policy and approver)
- `optional_checks` (warnings, tracking backlog, SLA for promotion to required)
- `artifact_spec` (image digest policy, binary hash, SBOM format, provenance attestation, registry, retention)
- `cache_policy` (cache key hash inputs, invalidation rules, security scope)
- `secret_handling` (vault/OIDC source, injection method, log masking, no static long-lived keys)
- `deployment_credentials` (OIDC federation, scope per environment, no shared admin role)
- `environment_promotion` (gates per tier: dev → staging → production; auto vs manual; window)
- `deployment_strategy` (per environment: recreate/rolling/blue-green/canary/GitOps; rollout %)
- `helm_pipeline` (lint/template/schema/rendered-manifest/policy/diff/upgrade/rollback/provenance evidence)
- `post_deploy_health_gate` (check type, timeout, auto-rollback trigger, on-call notification)
- `rollback_hook` (automated path, trigger condition, test evidence)
- `supply_chain_controls` (action pinning, SBOM, signing, scan thresholds)
- `infrastructure_pipeline` (module interface, state backend, state locking, plan file review, apply gate, drift detection, destructive resource detection, IAM diff review, cost delta review — if IaC)
- `cost_controls` (IaC plan cost impact review, cost delta summary for infra changes, budget approval gate for high-cost resources)
- `compliance_evidence` (deploy audit event, approval evidence, artifact digest evidence, SBOM evidence, vulnerability scan evidence, retention target)
- `monorepo_build_policy` (module graph, affected tests, incremental build tool, cache key inputs, generated file policy, devcontainer or reproducible local environment)
- `migration_gate` (expand/contract, backwards-compat validation — if DB migrations)
- `audit_trail` (fields emitted per deploy event, retention, sink)
- `flaky_check_policy` (quarantine criteria, owner SLA, promotion to required process)
- `ownership` (pipeline owner, review requirements for pipeline config changes)
- `dora_baseline` (current Deployment Frequency, Lead Time, Change Failure Rate, MTTR — or "unmeasured")

# Quality Gate

The pipeline design passes only when:

1. Build once, promote everywhere: single digest promoted across all environments.
2. All required checks (tests, SAST, scan) block on failure with no silent bypass.
3. Secrets injected via OIDC / vault; no static long-lived keys; log masking verified.
4. Deployment credentials are least-privilege and environment-scoped.
5. Post-deploy health check with auto-rollback is defined and tested.
6. Supply-chain controls: action pinning, lockfile, SBOM, signing present at SLSA L2+.
7. Flaky checks have owners and SLA; none are silently retried to green.
8. Audit trail captures: trigger, artifact digest, environment, approver, outcome.
9. Rollback tested in staging; documented trigger and expected recovery time.
10. Pipeline config itself is code-reviewed and has a named owner.
11. DORA metrics are either tracked or a tracking plan is in the output.
12. IaC changes include plan review, state lock, destructive action detection, IAM diff, cost delta, and budget approval when thresholds are exceeded.
13. Compliance evidence captures deploy audit event, approval, artifact digest, SBOM, vulnerability scan, and retention target.
14. Monorepo affected-test selection and build cache keys are deterministic and validated against a full-test fallback.

# Used By

- delivery-release-gate
- quality-test-gate

# Handoff

Hand off to `test-strategy` for coverage and layer selection; `dependency-vulnerability-scanning` for SCA and image risk; `release-rollback` for deployment reversal and feature-flag management; `containerization` for image construction; `secret-configuration-security` for credential and vault design; `delivery-release-gate` for release readiness review; `security-privacy-gate` for cloud IAM, public exposure, KMS, or compliance evidence risks; `performance-budgeting` for cost thresholds and per-feature ceilings.

# Completion Criteria

The capability is complete when the pipeline **builds once, tests deterministically, signs and bills-of-materials every artifact, gates each environment proportionally to blast radius, has an auto-rollback path with a tested health check, captures an immutable audit trail, and no unsafe or unreviewed change can reach production without a named approval decision**.
