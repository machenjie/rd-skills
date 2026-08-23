---
name: delivery-release-gate
description: "Use `analysis-agent` for release decisions, `task-agent` for delivery artifacts, or `review-agent` for readiness on deployment, migration, rollback, or production risk. Skip local work with no release decision."
---

# delivery-release-gate

## Role

- **Analysis mode (`analysis-agent`):** select rollout, containment, and recovery.
- **Task mode (`task-agent`):** produce the accepted release artifact and rollback metadata.
- **Review mode (`review-agent`):** judge rollout and recovery readiness.

## When To Use

- production release; irreversible deployment or migration

## Do Not Use

- local implementation only
- no release decision

## Required Inputs

- release boundaries; rollback requirements and recovery constraints
- **Analysis mode (`analysis-agent`):** current release topology, blast radius, compatibility, and recovery evidence.
- **Task mode (`task-agent`):** accepted release-artifact decision, provenance, rollout, and rollback checks.
- **Review mode (`review-agent`):** release artifact with mixed-version and recovery evidence.

## Professional Decision Rules

- Name the release decision owner.
- Load the named Reference for the open output.
- Require authority before action.

## High-Value Gotchas

- Artifact identity can drift between validation, packaging, promotion, and rollback.
- Rollback availability does not prove compatibility, data recovery, or restoration time.
- Mixed-version success can hide an irreversible migration or configuration boundary.

## Execution Checklist

- **Analysis mode:** Map blast radius, compatibility order, containment, and recovery authority.
- **Task mode:** Build the accepted release artifact with provenance and rollback metadata.
- **Review mode:** Verify built identity, mixed-version evidence, and recovery readiness.
- Record unproved environments, migrations, and operator actions as residual risk.
- Minimal validation: inspect built-artifact identity and run the selected compatibility or recovery check.

## Stop / Escalation Conditions

- Block stale artifact/environment, authority, containment, compatibility/migration, infrastructure-state, or recovery evidence.
- Refuse destructive, privileged, irreversible, or secret-bearing production action absent authority, sandbox/preview, recovery, and redaction.

## Output Contract

- **Analysis mode (`analysis-agent`):** release plan; authority boundary; rollout and rollback decisions.
- **Task mode (`task-agent`):** release artifact; provenance, compatibility, and rollback metadata.
- **Review mode (`review-agent`):** go/no-go verdict; readiness gaps; unreviewed deployment risk.

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [checklist](references/checklist.md) | decision-checklist | bounded L2 release checks remain unresolved | mode-specific closure or extended proof is required | analysis-agent, task-agent, review-agent | checklist-result, residual-risk |
| [delivery output and gates](references/delivery-output-and-gates.md) | targeted | L3-L5 release closure needs extended risk gates | compact L1-L2 release proof is sufficient | analysis-agent, task-agent, review-agent | gate-decision, residual-risk |
| [index](references/index.md) | index | competing release references require conflict or output-fragment selection | one task-named release reference resolves selection | analysis-agent, task-agent, review-agent | reference-selection |
| [release evidence](references/release-evidence-patterns.md) | evidence-pattern | release claims depend on runtime or artifact proof | no release claim needs fresh runtime evidence | analysis-agent, task-agent, review-agent | evidence-record, proof-limit, residual-risk |
