# Delivery Output And Gates

Load this reference when `delivery-release-gate` needs the full release output field list, exhaustive quality gate, or detailed handoff table. The skill body keeps default runtime context compact.

## Output Contract
Return a structured release plan with:
- **Mode selected**: standard rollout, migration-sensitive, progressive delivery, IaC/K8s/Helm/GitOps, incident hotfix, or regulated release, with trigger signal.
- **Boundaries inspected**: pipeline, artifact, config, secrets, migrations, flags, Helm/K8s/IaC, DNS/CDN/WAF/gateway, cloud IAM/KMS, dashboards, runbooks, consumers, and audit boundaries inspected or skipped with reason.
- **Professional judgment**: rollout, rollback, migration/config compatibility, canary, incident, or compliance decision and risks ruled out or retained.
- **Deployment strategy**: rolling / canary / blue-green with configuration (percentages, replica counts, traffic routing).
- **Pre-deployment checklist**: environment config validation, secrets audit, staging parity confirmation, migration compatibility check.
- **Cloud governance checklist**: IaC plan review, account/project boundary, namespace boundary, IAM diff, DNS/CDN/WAF/gateway rollback, KMS/key rotation impact, resource tagging, and audit trail.
- **Helm release plan**: chart version, values diff, rendered manifest diff, CRD/hook handling, atomic upgrade, rollback scope, and verification.
- **Migration sequence**: forward migration execution order (before or after code deploy), rollback migration, tested execution evidence.
- **Feature flag plan**: flag state at deployment, percent rollout schedule, disableability confirmation, cleanup task reference.
- **Rollback procedure**: step-by-step rollback instructions with expected execution time; tested in staging.
- **Communication plan**: consumer notification, partner coordination, on-call notification if needed.
- **Incident release plan**: SEV severity, mitigation vs. resolution, incident roles, customer/status page communication owner, and validation signal when applicable.
- **Compliance evidence**: change approval, deploy audit event, artifact digest, SBOM/vulnerability scan evidence, evidence owner, and retention period.
- **Post-release monitoring plan**: named owner, dashboards, metrics, SLO burn rate, duration of watch window.
- **Execution discipline evidence**: deployment commands or pipeline links, exit status, failed-attempt ledger when applicable, route repair decision, and closure package.
- **Tool permission/sandbox evidence**: deploy/migration/IaC/Helm/Kubernetes/cloud/secret action class, permission state, sandbox boundary, dry-run/rendered diff, rollback or revert path, and redaction rule.
- **Validation evidence**: pipeline, staging, rollback, Helm/IaC, config, canary, post-release, or audit checks run, with outcomes tied to the release obligation.
- **Reuse and placement rationale**: why migration, config, flag, Helm/IaC, pipeline, watch, and rollback responsibilities sit in the selected release boundary.
- **Minimal Correctness Decision**: existing release control selected or rejected, new release machinery avoided or justified, stale flag/config/script deletion plan, and shortcut ceiling with rollback trigger.
- **Behavior preservation**: old/new version compatibility, config defaults, feature flag off-state, public contract, and rollback behavior preserved or intentionally changed.
- **Release notes**: human-readable changelog entries (Keep a Changelog format) for affected audiences.
- **Evidence limits**: what pipeline, staging, rollback, Helm/IaC, config, canary, and post-release evidence proves and what production, consumer, or data risks remain unproven.
- **Residual risks**: known risks with mitigation or acceptance rationale.
- **Next gate/handoff**: reliability, security, data/API, docs, incident, or no-next-gate rationale.

## Quality Gate
1. Every deployment artifact is immutably tagged; no `latest` tags in production.
2. All environment variables required by the new version are verified to exist in the target environment.
3. All secrets are retrieved from an audited secret management service; none hardcoded or in plaintext logs.
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
15. Release-affecting tools have permission/sandbox evidence before execution, including dry-run/rendered diff when available, rollback/revert path, and redaction rules for secrets and command output.

## Handoff
- **reliability-observability-gate**: SLO burn rate targets, canary metric baselines, and post-release alert thresholds.
- **security-privacy-gate**: secrets management, container image security, or compliance evidence.
- **data-api-contract-changer**: migration rollback safety or API contract versioning must be confirmed before release.
- **change-documentation-gate**: release notes, runbook updates, and consumer migration guide publishing.
- **quality-test-gate**: release gate criteria require test evidence that has not yet been produced.
- **failure-diagnosis**: release is part of incident mitigation or root-cause confirmation.
- **agent-execution-discipline**: release closure lacks evidence, route repair, risk boundary, or validation results.
