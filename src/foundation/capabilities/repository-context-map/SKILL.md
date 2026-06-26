---
name: repository-context-map
description: Maps repository structure, ownership, conventions, callers, tests, configs, docs, and evidence limits before planning non-trivial code, skill, registry, hook, or documentation changes.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "118"
changeforge_version: 0.1.0
---

# Mission
Create a small, evidence-backed map of the repository area affected by a proposed change before planning or editing. The map identifies ownership, local conventions, callers and callees, tests, configuration, documentation, generated artifacts, and unknowns so the implementation plan is based on inspected project context rather than prompt-only assumptions.

# Stage Fit
Use before planning when the target area, ownership, source of truth, placement, reuse path, caller/callee impact, validation scope, or generated/runtime boundary is not already fresh and explicit. Use during implementation when edits add, move, delete, rename, or expose files. Use during review and repair when a fix claims narrow scope, reuses old context, or needs same-pattern scanning. Use before closure when validation freshness, report regeneration, build/install output, or handoff claims depend on which files were inspected after the final material edit.

# Repository Intelligence Tooling
When repository-intelligence tooling is available, prefer a fresh RepositoryGraph and TaskContextPack as the first evidence layer, then confirm selected source files directly. Graph facts are selectors, not behavior proof; stale, missing, or hash-mismatched graph evidence requires refresh or direct-source fallback. Load [references/context-pack-evidence-map.md](references/context-pack-evidence-map.md) for the full graph/context-pack field matrix.

# When To Use
- Before planning a non-trivial engineering change in an unfamiliar or partially inspected repository area.
- When adding, moving, deleting, or renaming files, capabilities, registry entries, hooks, tests, docs, or generated/runtime artifacts.
- When ownership, caller impact, stage model impact, generated output, validation scope, or source/generated boundary is not obvious.

# Do Not Use When
- The task is a pure question, translation, or explanation with no repository action.
- The change is a trivial typo in an already-open file, or a fresh equivalent map exists and no relevant file changed after it.

# Non-Negotiable Rules
- Before planning, inspect relevant files, tests, configs, docs, registry entries, owner module/artifact, reuse candidates, and placement conventions.
- Include callers, callees, generated artifacts, validators, docs, and release/install surfaces when the changed surface can affect them.
- Mark unknown ownership or uninspected boundaries as unknown with a next investigation owner; unknown is not safe.
- Separate source authoring content from generated runtime content and installed artifacts.
- Use fast repository searches and direct file reads as bounded evidence; do not assume an external knowledge source exists.
- Classify generated graph, memory, context-pack, report, and direct-source claims as `FACT`, `INFERENCE`, `ASSUMPTION`, or `OPEN QUESTION`.
- Do not treat the context map as completion evidence; final validation must still run after the final material diff.

# Industry Benchmarks
Monorepo impact analysis, ADR context-before-decision, docs-as-code, SRE change review, and secure development lifecycle boundary mapping.

# Mode Matrix
| Mode | Trigger signal | Professional focus | Required evidence | Companion route | Skip guidance |
| --- | --- | --- | --- | --- | --- |
| Planning map | Plan would name files before repository read. | Build source, owner, convention, and validation inputs before design. | Read paths, searches, source of truth, rejected locations. | `implementation-structure-design` | Skip only for already-open trivial edits. |
| Source/generated boundary | Dist, report, install, registry output, or runtime artifact appears editable. | Separate editable source from generated impact surface. | Source file, generated file, build command, freshness, rollback clue. | `repository-graph-analysis`, `delivery-release-gate` | Skip when no generated/install surface is touched. |
| Validation freshness map | Tests, reports, or builds may predate later edits. | Tie validators to final material diff. | Changed paths, command scope, covered paths, stale/current status. | `validation-broker`, `execution-trajectory-analysis` | Skip only for read-only advice with no completion claim. |
| Repair/review map | Local fix, fragile file, or post-review repair claims narrow scope. | Expand only to nearest dependents and same-pattern surfaces. | Same-pattern search, caller/callee evidence, reviewer gate. | `agent-execution-discipline`, `project-memory-governance` | Skip when no repository mutation or repair occurred. |

# Selection Rules
- Select this capability for L2+ engineering work or 2+ affected surfaces when the repository area is not already mapped, especially for skill, registry, stage model, hook runtime, dist, benchmark, or validator changes.
- Select `repository-graph-analysis` with this capability when repo graph, context pack, import/reference/test graph, source-of-truth, generated artifact, or graph freshness signals are present.
- Select it with `implementation-structure-design` for placement/reuse decisions and `change-impact-analyzer` when callers, consumers, or generated artifacts are uncertain.

# Proactive Professional Triggers
- **Signal:** A plan names files to edit but does not name files read, searches run, siblings checked, tests mapped, or owners identified. **Hidden risk:** prompt-only planning duplicates structure or edits the wrong surface. **Required professional action:** build a bounded context map before planning. **Route to:** `implementation-structure-design`, `validation-broker`, this capability. **Evidence required:** inspected paths, search patterns, source-of-truth decision, reuse candidates, rejected locations.
- **Signal:** A generated file, `dist/` artifact, report, install target, hook runtime output, registry output, or package output is proposed as the edit target. **Hidden risk:** generated-only changes are overwritten or installed without source truth. **Required professional action:** identify editable source, generator, profile, build command, and validation path. **Route to:** `repository-graph-analysis`, `delivery-release-gate`, this capability. **Evidence required:** source/generated pair, generator command, freshness, do-not-edit exclusion.
- **Signal:** A repository graph, context pack, project memory, ADR, compaction summary, or previous validation is reused after later edits. **Hidden risk:** stale context drives placement, validation, or closure. **Required professional action:** refresh, downgrade to selector-only, or confirm by direct source reread and execution-order review. **Route to:** `repository-graph-analysis`, `project-memory-governance`, `execution-trajectory-analysis`. **Evidence required:** freshness comparison, accepted/rejected claims, later edits, direct-source fallback.
- **Signal:** A local fix touches shared/common code, registry, hooks, stage model, test infrastructure, skill references, public exports, or docs. **Hidden risk:** hidden blast radius beyond the apparent file. **Required professional action:** map callers/callees, dependents, validators, same-pattern locations, and release/install surfaces. **Route to:** `change-impact-analyzer`, `module-boundary-design`, `quality-test-gate`, this capability. **Evidence required:** changed path map, dependency/reference search, affected validators, skipped-surface rationale.
- **Signal:** No validation command is mapped before edit or closure. **Hidden risk:** the final answer claims completion without evidence tied to the changed paths. **Required professional action:** create a changed-surface-to-validation map and rerun stale commands after final edits. **Route to:** `quality-test-gate`, `validation-broker`, `execution-trajectory-analysis`. **Evidence required:** command list, covered paths, freshness verdict, residual risk.

# Reference Loading Policy
- **L1 quick map:** Use this `SKILL.md` for ordinary read-before-plan, source-of-truth, placement, validation, and handoff requirements.
- **L2 graph/context-pack map:** Load [references/context-pack-evidence-map.md](references/context-pack-evidence-map.md) when graph/context-pack evidence, source-vs-generated boundaries, affected validation, or placement/reuse fields need exact structure.
- **L2 source/generated map:** Load [references/source-generated-boundary-map.md](references/source-generated-boundary-map.md) when editable source, generated artifacts, installed runtime content, reports, or build commands must be separated.
- **L2 validation/handoff map:** Load [references/validation-freshness-handoff.md](references/validation-freshness-handoff.md) when command freshness, changed-path coverage, reviewer scope, rollback note, or handoff evidence needs exact fields.
- **L3 coupling:** Pair with `repository-graph-analysis`, `project-memory-governance`, or `execution-trajectory-analysis` when graph freshness, memory freshness, or validation order affects confidence.
- **Anti-bloat rule:** Do not load or package whole-repository dumps; include only task-relevant files, edges, searches, omissions, and validation candidates.

# Risk Escalation Rules
- Escalate to `architecture-impact-reviewer` when the map reveals new or changed module boundaries, public exports, generated artifacts, or dependency direction.
- Escalate to `quality-test-gate` when changed-code-to-test mapping is unclear or affected-test selection may miss dependents.
- Escalate to `security-privacy-gate` when the mapped area touches auth, secrets, permissions, user data, external input, or tool execution.
- Escalate to `delivery-release-gate` when deployment, install, build, migration, hook runtime, or release packaging surfaces are involved; block planning if runtime source of truth cannot be found.

# Critical Details
- A repository map is not a broad inventory. It is the smallest evidence set that makes the plan reviewable.
- Directory and parent-module conventions are placement evidence; generated outputs are impact surfaces, not automatically source of truth.
- Tests, docs, and context freshness are part of the map because stale evidence and stale reader guidance cause false completion.
- Stale graph, missing graph edge, or graph/source mismatch requires graph refresh or explicit direct-source fallback.

# Failure Modes
- **Prompt-only plan**: The agent plans a new file without reading sibling files and duplicates an existing capability.
- **Wrong source of truth**: The agent edits generated runtime content instead of source registry or capability files.
- **Hidden or stale breakage**: dependents/tests are not mapped, validation predates generated/registry changes, or graph context becomes a full-repo dump.
- **Boundary leak**: A local helper or fixture is placed in shared code because owner conventions were not inspected.
- **Unclassified claim**: a graph, memory, summary, or search result is reported as fact without `FACT`, `INFERENCE`, `ASSUMPTION`, or `OPEN QUESTION` status.
- **Memory substitution**: project memory or a previous turn summary replaces current source, registry, test, report, or generated-artifact inspection.
- **Validation overclaim**: a narrow command, stale report, or build from before final edits is described as full proof.
- **Omitted high-volume area**: a broad caller/test/docs surface is skipped without naming the omission, owner, and residual risk.

# Output Contract
Return a `repository_context_map` with:
- **Mode selected:** planning, implementation, review, repair, validation freshness, source/generated boundary, or release/install map.
- **Change basis**: request, intended behavior, non-goals, and risk level.
- **Affected surface:** source files, generated artifacts, registry/config/docs/tests/build/install/runtime surfaces, and explicitly excluded areas.
- **Generated/context evidence:** graph/context-pack path or fallback, freshness, selected graph slice, omitted areas, and fact classification.
- **Source and inspection map:** source-of-truth files, generated/installed exclusions, files read, searches run, owners, caller/callee paths, dependents, and local conventions.
- **Graph-memory-execution reconciliation:** graph/context-pack, project memory, ADR, prior summary, and validation-order claims accepted, rejected, stale, partial, or not verified.
- **Placement and reuse decision:** direct reuse candidates, extension points, rejected locations, naming convention evidence, and new-structure justification if any.
- **Changed-surface validation map:** validators, tests, builds, report regeneration, docs checks, install checks, covered paths, and freshness after final edits.
- **Fact table:** each material claim labeled with evidence source, confidence, and whether it is allowed to influence planning, validation, or closure.
- **Review route:** owner capability, independent reviewer capability, repair route, and re-review condition for changed paths.
- **Evidence limits and handoff:** skipped surfaces, unknown owners, low-confidence edges, next owner/reviewer gate, rollback clue, and residual risk.

# Quality Gate
1. The map names inspected files/searches, source of truth, generated/installed exclusions, and owning module or escalated unknown owner.
2. Caller, callee, tests, docs, configs, validators, release/install surfaces, and generated artifacts are included when relevant.
3. Placement/reuse decisions cite local convention evidence, and evidence freshness, skipped surfaces, unknowns, and next owner are explicit.
4. Repository graph/context-pack evidence is task-bounded; stale or mismatched markers trigger refresh or direct-source fallback.
5. Every material claim has a fact class and source: direct file read, search result, generated graph, memory/ADR, validation output, or explicit inference.
6. Graph, memory, context-pack, prior summary, and execution-order evidence are reconciled before they influence planning or closure.
7. Changed-surface validation covers the final material diff; validation that predates later edits is marked stale or rerun.
8. Context is bounded to affected files and nearest dependents; omitted high-volume areas are named with rationale and residual risk.
9. Security, data/API, delivery, architecture, documentation, or test gates are escalated when the mapped surface touches those risks.

# Evidence Contract
Close a repository context map only when these answers are concrete:
- **Boundaries inspected:** target files, same-directory or parent conventions, relevant tests, configs, docs, registry/build/install surfaces, generated/installed exclusions, and skipped surfaces.
- **Reuse and placement rationale:** owner or unknown owner, reuse candidates, rejected locations, source-of-truth decision, caller/callee/dependent evidence, and why no new structure is introduced or why it is justified.
- **Validation evidence:** searches run with scope, validation candidates, graph/context freshness, covered paths, command/report/build/install freshness, and next validator.
- **What evidence proves:** which source, ownership, placement, dependency, generated-artifact, or validation-scope claims are directly supported.
- **What evidence does not prove:** uninspected behavior, omitted graph edges, unknown consumers, production runtime behavior, downstream adoption, or validation not yet run after final edits.
- **Residual risk and next gate:** unresolved limits, rollback clue, handoff owner, independent reviewer, and next professional gate.

# Benchmark Coverage
This capability covers monorepo impact analysis, ADR context-before-decision, docs-as-code locality, SRE change review, secure development lifecycle boundary mapping, source-vs-generated provenance, affected-test selection, and context minimization for AI coding agents.

# Routing Coverage
Route here when repository evidence is missing before planning, caller/callee graph is unclear, local convention scan is absent, source/generated boundary is ambiguous, context pack is missing or bloated, changed-surface validation is unmapped, or a small fix may have wider blast radius. Pair with `repository-graph-analysis` for graph extraction, `implementation-structure-design` for placement, `quality-test-gate` for validation mapping, and `execution-trajectory-analysis` when validation freshness depends on action order.

# Used By
`change-forge-router`, `backend-change-builder`, `frontend-change-builder`, `data-api-contract-changer`, `data-middleware-change-builder`, `integration-change-builder`, `delivery-release-gate`, `change-impact-analyzer`, `architecture-impact-reviewer`, `task-dag-planner`, `ai-code-review-refactor`, `quality-test-gate`, `change-documentation-gate`, `skill-authoring-expert`, `agent-execution-discipline`.

# Handoff
Hand off the map to the implementation owner before planning or editing. If mapping finds boundary, security, test, release, or documentation risk, hand off to the matching gate before implementation continues.

# Completion Criteria
The capability is complete when a reviewer can see exactly which repository evidence shaped the plan, which source artifacts own the change, which dependent surfaces were checked or skipped, and which validation commands are expected to prove the final patch.
