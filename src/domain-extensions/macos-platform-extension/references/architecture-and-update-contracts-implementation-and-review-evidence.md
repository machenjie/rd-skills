# Architecture and Update Implementation and Review Evidence

Load this Reference only after the accepted architecture/update
`boundary-decision` must be implemented or reviewed.

## Required Decision Input

Use the carried architecture inventory, updater/installer authority, artifact
source, and app/API compatibility matrix. Stop when any binding is stale.

## Implementation and Review Evidence

- Inspect every app, framework, plug-in, XPC service, helper, and bundled
  executable for each claimed architecture.
- Test native Apple Silicon and claimed Intel behavior; a universal main
  executable proves no dependent slice or runtime compatibility.
- Exercise interrupted install, invalid signature, partial helper update,
  unsupported architecture, old/new app and API combinations, downgrade, and
  recovery with client plus provider evidence.
- Treat developer-managed distribution as no proof of self-update behavior.

## Required Record

Return artifact slice evidence, hardware/translation results, updater source or
unproven state, mixed-version proof, proof limits, and residual risk.
