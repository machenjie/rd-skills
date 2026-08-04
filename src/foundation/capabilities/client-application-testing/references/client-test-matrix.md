# Installed-Client Test Matrix

Use this reference to select client-specific tests from the changed behavior and supported target matrix. It does not replace the general quality strategy or platform test documentation.

Official pages in this reference were recorded as accessed on 2026-07-24.

## Risk Matrix

| Risk family | Distinct cases to consider | Strong observable oracle |
|---|---|---|
| Lifecycle | Background and return, UI recreation, process death, relaunch, crash, low memory | Visible task continuity, durable state, released resources, no duplicate effect |
| Permission | Initial denial, partial grant, later revocation, process termination, settings return | Capability stops safely, stale access is cleared, recovery remains available |
| Connectivity | Offline launch, mid-operation loss, reconnect, duplicate delivery, unknown response | Honest pending state, authoritative reconciliation, bounded retry |
| External activation | Cold and warm deep link, notification, malformed input, wrong account, missing target | Exactly one intended destination or explicit recoverable rejection |
| Artifact state | Fresh install, upgrade, incompatible stored data, logout, account switch, uninstall | Intended preserve, migrate, quarantine, or clear behavior |
| Environment | Device class, operating-system version, architecture, display size, low memory | Same accepted behavior or documented target-specific branch |
| Presentation | Locale, timezone, text direction, font scaling, high contrast, reduced motion | Complete meaning and operation without clipping or stale formatting |
| Assistive technology | Screen reader, keyboard or switch path, focus, announcements, automation tree | User-observable completion with correct semantic and focus transitions |

## Selection Rules

- Map each changed failure mechanism to the lowest capable test boundary and retain an application or device test when the operating system owns the transition.
- Exercise the actual installable or release-equivalent artifact when packaging, architecture, optimization, entitlement, or upgrade behavior can differ from a debug process.
- Record every excluded operating-system, device, architecture, locale, accessibility setting, or destructive install state as unverified scope.
- Keep test hooks bounded to observation or controllable conditions; they must not replace production lifecycle, permission, network, or activation behavior.
- Reset application data, accounts, server fixtures, notifications, network conditions, permissions, clocks, and device settings after each applicable case.

## Primary Sources

- [Android testing strategies](https://developer.android.com/training/testing/fundamentals/strategies)
- [Android test your app's activities](https://developer.android.com/guide/components/activities/testing)
- [Android app compatibility](https://developer.android.com/guide/app-compatibility)
- [Android runtime permissions](https://developer.android.com/training/permissions/requesting)
- [Apple XCTest](https://developer.apple.com/documentation/xctest)
- [Microsoft test Windows App SDK applications](https://learn.microsoft.com/en-us/windows/apps/develop/testing/)
- [Microsoft Windows accessibility testing](https://learn.microsoft.com/en-us/windows/apps/design/accessibility/accessibility-testing)

## Version And Inference Limits

These are rolling platform pages. They do not establish the repository's SDK, toolchain, device inventory, operating-system support policy, test-runner capability, or release artifact.

Android activity recreation does not prove full process-death restoration. XCTest, Android instrumentation, Windows UI Automation, simulators, and emulators prove only the environments and paths exercised. No listed tool proves production reliability, every device configuration, accessibility conformance, store acceptance, or release readiness.

## Required Record

Return the changed client risk, selected cases and environments, artifact type, observable oracle, cleanup, skipped dimensions, command or manual evidence, and the claims that remain unproven.
