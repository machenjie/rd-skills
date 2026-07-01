# Task Contract Patterns

Use this reference when a task node must be executable by a fresh agent without hidden context. Keep each task contract concise and scoped to one owner surface and one reviewable artifact.

## Node Contract
- **Scope:** one goal, one owner surface, one risk domain, and one expected artifact.
- **Inputs:** exact files, configs, docs, generated artifacts, callers, tests, or previous node outputs to inspect.
- **Mutation boundary:** exact files to create, modify, or delete, plus public/internal/private visibility and compatibility impact.
- **Reuse and placement:** existing pattern or helper considered first, rejected locations, dependency direction, and why new structure is or is not needed.
- **Validation:** literal command or validator, expected output, evidence artifact, freshness rule, and what the check does not prove.
- **Rollback:** revert command, rollback node, forward-fix decision, or manual owner when rollback is not immediate.
- **Review and handoff:** independent review gate, completion evidence, downstream unblock condition, and residual risk owner.

## Splitting Rules
- Split a node when it mixes migration, API contract, authorization, UI behavior, data backfill, release, or documentation evidence.
- Split a node when two owners, two mutable shared resources, or two validation commands are required to prove completion.
- Keep nodes together only when splitting would create artificial handoff overhead and the same reviewer can validate the full artifact in one pass.

