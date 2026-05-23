# Security Checks

## Threat Surface

This benchmark touches Helm values, Kubernetes manifests, release pipelines, and secret sourcing. A flawed implementation can expose credentials, ship unsafe defaults, or make rollback look safer than it is.

## Required Checks

- Verify that production values and environment values contain no plaintext secret material.
- Verify that secret-like keys route to ExternalSecrets, SealedSecrets, CSI Secret Store, Vault, or platform secret managers.
- Verify that rendered manifests are checked for accidental Secret literals or ConfigMap credential leakage.
- Verify that rollback notes reject treating Helm rollback as full system rollback.

## Rejection Cases

- Reject any solution that keeps API tokens in values-prod.yaml.
- Reject any solution that skips helm template validation.
- Reject any solution that uses helm upgrade without atomic, wait, and timeout semantics.
- Reject implementations that pass happy path checks while skipping denial, rollback, or failure-mode evidence.
