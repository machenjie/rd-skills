---
name: project-memory-governance
description: Governs append-only project memory events, deterministic projections, repeat-failure gates, fragile-file gates, stale-context gates, privacy boundaries, and human promotion.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "125"
changeforge_version: 0.1.0
---

# Project Memory Governance

## Mission
Use project memory only as human-governed experience evidence: append-only events may inform risk and retrieval, but they are not source facts and do not automatically rewrite skill, registry, or repository truth.

## When To Use
- When a task mentions project memory, repeat failure, fragile file, stale context, previous fix failed, or latest commit review follow-up.
- When runtime support records repeated failures, fragile files, stale context, or prior validation gaps.
- Before relying on memory-derived summaries in planning, review, validation, or handoff.
- When deciding whether a memory observation should be promoted into source documentation, tests, or registry rules.

## Do Not Use When
- The task can be answered from current source evidence without historical experience.
- Memory is requested as automatic learning, source indexing, or background ingestion.
- The memory event would contain secrets, raw prompts, personal data, full command output, or private archive content.

## Non-Negotiable Rules
- Store only append-only memory events with bounded facts, category, timestamp, source path, and privacy classification.
- Derive memory projection deterministically from events; do not mutate history to fit current work.
- Treat memory summary as experience input, not a source fact or replacement for repository inspection.
- Trigger repeat failure gate on the third same-path or same-cause attempt unless a new hypothesis and validation plan exist.
- Trigger fragile file gate before editing files marked high-risk by prior repairs, generated-source coupling, or repeated breakage.
- Trigger stale context gate when memory or context pack predates relevant source changes.
- Human promotion only: memory can suggest docs, tests, or registry updates, but a maintainer must approve source promotion.

## Industry Benchmarks
- **Append-only event sourcing**: Historical observations are immutable and projected into current views.
- **Deterministic retrieval**: The same query and event set produce the same memory projection.
- **Incident learning discipline**: Repeated failures require changed hypotheses and stronger evidence.
- **Privacy by design**: Memory stores bounded classifications, not raw sensitive content.
- **Human governance**: Durable process changes require review and explicit promotion.

## Selection Rules
- Select this capability with `agent-execution-discipline` when repeated failure or stale context affects closure.
- Select it with `ai-code-review-refactor` when prior review findings or fragile files should inform review scope.
- Select it with `repository-context-map` and `repository-graph-analysis` when memory points to likely source areas but source evidence still needs inspection.
- Select it with `quality-test-gate` when prior failed validations change validator choice or freshness requirements.

## Risk Escalation Rules
- Escalate when memory suggests a repeat failure and the current plan repeats the same path.
- Escalate when a fragile file lacks preflight inspection, owner check, or targeted validation.
- Escalate when stale context is being used as current source evidence.
- Escalate to `security-privacy-gate` when a proposed memory event includes secrets, raw prompts, personal data, or full command output.
- Escalate to a human maintainer before promoting memory into docs, tests, registries, or source rules.

## Critical Details
- Append-only memory event fields should include event id, kind, bounded path, failure class, validation result, timestamp, and privacy boundary.
- Memory projection must name included events, excluded events, retrieval key, and determinism version.
- Repeat failure gate requires a new diagnosis, alternative approach, or explicit blocked handoff.
- Fragile file gate requires preflight read, owner or source-of-truth check, same-pattern scan, and validator mapping.
- Stale context gate compares memory timestamps against source changes, generated artifacts, and validation runs.

## Failure Modes
- **Auto-learning claim**: Memory is described as automatically updating source policy.
- **Source substitution**: A memory summary replaces reading current repository files.
- **Private data retention**: Raw prompt or command output is stored as memory.
- **Repeat retry loop**: A third failed approach proceeds without a new hypothesis.
- **Unreviewed promotion**: Memory becomes docs or registry content without maintainer approval.

## Output Contract
Return a `project_memory_governance_record` with:
- **Append-only memory event**: bounded event facts, privacy class, source path, timestamp, and retention boundary.
- **Memory projection**: deterministic retrieval key, included events, excluded events, summary, and confidence.
- **Gates**: repeat failure gate, fragile file gate, and stale context gate status.
- **Source check**: current repository evidence that confirms, refutes, or limits the memory summary.
- **Promotion decision**: none, proposed human promotion, or approved promotion with owner.
- **Residual risk**: memory gaps, stale projection, privacy limits, and next owner.

## Quality Gate
1. Memory events are append-only and bounded.
2. Projection is deterministic and cites included event ids.
3. Memory is not treated as source fact.
4. Repeat failure, fragile file, and stale context gates are evaluated when signals exist.
5. Privacy boundary excludes raw prompts, secrets, personal data, and full command output.
6. Promotion into source artifacts is human-approved or explicitly deferred.

## Used By
- `change-forge-router`
- `quality-test-gate`
- `ai-code-review-refactor`
- `change-documentation-gate`
- `agent-execution-discipline`
- `skill-authoring-expert`

## Handoff
Hand off gated memory findings to the owner skill with source evidence requirements. Hand off promotion candidates to a maintainer rather than editing durable policy automatically.

## Completion Criteria
The capability is complete when project memory informs risk through bounded deterministic projections, gates repeated or fragile work, preserves privacy, and keeps durable source promotion under human control.
