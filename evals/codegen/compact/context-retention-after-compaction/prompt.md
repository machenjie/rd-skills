# Benchmark Prompt

## Task

Implement bounded evidence that a task can continue correctly after context compaction.

## Context

This assertion-backed live benchmark verifies Context Compaction Retention. It is not a runtime content corpus and must not depend on hidden files, network access, user-specific state, or local absolute paths.

## Requirements

1. Produce a PDD, DDD, SDD, and TDD plan for the starter repository.
2. Modify one repository file.
3. Run a validation command and record whether that validation is fresh after the latest material edit.
4. Review the change, find at least one issue, and record that repair is needed.
5. Simulate a pre-compact checkpoint and a post-compact or SessionStart compact reinjection using bounded facts only.
6. Continue after compaction, repair the issue, and re-review it.
7. Hand off with the preserved original acceptance criteria, DDD invariant, SDD placement/error/logging decision, TDD validation command, changed files, validation freshness, review finding, repair and re-review state, residual risk, and selected skills/capabilities/gates.
8. Include these machine-readable retained context fields: `route_id`,
   `selected_skills`, `selected_capabilities`, `required_quality_gates`,
   `current_stage`, `pdd_summary`, `ddd_invariants`, `sdd_decisions`,
   `tdd_validation_plan`, `changed_paths`, `read_paths`, `validation_results`,
   `validation_freshness`, `review_findings`, `repair_events`,
   `rereview_events`, `residual_risk`, `memory_references`,
   `repo_graph_references`, `active_skill_context`,
   `last_material_edit_index`, and `last_validation_command_index`.

## Constraints

- Keep machine-readable evidence in `COMPACTION_CONTEXT.json`.
- Keep concise human evidence in `CAPABILITY_EVIDENCE.md`.
- Update the starter implementation so validation has a real changed file.
- Do not store raw prompt text, raw assistant messages, raw command output, environment variables, secrets, API keys, full file contents, full diff body, or local absolute user paths.
- Use repo-relative paths for `changed_paths` and `read_paths`; a redacted
  `<local-path>` value is privacy-safe but is not usable retained context.
- Report `privacy_redaction_status`, `context_usable_status`, and
  `context_retention_status` separately.
- Do not claim stale validation as fresh; if an edit occurs after validation, record stale status and rerun validation before final handoff.

## Deliverables

- Updated starter repository implementation.
- `COMPACTION_CONTEXT.json` with bounded compact-retention evidence.
- `CAPABILITY_EVIDENCE.md` as auxiliary readable evidence.
- Final handoff that cites preserved context, validation freshness, review/repair/re-review state, and residual risk.

## Completion Evidence

The case passes only when assertions can inspect concrete artifacts with pre-compact snapshot evidence, post-compact reinjection evidence, preserved required context fields, repair continuation after compaction, re-review, privacy redaction, validation freshness, and residual risk.
