# Graph Context Validation Coupling

Use this reference when repository graph evidence drives source-of-truth selection, context packaging, validation choice, owner routing, generated artifact repair, memory reconciliation, or execution trajectory review. The `SKILL.md` body owns routing and gate decisions; this reference carries the detailed edge taxonomy and context-pack schema.

## Contents

- [Edge Taxonomy](#edge-taxonomy)
- [Graph Evidence Field Schema](#graph-evidence-field-schema)
- [Context-Pack Matrix](#context-pack-matrix)
- [Graph Coupling Matrix](#graph-coupling-matrix)
- [Freshness And Confidence Rules](#freshness-and-confidence-rules)
- [Validation Coupling Rules](#validation-coupling-rules)
- [Output Template](#output-template)

## Edge Taxonomy

| Edge type | Evidence | Professional use | Required caveat |
| --- | --- | --- | --- |
| Symbol | Function, type, export, public entry point, capability id, registry key. | Identify source entry points and direct implementation files. | Symbol presence does not prove behavior. |
| Import | Module dependency direction, package boundary, layer, cycle, dependency manifest. | Detect dependency violations, affected modules, and architecture review scope. | Dynamic imports and generated imports may be incomplete. |
| Call/reference | Callers, consumers, config references, docs references, registry references, scripts. | Bound downstream behavior, documentation impact, and consumer risk. | Search misses indirect runtime use. |
| Test | Direct tests, indirect suites, fixtures, benchmark cases, eval cases, missing tests. | Feed `validation-broker` and `quality-test-gate`. | Absence of a test edge is a risk, not proof of safety. |
| Ownership | Maintainer hints, source-of-truth file, local convention owner, generated owner. | Route owner/reviewer and placement decisions. | Ownership conflict requires current source inspection. |
| Generated artifact | Source file, generated output, build command, profile, install target. | Prevent generated-only edits and stale runtime packages. | Generated artifact freshness must be rebuilt and validated. |
| Report/eval | Professionalism report, audit report, benchmark output, routing output, pressure output. | Use generated evidence without treating it as source truth. | Reports are stale after material source or validator changes. |
| Memory/trajectory | Fragile path, repeated failure, stale context, edit-before-read, repair/re-review. | Widen graph slice or require source reread/validation refresh. | Bounded experience evidence is not source proof. |

## Graph Evidence Field Schema

| Field | Required evidence | Exclusion |
| --- | --- | --- |
| `graph_id` | Stable identifier for the graph slice or context pack. | No whole-repository dump identifier used as task proof. |
| `graph_kind` | Symbol, import, reference, test, ownership, generated, report, memory, or trajectory. | No ambiguous "related files" bucket without edge type. |
| `bounded_target` | Path, capability id, skill id, registry key, generated artifact family, or report family. | No unrelated repository neighborhood. |
| `source_anchor` | Current file, registry entry, test, report, generator, or owner evidence to inspect. | No claim that graph proximity proves behavior. |
| `edge_confidence` | High, medium, low, stale, unknown, or conflict with reason. | No unstated confidence. |
| `freshness_basis` | Timestamp/order/hash/commit/report age/direct reread. | No false precision when only relative order is known. |
| `source_of_truth` | Editable source path and generated/do-not-edit policy when known. | No generated output as sole edit target. |
| `validation_candidate` | Direct test, suite, build, eval, install check, or not-found gap. | No guessed command without graph/source basis. |
| `owner_route` | Owner skill, reviewer skill, maintainer hint, or unknown-owner risk. | No silent self-review closure. |
| `omission_reason` | Out of scope, high volume, low confidence, stale, generated-only, or unknown. | No silent omission of known high-risk edges. |

## Context-Pack Matrix

| Context-pack field | Include | Exclude |
| --- | --- | --- |
| Source-of-truth decision | Editable source paths, generated outputs, registry entries, build command, do-not-edit policy. | Whole-directory dumps or generated output without source. |
| Selected nodes | Nodes needed for the task, owners, direct tests, affected docs, generated artifacts, reports. | Unrelated graph neighborhoods. |
| Edge classification | Symbol/import/reference/test/ownership/generated/report/memory/trajectory edge type and confidence. | Flattened file lists with no edge reason. |
| Omitted areas | High-volume, stale, low-confidence, unknown, or out-of-scope graph areas and why omitted. | Silent omission of known high-risk edges. |
| Validation candidates | Commands, suites, fixtures, benchmark/eval paths, build/install checks, missing test edges. | Guesswork not backed by test or source graph. |
| Memory reconciliation | Repeated failures, fragile paths, stale-context markers, accepted/rejected memory claims. | Memory as source fact. |
| Trajectory constraints | Required read-before-edit, repair/re-review, stale validation checks, closure limits. | Raw execution logs or full command output. |
| Anti-bloat decision | Context budget, excluded clusters, direct-source fallback, next owner. | Excess file content copied into the pack. |

## Graph Coupling Matrix

| Graph signal | Required coupling | Closure limit |
| --- | --- | --- |
| Generated artifact edge | Map generated output to source file, generator, build command, runtime profile, and validator. | Cannot edit or install generated output alone. |
| Missing test edge | Route to `validation-broker` and `quality-test-gate`; name not-run or not-found risk. | Cannot claim full validation from an unrelated command. |
| Ownership conflict | Route to `repository-context-map`, owner skill, or reviewer route; inspect current source. | Cannot use graph ownership as closure evidence until conflict resolves. |
| Import cycle or boundary violation | Route to `architecture-impact-reviewer` or module-boundary owner. | Cannot treat local patch as isolated until dependency direction is accepted. |
| Reference/caller fan-out | Route to `change-impact-analyzer`; bound consumers and omitted dynamic references. | Cannot say "no callers" without scope and confidence. |
| Stale graph or report | Route to `project-memory-governance` or `execution-trajectory-analysis`; refresh or downgrade evidence. | Stale graph is a selector only, not proof. |
| Context pack bloat | Route to `context-packaging`; shrink to task nodes and omit with reason. | Large pack cannot prove reviewer coverage. |
| Security/API/data/release edge | Route to the corresponding gate and validation scope. | Graph does not replace specialist review. |

## Freshness And Confidence Rules

1. Compare graph creation or report generation order against final material edits, generated outputs, registry changes, and validation commands.
2. Treat graph evidence as stale when any selected source, generated artifact, report, dependency manifest, or registry entry changed after the graph was built.
3. Mark confidence high only when the extractor/source and current file inspection agree.
4. Mark confidence medium when graph evidence is current but source semantics still require inspection.
5. Mark confidence low or unknown when the edge comes from broad search, dynamic behavior, generated code, or incomplete metadata.
6. Preserve conflicts rather than choosing the convenient edge; conflicts route to source inspection or owner review.
7. Use direct-source fallback when a graph cannot be refreshed in time.

## Validation Coupling Rules

1. If the graph identifies generated outputs, validation must include the source build and generated artifact check.
2. If changed paths have test edges, the validation broker maps direct tests first, then risk-based broader checks.
3. If changed paths lack test edges, the output states the gap and routes to `quality-test-gate`.
4. If ownership or source-of-truth edges conflict, the graph is not closure evidence until source inspection resolves the conflict.
5. If memory marks a path fragile, graph selection includes callers, tests, generated outputs, and known owner surfaces before editing.
6. If trajectory shows validation before later edits, graph-derived validation candidates must be re-run or marked stale.
7. If an omitted edge is high risk, map it to an owner response, validator, review check, or residual risk.

## Output Template

```yaml
repository_graph_analysis:
  mode_selected: "affected validation graph"
  boundaries_inspected:
    source: []
    generated_artifacts: []
    registries_configs_docs: []
    tests_fixtures_evals: []
    reports: []
    owners: []
    memory_signals: []
    trajectory_ledger: []
    skipped_with_reason: []
  graph_sources:
    symbol: ""
    import: ""
    reference: ""
    test: ""
    ownership: ""
    generated: ""
    report: ""
  freshness:
    graph_order_or_hash: ""
    compared_files_or_commit: ""
    drift_status: "current|stale|unknown|conflict"
    refresh_action: ""
    direct_source_fallback: ""
  context_pack:
    selected_nodes: []
    selected_edges: []
    confidence: ""
    source_of_truth_decision: ""
    validation_candidates: []
    omitted_areas: []
    context_budget: ""
  coupling_map:
    memory: "accepted|rejected|stale|not_verified"
    trajectory: ""
    validation_broker_inputs: []
    owner_reviewer_route: ""
    closure_consequence: ""
  changed_graph_to_validation_map: []
  anti_bloat_decision: ""
  residual_risk:
    stale: []
    missing: []
    ambiguous: []
    conflicting: []
    unknown_consumers: []
    next_gate: ""
```
