# Data, Keychain, and Extension Contracts

Load this Reference only when local secrets, protected files, shared containers,
app groups, or app-extension data boundaries change.

Official Apple Developer pages below were accessed on 2026-07-24.

## Data and Key Decision

- Classify each value by sensitivity, account, durability, protection while
  locked, migration, backup, logout, deletion, and recovery requirements.
- Use Keychain only for a declared small-secret purpose.
- Bind each item to its accessibility class, access group, authentication
  policy, account, invalidation, and recovery.
- Select Data Protection from required locked-device behavior.
- Verify effective file protection rather than assuming a default.

## Shared and Extension Boundary

- Bind each app group and shared container to the exact app and extension
  targets, team, entitlement, schema, and concurrent-access protocol.
- Treat the host and extension as separate processes with separate lifecycle,
  memory, failure, and least-privilege boundaries.
- Exercise device lock, missing or invalid key, account switch, partial
  migration, extension termination, corrupt data, and mismatched entitlement.

## Required Record

Return the data inventory, storage/key owner, protection and access-group rule,
shared schema/coordination, migration/recovery proof, limits, and residual risk.

## Primary Sources

- [Keychain services](https://developer.apple.com/documentation/security/keychain-services/)
- [FileProtectionType](https://developer.apple.com/documentation/foundation/fileprotectiontype)
- [Configuring app groups](https://developer.apple.com/documentation/xcode/configuring-app-groups/)
- [App extensions](https://developer.apple.com/documentation/uikit/app-extensions)

## Source Limits

These rolling pages do not establish repository schemas, threat model, effective
entitlements, backup transport, device lock state, extension types, privacy
retention, or end-to-end protection. Reusable privacy rules stay in Foundation.
