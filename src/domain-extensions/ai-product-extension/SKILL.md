---
name: ai-product-extension
description: "For analysis/task/review agents using a Professional Skill on models, RAG, agents, evaluation, or safety; not for work without AI decision impact."
---

# ai-product-extension

## Role

Focused Layer 3 Domain Skill: `analysis-agent` maps authority, `task-agent` applies controls, `review-agent` judges evidence.

## When To Use

- model, prompt, retrieval, embedding, evaluation, agent tool-use, or AI data behavior

## Do Not Use

- deterministic behavior or documentation with no AI decision surface
- AI terminology, static algorithms, or ordinary search without a model decision

## Required Inputs

- model/provider, data and permission boundary, user impact, and fallback
- evaluation target, current evidence, affected actors, and allowed proof scope

## Professional Decision Rules

- Preserve Professional ownership.
- Load the checklist only for an active AI decision.
- Close with current authority, evaluation, failure/fallback, and residual risk.

## High-Value Gotchas

- Plausible or averaged model output does not prove authorization, safety, or consequential-cohort behavior.

## Execution Checklist

1. Confirm the active AI decision, owner, authority, and affected invariant.
2. Load the checklist and close its applicable controls with current evidence.
3. Report fallback, proof limits, escalation, and residual risk.

## Stop / Escalation Conditions

- Stop without provenance, authority, fallback, or safety proof.
- Escalate irreversible, regulated, sensitive-data, or unsupported-provider decisions.

## Output Contract

- Risk, outcome, control, evaluation limit, fallback, residual risk.

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [checklist](references/checklist.md) | decision-checklist | model prompt retrieval embedding tool or evaluation behavior crosses product surfaces | AI terminology describes a static algorithm or ordinary search without a model decision | analysis-agent, task-agent, review-agent | checklist-result, residual-risk |
