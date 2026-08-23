# Documentation Checklist

- Check README and developer setup notes.
- Check API docs, schema docs, and client examples.
- Check migration notes, rollout notes, and rollback notes.
- Check ADR or design decision records.
- Check changelog and release notes.
- Check runbooks, dashboards, alerts, and troubleshooting.
- Check user-facing help, product copy, and workflow docs.
- Check configuration and environment variable docs.
- Record skipped docs with rationale.

## Professional Decision Rules

- Update documentation when behavior, public contract, configuration, operations, migration, deprecation, or user workflow changes.
- Keep examples executable and consistent with current names, defaults, errors, and version behavior.
- Place facts in the owning source document and link rather than duplicate unstable details.
- Validate links, commands, generated outputs, and migration instructions against the final implementation.

## High-Value Gotchas

- Stale examples are worse than missing examples.
- Generated docs must be changed at their source.
- A migration guide without rollback and version boundaries is incomplete.

## Execution Checklist

1. Trace the behavior delta to its audience, owning document, generated origin, and version boundary.
2. Choose update, migration note, deprecation guidance, or evidence-backed no-docs treatment.
3. Verify examples, commands, links, rollback guidance, and safe-disclosure boundaries.
4. **Task mode:** update the owning source for the accepted behavior delta.
5. **Review mode:** judge examples, commands, links, and migration guidance.
6. Stop closure when source behavior and published guidance cannot be reconciled.
