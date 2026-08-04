# Non-Goal Boundary Definition Checklist

- Select the mode: v1 boundary, anti-scope-creep review, deferred decision control, contract/compatibility boundary, risk-sensitive exclusion, or evidence reuse boundary.
- State source evidence inspected: request/ticket, current docs, registry, source paths, API/schema specs, tests, repository inspection, prior task evidence, observable action sequence, and freshness limits.
- State approved in-scope behavior with actors, contexts, endpoints, UI, data entities, permissions, jobs, events, flags, and observability where applicable.
- State out-of-scope behavior using concrete surfaces and workflows, including excluded adjacent redesigns, migrations, platform or policy changes, docs, jobs, events, and feature flags.
- Define current version boundary, immutable contract, and deferred version work.
- Keep non-goal assumptions from altering current code, schemas, contracts, permissions, events, jobs, documentation, or tests.
- If safety or compatibility depends on the assumption, return it to the owning decision instead of excluding it.
- Confirm exclusions do not bypass required security, compliance, data integrity, reliability, accessibility, compatibility, or customer commitments.
- Reject placeholder artifacts: stub endpoints, nullable future fields, reserved enum values, hidden UI, unused roles, future flags, unused jobs/events, and speculative docs.
- Record owner, trigger, and blocking/non-blocking status for deferred decisions.
- Assess whether the v1 decision creates an avoidable known blocker for a likely v2 path, while declining speculative v2 surface that lacks current approval.
- Add review scans for unauthorized expansion in diffs, schemas, routes, migrations, permissions, jobs, events, docs, and tests. Pair them with acceptance checks proving excluded behavior, fields, endpoints, UI, jobs, events, and docs are absent.
- Map each included behavior, excluded surface, forbidden artifact, deferred decision, and compatibility constraint to validation evidence or residual risk.
- Record current source, diff, and validation reuse judgment, freshness limits, evidence gaps, and residual risk before handoff.
- Name handoff boundaries for clarification, structuring, scenarios, acceptance, quality, security, reliability, data/API, release, and task planning.
