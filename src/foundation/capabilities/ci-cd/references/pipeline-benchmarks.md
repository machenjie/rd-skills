# CI/CD Pipeline Benchmarks And Patterns

Use this reference when CI/CD work needs stage ordering, deployment strategy selection, gate-blocking decisions, supply-chain hardening, IaC/Helm/monorepo detail, graph/memory/execution reconciliation, or anti-pattern review. The decision-critical rule stays in `SKILL.md`: required checks block promotion except through a named, audited emergency override.

# Pipeline Stage Design

| Stage | Typical checks | Block on failure? | Speed target |
| --- | --- | --- | --- |
| Pre-merge / PR | Lint, format, unit tests, secret scan, PR policy | Yes | < 5 min |
| CI on trunk | Full test suite, SAST, license check, SBOM generation | Yes | < 15 min |
| Build / package | Reproducible build, signing, container scan, provenance | Yes | < 10 min |
| Deploy to dev/test | Promote artifact, integration smoke test | Yes | < 5 min |
| Deploy to staging | Promote artifact, regression/performance/config drift gate | Yes | < 30 min |
| Deploy to production | Approval, deploy window, progressive rollout, health gate | Yes plus human gate | Per org policy |
| Post-deploy | Synthetic monitors, SLO burn-rate, auto-rollback trigger | Auto-rollback when failed | < 5 min |

# Deployment Strategy Selection

| Strategy | Traffic shift | Rollback speed | Blast radius | Use when |
| --- | --- | --- | --- | --- |
| Recreate | All at once | Slow redeploy | 100% | Dev/test or acceptable downtime |
| Rolling | Gradual pods | Moderate | Partial | Stateless services and normal deploys |
| Blue/green | Instant switch | Fast traffic flip | 0% until cutover | Database-compatible migration and fast rollback need |
| Canary | Percent traffic | Fast canary drain | Small cohort | Production risk reduction with enough traffic signal |
| Shadow / mirror | No live impact | Not applicable | 0% | New path validation without user impact |
| Feature flag | Cohort-based | Instant flag off | Per cohort | Decouple deploy from release |

## Decision Tree: Should This Gate Block?

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

# Supply-Chain Security Hardening

| Control | Implementation evidence | Standard anchor |
| --- | --- | --- |
| Pin third-party actions | Commit SHA pin instead of mutable tag | GitHub hardening |
| OIDC cloud credentials | Short-lived role assumption per environment | SLSA / cloud OIDC |
| Minimal job permissions | Explicit `permissions` block with no inherited write-all | GitHub hardening |
| Image digest pinning | Base and release images referenced by digest | SLSA L2 |
| SBOM at build time | Syft, CycloneDX, or SPDX artifact retained | CycloneDX / SPDX |
| Build provenance | Cosign or in-toto attestation stored with artifact | SLSA L2/L3 |
| Container scan | Trivy, Grype, Snyk, or registry scan threshold | NIST SSDF |
| Dependency lockfile | Lockfile/hash validation in install step | SLSA L1 |
| Secret scanning | Pre-commit and CI scan, with owner for findings | OWASP SAMM |

# IaC And Helm Gate Detail

- IaC plan/apply pipelines capture immutable plan artifact, state lock, drift status, destructive action review, IAM diff, cost delta, reviewer, environment, and commit SHA.
- High-cost resources require budget threshold and approval before apply.
- Helm pipelines run dependency build with committed lock, lint, template for each values file, values schema validation, rendered manifest validation, policy checks, diff review, atomic waited upgrade or GitOps sync, and chart provenance when published.
- Release evidence includes chart version, appVersion, values checksum, rendered manifest digest, reviewer, deployment outcome, and rollback scope.

# Monorepo And Cache Correctness

- Module graph maps changed files to direct modules, dependents, contract tests, generated inputs, and release artifacts.
- Affected-test selection declares what is included, what is excluded, and the full-suite fallback cadence.
- Build cache keys include lockfiles, compiler/tool versions, environment inputs, generated source inputs, and test fixtures.
- Generated file policy states which generated files are committed, ignored, or regenerated in CI.
- Devcontainer or equivalent reproducible local environment keeps setup drift measurable.

# Graph, Memory, And Execution Coupling

- Treat previous green builds, generated reports, project memory, and repository graph output as hypotheses until current workflow files, validation scripts, registry, reports, and dist output confirm them.
- Mark evidence stale when workflow files, lockfiles, test selection, cache keys, generated inputs, artifact rules, permissions, registry paths, validators, or build scripts change after the last run.
- Record whether inspected commands are read-only or state-mutating; deploy, publish, IaC apply, Helm/Kubernetes, cloud, secret, rollback, and package-release actions need tool permission and sandbox evidence before execution.
- Local skill-authoring validators prove source/report/dist consistency, not live CI provider behavior, credential correctness, cloud IAM effective policy, or production release readiness.

# Anti-Patterns To Reject

| Anti-pattern | Failure |
| --- | --- |
| `FROM python:latest` or install without lockfile | Same git SHA can produce different artifacts |
| Long-lived deploy token in CI secret | Token theft enables unauthorized production deploy |
| `continue-on-error: true` on SAST | Security findings are silently ignored |
| Rebuild image per environment | Production runs a different binary than staging tested |
| Silent retry-to-green flaky test | Intermittent race ships while pipeline appears green |
| `terraform apply -auto-approve` | Unreviewed infrastructure mutation can destroy resources |
| Deploy role has broad administrator access | Pipeline compromise owns the account boundary |
| No post-deploy health check | Recovery time starts when users notice |
