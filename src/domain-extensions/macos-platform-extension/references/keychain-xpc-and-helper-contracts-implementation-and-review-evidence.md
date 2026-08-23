# Keychain, XPC, and Helper Implementation and Review Evidence

Load this Reference only after the accepted secret/process/helper
`decision-record` must be implemented or reviewed.

## Required Decision Input

Use the carried secret owner, process topology, peer/auth contract, helper
lifecycle, and privilege boundary. Stop when protocol or identity is stale.

## Implementation and Review Evidence

- Verify peer identity, entitlements, input authorization, protocol version,
  cancellation, timeout, restart, and idempotency at every process boundary.
- Exercise missing helper, rejected peer, protocol skew, crash/restart, disabled
  login item, partial upgrade, removal, and orphaned registration.
- Bind signed artifacts and installer state to the selected helper topology.

## Required Record

Return protocol and helper evidence, failure results, OS/version scope,
unavailable installer or privilege proof, proof limits, and residual risk.
