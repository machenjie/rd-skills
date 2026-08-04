# Native Platform Source Contracts
Load only the section for an affected native target. These records support source decisions and do not replace repository evidence or version-matched platform documentation.
Official pages in this reference were recorded as accessed on 2026-07-24.
## Android
Use the current manifest, build variants, minimum and target SDKs, lifecycle owner,
and device tests as the local contract.
- Separate transient UI state from durable data and process-restorable state.
- Treat background work, permission state, and verified links as platform contracts.
- Recheck package metadata and the final application artifact when those inputs change.
Primary sources:
- [Activity lifecycle](https://developer.android.com/guide/components/activities/activity-lifecycle)
- [Save UI states](https://developer.android.com/topic/libraries/architecture/saving-states)
- [Background tasks overview](https://developer.android.com/develop/background-work/background-tasks)
- [Android App Links](https://developer.android.com/training/app-links)
- [Runtime permissions](https://developer.android.com/training/permissions/requesting)
- [Publish and package an app](https://developer.android.com/studio/publish)
Version limit: these are rolling Android pages. They do not establish the repository's
SDK levels, Play policy, device-vendor behavior, or supported form factors.
## iOS, iPadOS, and macOS
Use the selected SDK, deployment target, application or scene owner, entitlements,
associated domains, and archive configuration as the local contract.
- Handle launch, scene or window restoration, background expiration, and termination as distinct outcomes.
- Validate universal-link association on both the application and website sides.
- Treat entitlements, signing, and archive contents as part of the source change.
Primary sources:
- [UIKit application lifecycle](https://developer.apple.com/documentation/uikit/managing-your-app-s-life-cycle)
- [AppKit application delegate](https://developer.apple.com/documentation/appkit/nsapplicationdelegate)
- [Background Tasks](https://developer.apple.com/documentation/backgroundtasks)
- [Universal links](https://developer.apple.com/documentation/xcode/allowing-apps-and-websites-to-link-to-your-content/)
- [Xcode beta and release distribution](https://developer.apple.com/documentation/xcode/distributing-your-app-for-beta-testing-and-releases)
Version limit: Apple pages follow current SDKs. They do not prove behavior for the
project's Xcode version, deployment target, signing account, or store policy.
Do not infer watchOS, tvOS, or visionOS coverage.
## Windows Desktop
Use the current packaged or unpackaged model, manifest, activation registration,
runtime dependency, architecture, and installer tests.
- Preserve launch, file, protocol, notification, and existing-instance activation paths.
- Validate MSIX identity and runtime dependencies when packaging inputs change.
- Keep installation and application behavior evidence separate.
Primary sources:
- [Windows App SDK activation](https://learn.microsoft.com/en-us/windows/apps/develop/launch/activate-an-app)
- [MSIX overview](https://learn.microsoft.com/en-us/windows/msix/overview)
- [Windows App SDK packaged deployment](https://learn.microsoft.com/en-us/windows/apps/windows-app-sdk/deploy-packaged-apps)
Version limit: Windows App SDK and MSIX behavior depends on the selected SDK,
packaging model, OS version, architecture, and distribution channel.
## Linux Desktop
Use the current desktop file, application ID, D-Bus or portal boundary, sandbox
format, desktop environment, and package test as the local contract.
- Validate desktop-entry identity, activation, MIME, and launch fields after changes.
- Use portals when the package or desktop environment requires mediated host access.
- Test affected behavior in each supported sandbox and desktop session.
Primary sources:
- [Desktop Entry Specification 1.5](https://specifications.freedesktop.org/desktop-entry/latest-single/)
- [XDG Desktop Portal](https://flatpak.github.io/xdg-desktop-portal/docs/)
Version limit: these sources do not prove identical behavior across distributions,
desktop environments, X11, Wayland, Flatpak, Snap, AppImage, or native packages.
## Required Record
Return the selected target and version, affected native owner, source contract,
normal and failure paths, validation evidence, and explicit non-inferences.
