# Example Output

```markdown
## Route Plan

Route:
- /projects/:projectId/settings

Guards:
- Unauthenticated: redirect to sign-in with a safe return destination.
- Authenticated without project access: show unauthorized without confirming private details.
- Missing project: show project-scoped not-found with link to project list.

Deep-link behavior:
- Load project summary and permissions before rendering settings.
- If the project was archived, show read-only archive state with recovery navigation.

Redirects:
- /projects/:projectId/admin redirects to /projects/:projectId/settings only for users with settings access.
- Redirect is replaced in history to avoid back-button loops.

Recovery:
- Retry data load.
- Navigate to project list.
- Preserve last valid tab when the user refreshes.
```
