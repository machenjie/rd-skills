# Non-Goal Boundary Definition Checklist

- Select the mode: v1 boundary, anti-scope-creep review, deferred decision control, contract/compatibility boundary, risk-sensitive exclusion, or evidence reuse boundary.
- State source evidence inspected: request/ticket, current docs, registry, source paths, API/schema specs, tests, repository graph, project memory, execution trajectory, and freshness limits.
- State approved in-scope behavior with actors, contexts, endpoints, UI, data entities, permissions, jobs, events, flags, and observability where applicable.
- State out-of-scope behavior using concrete surfaces and workflows.
- Define current version boundary, immutable contract, and deferred version work.
- Identify adjacent redesigns, migrations, platform changes, policy changes, docs, jobs, events, and feature flags that are excluded.
- Identify assumptions that must not influence code, schema, API, UI, permissions, events, jobs, docs, or tests.
- Confirm exclusions do not bypass required security, compliance, data integrity, reliability, accessibility, compatibility, or customer commitments.
- Reject placeholder artifacts: stub endpoints, nullable future fields, reserved enum values, hidden UI, unused roles, future flags, unused jobs/events, and speculative docs.
- Record owner, trigger, and blocking/non-blocking status for deferred decisions.
- Judge future compatibility: v1 must not close the path to v2, and must not add speculative surface for v2.
- Add review checks that detect unauthorized expansion in diffs, schemas, routes, migrations, permissions, jobs, events, docs, and tests.
- Add acceptance exclusions that prove excluded behavior, fields, endpoints, UI, jobs, events, and docs are not present.
- Map each included behavior, excluded surface, forbidden artifact, deferred decision, and compatibility constraint to validation evidence or residual risk.
- State graph/memory/trajectory reuse judgment: accepted, rejected, or not verified, with freshness limits.
- Name handoff boundaries for clarification, structuring, scenarios, acceptance, quality, security, reliability, data/API, release, and task planning.
- State evidence limits and residual risks before handoff.
