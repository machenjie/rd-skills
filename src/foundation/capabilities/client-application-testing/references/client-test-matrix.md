# Installed-Client Test Matrix

Load for installed-client lifecycle, OS, environment, artifact, or accessibility risk; exclude strategy or platform instructions.

## Risk Matrix

- Lifecycle: background/return, recreation, process death, relaunch, crash, low memory -> continuity, durable state, resource release, no duplicate.
- Permission: denial, partial grant, revocation, process termination, settings return -> safe stop, stale-access removal, recovery.
- Connectivity: offline launch, mid-operation loss, reconnect, duplicate delivery, unknown response -> honest pending, reconciliation, bounded retry.
- Activation: cold/warm deep link, notification, malformed input, wrong account, missing target -> one destination or recoverable rejection.
- Artifact: install, upgrade, incompatible data, logout, account switch, uninstall -> intended preserve/migrate/quarantine/clear.
- Environment: device class, OS, architecture, display size, low memory -> accepted behavior or documented target branch.
- Presentation: locale, timezone, direction, font scale, contrast, reduced motion -> operable meaning without clipping/stale formatting.
- Assistive technology: screen reader, keyboard/switch, focus, announcements, automation tree -> correct completion semantics/focus.

## Selection Rules

- Map each failure to the lowest capable boundary; retain device coverage for OS transitions.
- Use release-equivalent artifacts for packaging, architecture, optimization, entitlement, or upgrade.
- Record excluded OS/device/architecture/locale/accessibility/destructive-install dimensions as unverified.
- Require hooks to observe/control conditions without replacing production lifecycle, permission, network, or activation behavior.
- Reset app data/accounts/server fixtures/notifications/network/permissions/clocks/device settings.

## Primary Sources

Accessed 2026-07-24: [Android strategy](https://developer.android.com/training/testing/fundamentals/strategies), [activities](https://developer.android.com/guide/components/activities/testing), [compatibility](https://developer.android.com/guide/app-compatibility), [permissions](https://developer.android.com/training/permissions/requesting), [XCTest](https://developer.apple.com/documentation/xctest), [Windows App SDK](https://learn.microsoft.com/en-us/windows/apps/develop/testing/), and [Windows accessibility](https://learn.microsoft.com/en-us/windows/apps/design/accessibility/accessibility-testing).

## Proof Limits

Current pages establish no repository SDK/toolchain, devices, support, runner, or release artifact. Recreation is not process-death proof. XCTest, instrumentation, UI Automation, simulators, and emulators prove exercised paths only—not production reliability, every device, accessibility conformance, store acceptance, or release readiness.

## Required Record

Record risk, matrix, artifact, oracle, cleanup, exclusions, command/manual evidence, and unproved claims.

## Anti-Patterns

- Reject recreation-as-process-death, one-target-as-supported-matrix, and screenshot/tree-only oracles.
