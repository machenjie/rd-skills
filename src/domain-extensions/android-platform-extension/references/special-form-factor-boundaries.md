# Special Form-Factor Boundaries

Load this Reference only for an explicit Android TV, Wear OS, or Android
Automotive target or coverage claim.

Official Android Developers pages below were accessed on 2026-07-24.

## Target Boundary

- Record separate support states for Android TV, Wear OS, and Android Automotive:
  supported-and-proven, supported-with-gaps, explicitly unsupported, or unknown.
- Do not inherit touch, focus, navigation, background, input, display, power,
  distraction, packaging, or distribution assumptions from handheld Android.
- Select target-specific manifest, interaction, lifecycle, quality, device, and
  Play evidence before claiming support.
- For a multi-form-factor package, keep each target's artifact and validation
  result distinct even when source is shared.

## Primary Sources

- [TV app quality](https://developer.android.com/docs/quality-guidelines/tv-app-quality)
- [Wear OS app quality](https://developer.android.com/docs/quality-guidelines/wear-app-quality)
- [Car app quality](https://developer.android.com/docs/quality-guidelines/car-app-quality)

## Source Limits

These rolling quality pages do not prove repository declarations, current Play
policy, target-category eligibility, actual hardware behavior, reviewer
qualification, or complete form-factor support. Handheld tests and one shared
code path cannot close any special-form-factor claim.
