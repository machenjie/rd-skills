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
Owns release-delivery; also serves infrastructure-deployment, kubernetes-helm, and ci-cd surfaces across the execution path:
- **Planning and implementation:** map deployable artifacts, environment config, migration order, flag state, release owners, rollback boundary, and existing platform controls before coding or changing release machinery.
- **Coding support:** keep release-affecting config defaults, feature-flag branches, deploy scripts, Helm/IaC values, and pipeline changes compatible with old and new runtime versions.
- **Debugging and bug-fix:** diagnose failed pipeline, deploy, migration, config, canary, rollback, or post-release signal with fresh evidence before retrying the same path.
- **Code-review and refactoring:** reject speculative wrappers, unowned flags, hidden config switches, mutable deploy artifacts, and refactors that weaken rollback, audit, or release observability.
- **Testing, release, and handoff:** require staging, rollback, canary, config, audit, post-release watch, and release-note evidence with residual risk and next gate.

## Non-Negotiable Rules
- **Direct use still runs the runtime prompt flow.** When `delivery-release-gate` is invoked directly and router reclassification is skipped, target-project engineering work must still clarify requirements before action, inspect relevant code/tests/config/docs before planning, name a TDD or validation signal before implementation, map each action to an owner skill and a different review skill, repair and re-review findings, and hand off with validation evidence, residual risk, and route/stage manifests when routed.
- Non-trivial direct use still requires `repository-context-map` before planning when affected files, callers, local conventions, or source-of-truth boundaries are not already inspected.
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
- **Prefer existing release controls before new release machinery** — use current CI jobs, platform feature flags, staged rollout controls, rendered diff checks, config validation, and rollback paths before adding a new pipeline wrapper, deployment tool, environment switch, hook, or script.
- **Release tools require permission and sandbox evidence** — before deploy, migration, rollback, IaC apply, Helm/Kubernetes command, secret rotation, cloud change, or network write, record the tool, permission state, sandbox boundary, dry-run/rendered diff, rollback/revert path, and secret/output redaction rule.

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
- **Minimal correctness**: Existing CI/CD, release platform, flag service, config validation, and rollback mechanism considered before new tool, wrapper, script, hook, or runtime branch.
- **Compliance evidence**: Which approval, artifact digest, SBOM, vulnerability scan, change ticket, and deploy audit event must be retained?
- **Incident mitigation**: If this release is part of a SEV response, which action is mitigation, which action is resolution, and who owns customer-facing updates?

## Mode Matrix
Select the release mode before approving deployment, migration, config, IaC, rollback, or incident hotfix work.

| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities | Skip by default |
|---|---|---|---|---|---|
| Standard rollout | App deploy, config, feature flag, artifact, or pipeline release. | Immutable artifact, config compatibility, watch owner, rollback signal. | Pipeline output, env audit, flag state, monitoring window. | `ci-cd`, `release-rollback`, `configuration-runtime-policy`, `reliability-observability-gate` | Canary unless blast radius requires it. |
| Migration-sensitive release | DB/schema/backfill/contract/migration or old/new version coexistence. | Expand/migrate/contract, rollback, version skew, data safety. | Forward/rollback migration test, compatibility matrix, sequence. | `data-migration-design`, `data-api-contract-changer` | Contract/delete phase until consumers migrate. |
| Progressive delivery | Canary, blue-green, traffic split, feature flag rollout. | Metrics thresholds, promotion/abort decision, statistical signal. | Canary plan, request volume, SLO burn, rollback action. | `reliability-observability-gate`, `performance-budgeting` | 100% rollout before signal threshold. |
| IaC/K8s/Helm/GitOps | Terraform/Pulumi/Helm/K8s/Gateway/IAM/DNS/CDN/WAF/KMS. | Plan diff, blast radius, policy/security, state lock, rollback. | Rendered diff, plan/apply output, drift check, rollback note. | `kubernetes-gateway`, `secret-configuration-security`, `security-privacy-gate` | Manual apply without reviewed plan. |
| Incident hotfix | SEV mitigation, emergency config, rollback, traffic shift. | Separate mitigation from resolution, preserve evidence, communicate. | Incident roles, validation signal, rollback decision, comms owner. | `failure-diagnosis`, `reliability-observability-gate`, `change-documentation-gate` | Cleanup/refactor during mitigation. |
| Regulated/compliance release | SOC2/ISO/PCI/HIPAA/SOX, artifact signing, approval, audit retention. | Audit-ready evidence, exception owner, retention, approval trail. | Approval, artifact digest, SBOM/scan, deploy event, retention owner. | `security-privacy-gate`, `change-documentation-gate` | Release approval without evidence packet. |

## Proactive Professional Triggers

- **Signal:** rollback plan says only "revert/redeploy" while migration, config, feature flag, or external state changes. **Hidden risk:** rollback fails after state moves forward. **Required professional action:** define state-aware rollback. **Route to:** `release-rollback`, `data-api-contract-changer`. **Evidence required:** rollback command/test, data compatibility.
- **Signal:** migration adds NOT NULL, drop/rename, backfill, or contract phase without old/new version matrix. **Hidden risk:** rolling deploy crashes old or new pods. **Required professional action:** enforce expand/migrate/contract. **Route to:** `data-migration-design`, `backend-change-builder`. **Evidence required:** compatibility matrix and migration tests.
- **Signal:** feature flag cannot be disabled without deploy or lacks cleanup owner. **Hidden risk:** incident mitigation fails, rollback is blocked, or permanent flag debt remains ownerless. **Required professional action:** require remote disable path, runtime policy, and cleanup/deletion governance before release. **Route to:** `configuration-runtime-policy`, `cleanup-deletion-governance`, `release-rollback`. **Evidence required:** flag config diff, disable-test output, owner, expiry, removal ticket, and rollback behavior.
- **Signal:** config/secret/env var changes are not validated in target environment. **Hidden risk:** startup crash, secret leak, or environment drift during deployment. **Required professional action:** run config policy and secret audit before deploy. **Route to:** `configuration-runtime-policy`, `secret-configuration-security`, `security-privacy-gate`. **Evidence required:** typed config/defaults, environment diff, secret source proof, rotation impact, and validation output.
- **Signal:** canary has too little traffic or no SLO burn/error/latency threshold. **Hidden risk:** false confidence before full rollout. **Required professional action:** set promotion/abort criteria. **Route to:** `reliability-observability-gate`. **Evidence required:** request volume, dashboard, threshold.
- **Signal:** Helm/K8s/GitOps/IaC plan changes IAM, ingress, DNS, CDN, WAF, KMS, namespace, probes, or CRDs without rendered diff/rollback. **Hidden risk:** infrastructure outage or public exposure. **Required professional action:** require plan review and rollback. **Route to:** `kubernetes-gateway`, `security-privacy-gate`. **Evidence required:** plan/rendered diff, policy impact, rollback note.
- **Signal:** release depends on architecture, generated-file, import, export, or forbidden-dependency rules that are only documented and not enforced in CI. **Hidden risk:** release quality depends on memory and review discipline, so drift reappears after deployment. **Required professional action:** make the rule enforceable or define a timeboxed report-only migration before release. **Route to:** `architecture-enforcement-tooling`, `ci-cd`, `quality-test-gate`. **Evidence required:** rule list, tool choice, CI command, representative failure, generated-code exceptions, owner, and migration path.
- **Signal:** release lacks post-release owner, watch window, or dashboard. **Hidden risk:** regression discovered by users. **Required professional action:** assign operational watch. **Route to:** `reliability-observability-gate`. **Evidence required:** owner, duration, metrics, rollback trigger.
- **Signal:** regulated release lacks approval, artifact digest, SBOM/scan, deploy audit event, or retention metadata. **Hidden risk:** missing evidence causes audit failure after release. **Required professional action:** block until the release evidence chain exists. **Route to:** `change-documentation-gate`, `security-privacy-gate`. **Evidence required:** audit packet with approval, artifact digest, scan report, deploy event, retention owner, and freshness date.
- **Signal:** release work adds a new CI/CD wrapper, deploy script, hook, feature-flag branch, config switch, or IaC abstraction while the existing platform can express the rollout, validation, and rollback requirement. **Hidden risk:** release complexity becomes another failure surface and bypasses known audit paths. **Required professional action:** run minimal-correctness review and keep any shortcut tied to a rollback owner and cleanup trigger. **Route to:** `minimal-correct-implementation`, `configuration-runtime-policy`, `cleanup-deletion-governance`. **Evidence required:** existing release control considered, rejected new machinery or justification, rollback proof, cleanup owner, and validation command.
- **Signal:** deploy, migration, Helm/Kubernetes, IaC, cloud, secret, or rollback command lacks permission/sandbox classification. **Hidden risk:** the agent mutates live release state without reviewed boundary or rollback evidence. **Required professional action:** classify tool permission and sandbox before execution. **Route to:** `agent-tool-permission-sandbox`, `security-privacy-gate`. **Evidence required:** command/action class, permission state, sandbox/dry-run/rendered diff, rollback path, and redaction rule.

## Foundation Capability Support

- **configuration-runtime-policy** — when release behavior depends on typed config, env vars, defaults, feature flags, kill switches, mode/kind switches, or config validation.
- **cleanup-deletion-governance** — when flags, fallbacks, compatibility branches, deprecated APIs, or rollout shims need owner, expiry, removal condition, telemetry, and rollback.
- **architecture-enforcement-tooling** — when release readiness depends on module/import/export/generated-code rules being enforced by CI rather than documented only.

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
- L2 changes: read `references/capabilities/index.md`, only capability files explicitly selected by `change-forge-router`, and [references/checklist.md](references/checklist.md) when a deployable artifact, config, flag, migration, or rollback boundary is in scope.
- L3 changes: read all selected capability references plus [references/delivery-output-and-gates.md](references/delivery-output-and-gates.md) when the release plan needs the full field list, quality gate, or handoff table.
- L4/L5 changes: read all selected capability references, [references/release-evidence-patterns.md](references/release-evidence-patterns.md), and domain extension references when selected.
- Selected capability reference path format: `references/capabilities/<capability-id>-<capability-name>.md`.

Examples:
- `42 idempotency-retry-design` -> `references/capabilities/42-idempotency-retry-design.md`
- `82 solution-optimality-evaluation` -> `references/capabilities/82-solution-optimality-evaluation.md`

## Output Contract
Return a structured release plan with actionable evidence:
- **Mode selected:** standard rollout, migration-sensitive, progressive delivery, IaC/K8s/Helm/GitOps, incident hotfix, or regulated release, with trigger signal.
- **Boundaries inspected:** pipeline, artifact, config, secrets, migrations, flags, Helm/K8s/IaC, cloud/network, dashboards, runbooks, consumers, audit boundaries, and skipped areas with reason.
- **Release judgment:** rollout strategy, rollback boundary, migration/config compatibility, canary criteria, incident/compliance decision, risks ruled out, and risks retained.
- **Execution plan:** deployment strategy, pre-deploy checklist, cloud governance, Helm plan, migration sequence, feature flag plan, rollback steps, communication plan, and post-release watch.
- **Evidence package:** pipeline/staging/rollback/Helm/IaC/config/canary/post-release checks, artifact digest, SBOM/scan, deploy audit event, command status, failed-attempt ledger, and evidence limits.
- **Tool permission/sandbox evidence:** deploy/migration/IaC/Helm/Kubernetes/cloud/secret action class, permission state, sandbox boundary, dry-run/rendered diff, rollback/revert path, and redaction rule.
- **Approval decision:** approved, blocked, deferred, rollback-only, or no-go, with the required owner, stop condition, and next validation command.
- **Reuse / placement rationale:** why migration, config, flag, Helm/IaC, pipeline, watch, and rollback responsibilities sit in the selected release boundary.
- **Behavior preservation:** old/new version compatibility, config defaults, feature flag off-state, public contract, rollback behavior, residual risk, and next gate.
- **Evidence limits and residual risk:** what each release artifact proves, what remains unverified, who owns it, and whether release can proceed.

For the full output field list, quality gate, and handoff table, load `references/delivery-output-and-gates.md`.

## Evidence Contract
Close a release plan only when all five canonical answers are concrete (answer schema: `agent-execution-discipline`):
- **Basis**: the selected mode, rollout topology (flag/canary/blue-green), schema/config compatibility rule, incident mitigation goal, or compliance control the plan rests on.
- **Files and boundaries inspected**: environment config, migration scripts, IaC/Helm values, secret references, pipeline, artifact digest, flags, dashboards, runbooks, consumers, and staging/prod parity boundary confirmed.
- **Placement rationale**: why the migration sequences before or after the code deploy, and why the rollback boundary is drawn where it is.
- **Validation commands**: staging deploy, rollback rehearsal, `helm diff`/IaC plan, rendered manifest diff, pipeline run, config audit, and post-release query run, each with its outcome, what evidence proves, and what evidence does not prove.
- **Release judgment and handoff**: mode selected, rollout/rollback judgment, behavior preservation, evidence limits, and next gate.
- **Residual risk**: rollback trigger, post-release watch signal, config parity, migration compatibility, IaC rollback, or unverified consumer path that remains, with the named owner.

## Quality Gate
- Deployment artifacts are immutable; target environment config, audited secrets, staging parity, and production-equivalent integration surfaces are verified.
- Migration, feature flag, cloud/IaC, Helm/K8s, consumer coordination, and rollback paths are compatible with old/new versions and tested proportionally to risk.
- Post-release watch has named owner, dashboard, duration, SLO/error/latency signals, and rollback trigger.
- Release notes, regulated evidence, incident role split, deploy audit event, artifact digest, SBOM/scan evidence, owner, and retention are present when applicable.
- Agent-assisted release work includes evidence inventory, route repair after repeated failure, residual risks, handoff target, and tool permission/sandbox evidence.

## Handoff
- Hand SLO burn, canary metrics, post-release alerts, secrets, container image security, and compliance evidence to reliability and security gates.
- Hand migration rollback safety, API contract versioning, release notes, runbooks, consumer migration guides, and missing test evidence to data/API, documentation, and quality gates.
- Hand incident mitigation/root-cause confirmation or missing release evidence, route repair, risk boundary, and validation results to `failure-diagnosis` or `agent-execution-discipline`.

## Completion Criteria
The change has an approved release plan with an immutably tagged artifact, verified environment configuration, cloud/IaC governance evidence when applicable, a backward-compatible migration sequence with tested rollback, a disableable feature flag if applicable, a tested rollback procedure, a named post-release monitoring owner, incident or compliance evidence when applicable, a communication plan executed, and release notes published before the deployment window opens.
