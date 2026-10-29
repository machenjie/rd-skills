# Mini-Program Lifecycle and Bridge Contracts

Load for mini-program page lifetime, view/logic communication, login, permissions, or device behavior.
Skip browser-only applications and unconfirmed mini-program targets.

## Decision Rules

- Bind the concrete platform, base-library version, manifest, APIs, and supported devices.
- Distinguish app lifetime from page load, visibility, readiness, and unload transitions.
- Treat repeated show/hide events separately from first load and permanent unload.
- Bind asynchronous callbacks to the page or operation generation that still owns their result.
- Validate view/logic payloads against the selected bridge serialization and update contract.
- Avoid assuming that an asynchronous view update completed when the logic-side assignment returned.
- Exchange login codes through the intended backend flow; do not treat a temporary code as durable user authority.
- Handle expired sessions and revoked permissions according to the platform and product contracts.
- Recover necessary page state after background eviction or a supported application upgrade.
- Compare developer-tool behavior with real-device lifecycle, network, permissions, and rendering.

## Failure Probes

| Sequence or probe | Required observation |
|---|---|
| Page hides, shows, then unloads | Subscriptions follow the appropriate lifetime |
| Old callback arrives after page replacement | Obsolete result cannot mutate the current page |
| Bridge rejects or normalizes a value | Logic and rendered state remain consistent |
| Login expires or permission is revoked | Recovery does not reuse obsolete authority |
| Background process is evicted during work | Required state reconstructs on the actual device |

## Proof Limits

- These sources describe WeChat contracts; another mini-program host needs its own versioned documentation.
- Typings and developer tools do not prove all base-library versions or real-device behavior.

## Sources

- [Tencent page lifecycle typings](https://raw.githubusercontent.com/wechat-miniprogram/api-typings/master/types/wx/lib.wx.page.d.ts)
- [Tencent API and bridge typings](https://raw.githubusercontent.com/wechat-miniprogram/api-typings/master/types/wx/lib.wx.api.d.ts)
