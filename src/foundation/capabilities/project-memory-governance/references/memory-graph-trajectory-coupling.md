# Memory Graph Trajectory Coupling

Use this reference when project memory influences repository graph selection, execution trajectory review, validation freshness, privacy review, or durable source promotion. The `SKILL.md` body owns routing and gate decisions; this reference preserves the deeper field and coupling matrix without forcing every memory signal to load it.

## Contents

- [Memory Event Field Schema](#memory-event-field-schema)
- [Projection Determinism Rules](#projection-determinism-rules)
- [Projection And Coupling Matrix](#projection-and-coupling-matrix)
- [Source Reconciliation Checklist](#source-reconciliation-checklist)
- [Privacy And Retention Matrix](#privacy-and-retention-matrix)
- [Promotion Gate](#promotion-gate)
- [Output Template](#output-template)

## Memory Event Field Schema

| Field | Required Evidence | Exclusion |
| --- | --- | --- |
| `event_id` | Stable identifier for one bounded observation. | No raw prompt, transcript, or full command output. |
| `event_kind` | Repeat failure, fragile file, stale context, validation gap, review follow-up, graph drift, or promotion candidate. | No free-form personal archive category. |
| `bounded_target` | Repository path, skill id, capability id, registry key, report family, or generated artifact family. | No home directory crawl, unrelated corpus, or user-specific mapping. |
| `source_anchor` | Current file, registry entry, test, report, generated source-of-truth, or owner evidence to inspect. | No claim that memory alone proves current behavior. |
| `failure_class` | Verified cause class, repeated approach class, validation-gap class, or unknown-with-hypothesis-needed. | No speculative diagnosis recorded as fact. |
| `attempt_signature` | Bounded route, command class, patch path, or validation class that identifies repeated same-path attempts. | No full command output, secrets, arguments containing private data, or environment dumps. |
| `validation_result` | Command class, outcome, freshness, covered path class, and evidence limit. | No "probably passed" or unparsed validation claim. |
| `trajectory_marker` | Edit-before-read, repair-after-review, stale-validation, skipped-stage, or closure-gap marker when relevant. | No raw lifecycle transcript. |
| `graph_selector` | Source, caller, owner, generated artifact, or affected-test edge that memory suggests should be inspected. | No graph dump or unverified dependency certainty. |
| `privacy_boundary` | Public repo fact, project-local bounded fact, sensitive-excluded, promotion-forbidden, or owner-approved promotion. | No secrets, personal data, raw prompts, environment variables, credentials, or private archives. |
| `promotion_status` | None, proposed, approved by maintainer, rejected, or source artifact updated. | No automatic skill, registry, doc, test, or eval mutation. |
| `recorded_at_or_order` | Timestamp, command order, commit order, or comparable lifecycle sequence when available. | No false precision when only relative order is known. |
| `retention_policy` | Keep bounded event, expire after closure, promote then close, or do not store. | No unbounded retention of sensitive or unrelated material. |

## Projection Determinism Rules

1. Use the same retrieval key, event set, event filters, ordering rule, and projection version to produce the same projection.
2. Sort included events by recorded order, then event id when order is equal or unknown.
3. Classify every candidate event as included, excluded by scope, excluded by privacy, stale, superseded, or not verified.
4. Summaries must be derivable from included bounded fields, not from unstored raw prompts or logs.
5. A projection may select source files, graph edges, validators, or trajectory review, but it cannot certify current behavior.
6. If projection inputs changed after a plan, mark the previous projection stale and re-run the gate before closure.

## Projection And Coupling Matrix

| Memory signal | Projection output | Required coupling | Closure limit |
| --- | --- | --- | --- |
| Repeated same-path failure | Prior failed approach classes, verified causes, unknown causes, skipped alternatives, and attempt count. | Route to `failure-diagnosis`, `agent-execution-discipline`, or `execution-trajectory-analysis`; require a changed hypothesis or blocked handoff. | Cannot claim completion while repeating the same path after two failures without new evidence. |
| Fragile file | Affected paths, prior breakage class, owner hints, generated boundary, and validator history. | Expand `repository-graph-analysis` and `validation-broker` scope to owners, generated sources, same-pattern files, and affected tests. | Cannot rely on narrow local validation without explaining omitted graph edges and source-of-truth checks. |
| Stale context | Memory timestamp/order, source change order, generated artifact freshness, validation age, and confidence. | Require current source reread, graph refresh, direct-source fallback, or trajectory freshness review. | Memory is a selector only until current source confirms it. |
| Review follow-up | Finding id, changed paths, requested evidence, repair status, and reviewer expectation. | Require `ai-code-review-refactor` or owner-skill re-review after material repair. | Prior approval is stale after material edits until re-review or explicit owner acceptance. |
| Validation gap | Previous command, outcome, covered paths, skipped surfaces, and later edits. | Route to `validation-broker` for validator depth and freshness status. | A targeted or stale pass cannot be described as full-suite verification. |
| Graph drift | Prior graph edge, source-of-truth hint, generated artifact relation, owner edge, or affected-test edge. | Route to `repository-graph-analysis`; refresh graph or inspect current source directly. | Graph-memory agreement is not semantic proof without current source inspection. |
| Compaction or handoff memory | Bounded summary of route, target, edits, validation, unknowns, and next gate. | Route to `plan-execution-consistency` or `execution-trajectory-analysis` when closure depends on ordering. | Handoff memory cannot replace final diff, source, and validation freshness checks. |
| Promotion candidate | Candidate doc/test/registry/skill/eval rule, supporting incidents, and privacy class. | Maintainer approval plus source placement rationale, validation plan, and rollback note. | Memory does not become durable policy by itself. |

## Source Reconciliation Checklist

- Inspect current source, registry/config/docs, tests, reports, generated artifact source-of-truth, and owner evidence relevant to the memory signal.
- Mark each memory claim accepted, rejected, stale, or not verified.
- Record the graph/context slice widened by memory and the omitted graph edges with reason.
- Record validation freshness after final material edits; stale validation stays negative evidence.
- Record trajectory findings when edit order, repair after review, repeated attempts, or compaction affects closure.
- Preserve direct-source fallback when graph or memory evidence cannot be refreshed.
- State residual risk for unknown owners, missing tests, unrefreshed generated artifacts, or not-run validators.

## Privacy And Retention Matrix

| Class | Store | Do not store | Default action |
| --- | --- | --- | --- |
| Public repo fact | Path, capability id, command class, validation outcome, bounded report name. | Full output if it contains irrelevant or sensitive data. | Keep bounded event. |
| Project-local bounded fact | Failure class, graph selector, validator class, owner role, promotion status. | Raw prompt, transcript, private user content, personal archive names. | Keep only if it changes risk or validation. |
| Sensitive-excluded | Redacted fact that a secret, credential, PII, env var, or private archive was encountered. | The sensitive value or surrounding raw text. | Store exclusion marker or do not store. |
| Promotion-forbidden | Memory that is useful for current closure but unsafe as durable source policy. | Any policy mutation derived from unsafe memory. | Use for handoff only, then expire or reject. |
| Owner-approved promotion | Confirmed pattern, approved artifact path, maintainer, validation, rollback note. | Unapproved broad rule or corpus-derived claim. | Promote through normal source review, not memory mutation. |

## Promotion Gate

1. Current source confirms the repeated pattern, fragile boundary, stale-context failure, or validation gap.
2. The proposed durable artifact has an owner, placement rationale, source-vs-dist decision, and rejected-location note.
3. The source update has tests, validators, eval fixtures, or review checks appropriate to its risk.
4. The memory record excludes secrets, prompts, personal data, environment variables, credentials, full command output, and private archives.
5. A maintainer explicitly approves, defers, or rejects promotion.
6. The handoff states rollback path, residual risk, and the next owner for unpromoted memory.

## Output Template

```yaml
project_memory_governance_record:
  mode_selected: "fragile file gate"
  boundaries_inspected:
    current_source: []
    registry_config_docs: []
    tests_reports_generated_artifacts: []
    graph_slice: []
    trajectory_ledger: []
    skipped_with_reason: []
  memory_event:
    event_id: ""
    event_kind: ""
    bounded_target: ""
    failure_class: ""
    validation_result: ""
    privacy_boundary: ""
    retention_policy: ""
    promotion_status: "none"
  memory_projection:
    retrieval_key: ""
    projection_version: ""
    included_events: []
    excluded_events: []
    verdict: "accepted|rejected|stale|not_verified"
    confidence: ""
    freshness_limit: ""
  source_check:
    confirmed: []
    refuted: []
    not_verified: []
  coupling_decision:
    graph_context_scope: ""
    validation_freshness: ""
    trajectory_review: ""
    promotion_path: ""
  changed_memory_to_validation_map: []
  promotion_and_risk:
    approval_status: "none|proposed|approved|rejected"
    owner: ""
    rollback_note: ""
    residual_risk: []
    next_gate: ""
```
