---
name: delivery-release-gate
description: "Use `analysis-agent` for release decisions, `task-agent` for delivery artifacts, or `review-agent` for readiness on deployment, migration, rollback, or production risk. Skip local work with no release decision."
---

# delivery-release-gate

## Role

- **Analysis mode (`analysis-agent`):** Decide rollout, containment, and recovery behavior.
- **Task mode (`task-agent`):** Produce the accepted release artifact and rollback metadata.
- **Review mode (`review-agent`):** Judge artifact readiness against rollout and recovery criteria.

## When To Use

- production release; irreversible deployment or migration

## Do Not Use

- local implementation only
- no release decision

## Required Inputs

- release boundaries; rollback requirements and recovery constraints
- **Analysis mode (`analysis-agent`):** current release topology, blast radius, compatibility, and recovery evidence.
- **Task mode (`task-agent`):** accepted release-artifact decision with provenance, rollout, and rollback checks.
- **Review mode (`review-agent`):** release artifact with mixed-version and recovery evidence.

## Professional Decision Rules

- Prove release dimensions material to selected artifact, configuration, compatibility, migration, rollout, observability, and recovery risk.
- Select rollout, watch, approval, and containment from blast radius, reversibility, current controls, and policy.
- Test old/new coexistence or recovery against the actual artifact and material environment dimensions when triggered.
- Reserve destructive, production, privileged, or irreversible actions for explicit user authority.

## High-Value Gotchas

- A rollback command does not prove recovery.
- Clean deployment can miss version skew.
- Early cleanup can remove recovery.

## Execution Checklist

1. Trace artifact identity, configuration, migration, compatibility, blast radius, and recovery ownership.
2. Choose rollout, watch, containment, and rollback controls from reversibility and current policy.
3. Verify mixed-version behavior, promotion provenance, stop signals, and recovery feasibility.
4. **Analysis mode:** select rollout, watch, containment, and rollback controls.
5. **Task mode:** produce artifact provenance, compatibility, and rollback metadata.
6. **Review mode:** judge mixed-version, stop-signal, and recovery evidence.
7. Stop when authority, artifact identity, or recovery proof remains implicit.

## Stop / Escalation Conditions

- Block when required immutable artifact identity is unproven.
- Block unverified target configuration, secrets, or environment equivalence.
- Require rollout approval, watch ownership, stop signals, and containment when risk triggers them.
- Require rollback rehearsal only when risk or policy demands it.
- Block migration or contract release lacking triggered mixed-version, ordering, coordination, reconciliation, rollback, or forward-repair proof.
- Block infrastructure release when desired/effective change, blast radius, authority, drift or state handling, or containment cannot be inspected.
- Refuse write tools without permission, sandbox, preview, recovery, and redaction evidence.

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
