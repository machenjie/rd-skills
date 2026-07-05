# Example Output

```markdown
## Frontend API Integration Plan

Mode selected:
- Read lifecycle with pagination and cache freshness.

Source evidence:
- Current route component, API client wrapper, generated activity DTO, MSW handlers, and activity-feed tests inspected.
- Repository graph and project memory were used only as selectors; current source confirmed the cache key and handler pattern.

Operation:
- Load project activity feed with cursor pagination: `GET /api/projects/{projectId}/activity?cursor=...`.

Request lifecycle:
- Start in loading on first page and stale-while-revalidate on subsequent refresh.
- Cancel in-flight request when the route, project id, filter set, or cursor changes.
- Ignore any response whose project id, cursor, or filter hash does not match the latest request identity.
- Timeout after 5 seconds for foreground loads and 30 seconds for background revalidation.

Auth expiry:
- Attempt session refresh once.
- If refresh fails, clear protected activity cache and redirect to sign-in with safe return destination.

Pagination:
- Use server cursor and stable descending event time.
- Show empty state only when first page is empty.
- Treat empty next page as end-of-list, not a load error.

Response validation:
- Reject missing event id, timestamp, actor label, or event type before rendering.

Error mapping:
- `401`: refresh once, then sign-in redirect.
- `403`: show non-leaking denied state.
- `429` or `503`: retry read with Retry-After or bounded backoff.
- Malformed response: show unexpected-response state and capture safe diagnostic trace id.

Cache strategy:
- Cache key includes project id, filter hash, and cursor.
- Invalidate feed on successful activity-creating mutations and clear on sign-out.

Validation map:
- Stale response: component integration test with two delayed MSW responses.
- Auth expiry: refresh success and refresh failure tests.
- Malformed response: schema failure test.
- Pagination: end-of-list and filter-change tests.
- Cache invalidation: mutation success invalidates feed.

Handoff boundaries:
- API contract shape and error codes remain owned by `api-contract-design` and `error-code-design`.
- Component tests and MSW fixtures remain owned by `frontend-testing`.

Evidence limits:
- This plan does not prove deployed auth behavior, production cache behavior, real browser navigation timing, or third-party API availability.
```
