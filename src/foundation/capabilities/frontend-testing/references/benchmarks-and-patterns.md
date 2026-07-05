# Frontend Testing Benchmarks And Patterns

Load this reference when a frontend test plan needs detailed benchmark anchors, test-level selection, state coverage detail, or API mock alignment examples. Do not load it for pure routing decisions or minor wording changes where the `SKILL.md` body and checklist are sufficient.

## Benchmark Anchors

- Testing Library (`@testing-library/react`, Vue, Svelte): accessible query priority; user-visible behavior over implementation details.
- user-event: realistic pointer, keyboard, clipboard, and focus interactions; prefer over low-level event firing for user flows.
- Vitest and Jest: deterministic component/unit runners with mock/spying support.
- MSW: network-level API mocking for `fetch`/`XMLHttpRequest`; preferred over mocking the HTTP client module.
- Storybook interaction tests and Chromatic/Percy: story-level behavior and visual regression when layout or visual state is the risk.
- axe-core / jest-axe / Playwright accessibility checks: automated WCAG 2.2 signal for labels, roles, ARIA, and common violations.
- Testing Trophy: component/integration tests carry most frontend confidence; unit tests cover pure logic; E2E stays narrow for critical journeys.
- WCAG 2.2 Level AA: focus order, focus visible, name/role/value, status messages, and keyboard access.

## Test Level Decision Matrix

| Behavior to test | Recommended level | Tool | Why |
| --- | --- | --- | --- |
| Single component rendering | Component integration test | Testing Library + Vitest/Jest | Fast; tests DOM output; not implementation |
| Form validation UX | Component integration test | Testing Library + MSW | Verifies field messages, submit state, and recovery |
| Permission-differentiated rendering | Component integration test | Testing Library + role fixtures | Exhaustive across roles without browser overhead |
| Multi-component data flow | Component integration test | Testing Library rendering parent subtree | Proves real prop/context wiring |
| Async data loading states | Component integration test | Testing Library + MSW | Mock network; assert loading/success/error |
| Core single-page user flow | Integration test | Testing Library + MSW | Tests realistic path without full browser |
| Cross-page navigation flow | E2E test | Playwright / Cypress | Requires real browser routing |
| Pure utility function | Unit test | Vitest / Jest | No DOM; pure logic |
| Visual regression | Visual snapshot | Storybook + Chromatic/Percy | Catches layout and visual state breaks |
| WCAG accessibility rules | Accessibility test | jest-axe / axe-core | Catches common ARIA/label/role issues |

## State Coverage Checklist

Every component or view with dynamic behavior should cover applicable states:

```text
Rendering states:
  - Loading: skeleton, spinner, progress indicator visible
  - Success: data rendered correctly
  - Empty: no data, empty message, create/reset action where applicable
  - Error: error message, recovery action present and functional
  - Stale: stale data indicator if applicable

Permission states:
  - Each role variant that changes visible elements or actions
  - Unauthenticated: redirect/login prompt and no protected content
  - Permission-denied: denied state and correct recovery/request-access action

Interaction states:
  - Disabled: reason communicated and reachable
  - In-progress: no double-submit
  - Validation error: field-level and form-level recovery
  - Confirmation required: destructive action confirmation path

Accessibility states:
  - Focus moves to the expected element after action
  - Keyboard navigation follows expected order
  - Interactive elements have accessible names
  - axe-core or equivalent has no violations for the rendered state
```

## API Mock Alignment Pattern

```typescript
// BAD: hand-crafted mock may diverge from contract.
jest.mock('../api/users', () => ({
  fetchUser: jest.fn().mockResolvedValue({ id: '1', name: 'Alice' })
}));
// Risk: API adds required field 'email'; mock silently misses it; test passes; production fails.

// GOOD: MSW with contract-aligned fixture.
import { http, HttpResponse } from 'msw';
import { server } from '../mocks/server';
import { userFactory } from '../test-factories/user';

it('renders user email', async () => {
  server.use(
    http.get('/api/users/:id', () => {
      return HttpResponse.json(userFactory.build({ email: 'alice@example.com' }));
    })
  );
  render(<UserProfile userId="1" />);
  expect(await screen.findByText('alice@example.com')).toBeInTheDocument();
});
```
