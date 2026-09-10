# Accessibility Representation, Input, and Scaling Implementation and Review Evidence

Load this Reference only after the accepted Android accessibility
`decision-record` must be implemented or reviewed.

## Evidence

- Inspect merged and unmerged Compose semantics when merging or clearing changes.
- Inspect the effective Views/Compose representation.
- Exercise TalkBack or Switch Access, keyboard/D-pad traversal, and the maximum
  supported font/display scaling when each path is in scope.
- Across recreation, process-death restoration, and navigation return, verify a
  valid focus fallback and suppress stale or duplicate announcements.
- Combine automated checks with manual service evidence.

## Required Record

Return service/input/scaling evidence, unavailable devices and OS versions,
proof limits, and residual risk.
