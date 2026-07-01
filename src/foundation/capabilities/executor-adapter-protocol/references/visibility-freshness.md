# Visibility Freshness

Load this reference when adapter closure depends on repository graph, project memory, prior execution traces, old validation output, generated hook artifacts, or compaction summaries. Treat those sources as selectors until checked against current adapter capabilities after the final edit.

## Freshness Record

Record these fields before approving adapter evidence:

- `current_adapter_boundary`: adapter capability matrix, hook templates, normalized event fields, permission visibility, validation visibility, changed-path visibility, stop/compaction support, generated artifacts, reports, and consumers inspected after the final edit.
- `graph_claims`: hook paths, consumer paths, generated artifact relationships, event families, or gate dependencies accepted, rejected, or unknown; include command or report path.
- `memory_claims`: prior executor behavior, missing field, warning, incident, or maintainer decision accepted or rejected; include source/date when available.
- `execution_claims`: adapter fixture, validator, hook dry-run, permission command, validation log, compaction summary, or stop record used; include command, exit code, and report path.
- `stale_evidence`: any scan, memory, fixture, generated artifact, validation log, or compaction summary that predates adapter capability, event field, permission, path visibility, fail policy, or closure-contract edits.
- `freshness_decision`: current, partial, stale, unsupported, or not verified, with residual owner and rollback note.

## Reconciliation Rules

- A graph scan before hook template, normalized field, generated artifact, or consumer changes cannot prove current adapter visibility.
- Project memory without source/date can suggest a missing field, but it cannot prove support, privacy boundary, or closure status.
- A validation log before final adapter edits cannot prove command outcome, path coverage, or stop visibility.
- Compaction summaries prove only retained bounded facts; they do not prove raw event order, hidden prompts, secrets, or full command output.
