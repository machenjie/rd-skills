# File, Sandbox, and Entitlement Implementation and Review Evidence

Load this Reference only after the accepted file and sandbox
`boundary-decision` must be implemented or reviewed.

## Required Decision Input

Use the carried authority type, bookmark lifecycle, sandbox owner, and exact
entitlement decision. Stop when file identity, target, or channel is stale.

## Implementation and Review Evidence

- Compare source entitlements with the signed app, helper, XPC service,
  extension, and selected distribution channel.
- Exercise denial, revocation, moved/deleted files, stale bookmark data,
  unavailable volumes, renewal, and balanced security-scope lifetime.
- Do not treat an entitlement as user authorization or data-lifecycle proof.

## Required Record

Return artifact entitlement evidence, denied/stale recovery, OS/deployment and
channel scope, unavailable authority proof, proof limits, and risk.
