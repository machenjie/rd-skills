# Service, Background, and Notification Implementation and Review Evidence

Load this Reference only after the accepted Windows service/background owner and
failure decision requires implementation or review evidence.

## Required Decision Input

- Consume the accepted Professional owner, execution mechanism,
  principal/session, installation, recovery, and any affected notification contract. This
  Reference never selects or changes the route.

## Implementation and Review Evidence

- Exercise affected paths from the accepted execution mechanism: start/stop/restart,
  crash recovery, shutdown, account/session, background cancellation, notification
  activation, and upgrade. Absent background or notification surfaces need no proof.
- Use the selected IPC and user-session handoff instead of interactive-service UI.

## Required Record

Return an evidence record, proof limit, and validation plan for accepted-owner
failure behavior, recurrence proof, and untested paths.
