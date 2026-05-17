# Example Output

```markdown
## Integration Test Plan

Boundary: POST /projects/:id/invitations through API, service, mail adapter, and database.

Success:
- Admin creates invitation.
- Invitation row is persisted with pending status.
- Mail adapter receives one message with expected template data.

Failure:
- Duplicate invite returns conflict and does not enqueue another email.
- Mail adapter timeout leaves invitation pending_notification and emits retry job.

Data:
- Per-test project and user records.
- Cleanup invitation rows and queued messages after each case.
```
