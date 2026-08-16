---
name: routing-quality-review
description: "Use an independently assigned `review-agent` for post-authoring review of changed rd-skills routing registries, fixtures, mappings, or owner conflicts without repair. Skip product work and in-task global rerouting."
---

# Routing Quality Review

## Role

Support `review-agent` in auditing rd-skills routing ownership, triggers,
anti-triggers, and fixtures.

## When To Use

- rd-skills routing registry or router change
- route fixture owner conflict
- independently assigned post-authoring review of a changed rd-skills routing asset

## Do Not Use

- ordinary product engineering task
- global re-routing from inside a dispatched task agent
- no changed rd-skills routing asset or route-owner conflict to review

## Required Inputs

- The four current Skill registries.
- `engineering-control-plane/references/professional-skill-router.md`.
- Routing fixtures and the specific coverage gap being changed.

## Professional Decision Rules

- Keep one primary Professional Skill per Task. Treat Task Review Skills as
  requirements; the global Review Boundary realizes them through one primary
  and zero or more specialist review-agent assignments with exactly one Review
  Skill each.
- Add Layer 3 candidates only for concrete risk signals; keep both Task-side
  implementation selection and each review assignment's independent
  review-risk selection to zero through three. Never copy or union Task Layer 3
  into a review assignment.
- Prefer deterministic signal-to-owner mappings and explicit anti-triggers.
- Do not select this Skill as an implementation owner; keep it non-routable and assign it only for post-authoring review.
- Validate that every selected Skill and reference is present in built output.

## High-Value Gotchas

- A broad route that matches every task recreates context pollution.
- A task-agent that invokes global routing can change ownership mid-task.
- Installing a catalog is not permission to load it in full.

## Execution Checklist

1. Identify one failing or missing routing case.
2. Identify the smallest registry, router, or fixture correction.
3. Check adjacent owner conflicts and anti-triggers.
4. Check affected routes with routing, registry, and reference validators.
5. Record required corrections and intentionally unsupported surfaces.

## Stop / Escalation Conditions

- Stop when the change would create two plausible primary owners for the same signal.
- Escalate when a new Professional Skill or Layer 3 boundary is required.

## Output Contract

- routing findings with required corrections
- trigger and anti-trigger conflicts
- coverage gaps and affected fixtures
- validation results and residual ambiguity

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [routing maintenance](references/routing-maintenance-checklist.md) | decision-checklist | routing review detects owner, trigger, or fixture conflicts | routing registry and fixtures are unchanged or already agree | review-agent | checklist-result, residual-risk |
