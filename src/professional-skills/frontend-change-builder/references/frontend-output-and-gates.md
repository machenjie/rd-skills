# Frontend Output And Gates

Use this reference when `frontend-change-builder` needs deeper closure than the main `SKILL.md` should carry. Keep the body focused on routing and critical rules; use this file for implementation evidence, gate mapping, and handoff shape.

## Implementation Evidence Matrix

| Concern | Required decision | Evidence pattern | Stop condition |
| --- | --- | --- | --- |
| Component placement | Feature-local, design-system, shared UI, route-level, or generated surface. | Reuse scan, existing owner, consumer list, public/private boundary, and test placement. | New shared component has one consumer or hidden domain assumptions. |
| State ownership | Local, form, URL, server cache, context, global store, or derived state. | State owner, invalidation/reset behavior, persistence boundary, and failure transition. | Local behavior is promoted globally without current cross-feature consumers. |
| API and failure contract | Loading, empty, validation, permission, conflict, timeout, retryable, terminal, and dependency failures. | Error mapping table, safe user message, retry stance, input preservation, and diagnostic owner. | Generic catch collapses failures or hides recovery path. |
| Accessibility | Keyboard, focus, accessible name, role, live region, contrast, target size, and reduced motion. | Keyboard path, axe/manual check, screenshot/report path, and limits. | Primary interaction has no keyboard or screen-reader proof. |
| Security | User/API content rendering, token storage, third-party script, CSP, and browser storage. | Sanitizer/CSP/token-storage review and malicious-content or denied-path test. | User-controlled content reaches raw HTML without sanitizer proof. |
| Testability | Public behavior seam, API fake, clock/randomness control, fixture owner, and private-helper boundary. | User-observable test plan and fixture ownership. | Tests assert private hooks, CSS selectors, or mock counts as the primary proof. |

## State-To-Validation Map

```yaml
frontend_state_validation:
  - state: loading | empty | success | error | validation | disabled | permission_denied | timeout | partial
    component_or_route: ""
    user_visible_behavior: ""
    validator_or_test: ""
    artifact_or_report: ""
    exit_code_or_status: ""
    proves: ""
    does_not_prove: ""
    owner: ""
```

## Same-Pattern Scan Requirements

- For bug fixes, search sibling components, hooks, stores, validators, API clients, and tests for the same state, error, a11y, security, or placement pattern.
- Record searched paths, related occurrences, why each occurrence is in scope or out of scope, and why the final fix is local or broad.
- Treat design-system wrappers, generated clients, shared hooks, and global stores as higher blast-radius surfaces; route to architecture or security gates when they change.
- Do not claim "no similar pattern" without search evidence.

## Gate-Specific Checks

- **Experience gate**: full state matrix, content, focus, recovery, and analytics remain coherent.
- **API/data gate**: DTO/view model mapping, null/default semantics, generated clients, and error contracts are explicit.
- **Security gate**: auth remains server-enforced, unsafe HTML is sanitized, tokens stay out of browser storage, and sensitive data is not leaked through DOM/logs.
- **Reliability/performance gate**: cache, render, bundle, Core Web Vitals, request fan-out, and memory cleanup are measured or explicitly out of scope.
- **Quality/test gate**: tests assert user behavior through accessible queries and name what they do not prove.

## Anti-Patterns To Reject

- New shared UI or hook created because feature-local code felt repetitive after one consumer.
- CSS selector or snapshot-only test accepted as proof of an interactive flow.
- Server error, timeout, validation error, and permission denial all render the same generic message.
- UI guard treated as authorization proof.
- `dangerouslySetInnerHTML`, `innerHTML`, `v-html`, or markdown rendering accepted without sanitizer and malicious fixture.
- Performance claims based on "feels fast" without a benchmark, profiler, budget, or explicit not-run risk.

## Handoff Closure

Close frontend work with boundaries inspected, placement rationale, state/API/failure map, accessibility and security evidence, same-pattern scan, tests and artifacts, proof limits, residual risk, and recommended next step.
