# Framework, Lifecycle, Window, and Document Implementation and Review Evidence

Load this Reference only after the accepted framework and lifecycle
`selected-approach` must be implemented or reviewed.

## Required Decision Input

Use the carried framework/bridge owner, lifecycle matrix, responder route, and
document save/close rule. Stop when ownership or OS/SDK scope is stale.

## Implementation and Review Evidence

- Exercise activation, termination, zero/multiple windows, reopen, tabbing,
  full screen, restoration, failed save, close during work, missing windows,
  repeated commands, and unsaved termination.
- Verify commands through the actual responder chain and final framework bridge;
  visible-view or shared-source assumptions are insufficient.

## Required Record

Return exercised normal/failure paths, OS/SDK scope, unavailable window or
document proof, non-inferences, proof limits, and residual risk.
