# Lifecycle, Scenes, and Background Implementation and Review Evidence

Load this Reference only after the accepted lifecycle and background
`decision-record` must be implemented or reviewed.

## Required Decision Input

Use the carried lifecycle matrix, state owner, restoration identity, task class,
and expiration/cancellation decision. Stop if that decision or its scope is
missing, stale, or inconsistent with the current Brief.

## Implementation and Review Evidence

- Persist only the minimum resumable work state and make repeated execution
  idempotent.
- Exercise scene creation, disconnection, process termination, multiple active
  scenes, stale restoration, task expiration, duplicate scheduling, and no run.
- Do not treat callback or simulator evidence as proof of exact launch time,
  duration, completion, or device behavior.

## Required Record

Return the tested lifecycle and failure matrix, OS/SDK/device scope, unavailable
evidence, proof limits, and residual risk.
