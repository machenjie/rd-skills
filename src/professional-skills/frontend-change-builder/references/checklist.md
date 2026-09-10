# Frontend Checklist

- Match existing component, routing, and styling conventions.
- Define local, server, URL, and global state ownership.
- Cover empty, loading, error, success, disabled, and validation states.
- Map API errors to user-facing feedback.
- Check keyboard access, focus, labels, contrast, and announcements.
- Review responsive layout and text overflow.
- Avoid rendering untrusted content unsafely.
- Check performance: bundle, re-render, network, caching.
- Add component, integration, or E2E tests based on risk.

## Professional Decision Rules

- Keep state in the narrowest correct owner and derive rather than duplicate state.
- Handle loading, empty, error, success, disabled, permission, cancellation, retry, and stale-response behavior for async work.
- Reuse design-system components and preserve keyboard, focus, semantic, responsive, and screen-reader behavior.
- Map UI acceptance to component, integration, accessibility, and visual validation proportional to risk.

## High-Value Gotchas

- Duplicated derived state drifts.
- Unmount, cancellation, and out-of-order responses create race defects.
- Automated accessibility checks do not prove keyboard and screen-reader flows.

## Execution Checklist

1. Trace the affected interaction states, API outcomes, focus path, and responsive behavior.
2. Choose state ownership and component reuse from current design-system and lifecycle evidence.
3. Implement the bounded behavior with explicit cancellation, denial, failure, and recovery paths.
4. Stop closure when an affected state lacks accessibility or behavior proof.
