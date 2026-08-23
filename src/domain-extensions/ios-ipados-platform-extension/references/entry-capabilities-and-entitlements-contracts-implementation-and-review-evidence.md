# Entry, Capabilities, and Entitlements Implementation and Review Evidence

Load this Reference only after the accepted entry and entitlement
`boundary-decision` must be implemented or reviewed.

## Required Decision Input

Use the carried exposed-entry inventory, trust checks, capability owner, and
target/App ID binding. Stop when that boundary or its artifact scope is stale.

## Implementation and Review Evidence

- Compare source entitlements, provisioning entitlements, and the signed
  artifact; project settings alone are not final proof.
- Exercise missing, revoked, mismatched, malformed-entry, replay, wrong-account,
  and duplicate-delivery outcomes without logging APNs tokens.

## Required Record

Return artifact entitlement evidence, provisioning-source limits, negative-path
results, unavailable provider/association proof, and residual risk.
