# Context Packaging Evidence Patterns

Use this reference when package closure depends on repository graph, project memory, execution trajectory, validation freshness, command output, compaction state, or tool-output sensitivity. Keep it as an evidence map, not a second context-packaging tutorial.

## Context Claim To Evidence Map

| Package claim | Minimum evidence | What it proves | What it does not prove |
| --- | --- | --- | --- |
| Source fact is current | Direct source path, line or section, commit/date, and read after latest relevant edit. | The inspected source says what the package claims. | Uninspected callers, runtime state, generated artifacts, or external consumers match it. |
| Repository graph is usable | Graph artifact id/path, indexed commit or repo hash, selected nodes, omitted nodes, and stale/re-index decision. | Graph can select likely files, callers, contracts, tests, and owners for this task. | The full repository is understood or current source reads can be skipped. |
| TaskContextPack is safe to reuse | Pack version, package version, freshness marker, changed paths since creation, and accepted/rejected stale claims. | The pack is a bounded selector and handoff artifact for this task. | The pack is source truth or a replacement for JIT reads. |
| Project memory informs scope | Memory signal, date if available, privacy boundary, current-source confirmation, and accepted/rejected/stale verdict. | Prior experience can widen inspection or validation. | Memory alone proves current requirements, owners, contracts, or behavior. |
| Execution trajectory is fresh | Command order, material edit order, validator/report path, exit code or not-run status, and final-edit freshness. | Closure evidence was produced after the last relevant change. | Later edits, external CI, production telemetry, or unrun validators are covered. |
| Tool output is safe to carry | Bounded summary, artifact/log path, sensitive-field exclusion, and permission/sandbox class. | The package can cite evidence without leaking raw prompts, secrets, env values, or full logs. | Full command output is safe to paste or persist. |

## Graph, Memory, And Execution Reconciliation

- Treat graph, memory, generated reports, prior summaries, old validation logs, and compaction notes as selectors until current source or a fresh artifact confirms them.
- Accept a graph edge only when the indexed commit/hash matches the working source or the package marks the graph stale and compensates with direct reads.
- Accept project memory only after current source, tests, contracts, reports, or owner evidence confirms the relevant claim; otherwise mark it stale, rejected, or experience-only.
- Mark validation stale after edits to source, tests, contracts, generated artifacts, registry metadata, reports, build/install outputs, package content, or route closure.
- Record execution trajectory when an agent already diagnosed, repaired, validated, skipped a gate, retried a path, or crossed a compaction boundary.
- Keep JIT retrieval plans explicit: selected reads, deferred reads, forbidden reads, line hints, source-truth status, and why omitted context is not needed.

## Tool Output And Permission Boundary

| Action | Boundary record |
| --- | --- |
| Source, registry, report, graph, and package inspection | Read-only local shell; cite searched/read paths and summarize bounded findings. |
| Validators, evals, builds, and installation checks | Local-write action limited to reports, caches, dist, build outputs, logs, or temp files; cite command, exit code, log/report path, and freshness. |
| Connector, ticket, telemetry, owner record, or production-data lookup | Connector/data-scoped read or write; record account boundary, redaction rule, unavailable evidence, and retention limit. |
| External write, cleanup, deploy, migration, or destructive command | High-risk action; require explicit approval, dry-run when available, rollback or compensation path, owner, and stop condition. |
| Large output, full graph, raw prompt, env, secret, credential, or private data | Do not paste into package; retain only bounded summary, selected nodes, excluded fields, artifact path, and residual risk. |

## Closure Template

```yaml
context_packaging_evidence_closure:
  inspected_boundaries:
    - boundary: ""
      current_source_or_artifact: ""
      finding: ""
  graph_memory_execution_coupling:
    graph: accepted | rejected | stale | partial | not_used
    memory: accepted | rejected | stale | experience_only | not_used
    prior_summary: accepted | rejected | stale | partial | not_used
    execution_trajectory: fresh | stale | partial | not_run
  source_to_package_map:
    - claim: ""
      evidence: ""
      fact_class: FACT | INFERENCE | ASSUMPTION | OPEN_QUESTION
      freshness: ""
      owner: ""
  validation_freshness:
    - command_or_artifact: ""
      exit_code_or_status: ""
      ran_after_final_material_edit: true
      proves: ""
      does_not_prove: ""
  tool_permission_boundary:
    action_class: ""
    sandbox_or_connector_scope: ""
    state_mutation: none | local_reports_dist_cache | external
    redaction: ""
  excluded_context:
    - item: ""
      reason: ""
  residual_risk:
    - risk: ""
      owner: ""
      next_gate: ""
```
