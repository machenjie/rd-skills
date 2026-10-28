---
name: change-documentation-gate
description: "Use `task-agent` to create or edit source-backed documentation, or `review-agent` to assess its accuracy and coverage. Covers standalone docs and maintenance after behavior changes; skip implementation-only work with no documentation task."
---

# change-documentation-gate

## Role

Support `task-agent` and `review-agent` for source-owned documentation accuracy,
including standalone documentation and guidance maintained after behavior changes.

- **Task mode (`task-agent`):** Create or edit the requested documentation at its owning source.
- **Review mode (`review-agent`):** Judge the requested guidance against its sources, audience task, and currentness.

## When To Use

- standalone documentation creation, editing, or review
- documentation impact from public behavior or operator workflow changes

## Do Not Use

- implementation-only work with no documentation task
- self review request

## Required Inputs

- documentation request, audience, and scope
- source evidence or accepted design; behavior delta when applicable
- **Task mode (`task-agent`):** owning documentation source, generated origin if applicable, and checks for the affected content.
- **Review mode (`review-agent`):** guidance under review with source and freshness evidence.

## Professional Decision Rules

- Honor standalone documentation requests without inventing a behavior delta; unchanged runtime behavior is not a reason to skip them.
- For behavior changes, update affected documentation or justify a no-docs decision from audience impact. Keep implementation with its selected Primary and unresolved business or architecture decisions with their owners.
- Place facts in the owning source and regenerate derived documentation instead of duplicating unstable details.
- Keep examples consistent with current names, defaults, errors, and version behavior.
- Match validation to the changed content: text diffs, affected links, changed commands/examples, or diagram meaning and target format. Render when presentation or generated output is affected; a prose correction needs no unrelated checks.
- Apply migration, runbook, ADR, release, or disclosure checks only to the affected artifact and its actual risk.

## High-Value Gotchas

- Generated documentation can pass source checks while rendered links or examples remain stale.
- A no-docs claim can hide audience impact when its evidence omits changed behavior.
- Safe-disclosure limits still apply to examples, runbooks, migration notes, and incident records.

## Execution Checklist

- **Task mode:** Map the requested documentation or behavior change to its owning source and any generated origin.
- **Task mode:** Validate the content that changed against its source and intended use.
- **Review mode:** Compare the guidance with the requested scope, source evidence, and applicable failure guidance.
- Record outstanding affected surfaces and validation limits. Unaffected artifacts are not documentation debt.

## Stop / Escalation Conditions

- Stop release when changed audience behavior lacks documentation or a source-backed no-docs rationale.
- Stop a no-docs decision when affected audiences or documentation sources have not been inspected; this decision does not replace an explicit documentation request.
- Stop publishing when docs expose secrets, internal topology, tenant-sensitive details, unapproved security posture, or customer/audit data without safe-disclosure review.
- Resolve evidence required by the affected artifact before closure. Migrations need recovery; runbooks need expected signals and escalation; ADRs need decision authority; incident/compliance records need applicable approval or retention.

## Output Contract

- **Task mode (`task-agent`):** documentation changes; source mapping and validation limits; outstanding affected documentation, if any.
- **Review mode (`review-agent`):** documentation verdict; accuracy and coverage findings; unverified claims and validation limits.

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [checklist](references/checklist.md) | decision-checklist | Documentation creation, editing, or review needs a quick coverage check across affected artifacts | A single local correction is fully covered by the root contract, or deeper artifact-specific guidance is needed | task-agent, review-agent | checklist-result, residual-risk |
| [documentation output and gates](references/documentation-output-and-gates.md) | targeted | Documentation needs reader-task organization or artifact-specific closure for guides, release notes, runbooks, migration notes, ADRs, incident/compliance packets, or no-docs decisions | Body output contract is sufficient for a small decision | task-agent, review-agent | gate-decision, residual-risk |
| [engineering diagrams](references/engineering-diagrams.md) | targeted | The documentation deliverable creates, edits, or reviews an engineering diagram of supplied facts or an accepted design | No diagram deliverable is requested or needed, or unresolved business or architecture decisions are the task instead of documenting an accepted view | task-agent, review-agent | selected-approach, validation-plan, proof-limit |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | Closure depends on source-to-doc freshness, consumer-impact proof, rendered/link/spec validation, evidence retention, safe disclosure, or tool-output boundaries | No evidence freshness, retention, or safe-disclosure risk is material | task-agent, review-agent | evidence-record, proof-limit, residual-risk |
| [index](references/index.md) | index | competing change documentation gate references require dependency, conflict, or output-fragment selection | the change documentation gate root or a task-named reference already resolves selection | task-agent, review-agent | reference-selection |
