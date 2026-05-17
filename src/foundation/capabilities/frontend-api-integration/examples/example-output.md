# Example Output

```markdown
## Frontend API Integration Plan

Operation:
- Load project activity feed with cursor pagination.

Lifecycle:
- Cancel in-flight request when the route changes or filters change.
- Ignore responses that do not match the latest cursor and filter set.

Retry:
- Retry read timeouts twice with bounded backoff.
- Do not retry mutation requests unless an idempotency key is present.

Auth expiry:
- Attempt session refresh once.
- If refresh fails, redirect to sign-in with safe return destination.

Pagination:
- Use server cursor and stable descending event time.
- Show empty state only when first page is empty.

Response validation:
- Reject missing event id, timestamp, actor label, or event type before rendering.
```
