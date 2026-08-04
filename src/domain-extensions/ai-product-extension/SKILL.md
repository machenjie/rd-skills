---
name: ai-product-extension
description: "For analysis/task/review agents using a Professional Skill on models, RAG, agents, evaluation, or safety; not for work without AI decision impact."
---

# ai-product-extension

## Role

Use this focused Layer 3 Domain Skill for AI product decisions. Give
`analysis-agent`, `task-agent`, and `review-agent` model-behavior,
retrieval-authorization, tool-authority, evaluation, safety, and cost constraints
across product surfaces.

## When To Use

- model, prompt, retrieval, embedding, evaluation, agent tool-use, or AI data behavior

## Do Not Use

- deterministic behavior or documentation with no AI decision surface
- AI terminology, static algorithms, or ordinary search without a model decision

## Required Inputs

- model/provider, data and permission boundary, user impact, and fallback
- evaluation target, current evidence, affected actors, and allowed proof scope

## Professional Decision Rules

- **Trace consequential claims**: distinguish source evidence, model inference, uncertainty, and abstention according to user harm.
- **Keep low-impact output proportional**: do not impose universal citations on creative or low-impact output.
- **Preserve retrieval authorization**: prove retrieved data honors source permissions, tenant scope, and revocation.
- **Contain untrusted prompt content**: prove user or retrieved content cannot override trusted policy or authorize action.
- **Bound tool authority**: prove least privilege, valid arguments, confirmation, auditability, and recovery for side-effecting calls.
- **Evaluate probabilistic changes**: compare baseline and treatment on representative success, refusal, adversarial, and boundary cases.
- **Calibrate evaluation effort**: derive datasets, metrics, and thresholds from product harm and observed variance.
- **Distrust model output downstream**: validate model output independently at data, execution, rendering, API, and policy boundaries.
- **Minimize context data**: include only authorized data needed for the task.
- **Prove sensitive-data lifecycle**: verify redaction and retention when sensitive data reaches providers or logs.

## High-Value Gotchas

- permission-blind retrieval leaks another tenant's chunks even when the source UI is secure
- indirect prompt injection turns retrieved content into unauthorized tool instructions
- evaluation averages hide severe failures in a small, consequential cohort
- provider or model changes alter refusal, token cost, or structured-output behavior without an application code change
- plausible output bypasses validation because downstream code treats model confidence as trust

## Execution Checklist

1. Identify the AI risk signal, affected invariant, and evidence available for this change.
2. Choose controls from the current permission model, harm, reversibility, and measured behavior.
3. Define representative failure tests, fallback, observability, escalation, and residual risk.

## Stop / Escalation Conditions

- Stop when authority, data provenance, permission behavior, or a consequential safety invariant cannot be verified.
- Escalate irreversible tool actions, regulated decisions, sensitive-data exposure, and unsupported provider assumptions to the owning gate.

## Output Contract

- State the AI risk, required outcome, selected control, evaluation limits, fallback, and residual risk.

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [checklist](references/checklist.md) | decision-checklist | model prompt retrieval embedding tool or evaluation behavior crosses product surfaces | AI terminology describes a static algorithm or ordinary search without a model decision | analysis-agent, task-agent, review-agent | checklist-result, residual-risk |
