# Example Output

```markdown
## Domain Rule Contract

Rule: a subscription cancellation changes active or past-due state to canceled and records the effective rule version.

Authority:
- The subscription aggregate owns the transition because it has current lifecycle state and can reject mutation before persistence.
- The application service owns actor authorization, transaction scope, persistence, and provider-reversal handoff.

Outcomes:
- Canceled with effective time and rule version.
- Denied for terminal state.
- Denied for missing administrator reason.

Bypass and evolution:
- API, admin, import, job, ORM mutation, migration, and fixture paths are scanned for direct status writes.
- Existing canceled records remain readable under their recorded rule version; a backfill is not implied.

Defenses:
- A storage version check protects a competing update; domain denial remains the readable rule authority.

Evidence limit:
- Current domain and storage fixtures cover named transitions and one competing-write case; uninspected support tools and production schedules remain residual scope.
```
