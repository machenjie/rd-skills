---
name: skill-authoring-expert
description: "`analysis-agent`/`task-agent`/`review-agent`: use when authoring SKILL.md, triggers, decisions, references, registry, routing, or validation; skip when no Skill content changes."
---

# skill-authoring-expert

## Registry Trigger

**Use when**

- add, rename, split, slim, audit, or remove a Control, Professional, Foundation,
  or Domain Skill
- change routing, references, registries, profile delivery, or Skill validation

**Do not use when**

- ordinary product implementation that does not modify rd-skills authoring assets
- user-specific content ingestion, indexing, mapping, or packaging

## Skill Role

Keep rd-skills source Skills, registries, generated profiles, Marketplace output, routing, and validators aligned without adding runtime control machinery.

## Inputs

- requested behavior and affected Skill layer
- adjacent Skills, four registry entries, routing fixtures, and build profiles
- current validation and generated-output boundaries

## High-Value Rules

- Define root `SKILL.md` ownership around routing, decisions, escalation, output, and targeted Reference links.
- References hold only decision-changing depth; every reference needs a loading signal.
- Frontmatter contains only `name` and a precise trigger/boundary `description`.
- Keep one primary Professional Skill per task and load Layer 3 only for named risks.
- Edit authoring source and regenerate without treating `dist/` as source truth.
- For a trigger, boundary, output, delivery, or validator behavior change, add
  missing deterministic evidence or reuse evidence that catches the regression.

## Anti-Patterns

- More headings or keywords do not make a Skill more professional.
- Reject broad Skill descriptions because they cause over-routing.
- Reject vague anti-triggers because they cause catalog loading.
- Copied rules create contradictory owners and inflate context.
- Generated files and installation layouts must trace back to authoring source.

## Execution Checklist

1. Identify the layer, owner, adjacent conflicts, and reuse option.
2. Define trigger, anti-trigger, required inputs, stop conditions, and output.
3. Keep the root concise and move only conditional depth to targeted references.
4. Update the Registry only when its contract changes; add or repair a
   routing/behavior fixture only when current evidence misses the changed behavior.
5. Run source, content, routing, build, installation, and link validation.

## Stop Conditions

- Stop new structure when an existing Skill or reference owns the decision.
- Escalate public profile, installation, security, or Marketplace compatibility changes.
- Reject any user-specific corpus behavior, source installation, hidden delivery,
  interception, persistent task state, or unsupported efficacy claim.

## Output Contract

- layer and ownership decision
- trigger, anti-trigger, reference split, and routing impact
- source and generated files changed
- validation results, proof limits, compatibility risk, and next action

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | Skill routing build or evaluation assertions require deterministic positive and negative proof | no Skill contract routing or generated artifact changes | analysis-agent, review-agent, task-agent | evidence-record, proof-limit, residual-risk |
| [pressure scenarios](references/pressure-scenarios.md) | targeted | a Skill must resist pressure to violate role scope safety or evidence boundaries | no pressure or boundary behavior is under evaluation | analysis-agent, review-agent, task-agent | validation-plan, evidence-gap |
| [tdd for skills](references/tdd-for-skills.md) | targeted | a Skill routing behavior build or installation contract changes and current deterministic evidence does not expose the regression | the change cannot alter Skill routing behavior build or installation contracts or existing deterministic evidence already covers the regression | analysis-agent, review-agent, task-agent | validation-plan, proof-limit |
