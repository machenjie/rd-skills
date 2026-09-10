# React Native Framework Contracts

Use this Reference only for the named react-native-framework-contracts decision.

## Decision Rules

- Distinguish JavaScript state from native application state and process recreation.
- Keep platform-specific behavior in the narrowest existing platform seam.

## Sources And Version Limit

Sources: [AppState](https://reactnative.dev/docs/appstate), [Linking](https://reactnative.dev/docs/linking), and [platform-specific code](https://reactnative.dev/docs/platform-specific-code).
Version limit: the latest pages do not establish the repository's React Native, Android, iOS, or native-module versions.
