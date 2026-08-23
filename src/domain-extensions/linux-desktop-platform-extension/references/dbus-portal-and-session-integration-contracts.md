# D-Bus, Portal, and Session Integration Contracts

Load this Reference only when D-Bus names/objects/interfaces, desktop portals,
consent, or graphical-session integration changes the decision.

Official D-Bus and XDG Desktop Portal pages below were accessed on 2026-07-24.

## Boundary Decision

- Record session/system bus, well-known and unique names, object paths,
  interfaces, signatures, activation, ownership transitions, and versioning.
- For D-Bus methods, validate arguments and caller authorization; define timeout,
  cancellation, disconnect, and retry behavior where the method supports it and
  is safe to repeat.
- For D-Bus signals, validate payload and sender identity where available, and
  define subscription lifetime, filtering, ordering, duplication, disconnect,
  and reconnect behavior.
- For D-Bus properties, define read/write authorization, value validation,
  change-notification and cache behavior, and object and session lifetime.
- Bind each portal to application ID, sandbox, parent window, user consent,
  request handle, response, document/token lifetime, and desktop backend.
- Do not silently replace denied or unavailable portal behavior with broader
  filesystem, capture, notification, or host access.

## Primary Sources

- [D-Bus specification](https://dbus.freedesktop.org/doc/dbus-specification.html)
- [XDG Desktop Portal documentation](https://flatpak.github.io/xdg-desktop-portal/docs/)
- [Portal API reference](https://flatpak.github.io/xdg-desktop-portal/docs/api-reference.html)

## Source Limits

These versioned or rolling pages do not establish installed D-Bus/portal
versions, desktop backend support, application permissions, repository
interfaces, policy decisions, or observed user consent.
