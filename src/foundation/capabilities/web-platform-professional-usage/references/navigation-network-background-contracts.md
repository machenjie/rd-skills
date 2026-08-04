# Web Navigation, Network, And Background Contracts

Use this reference when browser lifecycle, persistence, network policy, background execution, streaming, or compatibility decisions interact.

Official standards and project pages in this reference were recorded as accessed on 2026-07-24.

## Boundary Matrix

| Boundary | Required decisions | Failure signal |
|---|---|---|
| Navigation and history | Entry identity, same-document transition, reload, back and forward, cancellation, and scroll or focus restoration | Component mount is treated as the only entry |
| BFCache and visibility | Page hide and show, persisted return, stale resources, paused work, and discarded recovery | Restored page retains stale session or connection state |
| Cookies and storage | Origin, partition, credential use, expiry, quota, clearing, account binding, and sensitivity | Browser state crosses accounts or outlives its purpose |
| Fetch and CORS | Request mode, credentials, preflight, redirect, cache mode, response exposure, and server policy | CORS is treated as authorization or wildcard credentials are assumed safe |
| CSP | Delivery, disposition, directive fallback, nonce or hash ownership, and report handling | Report-only or a permissive fallback is called enforced protection |
| Service worker and cache | Registration scope, version, install, activation, client handoff, cache keys, freshness, fallback, and deletion | Old and new code use incompatible cache contents |
| Worker | Message schema, transfer ownership, cancellation, termination, and error propagation | Background work is assumed persistent because an object reference exists |
| WebSocket and SSE | Authentication, ordering, reconnect cursor, duplicate handling, backpressure, visibility, and cleanup | Reconnect duplicates effects or silently drops a gap |
| Compatibility | Supported browsers and versions, specification status, runtime tests, and fallback | Specification presence is reported as deployed support |

## Source-Derived Constraints

- HTML defines navigation, session history, workers, WebSocket, and server-sent event behavior; page restoration can bypass a new load.
- Fetch defines same-origin, CORS, credentials, redirects, and cache modes as separate inputs.
- Service workers are event-driven and user agents may terminate an idle worker; cached responses have an application-owned version and freshness problem.
- CSP is defense in depth and report-only delivery does not enforce a policy.
- Cross-browser Web Platform Tests provide interoperability evidence for tested features but do not prove product journeys or every supported configuration.

## Primary Sources

- [WHATWG HTML navigation and session history](https://html.spec.whatwg.org/multipage/browsing-the-web.html)
- [WHATWG HTML workers](https://html.spec.whatwg.org/multipage/workers.html)
- [WHATWG HTML WebSocket](https://html.spec.whatwg.org/multipage/web-sockets.html)
- [WHATWG HTML server-sent events](https://html.spec.whatwg.org/multipage/server-sent-events.html)
- [WHATWG Fetch Living Standard](https://fetch.spec.whatwg.org/)
- [W3C Service Workers](https://www.w3.org/TR/service-workers/)
- [W3C Page Visibility Level 2](https://www.w3.org/TR/page-visibility-2/)
- [W3C Content Security Policy Level 3](https://www.w3.org/TR/CSP/)
- [RFC 6265: HTTP State Management Mechanism](https://www.rfc-editor.org/rfc/rfc6265.html)
- [Web Platform Tests documentation](https://web-platform-tests.org/)
- [Mozilla BFCache overview](https://developer.mozilla.org/en-US/docs/Glossary/bfcache)

## Version And Inference Limits

HTML and Fetch are Living Standards. Service Workers, Page Visibility Level 2, and CSP Level 3 were current W3C specifications at different maturity levels when accessed.

RFC 6265 is the published cookie RFC; `draft-ietf-httpbis-rfc6265bis-22` was in the RFC Editor queue but was not yet a published RFC. Browser storage, BFCache eligibility, worker scheduling, connection limits, and feature support remain implementation- and version-dependent.

Do not infer browser support from specification status, WPT coverage, or one compatibility table. Do not infer that a service worker is a daemon, that BFCache performs network revalidation, that CSP replaces output encoding, or that CORS grants application authorization.

## Required Record

- Return navigation entries, restoration behavior, origin-bound state, fetch and policy settings, service-worker or channel lifecycle, and cache or reconnect recovery.
- Include the supported browser matrix, exercised WPT or product evidence, draft dependencies, skipped engines, and proof limits.
