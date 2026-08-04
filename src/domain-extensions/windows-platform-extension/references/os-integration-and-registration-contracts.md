# OS Integration and Registration Contracts

Load this Reference only when registry, file-association, protocol-handler, or
COM registration behavior changes the decision.

Official Microsoft Learn pages below were accessed on 2026-07-24.

## Registration Decision

- Inventory every key, hive, view, file type, protocol, COM class, server,
  manifest extension, install scope, owner, and removal rule.
- Select registration from the final identity, with an explicit migration when
  packaged manifests and unpackaged installers coexist.
- Treat activation payloads and COM calls as external inputs with explicit
  validation, caller/identity assumptions, threading, lifetime, and versioning.
- Bind registry and COM views plus upgrade, repair, rollback, and uninstall
  cleanup to each process architecture.
- Respect user/default-app choice; registration does not authorize silently
  taking a default association.

## Failure Proof

- Exercise missing/stale registration, malformed URI/file input, bitness
  mismatch, unavailable COM server, repair, upgrade, and partial uninstall.
- Prove prior-version registrations are migrated or removed without deleting
  unrelated user or machine state.

## Required Record

Return registration inventory, identity/scope, trust and bitness boundaries,
migration/removal rules, failure behavior, installed-host evidence, and risk.

## Primary Sources

- [Registry](https://learn.microsoft.com/en-us/windows/win32/sysinfo/registry)
- [COM portal](https://learn.microsoft.com/en-us/windows/win32/com/component-object-model--com--portal)
- [Handle file activation](https://learn.microsoft.com/en-us/windows/apps/develop/launch/handle-file-activation)
- [Activation](https://learn.microsoft.com/en-us/windows/apps/develop/launch/activate-an-app)

## Source Limits

These rolling pages do not establish application registrations, installer
scope, default-app policy, COM security, bitness inventory, migration safety,
or the target host's current state.
