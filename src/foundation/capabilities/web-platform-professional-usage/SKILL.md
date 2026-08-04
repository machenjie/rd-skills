---
name: web-platform-professional-usage
description: "`analysis-agent`/`task-agent`/`review-agent`: use for browser/PWA runtime; skip generic components with no web-platform semantic decision, TS-only, backend, or native-client work."
---

# web-platform-professional-usage

## Registry Trigger

**Use when**

- A browser or PWA change depends on web-platform document, rendering, navigation, storage, network, background, streaming, compatibility, or accessibility-tree behavior.

**Do not use when**

- The task is an installed native client, a non-browser backend, a general frontend workflow, or a language-only TypeScript decision.

## Skill Role

Define browser-runtime semantics that change decisions. Exclude component workflow, product state, TypeScript rules, servers, web security, and framework conventions.

## High-Value Rules

- **Prefer native document semantics.** Select HTML elements from content and interaction meaning before adding roles or scripted behavior that must recreate browser defaults.
- **Trace DOM events through the actual tree.** Account for capture, target, bubble, composition, retargeting, cancellation, default action, and listener lifetime before changing delegation.
- **Separate rendering stages when diagnosing visuals.** Distinguish DOM and style inputs, formatting and layout, paint order, stacking context, and compositing using evidence from supported engines.
- **Model navigation as state restoration.** Define initial load, same-document history, reload, page hide and show, BFCache return, visibility change, and discarded-document recovery.
- **Scope browser state by origin and lifetime.** Choose cookies, session storage, durable storage, or caches from identity, credential, expiry, partition, quota, and clearing behavior.
- **Keep fetch controls distinct.** Reconcile same-origin policy, CORS mode, credentials, HTTP caching, and CSP with the server contract without treating any one as authorization.
- **Treat service workers as interruptible event handlers.** Version cache contents, define install and activation handoff, bound offline fallback, and avoid dependence on persistent execution.
- **Own persistent channel lifecycle.** Define worker, WebSocket, and SSE startup, ordering, reconnection, backpressure, visibility behavior, cleanup, and browser-version evidence.

## Anti-Patterns

- Replace semantic HTML with generic elements and assume ARIA restores native behavior automatically.
- Treat `load` or component mount as the only entry path despite history traversal, BFCache, restored storage, or an active service worker.
- Infer browser support from a specification, one compatibility table, or one engine without testing the supported version matrix.

## Stop Conditions

Stop when supported browser versions, origin ownership, navigation model, storage lifetime, cache authority, or event ordering is unknown. Route injection and authorization to `web-security`, language semantics to `typescript-professional-usage`, and general implementation ownership to the selected Professional Skill.

## Output Contract

- web-platform decision with document semantics event rendering navigation restoration origin storage fetch policy service-worker channel lifecycle compatibility evidence proof limits and specialist routes

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [document event rendering contracts](references/document-event-rendering-contracts.md) | targeted | HTML semantics DOM events layout paint stacking compositing or accessibility-tree behavior remains unresolved | Existing native semantics and supported-engine evidence settle the changed document behavior | analysis-agent, task-agent, review-agent | selected-approach, proof-limit |
| [navigation network background contracts](references/navigation-network-background-contracts.md) | targeted | Navigation history storage cookies origins CORS CSP service workers caches BFCache visibility workers WebSocket SSE or compatibility changes | No browser lifecycle persistence network or background behavior changes | analysis-agent, task-agent, review-agent | validation-plan, residual-risk |
