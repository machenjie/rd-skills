---
name: repository-graph-analysis
description: Builds bounded repository intelligence from symbol, import, reference, test, ownership, and generated-artifact graphs into freshness-aware context packs.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "124"
changeforge_version: 0.1.0
---

# Repository Graph Analysis

## Mission
Use repository graphs to identify the relevant source-of-truth, dependencies, tests, owners, and generated artifacts for a change without dumping the whole repository into context.

## When To Use
- When source of truth, ownership, callers, tests, generated outputs, or affected dependencies are unclear.
- When a task mentions repo graph, symbol graph, import graph, call graph, reference graph, test graph, ownership graph, generated artifact graph, or context pack.
- Before planning broad skill, registry, hook runtime, API, architecture, or cross-module changes.
- When an existing repository graph may be stale and must be refreshed before planning.

## Do Not Use When
- A small read-only answer already has enough local evidence.
- The user asks for a general repository tour rather than a bounded change context.
- The only available graph is stale and cannot be refreshed; use `repository-context-map` with explicit limitations instead.

## Non-Negotiable Rules
- Build graphs from repository source and local metadata, not from unverified notes or assumed runtime corpora.
- Keep graph output bounded to the task; anti context-bloat is a quality requirement.
- Refresh graph evidence when file mtimes, commits, generated artifacts, registry entries, or dependency manifests changed after graph creation.
- Distinguish source files from generated `dist/`, reports, snapshots, and copied runtime artifacts.
- Context packs must cite graph freshness, selected nodes, omitted areas, and known drift risk.
- Do not treat graph edges as semantic proof without source inspection when behavior or ownership is disputed.

## Industry Benchmarks
- **Static dependency analysis**: Imports, references, symbols, and generated edges are used to bound impact.
- **Ownership mapping**: Change routing respects code ownership and source-of-truth boundaries.
- **Affected-test selection**: Test graph edges map changed paths to relevant validation.
- **Context minimization**: Only task-relevant graph slices are packaged for downstream work.
- **Freshness validation**: Graph results are invalidated by newer source changes.

## Selection Rules
- Select this capability with `repository-context-map` when graph data can sharpen the manual context map.
- Select it with `validation-broker` when changed paths must map to affected validators or tests.
- Select it with `architecture-impact-reviewer` for import cycles, module boundaries, and dependency direction.
- Select it with `change-documentation-gate` when generated artifacts or docs derive from source files.

## Risk Escalation Rules
- Escalate when the graph marks the target as generated and the source-of-truth is not identified.
- Escalate when graph freshness is stale or drifted and refresh cannot run.
- Escalate when ownership graph conflicts with import or reference graph evidence.
- Escalate when context pack size would hide critical omitted nodes or flood downstream review.
- Escalate when graph results suggest cross-module, API, security, migration, or release impact.

## Critical Details
- Symbol graph names functions, classes, types, exports, and public entry points.
- RepositoryGraph v2 records normalized symbols with `name`, `kind`, `path`,
  `line`, `visibility`, `owner_object`, `parent_symbol`, `language`, and
  `confidence`; low-confidence language nodes remain selectors, not proof.
- Import graph names module dependency direction, cycles, and boundary violations.
- Reference graph names callers, consumers, config references, docs references, and registry references.
- Test graph names direct, indirect, and missing validation targets.
- Ownership graph names owning surface, maintainer hints, generated owner, and local convention owner.
- Generated artifact graph names source files, generated files, build commands, and do-not-edit outputs.
- A context pack is the selected graph slice plus source evidence, freshness, omissions, and next gates.

## Failure Modes
- **Graph dump**: The agent includes every node instead of the bounded slice needed for the task.
- **Stale graph**: Planning uses graph data older than the edited files.
- **Generated edit**: The patch modifies `dist/` or generated reports while missing the source file.
- **Symbol-only certainty**: A symbol edge is treated as behavior proof without reading the implementation.
- **Missing test edge**: A changed path has no test graph mapping and validation is guessed.

## Output Contract
Return a `repository_graph_analysis` record with:
- **Graph sources**: symbol, import, reference, test, ownership, and generated artifact graph inputs used or unavailable.
- **Freshness**: graph timestamp, compared files or commit, drift status, and refresh action.
- **Selected nodes**: task-relevant source nodes, generated nodes, tests, docs, owners, and omitted high-volume areas.
- **Context pack**: bounded files, graph edges, source-of-truth decision, validation candidates, and context budget.
- **Anti-bloat decision**: excluded graph areas and reason.
- **Residual risk**: stale, missing, ambiguous, or conflicting graph evidence.

## Quality Gate
1. Graph freshness is current or explicitly stale with refresh required.
2. Source-of-truth and generated artifact boundaries are named.
3. Selected graph slice is bounded and task-relevant.
4. Test graph or validation candidate mapping is present when code changes are planned.
5. Omitted areas and context-pack limits are disclosed.
6. Graph evidence is backed by source inspection for behavior-critical claims.

## Used By
- `change-forge-router`
- `change-impact-analyzer`
- `architecture-impact-reviewer`
- `task-dag-planner`
- `quality-test-gate`
- `ai-code-review-refactor`
- `change-documentation-gate`
- `agent-execution-discipline`

## Handoff
Hand off the context pack to the planning, review, validation, or documentation owner. If the graph is stale, hand off a refresh requirement before implementation.

## Completion Criteria
The capability is complete when the graph slice identifies source truth, dependency/test/owner/generated edges, freshness, omissions, validation candidates, and residual drift risk without expanding into a whole-repository dump.
