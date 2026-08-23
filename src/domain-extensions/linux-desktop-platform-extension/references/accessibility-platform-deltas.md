# Accessibility Platform Deltas

Load this Reference only when Linux desktop toolkit, AT-SPI, keyboard, focus,
scaling, or assistive-technology behavior changes.

Official GNOME, KDE, and freedesktop.org pages below were accessed on 2026-07-24.

## Platform Delta Decision

- Keep reusable semantics, keyboard, focus, announcements, contrast, motion,
  text scaling, and test strategy in `accessibility-inclusive-design`.
- Record desktop/session, toolkit/version, accessibility bus state, AT-SPI
  roles/states/relations/actions, theme, scaling, and assistive technologies.
- Preserve logical reading, keyboard navigation, visible focus, accessible
  names/descriptions, value/state changes, and announcements across native,
  custom, embedded, and toolkit-bridged controls.
- Do not infer AT-SPI exposure, focus, keyboard, contrast, scaling, or screen
  reader behavior across GNOME/KDE, X11/Wayland, GTK/Qt, or versions.

## Primary Sources

- [GNOME accessibility guidelines](https://developer.gnome.org/documentation/guidelines/accessibility.html)
- [KDE accessibility and inclusiveness](https://develop.kde.org/hig/accessibility/)
- [AT-SPI 2 API](https://gnome.pages.gitlab.gnome.org/at-spi2-core/libatspi/index.html)

## Source Limits

These rolling pages do not establish application accessibility trees, installed
bus/provider versions, toolkit bridges, desktop policy, supported assistive
technologies, or completed user testing.
