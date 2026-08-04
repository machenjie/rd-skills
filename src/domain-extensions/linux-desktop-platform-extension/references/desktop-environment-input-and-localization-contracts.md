# Desktop Environment, Input, and Localization Contracts

Load this Reference only when desktop environment, input method, locale, font,
fractional scaling, or toolkit behavior changes the decision.

Official GNOME, KDE, GTK, and Qt pages below were accessed on 2026-07-24.

## Environment Decision

- Record distribution/version, desktop/version, compositor/session,
  toolkit/version, locale set, text direction, input method, font configuration,
  scale factors, monitor topology, and supported matrix.
- Bind IME preedit/commit, focus, surrounding text, composition cancellation,
  shortcuts, dead keys, and input-language changes to the actual toolkit/session.
- Bind localized desktop metadata, message catalogs, formatting, font fallback,
  shaping, truncation, and bidirectional layout to claimed locales and fonts.
- Test integer and fractional scaling only where the target
  desktop/compositor/toolkit combination publishes and enables it.
- Do not infer IME, font, scaling, locale, or toolkit behavior across GNOME/KDE,
  X11/Wayland, GTK/Qt, distributions, or versions.

## Failure Proof

- Exercise claimed IMEs/locales/scripts, missing fonts, long/RTL text, scale
  changes, mixed-DPI monitors, desktop/theme changes, and toolkit fallback paths.
- Record untested desktop/session/toolkit combinations as non-inferences.

## Required Record

Return environment matrix, input/localization/scaling decisions, normal/failure
evidence, unsupported combinations, source freshness, and proof limits.

## Primary Sources

- [GTK input method context](https://docs.gtk.org/gtk4/class.IMContext.html)
- [Qt input method](https://doc.qt.io/qt-6/qinputmethod.html)
- [Qt high DPI](https://doc.qt.io/qt-6/highdpi.html)
- [GNOME HIG](https://developer.gnome.org/hig/)
- [KDE HIG](https://develop.kde.org/hig/)

## Source Limits

These rolling pages do not establish installed toolkit modules, desktop policy,
compositor features, fonts, locales, IMEs, translation completeness, or
cross-environment equivalence.
