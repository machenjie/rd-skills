# Security, IPC, and Loading Implementation and Review Evidence

Load this Reference only after the accepted Windows security, IPC, and loading
boundary requires implementation or review evidence.

## Required Decision Input

- Consume the accepted decisions for affected principal/session, privilege/container,
  secret, IPC, or DLL boundaries.
- Record absent mechanisms; routing remains with Main.

## Implementation and Review Evidence

- Exercise relevant denied elevation, AppContainer, user/session, secret, IPC, or
  DLL-loading paths from those decisions; preserve negative proof for each affected boundary.
- Prove recovery does not broaden scope, expose secrets, or silently lower trust.

## Required Record

Return an evidence record, proof limit, and validation plan for failure behavior
and residual risk.
