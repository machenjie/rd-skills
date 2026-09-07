# Signing, Notarization, and Distribution Implementation and Review Evidence

Load this Reference only after the accepted artifact/channel
`decision-record` must be implemented or reviewed.

## Required Decision Input

Use the carried channel, artifact graph, hardened-runtime, entitlement, and
signing decision. Stop when the immutable artifact binding is missing or stale.

## Implementation and Review Evidence

- Verify signing and hardened-runtime obligations for the app, frameworks,
  plug-ins, XPC services, helpers, agents, command tools, and installer package.
- For independent distribution, bind timestamp, notarization log/ticket or
  stapling, package, and Gatekeeper evidence to the exact artifact.
- Keep build, local signature, notarization, Gatekeeper, App Store, and field
  installation as separate proof classes.
- Route certificate authority, submission, rollout, release, and rollback to
  `delivery-release-gate`.

## Required Record

Return artifact-graph evidence, signing-source limits, notarization/Gatekeeper
proof, unavailable evidence, authorization owner, OS scope, and risk.
