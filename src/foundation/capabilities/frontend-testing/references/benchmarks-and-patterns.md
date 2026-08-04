# Frontend Testing Benchmarks And Patterns

Load this reference when selecting frontend test level, dynamic state coverage, network fixture fidelity, browser behavior, visual risk, or accessibility evidence. Do not load it for a pure non-UI rule already owned by unit testing.

## Test Boundary Fit

| Risk | Candidate evidence | Escalate when |
| --- | --- | --- |
| Pure formatter/selector/rule | Unit/property test through its public API. | Browser, framework, locale runtime, or network behavior carries the risk. |
| Component/form/data state | Behavior test rendering the real component subtree with user-level events. | Routing, focus across documents, layout engine, or real browser APIs matter. |
| API-backed workflow | Component/integration test through a contract-aligned network boundary. | Provider/server deployment semantics or cross-page journey is the claim. |
| Routing/history/storage | Browser test for direct entry, refresh, back/forward, cancellation, and cleanup. | Backend authorization or external consumer compatibility is being inferred. |
| Visual/responsive change | Owned story plus visual comparison at relevant states/viewports. | Meaning, keyboard behavior, or assistive output is the risk. |
| Critical end-to-end journey | Narrow browser journey through real application boundaries. | Broad E2E setup would duplicate lower-level cases without new confidence. |

## Coverage And Fidelity

Select applicable loading, success, true/filtered empty, stale, error/retry, conflict, partial, permission/unauthenticated, disabled/in-progress, validation, confirmation, optimistic rollback, and cancellation states from the actual state model. Cover each role or scope only when rendered behavior differs, while backend denial remains a separate proof.

Drive interactions through accessible names/roles and realistic keyboard/pointer input. Assert caller-visible DOM, focus, announcements, navigation, cache/state changes, and outbound requests—not private helpers, hook call order, CSS class trivia, or snapshots as the sole semantic oracle.

Network mocks intercept the transport or generated client boundary and use schema/contract-owned factories. Include malformed/old-version/error fixtures when those are risks; a hand-written happy-path object can make production-impossible data look valid.

Automated accessibility checks catch a subset of structural defects. Manual or browser evidence is still needed for keyboard order, focus movement/restoration, screen-reader announcements and meaning, zoom/reflow, motion, and platform-specific behavior when applicable.

## Proof Limits And Routes

A component test does not prove browser layout or history. A browser test does not prove complete backend-policy coverage. A visual diff does not prove semantics. A mocked API does not prove deployed compatibility or provider behavior. Record browsers/viewports, roles, locales, assistive checks, mocked boundaries, and states not exercised.

Reject implementation-detail mocks, low-level events when user behavior matters, happy-path-only dynamic views, stale fixtures, snapshots without semantic assertions, automation-only accessibility claims, and large E2E suites used to avoid choosing narrower proof.

Route test-level sufficiency to `test-strategy`, form rules to `form-validation-design`, API lifecycle to `frontend-api-integration`, route behavior to `routing-navigation-design`, design-system state/accessibility to `design-system-rules`, and final command/freshness selection to `quality-test-gate`.
