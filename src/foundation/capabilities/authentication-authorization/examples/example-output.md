# Example Output

```markdown
## Auth Implementation Plan

mode_selected: review
authorization_decision: approved with conditions

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

Graph / Memory / Execution Validation:
- Graph evidence: route handler, project settings service, membership repository, audit writer, and existing project policy tests inspected.
- Memory evidence: prior "tenant admin can update project settings" rule accepted only after matching current policy file.
- Execution evidence: owner, viewer, wrong-tenant, missing-session, and mass-assignment tests required before handoff.

Changed Authz To Validation Map:
- project.settings.update -> project owner or tenant admin -> object-level membership check -> allow/deny tests.
- tenant boundary -> repository tenant predicate -> wrong-tenant denial test.
- denial behavior -> client-safe response plus audit reason code -> denial contract check.

Evidence Limits:
- No support override path inspected.
- No generated client or production policy state verified.
- Token/session lifecycle belongs to authentication-security.
```
