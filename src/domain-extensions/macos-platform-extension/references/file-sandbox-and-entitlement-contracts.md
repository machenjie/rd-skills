# File, Sandbox, and Entitlement Contracts

Load this Reference only when file authorization, security-scoped bookmarks,
App Sandbox containers, or macOS entitlements change.

Official Apple Developer pages below were accessed on 2026-07-24.

## File Authority Decision

- Classify access as user-selected, container-owned, temporary, read-only,
  read-write, bookmark-restored, or privileged; request only the required scope.
- Bind a security-scoped bookmark to file identity, account/document owner,
  storage location, staleness handling, renewal, and balanced access lifetime.
- Treat denial, revocation, moved/deleted files, stale data, and unavailable
  volumes as normal reachable states.

## Sandbox and Entitlement Decision

- Inventory files, network, devices, automation, app groups, temporary
  exceptions, and child-process needs before selecting entitlements.
- Compare source entitlements with the exact signed app, helper, XPC service,
  extension, and distribution channel.
- Do not use an entitlement as a substitute for user authorization or a defined
  data lifecycle.

## Required Record

Return authority type, bookmark lifecycle, sandbox owner, exact entitlements,
artifact evidence, denied/stale recovery, OS/deployment scope, and risk.

## Primary Sources

- [App Sandbox](https://developer.apple.com/documentation/security/app-sandbox)
- [Accessing files from the macOS App Sandbox](https://developer.apple.com/documentation/security/accessing-files-from-the-macos-app-sandbox)
- [Protecting user data with App Sandbox](https://developer.apple.com/documentation/security/protecting-user-data-with-app-sandbox)
- [Entitlements](https://developer.apple.com/documentation/bundleresources/entitlements)

## Source Limits

These rolling pages do not establish repository sandbox adoption, user consent,
effective signed entitlements, bookmark persistence, volume behavior, privacy
retention, distribution requirements, or least privilege.
