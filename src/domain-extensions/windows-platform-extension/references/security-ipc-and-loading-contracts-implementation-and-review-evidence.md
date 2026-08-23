# Security, IPC, and Loading Implementation and Review Evidence

Load this Reference only after the accepted Windows security, IPC, and loading
boundary requires implementation or review evidence.

## Required Decision Input

- Consume the accepted principal/session matrix, privilege/container decision,
  secret scope/recovery, IPC authorization, and DLL policy; do not reroute.

## Implementation and Review Evidence

- Exercise denied elevation, AppContainer denial, wrong user/session, secret
  invalidation, spoofed IPC, unavailable peer, and attacker-controlled DLL paths.
- Prove recovery does not broaden scope, expose secrets, or silently lower trust.

## Required Record

Return an evidence record, proof limit, and validation plan for failure behavior
and residual risk.
