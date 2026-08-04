# Framework Contracts
Load only the framework section that the repository actually uses. Pair it with the native target contract whenever platform behavior, permissions, links, packaging, or lifecycle is affected.
Official pages in this reference were recorded as accessed on 2026-07-24.
## Flutter
- Keep shared widget or state ownership separate from platform-channel ownership.
- Test restoration, links, plugins, and packaging on every affected release target.
Sources: [platform channels](https://docs.flutter.dev/platform-integration/platform-channels),
[adaptive targets](https://docs.flutter.dev/ui/adaptive-responsive), and
[deployment](https://docs.flutter.dev/deployment).
Version limit: the recorded Flutter pages identify Flutter 3.44 where stated.
Pin the repository SDK, plugins, and native projects before deciding behavior.
## React Native
- Distinguish JavaScript state from native application state and process recreation.
- Keep platform-specific behavior in the narrowest existing platform seam.
Sources: [AppState](https://reactnative.dev/docs/appstate),
[Linking](https://reactnative.dev/docs/linking), and
[platform-specific code](https://reactnative.dev/docs/platform-specific-code).
Version limit: the latest pages do not establish the repository's React Native,
Android, iOS, or native-module versions.
## Electron
- Keep lifecycle and privileged operating-system work in the main-process owner.
- Validate renderer-to-main boundaries, deep-link entry, and the packaged artifact.
Sources: [process model](https://www.electronjs.org/docs/latest/tutorial/process-model),
[deep links](https://www.electronjs.org/docs/latest/tutorial/launch-app-from-url-in-another-app),
[security](https://www.electronjs.org/docs/latest/tutorial/security), and
[distribution](https://www.electronjs.org/docs/latest/tutorial/distribution-overview).
Version limit: `latest` can describe a development branch. Match the repository's
Electron major and bundled Chromium and Node versions.
## Tauri
- Keep commands, plugins, capabilities, and webview callers inside their declared authority.
- Validate deep-link registration and the platform-specific bundle output.
Sources: [capabilities](https://v2.tauri.app/security/capabilities/),
[deep linking](https://v2.tauri.app/plugin/deep-linking/), and
[distribution](https://v2.tauri.app/distribute/).
Version limit: these are Tauri 2 pages. They do not establish plugin versions,
mobile support, target triples, signing, or installer behavior.
## Qt
- Preserve top-level window ownership and platform-specific window-manager behavior.
- Validate runtime libraries, plugins, QML modules, and platform package contents.
Sources: [application windows](https://doc.qt.io/qt-6/application-windows.html) and
[deployment](https://doc.qt.io/qt-6/deployment.html).
Version limit: the recorded pages identify Qt 6.11. They do not prove behavior for
the repository's Qt, compiler, window system, plugin, or packaging versions.
## .NET MAUI
- Map cross-platform window events to the affected native lifecycle.
- Validate platform lifecycle hooks, restored state, permissions, and each package target.
Source: [.NET MAUI app lifecycle](https://learn.microsoft.com/en-us/dotnet/maui/fundamentals/app-lifecycle).
Version limit: the recorded page resolves to .NET MAUI 10.0. Pin the repository's
target frameworks, workloads, native SDKs, and packaging configuration.
## Kotlin Multiplatform
- Put shared behavior only in source sets whose declared targets support it.
- Validate each target compilation and final binary or host-application integration.
Sources: [project structure](https://kotlinlang.org/docs/multiplatform/multiplatform-discover-project.html),
[expected and actual declarations](https://kotlinlang.org/docs/multiplatform/multiplatform-expect-actual.html),
and [native binaries](https://kotlinlang.org/docs/multiplatform/multiplatform-build-native-binaries.html).
Version limit: Kotlin and target stability are time-varying. Do not infer supported
targets, Compose Multiplatform use, binary production, or host packaging from KMP alone.
## Required Record
Return the framework and version, native targets, shared and native owners, bridge
contract, target-specific validation, packaging evidence, and proof limits.
