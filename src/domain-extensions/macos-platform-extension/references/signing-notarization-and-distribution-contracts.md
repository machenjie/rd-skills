# Signing, Notarization, and Distribution Contracts

Load this Reference only when hardened runtime, code signing, Developer ID,
notarization, Gatekeeper, Mac App Store, or independent distribution changes.

Official Apple Developer pages below were accessed on 2026-07-24.

## Artifact and Channel Decision

- Name Mac App Store or the exact independent channel before selecting sandbox,
  certificate, hardened-runtime, package, notarization, and update obligations.
- Bind the final app, frameworks, plug-ins, XPC services, helpers, agents,
  command tools, and installer packages to one artifact graph and signing plan.
- Inspect hardened-runtime exceptions and entitlements per executable; the main
  app signature does not prove nested code.

## Primary Sources

- [Hardened Runtime](https://developer.apple.com/documentation/security/hardened-runtime)
- [Notarizing macOS software](https://developer.apple.com/documentation/security/notarizing-macos-software-before-distribution)
- [Resolving common notarization issues](https://developer.apple.com/documentation/security/resolving-common-notarization-issues)
- [Distributing software on macOS](https://developer.apple.com/macos/distribution/)

## Source Limits

These rolling pages do not establish repository distribution channel, current
certificate or notarization authority, effective signatures, App Store policy,
Gatekeeper result, rollout, production installation, or release approval.
