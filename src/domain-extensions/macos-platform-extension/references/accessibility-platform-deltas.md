# Accessibility Platform Deltas

Load this Reference only when AppKit, SwiftUI, or Mac Catalyst changes macOS
keyboard, focus, VoiceOver, menu, window, or custom-control accessibility.

Official Apple Developer accessibility pages below were accessed on 2026-07-24.

## Platform Delta Decision

- Reuse `accessibility-inclusive-design` for semantic, focus, contrast, motion,
  scaling, announcement, and validation rules that are not macOS-specific.
- Preserve AppKit accessibility roles, labels, values, actions, relationships,
  notifications, and element identity for changed standard or custom controls.
- Trace full-keyboard, menu, command, responder-chain, window, sheet, popover,
  toolbar, and document focus behavior on changed paths.
- For SwiftUI or Mac Catalyst, inspect the resulting macOS accessibility tree
  and keyboard behavior instead of inferring it from shared source or iPad tests.

## Failure Proof

- Exercise VoiceOver navigation/action, keyboard-only operation, focus return,
  disabled and error states, window transitions, custom controls, and changed
  menus at the supported macOS/deployment range.

## Required Record

Return the platform-specific delta, accessibility owner, tree/focus/action
evidence, framework and OS scope, unavailable assistive-technology proof,
reused Foundation obligations, and residual risk.

## Primary Sources

- [Accessibility for AppKit](https://developer.apple.com/documentation/appkit/accessibility-for-appkit)
- [NSAccessibilityProtocol](https://developer.apple.com/documentation/appkit/nsaccessibilityprotocol)
- [Integrating accessibility into your app](https://developer.apple.com/documentation/accessibility/integrating-accessibility-into-your-app)
- [Mac Catalyst](https://developer.apple.com/documentation/uikit/mac-catalyst)

## Source Limits

These rolling pages do not establish repository framework versions, custom
control semantics, actual assistive-technology output, keyboard coverage,
deployment target, reviewer qualification, or complete accessibility.
