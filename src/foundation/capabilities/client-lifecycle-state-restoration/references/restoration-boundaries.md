# Client Restoration Boundaries

Use this reference to compare lifecycle and restoration choices across installed-client targets. It derives shared decisions without prescribing platform callbacks.

Official pages in this reference were recorded as accessed on 2026-07-24.

## Decision Matrix

| Boundary | Facts to establish | Decision consequence | Failure signal |
|---|---|---|---|
| Visibility | Which UI instance is visible, interactive, obscured, or disconnected | Gate user-facing effects and resource acquisition by the actual state | Background or detached UI receives a visible-only effect |
| Process lifetime | Whether the runtime can suspend, terminate, or relaunch without a final callback | Persist required continuity before the last guaranteed opportunity | Correctness depends on shutdown notification |
| Snapshot scope | Which values reconstruct user intent without becoming durable truth | Snapshot navigation, draft, selection, and bounded presentation state | Credentials, permissions, or server truth are restored from capture |
| Compatibility | Snapshot schema, application version, feature state, and migration support | Migrate, partially restore, or discard through an explicit branch | Decode failure or old state crashes launch |
| Identity | Account, session, workspace, tenant, and scene or window identity | Clear or partition restoration when identity changes | One user's state appears after logout or account switch |
| Initialization | Activation identity, instance ownership, and prior initialization state | Make registration and startup repeat-safe | Duplicate handlers, windows, subscriptions, or writes |
| Async work | Operation owner, lifecycle generation, cancellation, and authoritative result | Cancel disposable work and fence stale completion | Late work mutates a replaced screen or account |
| Consequential effects | Operation identity and current authoritative status | Reconcile pending effects instead of replaying a snapshot | Relaunch repeats payment, upload, send, or mutation |

## Source-Derived Constraints

- Android distinguishes activity recreation from process death and directs applications to preserve only the UI state needed to resume the user task.
- UIKit distinguishes foreground, background, scene disconnection, and relaunch, and permits restoration rejection when preserved state is incompatible.
- Windows application models differ: UWP can be suspended and terminated without a termination notification, while desktop Windows App SDK processes do not inherit that entire model.
- A platform-provided archive or callback is a mechanism; repository state authority, identity, compatibility, and effect reconciliation still determine safe contents.

## Primary Sources

- [Android activity lifecycle](https://developer.android.com/guide/components/activities/activity-lifecycle)
- [Android save UI states](https://developer.android.com/topic/libraries/architecture/saving-states)
- [Apple managing your app's life cycle](https://developer.apple.com/documentation/uikit/managing-your-app-s-life-cycle)
- [Apple preserving your app's UI across launches](https://developer.apple.com/documentation/uikit/preserving-your-app-s-ui-across-launches)
- [Windows UWP application lifecycle](https://learn.microsoft.com/en-us/windows/uwp/launch-resume/app-lifecycle)
- [Windows App SDK desktop application lifecycle](https://learn.microsoft.com/en-us/windows/apps/develop/launch/app-lifecycle)

## Version And Inference Limits

These Android, Apple, and Microsoft pages are rolling platform documentation. They do not establish the repository's SDK, deployment target, application model, framework abstraction, device-vendor behavior, or supported operating-system versions.

Do not infer that every client receives the same background or termination events. Do not infer that a framework snapshot is secure, compatible, authoritative, complete, or suitable after logout, upgrade, crash, or account switch.

## Required Record

Return the affected lifecycle states, last reliable persistence point, snapshot contents and exclusions, identity and version binding, duplicate-initialization behavior, stale-work handling, effect reconciliation, exercised interruption paths, and explicit non-inferences.

## Anti-Patterns

- Treat an in-memory resume, process recreation, and cold launch as the same path.
- Restore captured credentials, permissions, server responses, or completed commands as current truth.
- Use one global startup flag while multiple scenes, windows, activations, or tests can initialize independently.
