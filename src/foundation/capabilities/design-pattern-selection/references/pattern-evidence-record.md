# Pattern Evidence Record

Load this reference when a pattern decision depends on repository graph, project memory, prior validation, generated code, benchmark output, or execution history. Treat those sources as selectors until they are reconciled with the current source.

## Evidence Freshness Gate

Record these fields before approving a pattern:

- `current_source_boundary`: files, symbols, public APIs, tests, generated artifacts, and runtime entry points inspected after the final edit.
- `same_pattern_scan`: repository search for the same pattern name, interface shape, lifecycle owner, adapter boundary, registry/provider usage, or direct-code alternative.
- `graph_claims`: dependency or call graph facts accepted, rejected, or not verified; include command/report path and timestamp when available.
- `memory_claims`: project-memory facts accepted or rejected; include source/date and why the current module shares or does not share the same force.
- `execution_claims`: tests, validators, profiles, logs, traces, or benchmarks used; include working directory, command, exit code, and freshness after the final structure edit.
- `contradictions`: graph-memory-execution disagreements, stale reports, missing consumers, or changed public contracts.
- `decision`: selected pattern or direct-code rejection, rejected simpler alternative, deletion path, and owner for remaining risk.

## Stale Evidence Rules

- A same-pattern scan before a final file move, public API edit, registry/provider change, or generated-client update is stale.
- A memory note without source/date cannot approve a pattern; it can only suggest what to inspect.
- A benchmark before the selected pattern changes allocation, dispatch, IO, queueing, or locking cannot prove runtime safety.
- A passing unit test that mocks internal collaborators cannot prove pattern correctness when the contract is public behavior.
- A graph report that omits generated files, plugin registration, dynamic imports, framework wiring, or runtime configuration must name those omissions.

## Closure Wording

Use this wording in handoff when evidence is partial: "Pattern decision is accepted only for the inspected boundary; graph/memory/execution evidence does not prove uninspected consumers, generated clients, runtime load, or stale reports named here."
