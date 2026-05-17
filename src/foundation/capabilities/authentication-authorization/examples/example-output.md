# Example Output

```markdown
## Auth Implementation Plan

Operation:
- PATCH /projects/:projectId/settings

Authentication:
- Subject comes from verified session token.
- Service account subjects are allowed only through signed internal requests.

Authorization:
- Action: project.settings.update.
- Resource: projectId.
- Scope: subject must be project owner or tenant administrator for the project's tenant.
- Object-level check loads project membership before mutation.

Denials:
- Missing session returns unauthenticated response.
- Cross-tenant access returns client-safe denial without project details.

Audit:
- Log allow and deny for settings update with subject id, project id, tenant id, and correlation id.

Tests:
- Owner allowed.
- Viewer denied.
- Same role in another tenant denied.
```
