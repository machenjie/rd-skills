# Framework, Lifecycle, and Activation Implementation and Review Evidence

Load this Reference only after the accepted Windows framework and lifecycle
approach requires implementation or review evidence.

## Required Decision Input

- Consume the accepted framework/version, lifecycle owner, activation/instance
  policy, and thread boundary; do not reopen routing.

## Implementation and Review Evidence

- Exercise cold start, existing-instance activation, malformed activation,
  last-window close, dispatcher shutdown, and activation during update.
- Prove state and effects remain correct when activation arrives before UI
  readiness or after the prior instance becomes unreachable.

## Required Record

Return an evidence record, proof limit, and validation plan for failure behavior,
host evidence, and untested framework paths.
