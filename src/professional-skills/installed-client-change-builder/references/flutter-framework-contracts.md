# Flutter Framework Contracts

Use this Reference only for the named flutter-framework-contracts decision.

## Decision Rules

- Keep shared widget or state ownership separate from platform-channel ownership.
- Test restoration, links, plugins, and packaging on each affected release target in the accepted target set.
- Pin the repository SDK, plugins, and native projects before deciding behavior.

## Sources And Version Limit

Sources: [platform channels](https://docs.flutter.dev/platform-integration/platform-channels), [adaptive targets](https://docs.flutter.dev/ui/adaptive-responsive), and [deployment](https://docs.flutter.dev/deployment).
Version limit: the recorded Flutter pages identify Flutter 3.44 where stated.
