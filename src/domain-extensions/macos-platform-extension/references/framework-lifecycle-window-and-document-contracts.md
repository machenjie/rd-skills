# Framework, Lifecycle, Window, and Document Contracts

Load this Reference only when macOS framework ownership or app, window,
document, responder-chain, restoration, or termination behavior changes.

Official Apple Developer pages below were accessed on 2026-07-24.

## Framework and Lifecycle Decision

- Name AppKit, SwiftUI, Mac Catalyst, or a bridge as the owner of each window,
  command, document, state, restoration, and termination decision.
- Keep a single source of truth across delegate callbacks, SwiftUI scenes,
  representable bridges, and Catalyst availability boundaries.
- Model app activation/termination, zero-window operation, multiple windows,
  reopen, tabbing, full screen, and restored state separately.

## Document and Responder Decision

- Bind each document's model, file URL, edited state, window controllers,
  autosave, close approval, undo, and error presentation to one owner.
- Trace commands through the actual responder chain.
- Reject assumptions that the visible view receives menu or keyboard actions.

## Primary Sources

- [NSApplicationDelegate](https://developer.apple.com/documentation/appkit/nsapplicationdelegate)
- [NSResponder](https://developer.apple.com/documentation/appkit/nsresponder)
- [NSDocument](https://developer.apple.com/documentation/appkit/nsdocument)
- [SwiftUI App](https://developer.apple.com/documentation/swiftui/app)
- [Mac Catalyst](https://developer.apple.com/documentation/uikit/mac-catalyst)

## Source Limits

These rolling pages do not establish repository frameworks, bridge ownership,
document schema, target availability, lifecycle order, state restoration,
deployment range, or actual window behavior.
