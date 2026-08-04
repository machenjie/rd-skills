# Lifecycle, Task, and State Contracts

Load this Reference only when Android lifecycle, task, back-stack, configuration
recreation, process death, or saved state changes the decision.

Official Android Developers pages below were accessed on 2026-07-24.

## Decision Boundary

- Name the event: configuration recreation, background/foreground transition,
  process death, task removal, back navigation, or explicit finish.
- Assign each value to transient UI state, restorable state, or durable
  repository data; bind user and account identity before restoring it.
- Preserve task, launch mode, deep-link, and back behavior separately from
  screen rendering.
- Make one-time effects idempotent across recreation and restoration.

## Failure Proof

- Recreate the Activity without killing the process.
- Restore after system process death with the prior task or entry Intent.
- Exercise back, task removal, and relaunch without assuming identical callbacks.
- Prove stale account or obsolete navigation state is rejected.

## Required Record

Return the event matrix, state owner, restore key and invalidation rule, task/back
decision, recurrence proof, untested OEM or API paths, and residual risk.

## Primary Sources

- [Activity lifecycle](https://developer.android.com/guide/components/activities/activity-lifecycle)
- [Tasks and the back stack](https://developer.android.com/guide/components/activities/tasks-and-back-stack)
- [Handle configuration changes](https://developer.android.com/guide/topics/resources/runtime-changes)
- [Save UI states](https://developer.android.com/topic/libraries/architecture/saving-states)

## Source Limits

These rolling pages do not establish repository SDK levels, navigation
framework versions, manifest launch modes, OEM task behavior, or the supported
device and form-factor matrix. Do not infer process-death proof from
configuration recreation.
