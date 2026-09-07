# Architecture, Signing, and Distribution Contracts

Load this Reference only when x86/x64/ARM64, signing, Microsoft Store,
enterprise, or direct distribution evidence changes the decision.

Official Microsoft Learn pages below were accessed on 2026-07-24.

## Artifact Decision

- Read target architectures, runtime identifiers, native dependencies, package
  manifests, signing inputs, timestamp policy, and channel from repository facts.
- Inspect each executable, DLL, COM server, helper, runtime, and installer in the
  final artifact; a compatible main executable proves no dependent architecture.
- Bind signature identity and trust chain to the exact final artifact and
  installer while keeping keys private and development certificates outside
  release evidence.
- Separate Microsoft Store, enterprise management, and direct distribution
  requirements, identity, update ownership, policy, and recovery.
- Route signing authorization, channel approval, rollout, rollback, and
  distribution decisions to `delivery-release-gate`.

## Primary Sources

- [.NET RID catalog](https://learn.microsoft.com/en-us/dotnet/core/rid-catalog)
- [MSIX signing overview](https://learn.microsoft.com/en-us/windows/msix/package/signing-package-overview)
- [Publish to Microsoft Store](https://learn.microsoft.com/en-us/windows/apps/publish/)
- [Package and deploy](https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/)

## Source Limits

These rolling pages do not establish repository architecture declarations,
dependency slices, certificate custody, enterprise policy, Store acceptance,
installed population, rollout authorization, or hardware execution.
