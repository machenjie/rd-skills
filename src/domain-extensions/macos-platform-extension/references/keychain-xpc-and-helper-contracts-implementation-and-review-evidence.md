# Keychain, XPC, and Helper Implementation and Review Evidence

Load this Reference only after the accepted secret/process/helper
`decision-record` must be implemented or reviewed.

## Required Decision Input

For affected Keychain behavior, use the carried item/account, access-control/group,
migration, deletion, and recovery decisions.
For affected XPC or helpers, use the carried process topology, peer/auth, protocol,
lifecycle, and privilege decisions.
Stop when a required decision for the affected behavior or its controlling
identity/version is missing or stale.

## Implementation and Review Evidence

- For affected Keychain behavior, verify item/account selection, allowed and denied
  access, access-group scope, and selected migration, deletion, and recovery outcomes.
  Bind the result to the accepted secret lifecycle and actual OS/artifact scope.

- Verify the peer identity, entitlement, and input-authorization checks required
  by the accepted caller, channel, input, and privilege contract.
- Verify applicable protocol version, cancellation, timeout, restart, and
  idempotency behavior; a private same-authority channel does not itself require
  an additional peer or privilege gate.
- For affected XPC/helper behavior, exercise applicable missing helper, rejected peer, protocol skew, crash/restart, disabled
  login item, partial upgrade, removal, and orphaned registration.
- When helper deployment is affected, bind signed artifacts and installer state to its selected topology.

## Required Record

Return affected Keychain, XPC, or helper evidence and failure results, OS/version
scope, unavailable lifecycle/access/installer proof, proof limits, and residual risk.
