---
name: skill-authoring-expert
description: Professional skill-authoring and governance capability for designing, writing, reviewing, slimming, splitting, and maintaining ChangeForge skills, so every SKILL.md body, reference, capability, domain extension, registry entry, and routing rule keeps a clear boundary, precise triggers, explicit non-goals, a testable output contract, a disciplined context budget, progressive reference loading, and synchronized registry, build, and validation impact. Use when authoring or auditing skills, not as a general documentation or tutorial guide.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "103"
changeforge_version: 0.1.0
---

# Mission

Design, write, review, and maintain ChangeForge skills so that every SKILL.md has a clear boundary, professional content, low context waste, reliable routing, testable output, and progressive loading. The SKILL.md body owns routing, execution, boundary, and the output contract. References own deep checklists, examples, anti-examples, benchmarks, and long tables. A foundation capability is a compact engineering decision aid, not a tutorial. A professional skill is a runtime entry point and must not copy large foundation-capability bodies. This capability protects the skill mesh from over-routing, under-routing, context bloat, stale rules, missing references, and unreliable agent behavior.

# When To Use

Use this capability when:

- Adding or modifying a SKILL.md body.
- Adding or modifying a foundation capability.
- Adding or modifying a professional skill.
- Adding or modifying a domain extension.
- Editing `references` content.
- Editing `skills.yaml`, `capabilities.yaml`, `domain-extensions.yaml`, or `routing-rules.yaml`.
- Running a skill content audit.
- Performing skill slimming.
- Splitting an over-weight SKILL into a smaller body plus references.
- Merging duplicate capabilities.
- Deciding whether content belongs in the SKILL.md body or in references.
- Judging whether a skill over-routes or has an unclear boundary.
- Judging whether a skill is insufficiently professional or has drifted into tutorial content.

# Do Not Use When

- Do not use for ordinary README or general documentation writing.
- Do not use for product requirement document writing.
- Do not use for ordinary source-code comments.
- Do not use as a replacement for `change-forge-router`.
- Do not use as a replacement for a specific domain capability.
- Do not use to compress every skill into a vague summary.
- Do not delete necessary professional detail just to make a body shorter; move it into references first.

# Non-Negotiable Rules

1. **Skill boundary first.** Define the capability boundary before writing any content.
2. **Trigger precision.** When To Use must be specific; avoid catch-all triggers that match everything.
3. **Non-goal clarity.** Do Not Use When must actively prevent mis-triggering.
4. **Context budget discipline.** The body holds only high-frequency, decision-critical, executable content.
5. **Progressive disclosure.** Low-frequency content, long tables, examples, and deep checklists move to references.
6. **No tutorial drift.** A foundation capability is a decision aid, not a tutorial.
7. **No duplicated bodies.** Do not copy the same capability body into multiple professional skills; reference it through `used_by`.
8. **Registry consistency.** Any new or renamed skill must synchronize the registry, validators, and build/install impact.
9. **Runtime profile safety.** The recommended and full profiles must not promote a foundation capability into a top-level skill.
10. **Output contract must be testable.** Every skill must declare a verifiable output.
11. **Route impact must be stated.** Any content change must state which routing signals it affects.
12. **References must have a loading policy.** Any new reference must state when it is loaded.
13. **No dumping-ground references.** References must have an owner and a purpose; they are not a junk drawer.
14. **Preserve professional vocabulary.** Do not flatten professional rules into generic advice.
15. **No skill rule change without behavior evidence.** A skill or reference change must show the behavior it changes, not only the prose it edits. A new or edited skill includes a baseline failure scenario, or an explicit reason a baseline is impossible plus the expected-behavior case the change must pass.
16. **Discipline rules are pressure-tested.** A skill that enforces discipline must hold under a plausible excuse to skip it, not only on the cooperative path.
17. **Name the rationalizations.** A skill change names the rationalizations an agent may use to skip the rule, and the rule and its eval must reject each one.
18. **Trigger changes carry an over-routing guard.** A new or widened routing trigger ships with a guard case proving a trivial change does not pull it in.

# Industry Benchmarks

- Progressive disclosure.
- Task-oriented agent skills.
- Prompt and program separation.
- Technical-writing information architecture.
- Decision-record discipline.
- Risk-based quality gates.
- Reusable capability design.
- Semantic versioning for skill contracts.
- Context engineering and retrieval precision.

# Selection Rules

- Pair with `change-forge-router` when deciding how a new or changed skill should be routed and whether it over-routes or under-routes.
- Pair with `change-documentation-gate` when skill bodies, references, or registry documentation must stay consistent.
- Pair with `ai-code-review-refactor` when AI-generated or AI-modified skill content must be reviewed for professionalism, redundancy, and boundary drift.
- Pair with `quality-test-gate` when a skill change must be verified through eval, fixtures, build, and install.
- Pair with `implementation-structure-design` when new directories, files, references, or registry structure need a placement rationale.
- Pair with `agent-execution-discipline` when an agent must attach evidence, a same-pattern scan, and a validation handoff after editing skills.

# Risk Escalation Rules

- When a change touches the router, registry, or runtime profiles, escalate to `architecture-impact-reviewer`.
- When a change touches build, install, or doctor behavior, escalate to `delivery-release-gate`.
- When a change touches hooks, escalate to `reliability-observability-gate` and `quality-test-gate`.
- When a change touches a security, privacy, or secret-handling skill, escalate to `security-privacy-gate`.
- When deleting or merging a capability, require eval-routing and validate-installation to pass before handoff.
- When a SKILL body exceeds the context budget or the same content is duplicated across multiple skills, require a skill-slimming plan.
- When introducing a new top-level skill, require an explicit justification for why it cannot be a foundation capability or a reference.

# Critical Details

1. **Body versus references.** The `SKILL.md` body carries boundary, triggers, non-goals, decision rules, and output contract; `references` carries deep checklists, examples, anti-examples, benchmarks, and long tables.
2. **Layer responsibilities.** A professional skill is a runtime entry point; a foundation capability is a compact decision aid compiled into professional `references`; a domain extension adds domain-specific product rules.
3. **Registry alignment.** Registry entries, routing rules, `used_by`, and expected counts must stay mutually consistent; `used_by` drives which professional skills compile a capability.
4. **Reference loading policy.** Source/dev-only authoring note: new professional-skill references must align with the L1–L5 Reference Loading Policy and state when each reference loads, anchored on the compiled professional-skill `references/capabilities/index.md` and per-capability files.
5. **Move, do not delete.** Large anti-examples, benchmarks, and deep checklists move into references rather than being deleted from the system.
6. **Content is decisions, not keywords.** A skill must carry decision rules, failure modes, and an output contract, not just trigger keywords.
7. **Naming consistency.** A new skill name is kebab-case, and the directory name, frontmatter name, and registry name must match exactly.
8. **Compact capability.** A new capability stays compact and must not become an introductory tutorial.
9. **Adjacency and handoff.** Every capability states its adjacent capabilities and its handoff targets.
10. **Slimming preserves rigor.** No slimming action may reduce professional rigor; detail moves to references instead.
11. **Description is a trigger, not a workflow.** The frontmatter description states when to use the skill and its scope; the workflow, gates, and output contract live in the body, and deep detail in references. A description that summarizes the workflow lets an agent act from the description without reading the body, and an over-broad description causes catch-all routing.

# Failure Modes

- A skill becomes a catch-all that triggers on everything.
- A skill drifts into tutorial form, explaining background but giving no execution rules.
- A skill body grows too long and wastes context.
- A reference becomes a dumping ground with no loading policy.
- Multiple professional skills copy the same capability body instead of referencing it.
- `used_by` is not synchronized, so a capability is not compiled into the relevant professional skill.
- The registry is not synchronized, so build or validation fails.
- A routing trigger is too broad, causing over-routing.
- Do Not Use When is too weak, causing mis-triggering.
- Detail is deleted instead of moved to references, lowering professional rigor.
- A new capability overlaps the boundary of an existing capability.

# Output Contract

Return a Skill Authoring Review:

- Target skill/capability:
- Change type:
- Skill layer:
- Boundary:
- Trigger signals:
- Non-goals:
- Main body decision:
- Reference split decision:
- Registry impact:
- Routing impact:
- Runtime profile impact:
- Validation impact:
- Context budget risk:
- Adjacent capabilities:
- Required tests:
- Baseline failure scenario:
- Pressure scenario:
- Expected failure without change:
- Expected behavior after change:
- Rationalizations blocked:
- Eval/fixture impact:
- Before/after behavior evidence:
- Reference loading impact:
- Handoff:

Also return a Skill Behavior Test Decision:

- Test type: routing / pressure / reference retrieval / output contract / hook fixture / agent behavior sample
- Required files:
- Expected pass/fail criteria:
- Validation command:

When slimming or restructuring, also return a Skill Slimming Decision:

- Keep in SKILL.md:
- Move to references:
- Split capability:
- Merge duplicate:
- Defer:
- Rationale:

# Quality Gate

1. Name, directory, and registry entry are consistent.
2. Frontmatter is complete.
3. All required sections are present.
4. `used_by` is reasonable and references real skills.
5. Triggers are precise rather than catch-all.
6. Risk notes are specific.
7. Expected outputs are verifiable.
8. The body shows no obvious tutorial drift.
9. The body holds no large, low-frequency content that belongs in references.
10. New references declare a loading policy.
11. validate-skills, validate-capabilities, validate-registry, and validate-installation pass.
12. A skill rule change carries a baseline failure scenario, or an explicit reason a baseline is impossible plus an expected-behavior case.
13. A discipline-rule change names the rationalizations it blocks and has a pressure case that applies them.
14. A new or widened routing trigger has an over-routing guard case.

# Reference Loading Policy

The body carries the decision-critical authoring rules and is the part compiled into the professional-skill references that use this capability. Deep authoring material loads only when authoring or auditing a skill change:

- [references/tdd-for-skills.md](references/tdd-for-skills.md) — the behavior-first loop, baseline failure template, and test-type selection.
- [references/pressure-scenarios.md](references/pressure-scenarios.md) — the pressure scenario catalog, rationalizations to reject, and pressure case fields.

# Used By

- change-forge-router
- change-documentation-gate
- ai-code-review-refactor
- quality-test-gate

# Handoff

- Routing-boundary and over/under-routing questions: hand to `change-forge-router`.
- Documentation and reference consistency questions: hand to `change-documentation-gate`.
- AI-generated skill quality, redundancy, and boundary questions: hand to `ai-code-review-refactor`.
- Validation, eval, fixture, build, and install strategy questions: hand to `quality-test-gate`.
- File, directory, reference, and registry placement questions: hand to `implementation-structure-design`.
- Execution evidence, same-pattern scan, and validation handoff: hand to `agent-execution-discipline`.

# Completion Criteria

This capability is complete when it lets an agent add, modify, review, slim, or split a ChangeForge skill while producing a clear boundary, precise triggers, an explicit context budget, a reference split, registry impact, routing impact, and validation impact, and while preventing tutorial drift, catch-all triggers, duplicated bodies, and body bloat.
