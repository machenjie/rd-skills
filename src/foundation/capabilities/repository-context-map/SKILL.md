---
name: repository-context-map
description: Maps repository structure, ownership, conventions, callers, tests, configs, docs, and evidence limits before planning non-trivial code, skill, registry, hook, or documentation changes.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "118"
changeforge_version: 0.1.0
---

# Repository Context Map

## Mission
Create a small, evidence-backed map of the repository area affected by a proposed change before planning or editing. The map identifies ownership, local conventions, callers and callees, tests, configuration, documentation, generated artifacts, and unknowns so the implementation plan is based on inspected project context rather than prompt-only assumptions.

## Repository Intelligence Tooling
When repository-intelligence tooling is available, prefer a freshly generated RepositoryGraph and TaskContextPack as the first evidence layer for this capability. The generated graph supplies deterministic file roles, Python symbol/import edges, Markdown/SKILL heading and reference edges, YAML/JSON registry references, skill-capability-registry relationships, hook-template/build-output relationships, test links, and freshness metadata.

The generated graph does not replace professional judgment. Agents must still inspect the selected source files, confirm source-of-truth ownership, and label anything the graph cannot prove as `INFERENCE`, `ASSUMPTION`, or `OPEN QUESTION`. If the graph is stale, missing a changed path, or built from a different commit/hash than the current working tree, re-index before using it as evidence.

## When To Use
- Before planning a non-trivial engineering change in an unfamiliar or partially inspected repository area.
- When adding, moving, deleting, or renaming files, capabilities, registry entries, hooks, tests, or docs.
- When ownership, caller impact, stage model impact, generated output, or validation scope is not obvious.
- When a local fix claims a narrow blast radius but sibling patterns or call sites may exist.
- When source and generated runtime content boundaries must stay separate.

## Do Not Use When
- The task is a pure question, translation, or explanation with no repository action.
- The change is a trivial typo in a single already-open file with no behavioral or registry effect.
- A fresh repository map with the same files and validation inputs already exists for the current turn and no relevant file changed after it.

## Non-Negotiable Rules
- Do not plan implementation before inspecting the relevant repository files, tests, configs, docs, registry entries, and local naming or placement conventions.
- Map the owning module or artifact first; do not create a new structure until reuse and existing placement have been checked.
- Include callers, callees, generated artifacts, validators, and docs when the changed surface can affect them.
- Mark unknown ownership or uninspected boundaries as unknown with a next investigation owner; do not treat unknown as safe.
- Separate source authoring content from generated runtime content and installed artifacts.
- Use fast repository searches and direct file reads as evidence; do not assume an external knowledge source exists.
- Keep the map bounded to the affected area and its nearest dependent surfaces.

## Industry Benchmarks
- **Monorepo impact analysis**: Map direct and transitive dependents before changing shared packages, generated files, or affected-test rules.
- **Architecture Decision Records**: Document context before decision so placement and boundary choices can be reviewed.
- **Docs-as-code**: Validate repository documentation beside the source behavior it describes.
- **SRE change review**: Identify operational artifacts, configs, release gates, and rollback signals before production-bound work.
- **Secure development lifecycle**: Identify trust boundaries and ownership before modifying permission, secret, or data paths.

## Selection Rules
- Select this capability for L2 or higher engineering work when the affected repository area is not already mapped in the current turn.
- Select it when a plan names files to edit but does not list files inspected.
- Select it when a skill, capability, registry, stage model, hook runtime, generated dist output, benchmark, or validator is touched.
- Select it with `implementation-structure-design` when file placement or reuse is part of the decision.
- Select it with `change-impact-analyzer` when caller, consumer, or generated artifact impact is uncertain.

## Risk Escalation Rules
- Escalate to `architecture-impact-reviewer` when the map reveals new or changed module boundaries, public exports, generated artifacts, or dependency direction.
- Escalate to `quality-test-gate` when changed-code-to-test mapping is unclear or affected-test selection may miss dependents.
- Escalate to `security-privacy-gate` when the mapped area touches auth, secrets, permissions, user data, external input, or tool execution.
- Escalate to `delivery-release-gate` when the map includes deployment, install, build, migration, hook runtime, or release packaging surfaces.
- Block planning when the owning source of truth cannot be found and the proposed change could affect runtime behavior.

## Critical Details
- A repository map is not a broad inventory. It is the smallest evidence set that makes the plan reviewable.
- The same directory and parent-module convention are evidence for naming and placement decisions.
- Generated outputs are impact surfaces but not necessarily source-of-truth locations.
- Tests and docs are part of the map because stale evidence and stale reader guidance cause false completion.
- Repository context must be refreshed after meaningful edits if the plan, tests, or validation depend on changed files.

## Failure Modes
- **Prompt-only plan**: The agent plans a new file without reading sibling files and duplicates an existing capability.
- **Wrong source of truth**: The agent edits generated runtime content instead of source registry or capability files.
- **Hidden caller breakage**: A public output contract changes but dependents and tests were not mapped.
- **Stale validation**: Tests are chosen before generated outputs or registry references are updated, so the validation no longer proves the final patch.
- **Boundary leak**: A local helper or fixture is placed in shared code because owner conventions were not inspected.
- **Graph dump bloat**: The agent treats a repository graph as a full-repo prompt dump instead of selecting the smallest task-relevant context.

## Output Contract
Return a `repository_context_map` with:
- **Change basis**: request, intended behavior, non-goals, and risk level.
- **Generated evidence**: repository graph path/hash, context-pack path/hash when available, indexed commit or fallback mtime, and whether the graph was refreshed for the current task.
- **Source of truth**: files or registries that own the behavior, plus generated or installed artifacts explicitly excluded from source edits.
- **Files inspected**: exact paths read before planning, including sibling files, parent module files, tests, docs, configs, validators, and build scripts.
- **Searches run**: patterns searched, paths or globs searched, and what was found or not found.
- **Ownership map**: owning module, skill, capability, gate, or artifact owner; unknown owners marked explicitly.
- **Caller/callee and dependent map**: imports, references, registry links, generated references, tests, docs, and consumers affected or ruled out.
- **Local conventions**: naming, placement, structure, frontmatter, schema, test, and documentation conventions observed.
- **Plan inputs**: reuse candidates, placement constraints, affected validation commands, and docs to update.
- **Fact classification**: mark each generated or inspected claim as `FACT`, `INFERENCE`, `ASSUMPTION`, or `OPEN QUESTION`.
- **Evidence limits**: what was not inspected and what risk remains.
- **Next gate**: owner skill and independent review skill for the planned action.

## Quality Gate
1. The map names inspected files and searches, not only inferred areas.
2. Source of truth is distinguished from generated, installed, or runtime content.
3. Owning module or artifact is identified, or unknown ownership is escalated.
4. Caller, callee, tests, docs, configs, and validators are included when relevant.
5. Placement and reuse decisions cite local convention evidence.
6. Evidence freshness is stated when validation depends on files that may change later.
7. Unknowns and skipped surfaces include rationale and next owner.
8. Generated repository graph/context-pack evidence is bounded to task-relevant files and is not used as a full-repository dump.
9. Stale or mismatched graph freshness markers trigger re-indexing before implementation planning.

## Used By
- `change-forge-router`
- `backend-change-builder`
- `frontend-change-builder`
- `data-api-contract-changer`
- `data-middleware-change-builder`
- `integration-change-builder`
- `delivery-release-gate`
- `change-impact-analyzer`
- `architecture-impact-reviewer`
- `task-dag-planner`
- `ai-code-review-refactor`
- `quality-test-gate`
- `change-documentation-gate`
- `skill-authoring-expert`
- `agent-execution-discipline`

## Handoff
Hand off the map to the implementation owner before planning or editing. If mapping finds boundary, security, test, release, or documentation risk, hand off to the matching gate before implementation continues.

## Completion Criteria
The capability is complete when a reviewer can see exactly which repository evidence shaped the plan, which source artifacts own the change, which dependent surfaces were checked or skipped, and which validation commands are expected to prove the final patch.
