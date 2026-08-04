# Service, Background, and Notification Contracts

Load this Reference only when Windows service, background-task, or app
notification behavior changes the decision.

Official Microsoft Learn pages below were accessed on 2026-07-24.

## Owner Decision

- Select the actual service Professional before this Domain modifier, using
  `backend-change-builder` for bounded backend service implementation instead of
  `installed-client-change-builder` based only on Windows.
- Keep service lifetime, recovery, protocol, workload, and observability in that
  Professional; add Windows account, session, SCM, installation, and control
  semantics here.
- Distinguish SCM services, MSIX background tasks, Task Scheduler work, and
  foreground client execution from repository and packaging facts.
- Bind notifications to package/app identity, user session, activation, consent,
  expiration, duplicate suppression, and unavailable foreground state.

## Failure Proof

- Exercise start/stop/restart, crash recovery, shutdown, account denial, session
  absence, background cancellation, notification activation, and upgrade.
- Use the selected IPC and user-session handoff instead of interactive-service UI.

## Required Record

Return Professional owner, execution mechanism, principal/session, install and
recovery behavior, notification contract, recurrence proof, and untested paths.

## Primary Sources

- [About services](https://learn.microsoft.com/en-us/windows/win32/services/about-services)
- [Interactive services](https://learn.microsoft.com/en-us/windows/win32/services/interactive-services)
- [Windows app background tasks](https://learn.microsoft.com/en-us/windows/apps/windows-app-sdk/applifecycle/background-tasks)
- [App notifications quickstart](https://learn.microsoft.com/en-us/windows/apps/develop/notifications/app-notifications/app-notifications-quickstart)

## Source Limits

These rolling pages do not select the service Professional, establish repository
service topology, accounts, recovery policy, package identity, notification
consent, production availability, or release approval.
