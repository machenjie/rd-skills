# Components, Permissions, and Background Contracts

Load this Reference only when external Android entry or continued execution
authority changes.

Official Android Developers pages below were accessed on 2026-07-24.

## Entry and Authority Decision

- Inventory Intent filters, App Links, custom schemes, exported components,
  caller-controlled extras, and the destination task/account.
- Default components to private; justify every exported surface and validate
  input before privileged work.
- Treat runtime permissions and notification access as revocable state, not an
  installation invariant.

## Continued Execution Decision

- Select foreground service only for current user-noticeable work that satisfies
  its declared type, start, timeout, permission, and notification constraints.
- Select persistent scheduled work from durability and constraint needs.
- Do not promise exact execution time from a persistent-work request.
- Define cancellation, retry, deduplication, reboot, app-stop, and process-death
  outcomes before implementation.

## Primary Sources

- [Intents and intent filters](https://developer.android.com/guide/components/intents-filters)
- [Android App Links](https://developer.android.com/training/app-links)
- [Request runtime permissions](https://developer.android.com/training/permissions/requesting)
- [Background work](https://developer.android.com/develop/background-work)
- [Foreground services](https://developer.android.com/develop/background-work/services/fgs)
- [Notification runtime permission](https://developer.android.com/develop/ui/views/notifications/notification-permission)

## Source Limits

These rolling pages do not prove the repository manifest, current target SDK,
Play policy, exact scheduler timing, OEM power management, or notification
delivery. Recheck version-matched restrictions for the selected API/SDK range.
