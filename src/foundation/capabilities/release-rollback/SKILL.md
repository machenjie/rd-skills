---
name: release-rollback
description: "`analysis-agent`/`task-agent`/`review-agent`: use for release identity, compatibility, exposure, stop, rollback, or recovery; skip pipeline-only and no-release work."
---

# release-rollback

## Registry Trigger

**Use when**

- design release identity ordering compatibility exposure observation stop rollback and forward recovery across changed surfaces

**Do not use when**

- work is limited to pipeline mechanics image construction cluster resources data migration execution or local validation with no release decision

## Skill Role

Own release identity, exposure, recovery, irreversible boundaries, and proof limits; consume `version-compatibility` and exclude mechanics.

## High-Value Rules

- Bind one release identity and current compatibility decision before exposure or recovery.
- Give each changed surface an owned rollback, disable, compensation, restore, reconciliation, or forward-repair path.
- Load the named benchmark, checklist, or evidence Reference according to the open output.

## Anti-Patterns

- Do not call a previous artifact a rollback while other release state remains changed.

## Stop Conditions

- Stop on stale compatibility or unknown identity, authority, irreversibility, external reversal, partial recovery, or validation.
- Return compatibility and release authority to their owners.

## Output Contract

- Return a release-recovery decision: define identity, ordering, accepted compatibility decision, exposure, stop signals, per-surface recovery, evidence limits, and residual owner

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | a current accepted version-compatibility decision leaves release-specific exposure rollback compensation restore or forward-recovery mechanisms open | compatibility evidence is missing stale or unresolved or one bounded recovery path resolves the release | analysis-agent, task-agent, review-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | a release crosses artifacts states exposure signals irreversible effects or partial recovery after compatibility acceptance | compatibility evidence is missing stale or unresolved or no release recovery decision changes | analysis-agent, task-agent, review-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | Release identity compatibility exposure stop recovery authority or freshness claims need proof | Fresh scoped evidence closes each changed-surface recovery claim | analysis-agent, task-agent, review-agent | evidence-record, proof-limit, residual-risk |
