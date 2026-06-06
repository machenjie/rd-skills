---
name: delivery-release-gate
description: Guides release engineering for product changes across Docker, CI/CD, Kubernetes, gateway, environment configuration, migration rollout, feature flags, staging validation, canary or blue-green deployment, rollback, release notes, and post-release checks.
license: MIT
changeforge_kind: professional-skill
changeforge_version: 0.1.0
---

# Delivery Release Gate

## Mission
Make every release execution safe, observable, and reversible — by defining environment readiness, deployment strategy, migration sequencing, feature flag lifecycle, staged rollout controls, rollback path, post-release validation, and owner accountability — because a broken release without a tested rollback plan is not a deployment, it is an incident in progress.

## When To Use
- Any deployable change: service code, container images, Kubernetes manifests, infrastructure config, or database migrations.
- Feature flag additions, removals, or gradual rollouts.
- Environment configuration, secrets reference, or infrastructure topology changes.
- CI/CD pipeline changes that affect build, test, or deployment behavior.
- Infrastructure-as-code changes that affect cloud accounts, projects, IAM, DNS, CDN, WAF, gateway routing, KMS, network exposure, or resource cost.
- Canary, blue/green, or progressive delivery rollouts.
- Multi-service coordinated deployments with sequencing dependencies.
- Release coordination involving external consumers, partner integrations, or public announcements.
- Post-release monitoring and rollback readiness validation.
- Incident mitigation releases, emergency rollbacks, or hotfixes where mitigation must be separated from final resolution.
- Regulated or audited releases requiring change approval evidence, deployment audit events, and retention-ready release artifacts.
- Agent-assisted release work where a failed pipeline, migration, deploy, or rollback is being retried or closed.

## Do Not Use When
- The change is source-code-only with no deployment, runtime configuration, release coordination, or consumer notification involved.
- The change is a documentation-only edit with no deployment artifact.

## Stage Fit
Owns release-delivery; also serves infrastructure-deployment, kubernetes-helm, and ci-cd surfaces. Per-stage focus:
- **release-delivery**: rollout sequence, rollback trigger, config and migration compatibility, health checks, alert ownership.
- **documentation-handoff**: release notes, runbook, and post-release verification.

## Non-Negotiable Rules
- **Define rollback before release** — every deployable change must have a documented, tested rollback procedure before deployment begins; "revert the commit" is not a rollback plan.
- **Verify all environment configuration and secrets references** before deployment — missing or misconfigured environment variables are the leading cause of post-deploy failures.
- **Sequence migrations safely** — database migrations must be compatible with both the old and new application version during the rollout window (EMC discipline).
- **Feature flags must be disableable** — any flag that cannot be turned off independently of a code deploy is a safety risk, not a feature flag.
- **Post-release monitoring is not optional** — every deployment must have a defined owner watching key signals for at least 30 minutes (critical paths: 60 minutes) post-deployment.
- **Never deploy without staging parity** — if the staging environment does not represent production topology, config, or data shape, staging test results are unreliable.
- **Rollback must be tested in staging before production** — rollback procedures that have never been executed fail under pressure.
- **Secrets must never be in source code, container images, or plaintext environment variables in logs** — use a secrets manager with audit trail.
- **Container images must be immutable artifacts** — never pull `latest` in production; pin to a specific SHA256 digest or semantic tag.
- **Cloud governance changes require blast-radius boundaries before release** — account/project, namespace, VPC/subnet, gateway, DNS/CDN/WAF, KMS, IAM, and tagging changes must have rollback and audit evidence.
- **Emergency deployment does not remove evidence obligations** — hotfixes and incident mitigations still require approver, artifact, rollback, customer communication owner, and post-release validation.
- **Helm releases must document chart version, appVersion, values overlays, rendered manifest diff, CRD/hook behavior, upgrade flags, rollback scope, and post-upgrade verification.**
- **Helm rollback must not be treated as full system rollback.** Database schema, external config, CRDs, secrets, cloud resources, and migrated data may need separate rollback or forward-fix.
- **No repeated deploy retry without route repair.** After two failed pipeline or deployment attempts on the same signature, require inspected evidence, a new hypothesis, and a changed route before another attempt.

## Industry Benchmarks
- **DORA Metrics (Accelerate — Forsgren, Humble, Kim)**: Deployment frequency, Lead time for changes, Mean time to restore (MTTR), Change failure rate — the four metrics that measure delivery health. Elite teams: deployment frequency daily+, MTTR < 1 hour, change failure rate < 5%.
- **The Twelve-Factor App — Factor XI (Logs) and Factor VI (Processes)**: Stateless processes, environment-based config, log streams. Production-grade applications are stateless and config-injectable.
- **Progressive Delivery (James Governor)**: Feature flags + canary + blue-green — release and deploy are separate events; features are enabled independently of deployments.
- **SRE Release Engineering (Google SRE Book, Chapter 8)**: Hermetic builds, reproducible releases, automated binary provenance — every build artifact is uniquely identifiable and traceable.
- **Kubernetes Rolling Update / Canary / Blue-Green Patterns**: Rolling update is default; blue/green for zero-downtime contract changes; canary for risk-staged traffic routing.
- **GitOps (Argo CD / Flux)**: Declarative infrastructure, Git as the single source of truth for desired state, automated reconciliation — every production state change is git-traceable.
- **Feature Flag Lifecycle (LaunchDarkly / Split.io)**: Create, target, rollout (% traffic), evaluate, clean up — flags that outlive their usefulness become permanent complexity.
- **Change Advisory Board (ITIL CAB)**: High-risk changes require documented impact, risk rating, rollback plan, and communication plan — reviewed before execution.

### Deployment Strategy Selection Matrix

| Change Type | Recommended Strategy | Rollback Mechanism |
|---|---|---|
| Code-only change, stateless service | Rolling update | Rollback deployment to previous image |
| Schema migration + code change | Blue/green + EMC migration | Stop traffic, run rollback migration, rollback deploy |
| High-risk user-facing change | Canary (1% → 10% → 100%) | Reduce canary to 0%, rollback canary deploy |
| Feature flag–controlled change | Rolling update + flag disabled | Disable flag without code deploy |
| Infrastructure topology change | Blue/green (full environment) | Switch traffic back to old environment |
| Breaking API change with consumers | Versioned deploy + consumer coordination | Keep old version deployed, renegotiate consumers |
| Multi-service coordinated release | Sequential with validation gates | Reverse deployment sequence; rollback each service |

## Technical Selection Criteria
Evaluate the release plan against these dimensions:
- **Container image immutability**: Is the image tagged with a specific version? Is `latest` tag prohibited in production manifests?
- **Environment configuration validation**: Are all required environment variables verified to exist in the target environment before deployment?
- **Secrets management**: Are secrets retrieved from a managed secret store (Vault, AWS Secrets Manager, GCP Secret Manager) with audit logging?
- **CI/CD pipeline correctness**: Do the build, test, and deploy stages produce deterministic, hermetic artifacts?
- **Kubernetes readiness and liveness probes**: Are probes configured to catch failed pods before traffic is shifted? Is the `terminationGracePeriodSeconds` appropriate for in-flight request drain?
- **Migration sequencing**: Is the migration backward-compatible with the currently deployed service version during the rollout window?
- **Feature flag disableability**: Can the flag be disabled without a code deploy? Is the flag removal scheduled as a follow-up task?
- **Staging parity**: Does staging match production in topology, external integrations, and configuration surface?
- **Rollback procedure**: Is it documented? Has it been executed in staging? How long does it take?
- **Post-release monitoring**: Which dashboards, metrics, error rates, and SLO burn rates are being watched? Who owns the watch? For how long?
- **Communication plan**: Are API consumers, partner integrators, or on-call engineers notified of the change before deployment?
- **Cloud governance**: Which cloud account/project, namespace, VPC/subnet, security group/NACL/WAF, DNS/CDN/gateway, KMS key, and IAM role boundaries are affected?
- **Compliance evidence**: Which approval, artifact digest, SBOM, vulnerability scan, change ticket, and deploy audit event must be retained?
- **Incident mitigation**: If this release is part of a SEV response, which action is mitigation, which action is resolution, and who owns customer-facing updates?

### Decision Tree: What Deployment Strategy Is Needed?

```
Does the change include a database migration?
├── Yes → Requires EMC migration strategy + blue/green or staged deploy
Does the change modify a public API contract?
├── Yes → Requires versioned deploy + consumer notification + coordination
Does the change have high blast radius or low revert confidence?
├── Yes → Canary deployment required (1% → 10% → full)
Does the change use a feature flag?
├── Yes → Confirm flag is disableable without code deploy
Is staging parity confirmed?
├── No → Block deployment until parity is established
All checks pass → Rolling update with monitored rollout window
```

## Risk Escalation Rules
- Escalate when a database migration is not backward-compatible with the current application version — migration and deploy must be reordered.
- Escalate when the rollback procedure has never been executed in staging and the change has high blast radius.
- Escalate when secrets are hardcoded, stored in environment variable plaintext logs, or sourced from an unaudited mechanism.
- Escalate when staging does not match production configuration, topology, or integration surface.
- Escalate when an external consumer, partner integration, or mobile client requires coordination that has not been confirmed.
- Escalate when a feature flag cannot be disabled without a code deploy — that is not a feature flag, it is a hardcoded branch.
- Escalate when container images reference `latest` tags or are not pinned to an immutable digest.
- Escalate when there is no named owner for post-release monitoring and the change affects a production SLO path.
- Escalate when the deployment affects global gateway routing, CDN configuration, or DNS that has no automated rollback.
- Escalate when Terraform, Pulumi, Crossplane, or other IaC changes affect production IAM, public exposure, DNS, CDN, WAF, KMS, VPC/subnet, or cloud account/project boundaries without reviewed plan evidence.
- Escalate when a regulated release lacks change approval evidence, artifact digest, scan evidence, or audit retention target.
- Escalate when an emergency release lacks an incident commander, technical lead, communications owner, or rollback decision signal.
- Escalate to `agent-execution-discipline` when an agent claims deployment readiness without pipeline output, rollback evidence, residual risk, and handoff boundary.

## Critical Details
- **Kubernetes rolling update guarantee**: `maxUnavailable: 0` ensures no capacity reduction during rollout; `maxSurge: 1` controls the speed. Misconfigured rolling updates can take down entire services.
- **Readiness probe misconfiguration** is the second most common cause of post-deploy incidents: if the readiness probe path returns 200 before the application is actually ready, traffic is routed to a not-yet-initialized pod.
- **Migration window**: During a rolling update, both old and new application versions run simultaneously. A migration that adds a `NOT NULL` column without a default will crash old pods trying to `INSERT` without the new column.
- **Feature flag cleanup**: Flags that are never removed become permanent complexity. Every flag must have a removal ticket created before or at the time it is merged to production.
- **`kubectl rollout undo`** rolls back the Deployment, not the database migration. Always test database rollback migration before production deployment.
- **Config drift between environments**: The most common staging-to-production discrepancy is environment variable naming. Use a config audit before every deploy.
- **Canary traffic management**: A 1% canary at 100 RPS = 1 request/second to canary. At less than 1 RPS, a canary test has no statistical significance — monitor for at least 100 requests to canary before proceeding.
- **Secret rotation during deployment**: If a secret is rotated as part of the deployment, both old and new application versions must accept both old and new secret values during the rollout window.
- **IaC release order**: Plan review, approval, state lock, apply, post-apply verification, drift check, and rollback notes are distinct release steps. Skipping directly from plan generation to apply removes the evidence needed to diagnose failed infrastructure changes.
- **Cloud account/project blast radius**: A change in a shared production account has a larger rollback and audit burden than the same change in a per-service project. Release plans must state the boundary explicitly.
- **Incident hotfix cadence**: During SEV response, the release owner should publish concise internal updates on every mitigation attempt, validation result, rollback decision, and final resolution handoff.

### Anti-Examples

| Release Pattern | Problem | Corrected Approach |
|---|---|---|
| `image: myapp:latest` in prod manifest | Non-reproducible, can change without intent | `image: myapp@sha256:abc123...` or semantic tag `myapp:1.4.2` |
| "Rollback: git revert + redeploy" | Not tested; ignores data migration | Documented rollback procedure tested in staging; includes rollback migration |
| Migration adds `NOT NULL` column, deployed with code | Old pods crash on INSERT during rollout | Add nullable column first (backward compat), then add NOT NULL after all pods updated |
| Feature flag hardcoded in `if (env == 'production')` | Cannot be disabled without code deploy | Use feature flag service; flag evaluates based on flag state, not environment |
| Staging uses mock integrations, production uses live APIs | Staging results don't predict production failures | Mirror production integrations in staging with sandboxed/test accounts |

## Failure Modes
- **Code ships before migration compatibility**: New code expects a column that doesn't exist yet — all database writes fail immediately after deployment.
- **Feature flags cannot be disabled**: A flag is a hardcoded branch — disabling requires a hotfix deploy under incident pressure.
- **Rollback fails due to data migration**: The old service cannot read the new schema; rollback requires manual database intervention; the incident extends from minutes to hours.
- **Environment config differs from staging**: A required environment variable exists in staging but is missing in production — the service crashes on startup.
- **No post-release owner**: The deployment is "done" but no one is watching error rates — a 50% error rate in a low-traffic feature is discovered 3 hours later via a user report.
- **Secrets in container image**: A CI/CD script bakes a secret into the container during build — the secret leaks via docker image history inspection.
- **Canary at insufficient traffic**: A 1% canary runs for 5 minutes at 0.1 RPS — zero requests hit the canary; the rollout proceeds with no validation.
- **Multi-service deploy without sequencing**: Service A and Service B are deployed simultaneously; A expects B's new contract; during the window both old and new B run — A crashes against old B.

## Reference Loading Policy
Do not load every reference by default. Treat references as targeted support selected by the router and the task risk.

- L1 changes: do not read references unless the task touches security, data, auth, external integration, performance, release, or irreversible behavior.
- L2 changes: read `references/capabilities/index.md` and only capability files explicitly selected by `change-forge-router`.
- L3 changes: read all selected capability references and `references/checklist.md` when present.
- L4/L5 changes: read all selected capability references, `references/checklist.md` when present, and domain extension references when selected.
- Selected capability reference path format: `references/capabilities/<capability-id>-<capability-name>.md`.

Examples:
- `42 idempotency-retry-design` -> `references/capabilities/42-idempotency-retry-design.md`
- `82 solution-optimality-evaluation` -> `references/capabilities/82-solution-optimality-evaluation.md`

## Output Contract
Return a structured release plan with:
- **Deployment strategy**: Rolling / canary / blue-green with configuration (percentages, replica counts, traffic routing).
- **Pre-deployment checklist**: Environment config validation, secrets audit, staging parity confirmation, migration compatibility check.
- **Cloud governance checklist**: IaC plan review, account/project boundary, namespace boundary, IAM diff, DNS/CDN/WAF/gateway rollback, KMS/key rotation impact, resource tagging, and audit trail.
- **Helm release plan**: chart version, values diff, rendered manifest diff, CRD/hook handling, atomic upgrade, rollback scope, and verification.
- **Migration sequence**: Forward migration execution order (before or after code deploy), rollback migration, tested execution evidence.
- **Feature flag plan**: Flag state at deployment, % rollout schedule, disableability confirmation, cleanup task reference.
- **Rollback procedure**: Step-by-step rollback instructions with expected execution time; tested in staging.
- **Communication plan**: Consumer notification, partner coordination, on-call notification if needed.
- **Incident release plan**: SEV severity, mitigation vs. resolution, incident roles, customer/status page communication owner, and validation signal when applicable.
- **Compliance evidence**: Change approval, deploy audit event, artifact digest, SBOM/vulnerability scan evidence, evidence owner, and retention period.
- **Post-release monitoring plan**: Named owner, dashboards, metrics, SLO burn rate, duration of watch window.
- **Execution discipline evidence**: Deployment commands or pipeline links, exit status, failed-attempt ledger when applicable, route repair decision, and closure package.
- **Release notes**: Human-readable changelog entries (Keep a Changelog format) for affected audiences.
- **Residual risks**: Known risks with mitigation or acceptance rationale.

## Evidence Contract
Close a release plan only when all five canonical answers are concrete (answer schema: `agent-execution-discipline`):
- **Basis**: the rollout topology (flag/canary/blue-green) and schema/config compatibility rule the plan rests on.
- **Files and boundaries inspected**: the environment config, migration scripts, IaC/Helm values, and secret references read, and the staging-parity boundary confirmed.
- **Placement rationale**: why the migration sequences before or after the code deploy, and why the rollback boundary is drawn where it is.
- **Validation commands**: the staging deploy, rollback rehearsal, `helm diff`/IaC plan, and pipeline run, each with its outcome.
- **Residual risk**: the rollback trigger, post-release watch signal, and the unverified compatibility path that remains, with the named owner.

## Quality Gate
1. Every deployment artifact is immutably tagged — no `latest` tags in production.
2. All environment variables required by the new version are verified to exist in the target environment.
3. All secrets are retrieved from an audited secret management service — none hardcoded or in plaintext logs.
4. The database migration is backward-compatible with the current application version during the rollout window.
5. The rollback procedure is documented and has been executed in staging.
6. Feature flags can be disabled without a code deploy.
7. Staging has been validated with production-equivalent configuration and integration surface.
8. A named owner with a defined watch window and monitoring dashboard is assigned for post-release observation.
9. External consumers, partners, and on-call engineers are notified per the communication plan.
10. Release notes are accurate, human-readable, and audience-appropriate.
11. IaC/cloud governance changes have reviewed plan evidence, blast-radius boundary, IAM/network/KMS/DNS impact review, and rollback procedure.
12. Regulated releases retain approval, audit event, artifact digest, SBOM/vulnerability scan evidence, owner, and retention period.
13. Incident hotfixes distinguish mitigation from resolution and identify incident commander, technical lead, communications owner, and validation signal.
14. Agent-assisted release work includes evidence inventory, route repair after repeated failure, residual risks, and handoff target.

## Handoff
- **reliability-observability-gate** — for SLO burn rate targets, canary metric baselines, and post-release alert thresholds.
- **security-privacy-gate** — when secrets management, container image security, or compliance evidence is required.
- **data-api-contract-changer** — when migration rollback safety or API contract versioning must be confirmed before release.
- **change-documentation-gate** — for release notes, runbook updates, and consumer migration guide publishing.
- **quality-test-gate** — when release gate criteria require test evidence that has not yet been produced.
- **failure-diagnosis** — when a release is part of incident mitigation or root-cause confirmation.
- **agent-execution-discipline** — when release closure lacks evidence, route repair, risk boundary, or validation results.

## Completion Criteria
The change has an approved release plan with an immutably tagged artifact, verified environment configuration, cloud/IaC governance evidence when applicable, a backward-compatible migration sequence with tested rollback, a disableable feature flag if applicable, a tested rollback procedure, a named post-release monitoring owner, incident or compliance evidence when applicable, a communication plan executed, and release notes published before the deployment window opens.
