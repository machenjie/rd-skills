# Example Output

```markdown
## E2E Journey Decision

Journey: organization admin disables an active project member.
Why E2E: the risk crosses browser permission state, service authorization, persistence, session revocation, and audit delivery.

Owned setup:
- Create a run-scoped organization, admin, member, and project.
- Observe setup completion through the authoritative API before opening the journey.

Oracles:
- The admin sees the member become disabled.
- The disabled member loses project access after session refresh.
- The member record remains disabled and the audit entry names the admin actor.
- No unrelated member or project state changes.

Readiness and cleanup:
- Wait on the authoritative disabled state with bounded polling derived from the revocation behavior.
- Revoke sessions and delete run-owned records after pass, failure, timeout, or cancellation.

Evidence boundary:
- The accepted scoped journey is not yet run; the task owner must record the selected environment/browser result before the release verdict.
- Other roles, browser/device combinations, and production notification delivery remain outside this proof.
```
