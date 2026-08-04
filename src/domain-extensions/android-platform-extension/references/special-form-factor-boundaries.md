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

## Failure Proof

- Android TV needs remote/focus, large-distance UI, playback, manifest, and TV
  device evidence appropriate to the claimed tier.
- Wear OS needs watch interaction, power, connectivity, lifecycle, packaging,
  and physical or representative watch evidence.
- Android Automotive needs the exact car surface, parked/driving restrictions,
  allowed app category, distraction controls, and compatible vehicle evidence.

## Required Record

Return one row per form factor with support claim, source owner, manifest and
artifact scope, target-specific obligations, devices exercised, unavailable
evidence, non-inferences, and residual risk.

## Primary Sources

- [TV app quality](https://developer.android.com/docs/quality-guidelines/tv-app-quality)
- [Wear OS app quality](https://developer.android.com/docs/quality-guidelines/wear-app-quality)
- [Car app quality](https://developer.android.com/docs/quality-guidelines/car-app-quality)

## Source Limits

These rolling quality pages do not prove repository declarations, current Play
policy, target-category eligibility, actual hardware behavior, reviewer
qualification, or complete form-factor support. Handheld tests and one shared
code path cannot close any special-form-factor claim.
