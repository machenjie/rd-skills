# Provider API and Managed Service Authority

Load this Reference only when provider, SDK, service API compatibility, or
managed-service responsibility changes implementation or operations.

Official AWS, Azure, and Google Cloud documentation below was accessed on
2026-07-24.

## Compatibility Boundary

- Pin infrastructure provider, SDK, service API, schema, preview/stability
  status, location support, registration, and retirement evidence.
- Distinguish SDK lifecycle from service API lifecycle and source, wire, and
  semantic compatibility.
- Rehearse migration and rollback before a version or retired-surface change.

## Authority Boundary

- For each managed service, record provider authority, customer authority,
  configuration, data, identity, network, patch, upgrade, maintenance, backup,
  evidence, and escalation ownership.
- Verify service-specific responsibility and operational behavior; generic
  IaaS/PaaS/SaaS diagrams and the word managed prove no complete contract.
- Keep production apply, rollout, approval, and rollback with the delivery gate.

## Required Record

Return pinned versions and compatibility evidence, migration window,
provider/customer responsibility matrix, unverified obligations, proof limits,
and residual risk.

## Primary Sources

- [AWS SDK maintenance policy](https://docs.aws.amazon.com/sdkref/latest/guide/maint-policy.html)
- [AWS shared responsibility](https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/shared-responsibility.html)
- [Azure resource providers and types](https://learn.microsoft.com/en-us/azure/azure-resource-manager/management/resource-providers-and-types)
- [Azure shared responsibility](https://learn.microsoft.com/en-us/azure/security/fundamentals/shared-responsibility)
- [Google API versioning](https://google.aip.dev/185)
- [Google Cloud shared responsibility and shared fate](https://docs.cloud.google.com/architecture/framework/security/shared-responsibility-shared-fate)

## Source Limits

These policies do not prove current provider registration, API availability,
SDK support, deprecation window, region support, managed-service behavior,
customer configuration, SLA, or production readiness.
