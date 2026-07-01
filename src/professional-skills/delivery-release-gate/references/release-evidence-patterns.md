# Release Evidence Patterns

Use this reference when a release plan needs concrete proof for approval, rollback, audit retention, incident hotfix, or repeated failed-attempt closure. Keep evidence bounded to the release obligation and avoid copying full command output into the handoff.

## Evidence Map
- **Pipeline or artifact:** record pipeline run, immutable artifact tag or digest, build provenance, test gate, exit code, artifact location, and what the run does not prove about production config.
- **Config or secret:** record typed config validation, target environment diff, secret reference source, rotation compatibility, redacted output rule, and rollback or disable path.
- **Migration or backfill:** record forward command, rollback command or forward-fix decision, old/new version compatibility, lock/runtime impact, reconciliation signal, and owner.
- **Helm, Kubernetes, or IaC:** record rendered diff or plan, policy/security review boundary, state lock or GitOps sync status, apply command, rollback scope, drift check, and unowned external state.
- **Canary or post-release watch:** record promotion and abort thresholds, request volume, SLO/error/latency signal, watch owner, duration, dashboard/report artifact, and rollback trigger.
- **Incident or regulated release:** record approval, incident role split, mitigation versus resolution, customer communication owner, deploy audit event, SBOM/scan evidence, retention owner, and freshness date.

## Closure Rules
- Every accepted release proof names command or pipeline, validator when available, output/report artifact, exit code or status, evidence freshness, and evidence limit.
- A failed deploy, migration, canary, or rollback attempt must be logged with signature, hypothesis, changed route, next owner, and the reason another retry is safe.
- A release can proceed only when unresolved evidence gaps are explicitly approved, owned, and tied to a rollback or stop condition.

