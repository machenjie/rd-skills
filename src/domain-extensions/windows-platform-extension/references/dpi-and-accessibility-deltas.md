# DPI and Accessibility Deltas

Load this Reference only when Windows DPI, scaling, UI Automation, keyboard,
focus, input, or assistive-technology behavior changes.

Official Microsoft Learn pages below were accessed on 2026-07-24.

## Platform Delta Decision

- Keep reusable semantics, contrast, keyboard, focus, announcements, motion,
  text scaling, and test strategy in `accessibility-inclusive-design`.
- Record Windows build, framework, DPI-awareness mode, monitor topology, scale
  factors, input modes, UI Automation peers/providers, and assistive technologies.
- Recompute layout, hit targets, coordinates, raster assets, and window placement
  on per-monitor DPI changes; do not infer one framework's behavior from another.
- Preserve logical reading, keyboard, focus, names, roles, values, states, and
  notifications for custom controls and native/framework bridges.

## Primary Sources

- [High DPI](https://learn.microsoft.com/en-us/windows/win32/api/_hidpi/)
- [Windows accessibility overview](https://learn.microsoft.com/en-us/windows/apps/design/accessibility/accessibility-overview)
- [Accessibility checklist](https://learn.microsoft.com/en-us/windows/apps/design/accessibility/accessibility-checklist)

## Source Limits

These rolling pages do not establish application DPI declarations, framework
versions, custom-control providers, supported assistive technologies, hardware,
or completed user testing.
