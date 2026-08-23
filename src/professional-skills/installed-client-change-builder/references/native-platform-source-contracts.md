# Native Platform Source Contracts

Load only the affected native target; bind repository and version-matched evidence. Official pages were accessed 2026-07-24.

## Target Matrix

| Target | Current source contract | Required validation and limit |
| --- | --- | --- |
| Android | Manifest, variants, SDK levels, lifecycle owner; transient, durable, and restorable state; background, permission, and link contracts. | Recheck metadata/artifact and device paths. Rolling pages do not prove repository SDKs, Play policy, vendors, or form factors. |
| iOS/iPadOS/macOS | SDK, target, app/scene/window owner, entitlements, domains, archive; distinct launch, restoration, background, and termination outcomes. | Validate app/site links, signing, and archive. Current pages do not prove project Xcode, account, store policy, watchOS, tvOS, or visionOS. |
| Windows | Package model, manifest, activation, runtime, architecture; launch, file, protocol, notification, and existing-instance paths. | Validate identity, dependencies, installer, and app separately. Behavior depends on SDK, package model, OS, architecture, and channel. |
| Linux | Desktop file, app ID, D-Bus/portal, sandbox, desktop, package; identity, activation, MIME, launch, and mediated access. | Exercise supported sandboxes/sessions. Sources do not equate distributions, desktops, X11/Wayland, Flatpak, Snap, AppImage, or native packages. |

## Primary Sources

Android: [lifecycle](https://developer.android.com/guide/components/activities/activity-lifecycle), [state](https://developer.android.com/topic/libraries/architecture/saving-states), [background](https://developer.android.com/develop/background-work/background-tasks), [links](https://developer.android.com/training/app-links), [permissions](https://developer.android.com/training/permissions/requesting), [package](https://developer.android.com/studio/publish).

Apple: [UIKit](https://developer.apple.com/documentation/uikit/managing-your-app-s-life-cycle), [AppKit](https://developer.apple.com/documentation/appkit/nsapplicationdelegate), [background](https://developer.apple.com/documentation/backgroundtasks), [links](https://developer.apple.com/documentation/xcode/allowing-apps-and-websites-to-link-to-your-content/), [distribution](https://developer.apple.com/documentation/xcode/distributing-your-app-for-beta-testing-and-releases).

Windows: [activation](https://learn.microsoft.com/en-us/windows/apps/develop/launch/activate-an-app), [MSIX](https://learn.microsoft.com/en-us/windows/msix/overview), [deployment](https://learn.microsoft.com/en-us/windows/apps/windows-app-sdk/deploy-packaged-apps).

Linux: [desktop entry](https://specifications.freedesktop.org/desktop-entry/latest-single/), [portal](https://flatpak.github.io/xdg-desktop-portal/docs/).

## Required Record

Return target/version, native owner, source contract, normal/failure paths, evidence, and explicit non-inferences.
