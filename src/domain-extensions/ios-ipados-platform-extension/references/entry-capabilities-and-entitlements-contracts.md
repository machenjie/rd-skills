# Entry, Capabilities, and Entitlements Contracts

Load this Reference only when external entry, a capability, an entitlement,
App ID configuration, or provisioning changes.

Official Apple Developer pages below were accessed on 2026-07-24.

## External Entry Decision

- Inventory custom schemes, Universal Links, notification actions and payloads,
  associated domains, and their scene, navigation, and account destinations.
- Treat every incoming value as untrusted; validate syntax, authorization,
  replay, current account, and requested action before privileged work.
- Treat APNs device tokens as replaceable per app/device and bind provider
  registration to current identity without logging the token.

## Capability and Entitlement Decision

- Derive each capability from a product need and bind its entitlement value to
  the exact app or extension target, bundle/App ID, team, and distribution mode.

## Primary Sources

- [Defining a custom URL scheme](https://developer.apple.com/documentation/xcode/defining-a-custom-url-scheme-for-your-app)
- [Allowing apps and websites to link to content](https://developer.apple.com/documentation/xcode/allowing-apps-and-websites-to-link-to-your-content/)
- [Registering your app with APNs](https://developer.apple.com/documentation/usernotifications/registering-your-app-with-apns)
- [Adding capabilities to your app](https://developer.apple.com/documentation/xcode/adding-capabilities-to-your-app)
- [Entitlements](https://developer.apple.com/documentation/bundleresources/entitlements)

## Source Limits

These rolling pages do not prove current portal state, App ID ownership,
provisioning contents, signed entitlements, server authorization, APNs delivery,
Universal Link association deployment, or target OS/SDK behavior.
