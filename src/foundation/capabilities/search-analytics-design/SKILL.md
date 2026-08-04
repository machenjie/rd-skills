---
name: search-analytics-design
description: "`analysis-agent`/`task-agent`/`review-agent`: use for search relevance, freshness, analytical grain, metrics, or rebuilds; skip bounded source queries and operational telemetry."
---

# search-analytics-design

## Registry Trigger

**Use when**

- design search indexing relevance filtering faceting analytical metrics and derived data

**Do not use when**

- a bounded source-store query or index changes without search relevance or analytics semantics
- only logging, tracing, or operational monitoring changes
- no task-local search analytics design decision is required

## Skill Role

Define search and analytical authority, ingestion, visibility, freshness, rebuild, relevance, and metric semantics. Leave source meaning, transport, cutover/deployment execution, and consumer inventory to their owning skills. For model-backed retrieval, `ai-product-extension` owns model/embedding selection, evaluation, and lifecycle acceptance; search owns corpus, retrieval, permissions, freshness, and fallback integration.

## High-Value Rules

- Classify each derived surface as authoritative, derived, or mixed; name writers, conflict authority, allowed writes, and caller revalidation.
- Keep stale or unavailable derived data subordinate to its source or an explicit conflict rule.
- Define identity, deduplication, ordering, late arrival, correction, deletion, replay, and backfill overlap.
- Enforce visibility before results, counts, facets, aggregations, or retrieved context reach callers.
- Derive lag limits, stale handling, recovery ownership, and forbidden stale actions from separately measured source-change, ingestion, and query-visible timestamps plus decision consequence.
- Define corpus, retrieval, permissions, freshness, fallback integration, analyzers, mappings, and non-model ranking as search-owned; model/embedding selection, evaluation, and lifecycle acceptance as `ai-product-extension`-owned.
- Define analytical grain, identity, dedupe, timezone, correction, reconciliation, and decision ownership before pipelines.
- Route actual data/index/model cutover and deployment execution for search-defined rebuild, compatibility, validation, fallback, and cleanup requirements to `data-migration-design` and `delivery-release-gate`, including AI-accepted model-backed retrieval.

## Anti-Patterns

- Presenting a projection as source truth, using UI/post-query filtering as authorization, or returning global counts/facets that bypass visibility scope.
- Defining a metric without grain, identity, deduplication, late correction, and reconciliation, then treating dashboard agreement as correctness.
- Prescribing one freshness number, streaming stack, blue-green rebuild, or rollback window without product consequence and current engine/operational evidence.

## Stop Conditions

Stop when authority, permission ownership, freshness consequence, rebuild source, analytical grain, or current reconciliation evidence is missing. For model-backed retrieval, stop and route to `ai-product-extension` when model/embedding selection, evaluation, or lifecycle acceptance is missing; route unresolved cutover or deployment execution to `data-migration-design` and `delivery-release-gate`. Static inspection does not prove deployed permissions, live freshness, production relevance, metric trust, or cutover duration.

## Output Contract

- Search/analytics decision naming authority, ingestion, visibility, freshness, relevance or metric semantics, rebuild/fallback, evidence limits.

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | Authority relevance freshness analytical-grain or cutover mechanisms remain unresolved | Source contract and product consequence select one bounded derived-view design | task-agent, analysis-agent, review-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | Change affects ingestion identity permissions freshness relevance metrics rebuild fallback or retention | No search index analytical model or derived-view contract changes | task-agent, analysis-agent, review-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | Permission freshness relevance metric reconciliation or cutover claims need current proof | Fresh query sets judgments reconciliations and cutover checks prove each bounded claim | task-agent, analysis-agent, review-agent | evidence-record, proof-limit, residual-risk |
