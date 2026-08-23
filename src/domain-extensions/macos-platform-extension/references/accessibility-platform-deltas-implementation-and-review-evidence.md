# Accessibility Platform Delta Implementation and Review Evidence

Load this Reference only after the accepted macOS accessibility
`decision-record` must be implemented or reviewed.

## Required Decision Input

Use the carried platform delta, accessibility owner, affected tree/focus/action
scope, and reusable Foundation obligations. Stop when framework or OS scope is
stale.

## Implementation and Review Evidence

- Inspect the resulting macOS accessibility tree and keyboard behavior rather
  than inferring it from shared source or iPad tests.
- Exercise VoiceOver navigation/action, keyboard-only operation, focus return,
  disabled/error states, window transitions, custom controls, and changed menus
  at the supported deployment range.

## Required Record

Return tree/focus/action evidence, framework and OS scope, unavailable
assistive-technology proof, reused Foundation obligations, proof limits, and
residual risk.
