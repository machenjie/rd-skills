# Documentation Checklist

Use only the checks relevant to the requested document or affected audience. A local correction does not require an inventory of every artifact below.

- Check README and developer setup notes.
- Check API docs, schema docs, and client examples.
- Check migration notes, rollout notes, and rollback notes.
- Check ADR or design decision records.
- Check changelog and release notes.
- Check runbooks, dashboards, alerts, and troubleshooting.
- Check user-facing help, product copy, and workflow docs.
- Check configuration and environment variable docs.
- Record affected docs left outstanding with rationale.

## Professional Decision Rules

- Create, edit, or review requested documentation even when runtime behavior is unchanged; also maintain affected docs after behavior or contract changes.
- Keep examples executable and consistent with current names, defaults, errors, and version behavior.
- Place facts in the owning source document and link rather than duplicate unstable details.
- Validate changed content against its applicable source, with implementation evidence for behavioral claims.

## High-Value Gotchas

- Stale examples are worse than missing examples.
- Generated docs must be changed at their source.
- A migration guide without version boundaries and an executable recovery path is incomplete; explain rollback limits and any validated restore, forward repair, or containment alternative.

## Execution Checklist

- Trace the documentation request or behavior delta to its audience and owning source, including generated origin and version boundary when relevant.
- Choose the requested artifact, with migration, deprecation, or no-docs treatment only when the change calls for it.
- **Task mode:** create or edit the owning source and check the affected content.
- **Review mode:** judge accuracy, coverage, and applicable recovery or disclosure evidence.
- Stop closure when material claims and authoritative sources cannot be reconciled.
