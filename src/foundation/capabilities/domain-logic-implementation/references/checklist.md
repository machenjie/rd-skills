# Domain Rule Checklist

- Name the rule, trusted inputs, selected authority, lifecycle or consistency boundary, and rejected placements.
- Inventory reachable create, mutate, replay, import, admin, job, consumer, migration, fixture, ORM, and direct-write paths.
- Define allowed, denied, terminal, boundary, and typed failure outcomes before persistence or external effect.
- Record calculation basis, version, units, precision, rounding, currency, timezone, and effective-time semantics where relevant.
- Select persistence and concurrency defenses from the reachable race rather than from framework convention.
- Keep persistence, provider, queue, cache, file, and transport effects outside the domain authority.
- Define ownership for cross-boundary consistency, retry, compensation, reconciliation, and unknown outcomes.
- Cover existing values, old/new rule coexistence, replay, backfill, projections, and consumer interpretation.
- Tie rule, denial, bypass, boundary, and race claims to current source and scoped evidence with residual owners.
