---
name: repository-graph-analysis
description: Use when repo graph, symbol/import/call/reference/test/ownership/generated-artifact graph, context pack, source of truth, affected tests, owner route, generated dist boundary, or graph freshness affects planning, review, validation, or handoff.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "124"
changeforge_version: 0.1.0
---

# Mission
Build bounded repository intelligence from current source and local metadata so a change can identify source-of-truth files, dependencies, callers, affected tests, owners, generated artifacts, omitted graph areas, validation candidates, and downstream memory/trajectory consequences without dumping the repository into context.

# When To Use
- When source of truth, ownership, callers, tests, generated outputs, dependency direction, or affected modules are unclear.
- When a task mentions repo graph, symbol graph, import graph, call graph, reference graph, test graph, ownership graph, generated artifact graph, graph freshness, source of truth unknown, or context pack.
- Before planning broad skill, registry, hook runtime, API, architecture, release, documentation, or cross-module changes.
- When a memory signal, prior trajectory, or old context pack may be stale and graph evidence must be refreshed or rejected before planning or closure.

# Do Not Use When
- A small read-only answer already has enough current source evidence and no graph signal changes risk or validation.
- The user asks for a general repository tour rather than a bounded task context.
- The only available graph is stale and cannot be refreshed; use direct source inspection with explicit limitations instead.
- Graph output would become a whole-repository dump or substitute for reading behavior-critical source.

# Stage Fit
Use during read-before-plan, coding, bug-fix, debugging, code-review, refactoring, testing, release, review scoping, validation selection, repair, and final handoff stages when graph evidence changes the edit boundary or proof obligation. Re-run when files, generated artifacts, registries, dependency manifests, reports, validation inputs, or memory/trajectory signals changed after the graph was built.

# Non-Negotiable Rules
- Build graph evidence from current repository source, local metadata, registries, tests, reports, and generated artifact relationships, not from unverified notes or assumed runtime corpora.
- Keep graph output bounded to the task; anti context-bloat is a correctness requirement.
- Distinguish editable source from generated `dist/`, reports, snapshots, compiled runtime artifacts, copied install artifacts, and do-not-edit outputs.
- Record graph freshness using file timestamp/order, commit/order, source hash, report age, or direct reread evidence when available.
- Treat graph edges as selectors, not semantic proof. Behavior-critical, ownership-critical, and source-of-truth claims require current source inspection.
- Context packs must cite selected nodes, omitted nodes, graph confidence, freshness, source-of-truth decision, validation candidates, and residual drift risk.
- Generated-artifact edges must point back to source files and build commands before any edit, install, package, or closure claim.

# Industry Benchmarks
Anchor against static dependency analysis, ownership and codeowner mapping, affected-test selection, build graph/source-of-truth tracing, generated artifact provenance, context minimization, graph freshness invalidation, and reviewable impact analysis. Keep the body focused on route-time decisions; load the reference only when edge taxonomy, context-pack fields, or graph-memory-trajectory-validation coupling needs depth.

# Mode Matrix
| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities |
| --- | --- | --- | --- | --- |
| Source-of-truth slice | Source file, generated file, registry, report, or install target is ambiguous. | Identify editable source and do-not-edit outputs. | Source path, generated artifact, build command, freshness, rejected target. | `repository-context-map` |
| Impact graph | Callers, imports, references, owners, docs, or module boundaries are unclear. | Bound change impact without graph dumping. | Selected nodes/edges, confidence, omitted areas, owner route. | `change-impact-analyzer`, `architecture-impact-reviewer` |
| Affected validation graph | Changed path must map to direct tests, suites, builds, evals, or install checks. | Feed validation broker with current graph evidence. | Test edges, missing test edges, validator candidates, stale/partial status. | `validation-broker`, `quality-test-gate` |
| Generated artifact graph | Dist, generated clients, docs, reports, or packages may drift from source. | Prevent generated-only edits and require rebuild checks. | Source generator, command, generated output, runtime profile, validation command. | `delivery-release-gate`, `change-documentation-gate` |
| Graph freshness repair | Existing graph/context pack predates edits, reports, compaction, or memory. | Refresh, downgrade, or replace graph evidence. | Timestamp/order comparison, accepted/rejected graph facts, direct-source fallback. | `project-memory-governance`, `execution-trajectory-analysis` |

# Selection Rules
- Select this capability with `repository-context-map` when graph data can sharpen the owning surface, source-of-truth boundary, or local convention scan.
- Select it with `validation-broker` when changed paths must map to affected tests, builds, evals, generated artifacts, or install validators.
- Select it with `project-memory-governance` when memory marks a path fragile, stale, previously failed, or likely to require wider caller/test/generated scope.
- Select it with `execution-trajectory-analysis` when validation freshness, repair/re-review, edit-before-read, or compaction depends on event order.
- Select it with `architecture-impact-reviewer`, `change-impact-analyzer`, or `change-documentation-gate` when edges affect dependency direction, ownership, generated artifacts, docs, API/data boundaries, or release scope.

# Technical Selection Criteria
Evaluate graph use by source freshness, edge confidence, extractor/source, generated-artifact status, source-of-truth clarity, owner conflict, validation mapping, context budget, omitted-edge risk, memory/trajectory interaction, and closure consequence. A graph claim is usable only as accepted current evidence, rejected, stale, low-confidence selector, or not verified.

# Proactive Professional Triggers
- **Signal:** A generated file, `dist/` artifact, report, package, or install output is proposed as the edit target.
  **Hidden risk:** wrong generated output, rollback loss, or silent overwrite occurs because source truth is missing.
  **Required professional action:** inspect the source/generated pair and require source file, generator, build command, runtime profile, and validator before editing or closing.
  **Route to:** `repository-context-map`, `validation-broker`.
  **Evidence required:** source/generated map, build command, generated freshness report, selected validator.
- **Signal:** A local search finds no callers, tests, or consumers and the plan treats that as proof of no impact.
  **Hidden risk:** dynamic references, generated clients, docs, registries, jobs, or hidden consumers are missed.
  **Required professional action:** classify search scope, inspect selected graph edges, document omitted areas, and route unknown-consumer residual risk.
  **Route to:** `change-impact-analyzer`, `consumer-impact-analysis`.
  **Evidence required:** searched paths report, graph confidence, omitted-edge map, owner for unknowns.
- **Signal:** A context pack includes a broad directory or too many unrelated graph nodes.
  **Hidden risk:** wrong review scope hides the relevant edge because context is bloated.
  **Required professional action:** inspect selected nodes, block broad-pack closure, and require anti-bloat exclusions with a context budget.
  **Route to:** `context-packaging`, `agent-execution-discipline`.
  **Evidence required:** included-node map, excluded-node map, context budget, reason.
- **Signal:** A graph, report, memory projection, or prior context pack predates later edits or generated outputs.
  **Hidden risk:** stale graph drives planning, validation, or completion.
  **Required professional action:** compare graph order against final edits, verify direct source, and downgrade stale facts to selector-only.
  **Route to:** `project-memory-governance`, `execution-trajectory-analysis`.
  **Evidence required:** freshness comparison report, accepted/rejected graph facts, direct-source fallback.
- **Signal:** Changed files have no direct test edge or validator candidate.
  **Hidden risk:** wrong command choice is guessed and partial validation is overclaimed.
  **Required professional action:** route changed paths to validation broker, require missing-edge residual risk, and block full-verification language.
  **Route to:** `validation-broker`, `quality-test-gate`.
  **Evidence required:** changed-path map, missing/direct/indirect test edges, selected validator, not-run scope.

# Risk Escalation Rules
- Escalate when the graph marks the target as generated and source-of-truth is not identified.
- Escalate when graph freshness is stale, low-confidence, drifted, or cannot be refreshed before edit/closure.
- Escalate when ownership graph conflicts with import, reference, source-of-truth, registry, or generated artifact evidence.
- Escalate when context pack size hides critical omitted nodes or floods downstream review.
- Escalate when graph results suggest cross-module, API, data, security, migration, release, or documentation impact.
- Escalate when changed paths lack test edges or validator candidates and completion would rely on a guessed command.

# Critical Details
- RepositoryGraph records node and edge evidence with freshness, confidence, extractor, source hash, generated-artifact status, owner/source-of-truth hint, and edit policy when known.
- Edge classes include symbol, import, call/reference, test, ownership, generated artifact, registry/config/doc, report, and validation edge. Load [references/graph-context-validation-coupling.md](references/graph-context-validation-coupling.md) for the full matrix.
- Business semantic selector edges include `object_defined_in`, `rule_enforced_by`, `rule_previewed_by`, `rule_defended_by`, `workflow_transition_implemented_by`, `event_produced_by`, `event_consumed_by`, `golden_case_validates`, and `memory_warns_about`; they select source to inspect and never prove business facts alone.
- Load [references/graph-evidence-freshness-and-confidence.md](references/graph-evidence-freshness-and-confidence.md) when graph facts, reports, memory signals, or trajectory evidence may be stale, low-confidence, conflicting, or selector-only.
- Load [references/graph-source-generated-validation-map.md](references/graph-source-generated-validation-map.md) when source truth, generated artifacts, changed-path validators, reports, packages, or install outputs need a precise map.
- A context pack is the selected graph slice plus source evidence, freshness, omissions, validation candidates, owner/reviewer route, memory/trajectory coupling, and anti-bloat decision.
- Only current medium/high confidence graph evidence can support closure, and only after source inspection confirms behavior-critical claims.
- Low-confidence, stale, missing, or conflicting graph facts remain selectors, assumptions, validation suggestions, or residual risk.

# Failure Modes
- **Graph dump:** The agent includes every node instead of the bounded slice needed for the task.
- **Stale graph:** Planning uses graph data older than edited files, generated outputs, reports, or validation inputs.
- **Generated edit:** The patch modifies `dist/`, generated reports, or copied runtime artifacts while missing source files.
- **Symbol-only certainty:** A graph edge is treated as behavior proof without source inspection.
- **Missing test edge:** A changed path has no validation mapping and the command choice is guessed.
- **Silent omission:** Known high-risk callers, consumers, owners, or generated artifacts are omitted without reason.
- **Memory substitution:** stale memory or trajectory evidence is treated as graph proof without current source reread.
- **Validation edge overclaim:** a generated, report, package, or install path lacks a validator map but closure claims full verification.

# Reference Loading Policy
The `SKILL.md` body carries route-time rules, output, and gates.
- Load [references/graph-context-validation-coupling.md](references/graph-context-validation-coupling.md) when drafting a concrete graph/context pack, reconciling graph evidence with memory or trajectory, deciding source-vs-generated boundaries, or mapping changed paths to validation.
- Load [references/graph-evidence-freshness-and-confidence.md](references/graph-evidence-freshness-and-confidence.md) when graph/report/memory/trajectory evidence freshness, confidence, conflict handling, direct-source fallback, or evidence limits need exact fields.
- Load [references/graph-source-generated-validation-map.md](references/graph-source-generated-validation-map.md) when editable source, generated artifacts, changed-path validators, report freshness, package/install outputs, or rollback and handoff mapping need exact fields.

# Output Contract
Return a `repository_graph_analysis` record with:
- `mode_selected` (source-of-truth slice, impact graph, affected validation graph, generated artifact graph, or graph freshness repair).
- `boundaries_inspected` (source, generated artifacts, registries/config/docs, tests/fixtures/evals, reports, owners, memory signals, trajectory ledger, and skipped boundaries with reason).
- `graph_sources` (symbol, import, call/reference, test, ownership, generated, registry/config/doc/report inputs used or unavailable).
- `freshness` (graph timestamp/order/hash, compared files or commit, drift status, refresh action, and direct-source fallback).
- `context_pack` (selected source/generated/test/doc/owner nodes, edge types, confidence, omitted high-volume or low-confidence areas, source-of-truth decision, validation candidates, and context budget).
- `coupling_map` (memory signals accepted/rejected/stale, trajectory constraints, validation broker inputs, reviewer/owner route impacts, and closure consequence).
- `business_semantic_graph` when BSP is selected: business edge types, extractor, source-backed confirmation status, memory/graph selector limits, and skipped semantic edges.
- `changed_graph_to_validation_map` (each changed path, generated edge, omitted edge, and missing test edge mapped to validator, review, owner response, or residual risk).
- `anti_bloat_decision` (excluded graph areas and reason).
- `evidence_limits` (what evidence proves, what evidence does not prove, and source-inspection gaps).
- `residual_risk` (stale, missing, ambiguous, conflicting, low-confidence, or unknown-consumer graph evidence and next gate).
- `handoff` (closure decision, owner/reviewer route, rollback note, validation limits, and next gate).

# Evidence Contract
Close graph analysis only when these answers are concrete:
- **Basis:** graph signal, requested change, target boundary, and why graph evidence changes planning, validation, review, or handoff.
- **Boundaries inspected:** source files, registries/config/docs, tests, reports, generated artifact source-of-truth, graph slice, memory signals, trajectory, owner evidence, and skipped boundaries with reason.
- **Freshness and confidence:** graph extractor/source, timestamp/order/hash, confidence, stale facts, rejected facts, direct-source fallback, and omitted areas.
- **Placement and dependency direction:** source-vs-generated edit target, owner/reviewer route, dependency direction, rejected locations, and no whole-repository dump.
- **What evidence proves:** the bounded graph facts accepted for planning, validation, review, or handoff and the current-source checks that support them.
- **What evidence does not prove:** behavior semantics, unknown dynamic consumers, omitted edges, stale reports, or source truth not confirmed by current inspection.
- **Validation and closure:** changed-graph-to-validation map, validation freshness requirements, what remains not verified, rollback note, residual risk, and next owner.

# Benchmark Coverage
This capability covers static dependency graph analysis, ownership and source-of-truth mapping, generated artifact provenance, affected-test selection, bounded context packaging, graph freshness invalidation, omitted-edge disclosure, memory/trajectory reconciliation, validation brokerage inputs, and source inspection discipline.

# Routing Coverage
Routes from `change-forge-router`, `change-impact-analyzer`, `architecture-impact-reviewer`, `task-dag-planner`, `quality-test-gate`, `ai-code-review-refactor`, `change-documentation-gate`, and `agent-execution-discipline` should arrive here when graph evidence changes scope, source truth, dependency direction, context packaging, validation choice, generated artifact handling, or closure. Route away when the primary need is manual context mapping, detailed validation outcome parsing, memory governance, trajectory reconstruction, or code review without a graph signal.

# Quality Gate
1. Graph freshness is current or explicitly stale with refresh/direct-source fallback required.
2. Source-of-truth and generated artifact boundaries are named.
3. Selected graph slice is bounded and task-relevant.
4. Edge types, confidence, extractor/source, omitted areas, and anti-bloat decision are disclosed.
5. Test graph or validation candidate mapping is present when code, registry, hook runtime, docs, generated artifacts, reports, packaging, or install outputs change.
6. Graph evidence is backed by current source inspection for behavior-critical, ownership-critical, or source-of-truth claims.
7. Context packs name downstream validation, memory, and trajectory consequences of selected or omitted graph edges.
8. Generated artifacts map to source and build command before edit or closure.
9. Every changed path, missing test edge, generated edge, and omitted high-risk edge maps to validation, review, owner response, or residual risk.
10. Handoff states inspected evidence, unknown graph areas, validation limits, rollback note, and next owner.
11. Business semantic graph edges are treated as selectors until current source, owner review, or validation evidence confirms the claim.

# Used By
`change-forge-router`, `change-impact-analyzer`, `architecture-impact-reviewer`, `task-dag-planner`, `quality-test-gate`, `ai-code-review-refactor`, `change-documentation-gate`, `agent-execution-discipline`.

# Handoff
Hand off the context pack to the planning, review, validation, documentation, release, or owner skill with source evidence requirements and omitted-edge limits. If graph evidence is stale or incomplete, hand off refresh/direct-source fallback before implementation or closure.

# Completion Criteria
The capability is complete when the graph slice identifies source truth, dependency/test/owner/generated edges, freshness, omissions, validation candidates, memory/trajectory coupling, anti-bloat decisions, and residual drift risk without expanding into a whole-repository dump or replacing current source inspection.
