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

Use this capability when creating or modifying: CI workflows (GitHub Actions, GitLab CI, Jenkins, CircleCI, Buildkite, Azure Pipelines, Tekton, Drone), release pipelines, artifact build and publishing, image build and promotion, environment promotion logic, approval gates, deployment strategies (rolling, blue/green, canary), feature-flag cut-overs, infrastructure-as-code (Terraform, Pulumi, Crossplane) plan/apply pipelines, database-migration pipelines, monorepo affected-test and incremental-build workflows, supply-chain security controls (SBOM, signing, provenance), compliance evidence capture, failure handling and rollback hooks, or Helm chart pipelines (`helm lint`, `helm template`, `helm diff`, chart dependency locking, OCI chart packaging, rendered manifest validation).

# Do Not Use When

Do not use this capability to bypass local verification (`pre-commit`, unit tests), treat green pipeline as proof of correctness without acceptance evidence, hide flaky checks by retrying silently, or design general deployment architecture — that belongs to `release-rollback` and `containerization`.

# Stage Fit

- **Planning / design:** use when pipeline triggers, artifact identity, required checks, environment promotion, or release evidence are being designed.
- **Implementation / review:** use when workflow files, build jobs, test gates, image publishing, IaC plan/apply gates, Helm chart jobs, or monorepo affected-test logic change.
- **Validation / release:** use when a pipeline result must prove build/test/security/artifact/rollback readiness before promotion.
- **Repair / incident:** use when flaky checks, failed deploys, retry-to-green behavior, missing rollback hooks, or stale pipeline evidence are blocking a release.
- **Graph / memory / execution coupling:** treat old pipeline knowledge, generated reports, and prior green runs as leads only; reconcile current workflow files, registry, reports, dist output, and validation commands before closure.

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

Anchor against DORA four key metrics, SLSA v1.0, OpenSSF Scorecard, Sigstore/Cosign, CycloneDX/SPDX, NIST SSDF, OWASP SAMM, GitHub/GitLab CI security guidance, Tekton Chains, cloud OIDC federation, hermetic build discipline, GitOps, SemVer, and release-note automation. Keep the body focused on routing, gates, and evidence; load [references/checklist.md](references/checklist.md) for concise planning and [references/pipeline-benchmarks.md](references/pipeline-benchmarks.md) for stage ordering, deployment strategy, supply-chain hardening, gate-blocking decisions, graph/memory/execution coupling, and anti-pattern detail.

# Mode Matrix

| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities / gates | Skip guidance |
| --- | --- | --- | --- | --- | --- |
| PR / CI quality gate | Workflow, lint, test, SAST, affected tests, flaky checks. | Fail-fast checks that can block unsafe merge. | required-check list, failure action, owner, freshness. | `quality-test-gate`, `test-strategy` | skip release gates for local-only checks. |
| Artifact build and promotion | Package/image build, SBOM, signing, registry, provenance. | Build once and promote one immutable digest. | digest, SBOM, attestation, scan result, retention. | `containerization`, `dependency-vulnerability-scanning` | skip deploy design when no promotion occurs. |
| Environment deployment | Dev/staging/prod promotion, approvals, canary, health gate. | Gate by blast radius and rollback readiness. | environment map, deploy strategy, health check, rollback hook. | `delivery-release-gate`, `release-rollback` | skip canary when blast radius is low and rollback is fast. |
| IaC / Helm / GitOps pipeline | Terraform/Pulumi/Crossplane, Helm, rendered manifests, policy checks. | Review plan/rendered diff before state mutation. | plan diff, policy result, state lock, IAM/cost/destructive review. | `kubernetes-gateway`, `security-privacy-gate` | skip live apply when design-only. |
| Supply-chain and secret boundary | Actions, runners, credentials, dependency/image scan, provenance. | Least privilege, no secret leakage, traceable artifacts. | OIDC scope, permissions block, secret scan, CVE threshold. | `security-privacy-gate`, `secret-configuration-security` | skip broad compliance packet unless regulated/audited. |
| Evidence freshness | Old green build, memory, graph, report, dist, or prior pipeline output. | Reconcile current changed paths to validation. | changed-path map, command exit status, stale/not-run disclosure. | `validation-broker`, `agent-tool-permission-sandbox` | skip only for wording that makes no pipeline claim. |

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

# Proactive Professional Triggers

- **Signal:** A pipeline rebuilds, retags, or repackages per environment. **Hidden risk:** production runs a different artifact than staging tested. **Required professional action:** enforce build-once/promote-by-digest and record artifact identity. **Route to:** `ci-cd`, `containerization`, `delivery-release-gate`. **Evidence required:** digest, registry path, promotion path, and rollback target.
- **Signal:** Required checks are bypassed, marked warning-only, silently retried, or hidden behind emergency override. **Hidden risk:** known failure ships while the pipeline appears green. **Required professional action:** classify gate blocking, exception owner, expiry, and notification path. **Route to:** `quality-test-gate`, `agent-execution-discipline`. **Evidence required:** check name, failed output, override approver, expiry, and residual risk.
- **Signal:** CI credentials, runner permissions, logs, artifacts, summaries, or build layers may expose secrets. **Hidden risk:** pipeline compromise or log leak enables unauthorized deploy. **Required professional action:** use OIDC/vault, minimal job permissions, redaction, secret scan, and runner isolation. **Route to:** `security-privacy-gate`, `secret-configuration-security`. **Evidence required:** permission block, secret source, scan result, and redaction rule.
- **Signal:** IaC, Helm, GitOps, or cloud apply can mutate shared infrastructure without reviewed diff. **Hidden risk:** destructive resource, IAM, DNS, gateway, or cost change reaches production without audit. **Required professional action:** require plan/rendered diff, policy checks, state lock, budget/IAM review, and rollback note. **Route to:** `delivery-release-gate`, `kubernetes-gateway`. **Evidence required:** plan/diff artifact, policy output, approval, and rollback scope.
- **Signal:** A monorepo affected-test or cache rule decides what runs. **Hidden risk:** changed modules, generated inputs, lockfiles, or fixtures are skipped by stale graph/cache keys. **Required professional action:** map changed paths to modules/dependents and prove cache invalidation. **Route to:** `repository-graph-analysis`, `validation-broker`, `quality-test-gate`. **Evidence required:** graph edge, cache key inputs, selected tests, and full-suite fallback rule.
- **Signal:** Project memory, prior green builds, old reports, or generated dist output are used after workflow, gate, artifact, permission, registry, or validation scripts changed. **Hidden risk:** stale evidence is reused for a different release graph. **Required professional action:** reconcile current source and rerun mapped validators before closure. **Route to:** `project-memory-governance`, `execution-trajectory-analysis`, `agent-tool-permission-sandbox`. **Evidence required:** inspected path list, accepted/rejected prior claim, command result, sandbox record, and residual risk.

# Critical Details

The CI/CD pipeline is both a **quality enforcement mechanism and a supply-chain security boundary**. Key refinements:

- **Determinism before speed.** Cache keys include lockfiles, compiler/tool versions, environment inputs, generated source, and fixtures; cache hits must never change the artifact without a source change.
- **Fail-fast with named owners.** Pre-merge checks stay fast and mandatory; slow suites shard with fan-out/fan-in; flaky checks get owner, SLA, quarantine track, and promotion criteria.
- **Environment parity is evidence.** Staging results count only when topology, image digest, config shape, integration surface, and secret source match production expectations or gaps are disclosed.
- **GitOps and IaC are release surfaces.** Desired-state commits, rendered manifests, plan diffs, state locks, drift checks, IAM/cost/destructive reviews, and rollback notes are audit artifacts.
- **Migration gates are compatibility gates.** Schema migrations use expand/contract sequencing and are not bundled destructively with app deployment unless an explicit release gate accepts forward-fix risk.
- **Helm gates render before mutation.** Dependency build, lint, template, values schema, rendered-manifest validation, policy checks, diff, atomic/waited upgrade or GitOps sync, and release evidence are required for chart pipelines.
- **Supply-chain evidence travels with artifacts.** SBOM, signing/provenance, vulnerability scan, artifact digest, approver, retention, and deploy event must be attached to each promoted release.
- **Self-hosted runners are trust boundaries.** Prefer ephemeral isolated runners for privileged deploy jobs; shared runners cannot hold broad production credentials.
- **Pipeline ownership is code ownership.** Workflow files have owners, review requirements, emergency exception policy, and audit retention.

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

# Reference Loading Policy

- Use the `SKILL.md` body for routing, mode selection, triggers, output contract, evidence, quality gates, and handoff.
- Load [references/checklist.md](references/checklist.md) when drafting or reviewing a concrete CI/CD plan and a compact checklist is enough.
- Load [references/pipeline-benchmarks.md](references/pipeline-benchmarks.md) when stage ordering, deployment strategy, gate-blocking decisions, supply-chain hardening, IaC/Helm/monorepo detail, graph/memory/execution coupling, or anti-pattern review needs depth.
- Use [examples/example-output.md](examples/example-output.md) only when the expected output shape is unclear.
- Do not load references for a pure routing decision or a local wording edit with no pipeline behavior claim.

# Output Contract

Return a CI/CD pipeline specification with:

- `triggers_and_stages` (push/PR/schedule/manual/tag triggers; ordered jobs, parallelism, fail-fast policy, speed target)
- `required_and_optional_checks` (merge/deploy gates, failure action, override policy, approver, warning backlog, owner SLA)
- `artifact_spec` (digest policy, binary hash, SBOM, provenance attestation, registry, retention, promotion path)
- `cache_policy` (cache key hash inputs, invalidation rules, security scope)
- `secrets_and_credentials` (vault/OIDC source, injection method, log masking, environment-scoped role, no shared admin credential)
- `environment_promotion_and_strategy` (dev/staging/prod gates, deploy window, rolling/blue-green/canary/GitOps choice, rollout percentage)
- `helm_iac_pipeline` (lint/template/schema/rendered manifest/policy/diff/upgrade/rollback/provenance, state lock, IAM/cost/destructive review)
- `post_deploy_and_rollback` (health check, timeout, auto-rollback trigger, rollback hook, test evidence, on-call notification)
- `supply_chain_controls` (action pinning, SBOM, signing, provenance, scan thresholds, dependency lock/hash policy)
- `compliance_and_audit_trail` (deploy event, approval, artifact digest, SBOM/scan evidence, retention target, immutable sink)
- `monorepo_build_policy` (module graph, affected tests, cache key inputs, generated file policy, full-suite fallback)
- `migration_gate` (expand/contract and backwards-compat validation when DB migrations are in the pipeline)
- `flaky_check_policy` (quarantine criteria, owner SLA, promotion to required process)
- `ownership` (pipeline owner, review requirements for pipeline config changes)
- `dora_baseline` (current Deployment Frequency, Lead Time, Change Failure Rate, MTTR — or "unmeasured")
- `graph_memory_execution_coupling` (current workflow/config/report/dist facts used, prior evidence accepted or rejected, validation freshness)
- `tool_permission_boundary` (read-only vs state-mutating pipeline/deploy/IaC actions, sandbox, dry-run/rendered diff, rollback, redaction)
- `evidence_scope` (what evidence proves, what remains unproven, residual owner/risk)

# Evidence Contract

A CI/CD change is complete only when the output includes:

- **Boundaries inspected**: workflow files, runner trust, artifact registry, deployment targets, env config, secrets, IaC/Helm/GitOps, monorepo graph, generated reports, dist output, and skipped boundaries.
- **Source and artifact contract**: commit SHA, artifact digest, SBOM/provenance, promotion path, environment identity, and rollback target.
- **Validation evidence**: exact command, pipeline result, validator, rendered diff, scan, or report proving checks, artifact integrity, gate behavior, and fallback/rollback readiness.
- **What evidence proves**: the inspected pipeline enforces required checks, artifact traceability, secret handling, promotion gates, and audit evidence for the named scope.
- **What evidence does not prove**: live provider behavior, production runner isolation, cloud/IAM effective policy, real canary health, regional rollout, or uninspected downstream consumers unless verified separately.
- **Security/release review**: secrets, OIDC permissions, action pinning, scans, emergency overrides, IaC/Helm/cloud exposure, compliance evidence, and release approval boundaries.
- **Graph / memory / execution reconciliation**: repository graph, project memory, previous green builds, generated reports, and command outputs are current or rejected as stale.
- **Reuse / placement rationale**: why detail stays in this capability or its references and why registry, dist, shared/common, or runtime install paths are not changed.
- **Tool boundary**: read-only versus state-mutating commands, sandbox/approval state, dry-run or rendered output, rollback/revert path, and redaction rule.
- **Residual risk and handoff**: unrun live pipeline, unverified provider/cloud behavior, stale downstream evidence, next gate, and owner.

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
15. Helm chart pipelines run dependency build, lint, template, values schema validation, rendered manifest validation, policy checks, helm diff, and atomic waited upgrade or equivalent GitOps safeguards.
16. Helm release evidence includes chart version, appVersion, values checksum, rendered manifest digest, reviewer, and deployment outcome.
17. Graph, memory, report, and validation evidence is fresh relative to final workflow or skill edits.
18. Tool permission/sandbox evidence is recorded before deploy, IaC apply, Helm/Kubernetes, cloud, secret, publish, or rollback action.
19. Claims are bounded and do not imply live CI provider, secret store, cloud/IAM, canary, or production release proof unless those were actually inspected.

# Benchmark Coverage

This capability covers DORA-oriented delivery health, fail-fast CI stages, immutable artifact promotion, required checks, flaky-check governance, supply-chain provenance, OIDC/secret safety, IaC/Helm/GitOps gates, monorepo affected-test correctness, compliance audit evidence, rollback hooks, post-deploy health checks, and graph/memory/execution evidence freshness.

# Routing Coverage

Route here when pipeline mechanics, quality gates, artifact lifecycle, promotion, CI security, monorepo build policy, or deployment automation are primary. Combine with `delivery-release-gate` for live release readiness, `security-privacy-gate` for secrets/IAM/public exposure/compliance, `release-rollback` for recovery planning, `containerization` for image construction, `dependency-vulnerability-scanning` for CVE methodology, `kubernetes-gateway` for Helm/Kubernetes manifest behavior, `validation-broker` for freshness, and `agent-tool-permission-sandbox` for any pipeline/deploy/cloud command.

# Used By

- delivery-release-gate
- quality-test-gate

# Handoff

Hand off to `test-strategy` for coverage and layer selection; `dependency-vulnerability-scanning` for SCA and image risk; `release-rollback` for deployment reversal and feature-flag management; `containerization` for image construction; `secret-configuration-security` for credential and vault design; `delivery-release-gate` for release readiness review; `security-privacy-gate` for cloud IAM, public exposure, KMS, or compliance evidence risks; `performance-budgeting` for cost thresholds and per-feature ceilings.

# Completion Criteria

The capability is complete when the pipeline **builds once, tests deterministically, signs and bills-of-materials every artifact, gates each environment proportionally to blast radius, has an auto-rollback path with a tested health check, captures an immutable audit trail, and no unsafe or unreviewed change can reach production without a named approval decision**.
