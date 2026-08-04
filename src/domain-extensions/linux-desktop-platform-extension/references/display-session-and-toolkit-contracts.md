# Display, Session, and Toolkit Contracts

Load this Reference only when X11, Wayland, Xwayland, compositor, window, focus,
coordinate, clipboard, input, or toolkit behavior changes the decision.

Official freedesktop.org, Wayland, and X.Org pages below were accessed on
2026-07-24.

## Session Decision

- Record distribution/version, desktop, compositor, session type, Xwayland use,
  toolkit/version, graphics stack, remote-session state, and supported matrix.
- Separate X11 server-global mechanisms from Wayland compositor-mediated
  protocols; use portals or compositor protocols only when target facts require.
- Bind window activation, focus, coordinates, scaling, input capture, clipboard,
  drag-and-drop, and global shortcuts to the selected session and toolkit.
- Do not infer Wayland behavior from Xwayland success, one compositor from
  another, or toolkit fallback behavior from framework names.

## Failure Proof

- Exercise native X11, native Wayland, and Xwayland only where supported.
- Exercise denied/unsupported protocol, compositor restart, multi-monitor
  scaling, focus transfer, clipboard loss, and remote or nested sessions.

## Required Record

Return environment matrix, selected protocol/mechanism, rejected fallback,
normal/failure evidence, unsupported combinations, and non-inferences.

## Primary Sources

- [Wayland architecture](https://wayland.freedesktop.org/docs/book/Architecture.html)
- [Xwayland](https://wayland.freedesktop.org/docs/book/Xwayland.html)
- [X.Org documentation](https://xorg.freedesktop.org/archive/current/doc/)
- [XDG desktop portals](https://flatpak.github.io/xdg-desktop-portal/docs/)

## Source Limits

These rolling pages do not establish repository toolkit settings, compositor
extensions, desktop policy, enabled protocols, remote-session behavior,
hardware/driver support, or cross-environment equivalence.
