# CI/CD Checklist

- Map triggers, protected targets, required and optional checks, skip/cancel/retry behavior, failure propagation, and bypass authority.
- Trace source revision and behavior-affecting inputs to build identity, SBOM/provenance when required, registry artifact, promotion path, deploy target, and rollback artifact.
- Review fork/event trust, runner identity, workflow permissions, third-party actions, caches, artifacts, credentials, environments, and log redaction.
- Verify affected-work and cache selection includes owners, dependents, contracts, generated inputs, toolchains, and config, with a fallback for uncertain graph coverage.
- Bind IaC, Helm, GitOps, or deploy plans to target state, authority, locking/concurrency, destructive effects, partial failure, and recovery limits.
- Preserve a redacted first-failure record and available artifact references for retries or quarantine; name replacement signal, owner, remediation, and promotion consequence.
- Verify pipeline gates encode the accepted approval, rollout exposure, observation signals, stop conditions, and post-deploy checks for current blast radius, reversibility, policy, and telemetry.
- Separate local/static proof from hosted-provider enforcement and live deployment state; record the unverified boundary.
