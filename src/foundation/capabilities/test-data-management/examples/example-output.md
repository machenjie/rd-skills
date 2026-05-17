# Example Output

```markdown
## Test Data Plan

Scope: Invitation workflow tests.

Factories:
- organizationFactory creates one tenant with deterministic id prefix.
- userFactory creates admin and viewer roles.
- invitationFactory creates pending and expired invitations.

Isolation:
- Each test uses tenant namespace `it_{run_id}`.
- Database changes run in rollback transaction for integration tests.
- E2E cleanup deletes tenant namespace and queued messages.

Safety:
- Synthetic emails use example.test domain.
- No production records, tokens, or credentials are copied.
```
