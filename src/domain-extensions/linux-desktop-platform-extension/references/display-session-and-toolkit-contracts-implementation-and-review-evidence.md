# Display, Session, and Toolkit Implementation and Review Evidence

Load this Reference only after the accepted Linux display-session and toolkit
boundary decision requires implementation or review evidence.

## Required Decision Input

- Consume the accepted environment matrix, protocol/mechanism, rejected
  fallback, and supported session/toolkit combinations; do not reopen routing.

## Implementation and Review Evidence

- Exercise native X11, native Wayland, and Xwayland only where supported.
- Exercise denied or unsupported protocol, compositor restart, multi-monitor
  scaling, focus transfer, clipboard loss, and remote or nested sessions.

## Required Record

Return an evidence record, proof limit, and validation plan for normal and
failure behavior, unsupported combinations, and non-inferences.
