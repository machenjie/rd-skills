---
name: web-platform-professional-usage
description: "`analysis-agent`/`task-agent`/`review-agent`: use for browser/PWA runtime; skip generic components with no web-platform semantic decision, TS-only, backend, or native-client work."
---

# web-platform-professional-usage

## Registry Trigger

**Use when**

- Browser or PWA document, rendering, navigation, storage, network, background, streaming, compatibility, or accessibility-tree behavior changes.

**Do not use when**

- Installed native client, backend, general frontend workflow, or TypeScript-only decision.

## Skill Role

Own browser-runtime semantics; exclude component workflow, product state, language rules, servers, web security, and framework conventions.

## High-Value Rules

- Bind behavior to current supported-engine and version evidence.
- Keep browser policy separate from application authorization.
- Load only the named runtime decision whose behavior is open.

## Anti-Patterns

- Do not substitute local success, specification presence, or one-engine behavior for web-platform evidence.

## Stop Conditions

Stop on unknown browser versions, origin ownership, navigation, storage lifetime, cache authority, or event ordering; return security, language, or implementation ownership.

## Output Contract

- web-platform decision with document semantics event rendering navigation restoration origin storage fetch policy service-worker channel lifecycle compatibility evidence proof limits and specialist routes

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [document semantics and accessibility tree contracts](references/document-semantics-and-accessibility-tree-contracts.md) | targeted | Document semantics or accessibility-tree behavior remains open | Native semantics and supported-engine evidence settle the changed document behavior | analysis-agent, task-agent, review-agent | selected-approach, boundary-decision, proof-limit |
| [event dispatch and default action contracts](references/event-dispatch-and-default-action-contracts.md) | targeted | DOM event dispatch, cancellation, or default action remains open | Current event path and default behavior are fixed | analysis-agent, task-agent, review-agent | decision-record, failure-decision, proof-limit |
| [layout paint and compositing contracts](references/layout-paint-and-compositing-contracts.md) | targeted | Layout, paint, stacking, or compositing behavior remains open | Supported-engine evidence settles the changed rendering behavior | analysis-agent, task-agent, review-agent | selected-approach, validation-plan, proof-limit |
| [navigation and restoration contracts](references/navigation-and-restoration-contracts.md) | targeted | Navigation, history, visibility, or restoration behavior remains open | Current navigation and restoration contract fixes all changed entries | analysis-agent, task-agent, review-agent | decision-record, failure-decision, proof-limit |
| [origin storage and fetch policy contracts](references/origin-storage-and-fetch-policy-contracts.md) | targeted | Origin, storage, cookie, fetch, CORS, or CSP policy remains open | No browser origin, storage, fetch, or policy boundary changes | analysis-agent, task-agent, review-agent | boundary-decision, failure-decision, proof-limit, residual-risk |
| [service worker and cache contracts](references/service-worker-and-cache-contracts.md) | targeted | Service-worker lifecycle or cache authority remains open | No service-worker or cache behavior changes | analysis-agent, task-agent, review-agent | decision-record, failure-decision, validation-plan, residual-risk |
| [worker and persistent channel contracts](references/worker-and-persistent-channel-contracts.md) | targeted | Worker, WebSocket, SSE, or persistent-channel lifecycle remains open | No worker or persistent-channel behavior changes | analysis-agent, task-agent, review-agent | decision-record, failure-decision, validation-plan, residual-risk |
| [browser compatibility and verification evidence](references/browser-compatibility-and-verification-evidence.md) | evidence-pattern | Browser compatibility or verification claim needs current evidence | No changed browser compatibility claim awaits verification | analysis-agent, task-agent, review-agent | evidence-record, validation-plan, proof-limit, residual-risk |
