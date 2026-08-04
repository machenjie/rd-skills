---
name: form-validation-design
description: "`analysis-agent`/`task-agent`/`review-agent`: use when form fields, validation, async checks, submit states, or recovery change; skip when form behavior is unaffected."
---

# form-validation-design

## Registry Trigger

**Use when**

- design form fields validation messages submission states and error recovery

**Do not use when**

- no task-local form validation design decision is required

## Skill Role

Define field meaning, client and authoritative validation handoff, async ordering, submit identity, error mapping, recovery, accessibility, and form evidence. Exclude business-rule authority and API contracts.

## High-Value Rules

- **Define field meaning and canonical value.** Name source, optionality, empty and null behavior, normalization, units, locale, sensitive classification, and the authoritative business object or command each field affects.
- **Split immediate guidance from authoritative validation.** Use client checks for timely structural feedback while preserving server, domain, permission, uniqueness, and current-state decisions at their owned boundaries.
- **Order asynchronous validation safely.** Bind results to field value, form identity, user or tenant context, and request generation so stale responses cannot clear or replace newer errors.
- **Give submission a stable operation boundary.** Prevent accidental duplicates, preserve unknown outcomes, coordinate cancellation and retry with idempotency, and distinguish accepted, pending, completed, rejected, and failed states.
- **Route ambient-credential mutations to security review.** When browsers attach credentials without an explicit per-request authorization act, require `web-security` and the selected security owners. Their decision defines request-integrity controls and proves cross-site denial.
- **Map errors to actionable recovery.** Preserve field, form, conflict, permission, dependency, and unexpected meanings, retain safe user input, focus or announce relevant feedback, and avoid leaking sensitive state.
- **Handle cross-field and server changes.** Re-evaluate dependent fields when inputs change and reconcile stale drafts, concurrent updates, expired state, and server-normalized values without silently discarding user intent.
- **Prove representative interaction paths.** Exercise keyboard and assistive use, invalid and boundary values, async races, duplicate submission, timeout, server rejection, recovery, and preserved-input behavior relevant to the task.

## Anti-Patterns

- Treat client validation as authority for permission, uniqueness, eligibility, current state, or consequential writes.
- Clear user input after an error or let a stale async response overwrite current field or form state.
- Disable submission with no discoverable reason, or show generic errors that cannot guide correction or safe retry.

## Stop Conditions

Escalate when field or business authority is unknown, submission can duplicate consequential effects, stale validation cannot be ordered, or sensitive values lack a handling policy. Also escalate when server errors cannot map safely, accessible recovery is unverified, or ambient-credential mutation lacks owned request-integrity and cross-site denied-path proof.

## Output Contract

- form-validation decision with field semantics, validation authority, async ordering, submission identity, error and recovery behavior, accessibility evidence, proof limits, and residual owners

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | Validation authority, async timing, duplicate submission, or recovery remains open | A copy-only edit leaves form behavior unchanged | task-agent, analysis-agent, review-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | Form changes business rules, session protection, errors, or partial failure | No field, submit, or recovery behavior changes | task-agent, analysis-agent, review-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | Form claims need fresh backend, race, and duplicate-submit proof | No authority or submission-safety claim awaits validation | task-agent, analysis-agent, review-agent | evidence-record, proof-limit, residual-risk |
