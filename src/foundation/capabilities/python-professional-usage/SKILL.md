---
name: python-professional-usage
description: "`analysis-agent`/`task-agent`/`review-agent`: use when Python changes cross import, async, resource, typing, mutability, or serialization boundaries; skip tool-only work."
---

# python-professional-usage

## Registry Trigger

**Use when**

- Python code changes import or initialization, async and blocking work, owned resources, public typing, shared mutability, or serialization behavior.
- Python runtime semantics can change failure, cleanup, cancellation, isolation, or consumer compatibility in the current scope.

**Do not use when**

- The open decision is language/runtime selection, dependency policy, build mechanics, test strategy, or a measured performance bottleneck.
- No Python-specific runtime or data boundary changes.

## Skill Role

Protect Python import and initialization behavior, async and blocking boundaries, resource lifetime, dynamic type and mutability hazards, and serialization semantics.

## High-Value Rules

- Identify import side effects, ordering, reload, fork/spawn, and failure behavior.
- Reject irreversible external effects during module import. Permit explicit immutable environment or configuration reads when deterministic, side-effect-bounded, reload/fork-safe, failure-defined, and validated across supported entrypoints.
- Classify blocking calls, spawned tasks, cancellation, exception observation, and context propagation on async paths.
- Bind files, responses, sessions, cursors, temporary resources, and locks to an explicit cleanup owner.
- Parse untrusted values before relying on static types; preserve missing, `None`, falsey, subclass, and coercion semantics.
- Define reset and synchronization ownership for mutable defaults, caches, and process or task globals.
- Bound serialization by format, version, admitted types, unknown fields, numeric/time semantics, and construction hooks.
- Preserve exception causes, cleanup, partial state, transaction outcome, and retry classification across layers.

## Anti-Patterns

- An async function calls blocking code or starts background work whose lifetime and failure have no owner.
- Import performs network, migration, registration, or mutable or implicit configuration work that changes under reload, workers, or fork/spawn.
- A type annotation, `Any`, cast, or successful deserialize is treated as proof that runtime input is valid and compatible.
- A mutable default, cached singleton, or shallow copy leaks state between requests or tests, while cleanup covers the happy path alone.

## Stop Conditions

- Route language, package, build, test, and performance decisions to their specialist owners.
- Route hostile deserialization or command execution to `security-privacy-gate`, public schemas to `data-api-contract-changer`, and money or timezone semantics to `i18n-timezone-money-safety`.

## Output Contract

- Python boundary decision with inspected import and initialization, async and cancellation, resource lifetime, typing and mutability, serialization and exception behavior, validation evidence, proof limits, residual risk, and specialist handoffs

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | Python change crosses import async resource mutability typing serialization or exception boundary whose failure semantics remain unclear | Current Python entrypoints value contracts and focused checks settle the changed boundary | task-agent, analysis-agent, review-agent | option-comparison, selected-approach |
