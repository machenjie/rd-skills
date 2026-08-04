# D-Bus, Portal, and Session Integration Contracts

Load this Reference only when D-Bus names/objects/interfaces, desktop portals,
consent, or graphical-session integration changes the decision.

Official D-Bus and XDG Desktop Portal pages below were accessed on 2026-07-24.

## Boundary Decision

- Record session/system bus, well-known and unique names, object paths,
  interfaces, signatures, activation, ownership transitions, and versioning.
- Treat every D-Bus method, signal, and property as an IPC contract with input
  validation, authorization, timeout, cancellation, disconnect, and retry rules.
- Bind each portal to application ID, sandbox, parent window, user consent,
  request handle, response, document/token lifetime, and desktop backend.
- Do not silently replace denied or unavailable portal behavior with broader
  filesystem, capture, notification, or host access.

## Failure Proof

- Exercise name contention, service activation failure, malformed/unknown
  messages, disconnect/reconnect, timeout, cancellation, denial, and missing backend.
- Prove stale responses and objects cannot mutate a new session or application
  instance.

## Required Record

Return bus/portal contract, identity/consent boundary, lifecycle and cancellation,
failure behavior, desktop/backend evidence, and proof limits.

## Primary Sources

- [D-Bus specification](https://dbus.freedesktop.org/doc/dbus-specification.html)
- [XDG Desktop Portal documentation](https://flatpak.github.io/xdg-desktop-portal/docs/)
- [Portal API reference](https://flatpak.github.io/xdg-desktop-portal/docs/api-reference.html)

## Source Limits

These versioned or rolling pages do not establish installed D-Bus/portal
versions, desktop backend support, application permissions, repository
interfaces, policy decisions, or observed user consent.
