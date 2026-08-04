# UI, Form-Factor, and Accessibility Contracts

Load this Reference only when UIKit/SwiftUI ownership, iPhone/iPad adaptation,
VoiceOver, or Dynamic Type behavior changes.

Official Apple Developer, Swift.org, and Swift Evolution pages below were
accessed on 2026-07-24.

## Framework and Form-Factor Decision

- Name the UIKit, SwiftUI, or bridged owner for navigation, presentation, state,
  lifecycle integration, and dismissal; do not create two owners.
- Prove compact and regular layouts, rotation, multitasking, keyboard/pointer
  input, multiple scenes, and changed iPhone/iPad navigation where supported.
- Keep Swift isolation, actor, value, ARC, and `Sendable` decisions in
  `swift-professional-usage`; framework choice does not transfer language rules.

## Accessibility Delta

- Preserve semantic identity, reading and focus order, actionable labels,
  announcements, and activation for changed UIKit/SwiftUI controls.
- Exercise VoiceOver navigation and actions plus Dynamic Type at supported
  content sizes without clipped, hidden, or unreachable required content.
- Reuse `accessibility-inclusive-design` for platform-independent requirements.

## Required Record

Return framework/state owner, iPhone/iPad behavior matrix, bridge boundary,
VoiceOver and Dynamic Type evidence, device/OS scope, limits, and residual risk.

## Primary Sources

- [UIKit](https://developer.apple.com/documentation/uikit)
- [SwiftUI](https://developer.apple.com/documentation/swiftui)
- [Supporting VoiceOver](https://developer.apple.com/documentation/uikit/supporting-voiceover-in-your-app)
- [Scaling fonts automatically](https://developer.apple.com/documentation/uikit/scaling-fonts-automatically)
- [Swift concurrency](https://docs.swift.org/swift-book/documentation/the-swift-programming-language/concurrency/)
- [Swift Evolution: Global actors](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0316-global-actors.md)

## Source Limits

These rolling sources do not establish repository framework/compiler versions,
deployment target, supported form factors, custom-control semantics, actual
assistive-technology behavior, or device coverage.
