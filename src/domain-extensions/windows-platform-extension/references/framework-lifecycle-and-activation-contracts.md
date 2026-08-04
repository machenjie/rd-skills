# Framework, Lifecycle, and Activation Contracts

Load this Reference only when Win32, WinUI, WPF, or Windows Forms lifecycle,
activation, single-instance, or UI-thread behavior changes the decision.

Official Microsoft Learn pages below were accessed on 2026-07-24.

## Framework Decision

- Read the published Windows target, project model, framework version, entry
  point, window ownership, dispatcher, and shutdown mode from the repository.
- Assign process, application, window, document, and UI-thread ownership before
  changing shared state or framework bridges.
- Treat launch, file/protocol activation, relaunch, and single-instance
  redirection as separate entries with payload validation and stale-instance
  recovery.
- Keep Win32, WinUI, WPF, and Windows Forms callbacks distinct; one framework's
  order or threading proof establishes none of the others.

## Failure Proof

- Exercise cold start, existing-instance activation, malformed activation,
  last-window close, dispatcher shutdown, and activation during update.
- Prove state and effects remain correct when activation arrives before UI
  readiness or after the prior instance becomes unreachable.

## Required Record

Return framework/version, lifecycle owner, activation/instance policy, thread
boundary, failure behavior, host evidence, and untested framework paths.

## Primary Sources

- [Win32 desktop apps](https://learn.microsoft.com/en-us/windows/win32/desktop-programming)
- [WinUI 3](https://learn.microsoft.com/en-us/windows/apps/winui/winui3/)
- [WPF overview](https://learn.microsoft.com/en-us/dotnet/desktop/wpf/overview/)
- [Windows Forms overview](https://learn.microsoft.com/en-us/dotnet/desktop/winforms/overview/)
- [App instancing](https://learn.microsoft.com/en-us/windows/apps/windows-app-sdk/applifecycle/applifecycle-instancing)
- [App activation](https://learn.microsoft.com/en-us/windows/apps/develop/launch/activate-an-app)

## Source Limits

These rolling pages do not establish repository framework versions, target
Windows builds, shutdown configuration, activation registrations, installer
behavior, or observed callback order.
