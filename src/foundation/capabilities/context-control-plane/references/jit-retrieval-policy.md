# Just-In-Time Retrieval Policy

Use route, stage, changed paths, repository graph, TaskContextPack, and validation signals to decide what to read next. Do not prefetch broad source trees or generated graphs. A context pack is an index, selector, and handoff artifact; the JIT retrieval plan controls the actual reads.

## Retrieval Record

For each JIT read, record:

- selector signal
- source path or artifact
- reason for reading now
- source freshness marker when available
- skipped adjacent paths with reason

TaskContextPack v3 records JIT reads as:

- `discovery`: bounded commands that verify graph, pack, validator, or search evidence; expected output must be a bounded summary, artifact reference, or read slice.
- `targeted_reads`: repository-relative source paths selected for direct inspection, with reason, line hint, read policy, and source/generated/unknown truth status.
- `deferred_reads`: repository-relative candidates intentionally left out of active context until evidence requires them.
- `forbidden_reads`: generated outputs, broad dependency folders, private VCS internals, and other paths that must not be read into active context.

## Source Truth

Repository graph, project memory, prior summaries, and generated reports can identify likely files, tests, validators, and owners. They do not replace current source reads for facts used in implementation, review, validation, or final closure.

Graph output is never active context by itself. Treat graph-selected files as read candidates, graph-selected closure evidence as confidence metadata, and skipped graph nodes as assumptions or residual risk until current source is inspected.
