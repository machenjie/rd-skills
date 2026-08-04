# Keychain, XPC, and Helper Contracts

Load this Reference only when macOS secrets, XPC, helpers, agents, daemons,
login items, interprocess protocols, or privilege boundaries change.

Official Apple Developer pages below were accessed on 2026-07-24.

## Identity and Protocol Decision

- Bind Keychain items to a declared secret, account, access control, access
  group, migration, deletion, and recovery rule.
- Define XPC request/response types, caller and peer identity, authorization,
  cancellation, timeout, restart, version negotiation, and idempotency.
- Treat every process boundary as untrusted until code identity, entitlements,
  input, and requested authority are verified.

## Helper and Login Decision

- Record whether work belongs in an embedded XPC service, login item, Launch
  Agent, Launch Daemon, or no helper, based on lifecycle and privilege.
- Bind helper registration, installation, user visibility, enable/disable,
  upgrade, removal, signing, sandbox, and crash recovery to one owner.
- Exercise missing helper, rejected peer, protocol skew, crash/restart, disabled
  login item, partial upgrade, and orphaned registration.

## Required Record

Return secret owner, process topology, peer/auth contract, helper lifecycle,
privilege and signing boundary, failure evidence, limits, and residual risk.

## Primary Sources

- [Keychain services](https://developer.apple.com/documentation/security/keychain-services/)
- [XPC](https://developer.apple.com/documentation/xpc)
- [SMAppService](https://developer.apple.com/documentation/servicemanagement/smappservice)

## Source Limits

These rolling pages do not establish repository helper topology, protocol
schema, peer requirements, installer authority, effective entitlements,
supported OS versions, privileged approval, or recovery behavior.
