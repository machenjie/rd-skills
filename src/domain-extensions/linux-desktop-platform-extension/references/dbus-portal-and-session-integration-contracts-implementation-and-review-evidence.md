# D-Bus, Portal, and Session Integration Implementation and Review Evidence

Load this Reference only after the accepted Linux D-Bus, portal, and session
decision requires implementation or review evidence.

## Required Decision Input

- Consume the accepted bus/portal contract, identity/consent boundary, and
  lifecycle/cancellation decision; do not reopen routing.

## Implementation and Review Evidence

- Exercise name contention, service activation failure, malformed or unknown
  messages, disconnect/reconnect, timeout, cancellation, denial, and missing backend.
- Prove stale responses and objects cannot mutate a new session or application
  instance.

## Required Record

Return an evidence record, proof limit, and validation plan for failure behavior
and desktop/backend evidence.
