# React Native Framework Contracts

Load when React Native lifecycle, links, or platform seams affect the change;
skip when JavaScript/native state and integration behavior remain unchanged.

## Decision Rules

- For a cold-start deep link, the existing app-entry/navigation owner handles `Linking.getInitialURL()`; for an already running app it handles the `url` event. Send both through the existing route handler and retain native scheme, intent, and AppDelegate wiring. A JavaScript listener alone does not register the app with the OS.
- Keep a Linking or AppState subscription with the component or service that owns its lifetime. Dispose it when that owner ends or is replaced, using the pinned API's removal contract. Creating listeners on each render can duplicate navigation or state updates; check remount and cleanup behavior.
- On Android, opening the notification drawer can emit `blur` without an AppState change. Choose focus events for interaction focus and application-state events for foreground/background behavior.
- Keep JavaScript screen/domain state separate from native process and application state; neither a focus event nor an AppState transition proves process recreation or restored domain state.
- Keep platform-specific behavior in the narrowest existing platform seam. Validate cold start, running-app delivery, and the affected target lifecycle; a JavaScript-only test does not prove native registration or process recreation.

## Sources And Version Limit

Resolve the repository's React Native, native-module and target pins and actual
architecture before selecting APIs. Use the matching versioned docs and local
bindings; apply legacy startup caveats when the pinned architecture matches.

Sources checked 2026-09-12: React Native 0.83 [Linking](https://reactnative.dev/docs/0.83/linking), [AppState](https://reactnative.dev/docs/0.83/appstate), and [platform-specific code](https://reactnative.dev/docs/0.83/platform-specific-code).
Version limit: the cited release is a documentation sample; it does not establish the repository's installed versions or imply an upgrade.
