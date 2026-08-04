# Lifecycle, Scenes, and Background Contracts

Load this Reference only when iOS/iPadOS app or scene lifecycle, restoration,
multiple scenes, or background execution changes.

Official Apple Developer pages below were accessed on 2026-07-24.

## Lifecycle and State Decision

- Name app-process, scene-session, foreground, background, disconnection, and
  restoration events separately; callbacks are not interchangeable.
- Assign state and one-time effects to a scene, app process, account, or durable
  repository owner before allowing multiple scenes.
- Restore by stable scene and account identity; reject stale navigation, deleted
  records, and duplicate effects.

## Background Decision

- Select the declared BackgroundTasks request or finite background allowance
  from work type, system eligibility, expiration, cancellation, and retry.
- Persist only the minimum resumable work state and make repeated execution
  idempotent.
- Do not promise exact launch time, duration, or completion.

## Failure Proof

- Exercise scene creation, disconnection, process termination, multiple active
  scenes, stale restoration, task expiration, duplicate scheduling, and no run.

## Required Record

Return the lifecycle matrix, state owner, restoration identity, task class,
expiration/cancellation behavior, OS/SDK/device scope, non-inferences, and risk.

## Primary Sources

- [Managing your app's life cycle](https://developer.apple.com/documentation/uikit/managing-your-app-s-life-cycle)
- [Supporting multiple windows on iPad](https://developer.apple.com/documentation/uikit/supporting-multiple-windows-on-ipad)
- [BackgroundTasks](https://developer.apple.com/documentation/backgroundtasks)

## Source Limits

These rolling pages do not establish repository lifecycle adoption, registered
task identifiers, permitted execution time, supported OS/SDK/deployment range,
actual scheduling, restoration design, or device coverage.
