---
name: skill-authoring-expert
description: Use when authoring, auditing, slimming, splitting, or maintaining ChangeForge SKILL.md bodies, references, capabilities, domain extensions, registries, or routing rules; governs trigger precision, context budget, reference loading, registry impact, and validation evidence.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "103"
changeforge_version: 0.1.0
---

# Mission

Keep ChangeForge skills professional, precise, efficient, and verifiable. A `SKILL.md` body owns boundary, trigger, selection, execution, output, and evidence rules; references own deep examples, anti-examples, pressure cases, benchmarks, and long tables. Skill authoring must couple source-of-truth files, registry graph, project memory, routing behavior, generated dist artifacts, validation broker output, and execution discipline without turning the repository into a user corpus or tutorial collection.

# When To Use

Use when adding, modifying, reviewing, slimming, splitting, merging, or maintaining:

- `SKILL.md` bodies, foundation capabilities, professional skills, domain extensions, or references.
- `skills.yaml`, `capabilities.yaml`, `domain-extensions.yaml`, routing rules, stage model, hook/runtime support artifacts, evals, or benchmark fixtures.
- Skill content audits, professionalism regressions, routing coverage, reference loading policy, output contracts, pressure behavior, or context budget decisions.
- Source-vs-dist, recommended/full/dev profile, build/install, generated report, or registry synchronization behavior.

# Do Not Use When

- The task is ordinary README writing, product requirements, source-code comments, or general documentation with no skill-system behavior.
- A specialist capability already owns the substantive domain and no skill body, reference, registry, routing, eval, hook, or generated artifact changes.
- The proposed action is to compress every skill into vague summaries, remove professional detail instead of moving it to references, or promote source authoring content directly into runtime install locations.

# Stage Fit

- **skill-authoring stage:** body/reference/registry/routing/eval/hook edits during coding, refactoring, testing, release, or documentation handoff; inspect source-of-truth files before plan.
- **read / plan:** repository context, registry graph, project memory, source-vs-dist boundary, reuse candidates, validation signal.
- **edit / review:** body-vs-reference placement, trigger precision, Mode Matrix, proactive triggers, Evidence Contract, output contract, and reviewer split.
- **test / build:** professionalism evals, routing/agent/pressure benchmarks, content audit, build profiles, runtime reference and installation validation.
- **handoff:** route manifest, changed source files, generated artifacts, validation freshness, evidence limits, residual risk, next gate.

# Mode Matrix

| Stage mode | Trigger signals | Professional focus | Required evidence | Companion capabilities / gates | Skip guidance |
| --- | --- | --- | --- | --- | --- |
| Body authoring | `SKILL.md` boundary, trigger, non-goal, output, or evidence rule changes | Keep decision-critical rules in body and deep material in references | Target body, source-of-truth paths, body-vs-reference decision, line/context budget | `skill-authoring-expert`, `code-clarity-maintainability` | Skip new references when existing references already own the detail |
| Reference split | Long examples, benchmark catalogs, pressure cases, anti-examples, or tables exceed body budget | Preserve rigor while moving low-frequency detail to targeted references | Moved content, loading hint, link validation, dev build output | `implementation-structure-design`, `repository-context-map` | Do not delete detail solely to reduce line count |
| Registry/routing | Capability used_by, route trigger, stage model, registry, or generated catalog changes | Preserve source graph, route precision, and over-routing guard | Registry diff, routing case, guard case, stage consistency, build/install result | `change-forge-router`, `skill-efficacy-benchmark` | Skip registry edits for prose-only body tightening |
| Discipline rule | Evidence, validation, pressure behavior, no-completion, or execution rule changes | Prove behavior under realistic rationalizations, not only cooperative path | Baseline or expected-behavior case, pressure scenario, forbidden behavior, validation output | `agent-execution-discipline`, `quality-test-gate` | Do not accept keyword-only score gains |
| Generated artifacts | Reports, marketplace catalog, dist, zips, or hook runtime output change after source edit | Regenerate from source and prove freshness | Generator command, exit code, generated paths, what evidence proves and does not prove | `validation-broker`, `plan-execution-consistency` | Never hand-edit `dist/` or install `src/` |

# Non-Negotiable Rules

1. **Boundary first:** define skill layer, owner, non-goals, selected users, and adjacent handoff before changing content.
2. **Trigger precision:** frontmatter description and When To Use state scope and trigger signals; body owns workflow, gates, and output contract.
3. **Context budget discipline:** keep high-frequency executable decisions in body; move low-frequency lists, examples, benchmarks, and pressure catalogs to references with loading hints.
4. **No tutorial drift:** foundation capabilities are compact decision aids; professional skills are runtime entry points; references are targeted support, not dumping grounds.
5. **Registry and source graph consistency:** name, directory, frontmatter, registry entry, `used_by`, routing rules, stage model, build counts, and generated catalogs stay aligned.
6. **Runtime profile safety:** recommended/full compile foundation capabilities into professional references; dev may expose top-level capabilities; no source authoring directory is installed directly.
7. **Behavior evidence over prose:** skill rule changes name baseline failure or expected behavior, pressure rationalization, over-routing guard when triggers widen, and validation command.
8. **No score gaming:** adding headings, copied Evidence Contracts, generic keywords, or checklist-only triggers is rejected unless behavior evidence and routing precision improve.
9. **Memory / graph / execution coupling:** compare project memory, repository graph, selected skills, validation broker output, generated artifacts, and final diff before handoff.
10. **No personal corpus behavior:** do not add user archive ingestion, scanning, mapping, packaging, private runtime content, or source install behavior.

# Industry Benchmarks

Use progressive disclosure, task-oriented skill design, prompt/program separation, information architecture, decision records, risk-based quality gates, semantic versioning, context engineering, retrieval precision, and evidence-based AI code review as authoring benchmarks.

# Selection Rules

Select this capability when:

- A skill body, reference, capability, domain extension, registry entry, routing rule, stage model, eval, benchmark, hook runtime artifact, generated report, build/install profile, or professionalism baseline is changed or audited.
- Trigger behavior, context budget, reference loading, route precision, output contract, evidence contract, pressure behavior, or skill efficacy is the review surface.
- A proposed skill change risks over-routing, under-routing, duplicated bodies, tutorial drift, stale references, registry mismatch, generated artifact drift, or unverified agent behavior.

Pair with `change-forge-router` for routing impact, `quality-test-gate` for eval/build/install evidence, `ai-code-review-refactor` for AI-generated content quality, `implementation-structure-design` for new files or placement, `repository-context-map` / `repository-graph-analysis` for source graph, `project-memory-governance` for prior-run signals, and `agent-execution-discipline` for closure.

# Proactive Professional Triggers

- **Signal:** A skill body edit widens When To Use or frontmatter description without an over-routing guard.
  **Hidden risk:** catch-all routing pulls trivial README, comment, or product docs work into ChangeForge skill authoring.
  **Required professional action:** require a routing case and an L1 guard case before accepting the trigger change.
  **Route to:** `change-forge-router`, `skill-efficacy-benchmark`, `quality-test-gate`.
  **Evidence required:** routing fixture output, forbidden over-route behavior, selected capabilities, and residual risk.
- **Signal:** A SKILL.md body grows past context budget because examples, benchmark catalogs, anti-examples, or pressure cases stay inline.
  **Hidden risk:** context bloat hides decision rules and slows every downstream professional skill.
  **Required professional action:** split low-frequency material into targeted references with loading policy and link validation.
  **Route to:** `implementation-structure-design`, `code-clarity-maintainability`.
  **Evidence required:** body line count, moved-content map, reference links, validation output, and what evidence does not prove.
- **Signal:** A rule is strengthened with no baseline failure, pressure rationalization, or expected behavior case.
  **Hidden risk:** prose-only discipline looks professional but does not change agent behavior under pressure.
  **Required professional action:** define behavior-first test decision or explicit not-applicable rationale before handoff.
  **Route to:** `skill-efficacy-benchmark`, `agent-execution-discipline`.
  **Evidence required:** baseline/expected behavior case, rationalizations rejected, pressure scenario, and validator command.
- **Signal:** Registry, used_by, stage model, or routing-rule changes are proposed without generated artifact and install validation.
  **Hidden risk:** recommended/full/dev profiles compile the wrong capability set or ship stale runtime references.
  **Required professional action:** inspect registry graph, rebuild profiles, validate runtime links, and reconcile generated reports.
  **Route to:** `repository-graph-analysis`, `validation-broker`, `plan-execution-consistency`.
  **Evidence required:** registry diff, build output, dist/reference link validation, installation validation, and next gate.
- **Signal:** Final handoff claims a skill change is complete after only reading the prose diff or a partial validator.
  **Hidden risk:** stale report, unbuilt dist, missing pressure behavior, or source-vs-dist drift remains hidden.
  **Required professional action:** block completion language until fresh validation covers changed source and generated artifacts.
  **Route to:** `agent-execution-discipline`, `quality-test-gate`, `validation-broker`.
  **Evidence required:** command, working directory, exit code, reports, generated paths, what evidence proves and does not prove.

# Risk Escalation Rules

- Escalate router, registry, stage model, runtime profile, or source-vs-dist changes to `architecture-impact-reviewer` and `quality-test-gate`.
- Escalate build, install, doctor, zip, or release checklist behavior to `delivery-release-gate`.
- Escalate hook/runtime support changes to `reliability-observability-gate`, `agent-tool-permission-sandbox`, and `quality-test-gate`.
- Escalate security/privacy/secret-handling skills or secret-bearing validation output to `security-privacy-gate`.
- Escalate deleted, merged, renamed, or newly top-level skills to full routing, professionalism regression, build, and install validation.

# Critical Details

- **Body versus references:** body = boundary, triggers, selection, skip guidance, output, evidence, quality gate; references = deep TDD, pressure cases, anti-examples, benchmarks, and long tables.
- **Layer responsibility:** professional skills are runtime entry points; foundation capabilities are compact compiled decision aids; domain extensions add domain-specific product rules.
- **Generated artifact boundary:** reports, catalogs, marketplace docs, dist skills, zips, and hook runtime files are generated from source; edit source and run generators.
- **Skill efficacy plan:** behavior case, expected treatment, overhead signal, over/under-routing guard, regression fixture, and validator command.
- **Forbidden edits:** personal archive ingestion, source install, runtime registry-source content, user corpus mapping, copied body duplication, and references with no loading purpose.

# Evidence Contract

Close only when these answers are concrete:

- **Basis:** authoring mode, artifact type, requirement, repository convention, registry rule, or professionalism benchmark driving the change.
- **Boundaries inspected:** target source, references, registry entries, stage/routing rules, generated artifacts, reports, validators, source-vs-dist boundary, and not-inspected areas.
- **Reuse / placement rationale:** existing skill/reference/registry pattern reused, body-vs-reference decision, owner boundary, rejected locations, and dependency direction for generated artifacts.
- **Behavior preservation:** existing trigger scope, runtime profile behavior, registry identity, reference loading, build/install contract, and old expected behavior preserved or intentionally changed.
- **Validation evidence:** literal commands, working directory, exit codes, updated reports, build outputs, runtime link/install checks, and validation broker freshness after latest edit.
- **What evidence proves:** route precision, content size, link integrity, generated artifact freshness, build profile compilation, installation shape, or professionalism score movement.
- **What evidence does not prove:** real-world adoption, every possible prompt, external runtime installation, untested pressure cases, or future routing changes.
- **Residual risk:** skipped fixture, unrun extended comparison, accepted partial evidence, untracked adjacent file, release-readiness warning, or owner decision.
- **Next gate:** reviewer skill, validator, build/install command, routing fixture, pressure behavior case, or human decision required before broader closure.

# Output Contract

Return a Skill Authoring Review with:

- **Mode selected:** body authoring, reference split, registry/routing, discipline rule, generated artifact sync, or not-applicable with reason.
- **Decision:** approved, blocked, partial, not verified, split required, registry update required, or handoff required.
- **Target and layer:** skill/capability/domain/reference/registry/eval/hook artifact, owner, boundary, adjacent capabilities, and non-goals.
- **Boundaries inspected:** source paths, references, registry, stage/routing rules, docs, generated artifacts, reports, memory/graph signals, and skipped areas.
- **Body/reference decision:** keep, move, split, merge, defer, and context budget rationale.
- **Routing impact:** trigger signals, over/under-routing risk, guard cases, `used_by`, runtime profile impact, and generated catalog impact.
- **Behavior test decision:** baseline failure or expected-behavior case, pressure scenario, rationalizations blocked, fixture/eval impact, and validation command.
- **Generated artifact decision:** reports, docs, dist, zips, hooks, and install outputs to regenerate or explicitly leave unchanged.
- **Validation evidence:** commands, exit codes, reports, build/install outputs, what evidence proves, what evidence does not prove, freshness, and residual risk.
- **Handoff:** next gate, owner, exact command or question, route manifest, and generated artifact boundary.

When slimming or restructuring, also include keep-in-body, move-to-references, split, merge, defer, and rationale decisions.

# Reference Loading Policy

The body carries decision-critical authoring rules compiled into professional-skill references. Load deep material only when authoring or auditing a skill change:

- [references/tdd-for-skills.md](references/tdd-for-skills.md) - behavior-first loop, baseline failure template, and test-type selection.
- [references/pressure-scenarios.md](references/pressure-scenarios.md) - pressure scenario catalog, rationalizations to reject, and pressure case fields.

# Failure Modes

- **Catch-all trigger:** skill fires for ordinary docs or comments.
- **Tutorial drift:** body gives background but no execution rule.
- **Body bloat:** decision rules are hidden beside material that belongs in references.
- **Reference dumping:** reference has no loading policy, owner, or purpose.
- **Copied body:** professional skills copy capability bodies instead of compiling references through `used_by`.
- **Stale graph:** registry, stage model, routing rules, build counts, generated reports, or dist output drift from source.
- **Over-routing trigger:** routing widens with no guard case.
- **Copied evidence:** Evidence Contract is generic and does not name behavior proof or limits.
- **Deleted rigor:** detail is deleted instead of moved.
- **Silent handoff:** completion is claimed without fresh validation, generated artifact check, residual risk, and next gate.

# Quality Gate

1. Name, directory, frontmatter, registry entry, `used_by`, and layer remain consistent.
2. Boundary, triggers, non-goals, Mode Matrix, proactive triggers, Evidence Contract, Output Contract, Failure Modes, Quality Gate, Reference Loading Policy, Handoff, and Completion Criteria are present when required.
3. Body stays decision-critical and within context budget; low-frequency detail has targeted reference links and loading hints.
4. Trigger changes include route evidence and over-routing guard; discipline rules include baseline/expected behavior and pressure rationalization.
5. Registry, stage, routing, profile, generated artifact, and documentation impacts are stated or explicitly not applicable.
6. Validation commands are fresh after the final edit and state what they prove and do not prove.
7. No source install, private corpus mapping, user archive ingestion, or direct `dist/` hand edit is introduced.
8. Final handoff includes route manifest, changed boundary, validation results, residual risk, rollback note, and next gate.

# Used By

- change-forge-router
- change-documentation-gate
- ai-code-review-refactor
- quality-test-gate

# Handoff

- `change-forge-router` - routing boundary, over-routing, under-routing, or stage route question.
- `change-documentation-gate` - docs, checklist, catalog, or reference consistency question.
- `ai-code-review-refactor` - AI-generated skill quality, redundancy, or boundary drift question.
- `quality-test-gate` - eval, fixture, build, install, and validation strategy question.
- `implementation-structure-design` - file, directory, reference, registry, or generated artifact placement question.
- `agent-execution-discipline` - evidence inventory, same-pattern scan, route repair, and closure handoff.

# Completion Criteria

This capability is complete when it lets an agent author, audit, slim, split, or maintain ChangeForge skill artifacts while preserving boundary, trigger precision, context efficiency, body/reference placement, registry graph, route behavior, runtime profile safety, generated artifact freshness, validation evidence, residual risk, and handoff clarity.
