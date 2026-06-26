---
name: project-memory-governance
description: Use when project memory, repeat failure, fragile file, stale context, previous fix failed, or latest commit review follow-up affects planning, review, validation, or handoff; governs bounded memory projection, privacy, and human promotion.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "125"
changeforge_version: 0.1.0
---

# Mission
Govern bounded project memory so prior failures, fragile files, stale context, validation gaps, and review follow-ups improve the next action without becoming source truth. Memory is an append-only selector: it may widen repository graph scope, require source refresh, strengthen validation freshness, trigger trajectory review, or propose maintainer promotion only after current evidence is reconciled.

# When To Use
- When the task mentions project memory, memory projection, repeat failure, fragile file, stale context, previous fix failed, latest commit review follow-up, or human promotion.
- When runtime support records repeated failures, fragile paths, stale assumptions, prior validation gaps, repair-without-re-review, or reviewer follow-up.
- Before relying on a memory-derived summary for planning, review, validation command selection, or final handoff.
- When deciding whether a repeated pattern should become a doc, test, registry rule, eval fixture, or other durable source artifact.

# Do Not Use When
- Current source, registry, tests, reports, and owner evidence are sufficient and no memory signal changes risk or scope.
- The request is automatic learning, source indexing, personal archive ingestion, background scanning, or user-specific corpus installation.
- The proposed event would retain raw prompts, secrets, personal data, environment variables, credentials, full command output, or unrelated private archives.
- Memory is being used to mutate source policy, registries, docs, tests, or skills without explicit maintainer approval.

# Stage Fit
Use during planning, coding, code-review, repair, testing, validation, and handoff after the target boundary is known and before a memory signal is allowed to change scope or closure. Re-run the gate after a second same-path failure, a fragile-file edit, a graph refresh, a repair after review, or any material source change that can make prior memory stale.

# Non-Negotiable Rules
- Memory events are append-only, bounded, and classified; do not rewrite history or store raw sensitive material.
- Memory projection is deterministic for the same retrieval key, event set, filter, and projection version.
- Memory is experience evidence, not source fact. Current source, registry, tests, generated artifact source-of-truth, reports, or owner evidence must confirm behavior-critical claims.
- A third same-path or same-cause attempt is blocked unless the record names a new hypothesis, a different route, stronger validation, or an explicit blocked handoff.
- Fragile-file signals require preflight read, source-of-truth or owner check, same-pattern scan, graph/context slice, and validator mapping before edit or closure.
- Stale-context signals require freshness comparison against current files, reports, generated artifacts, validation order, and execution trajectory.
- Promotion into docs, tests, registries, eval fixtures, or skills is human-governed; memory can propose, not silently install policy.

# Industry Benchmarks
Anchor against append-only event sourcing, deterministic projections, incident learning reviews, privacy-by-design retention minimization, audit-log immutability, evidence freshness control, human-in-the-loop knowledge management, and CI/CD validation gates. Keep runtime memory records small and load deeper coupling rules only when the signal changes graph, execution, validation, or promotion decisions.

# Mode Matrix
| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities |
| --- | --- | --- | --- | --- |
| Memory projection | Project memory or prior note is referenced. | Accept, reject, or mark stale before use. | Retrieval key, included/excluded events, projection version, source check. | `repository-context-map` |
| Repeat failure gate | Same command, patch path, diagnosis, or validation failure appears twice. | Stop loop and require a changed hypothesis. | Failed approach class, verified cause or unknown, new route, next validator. | `failure-diagnosis`, `agent-execution-discipline` |
| Fragile file gate | Prior breakage, owner warning, generated boundary, or hot file is signaled. | Expand context before editing and map validation. | Current file read, owner/source-of-truth, same-pattern scan, graph slice, affected tests. | `repository-graph-analysis`, `validation-broker` |
| Stale context gate | Old summary, graph, report, validation, or prior approval is reused. | Refresh or downgrade the evidence. | Timestamp/order comparison, changed files, accepted/rejected claims, freshness limit. | `execution-trajectory-analysis` |
| Promotion review | Memory suggests durable docs, tests, registry, skill, or eval fixture. | Require maintainer approval and source placement rationale. | Confirmed pattern, owner, artifact path, validation plan, privacy review. | `skill-authoring-expert`, `change-documentation-gate` |

# Selection Rules
- Select this capability with `agent-execution-discipline` when repeated failure, fragile files, stale context, or stop-closure evidence affects execution discipline.
- Select it with `repository-context-map` and `repository-graph-analysis` when memory points to source areas, generated artifacts, owners, affected tests, or context-pack risk.
- Select it with `validation-broker` or `quality-test-gate` when previous failures or stale validation change command depth, freshness, or negative-evidence handling.
- Select it with `execution-trajectory-analysis` when repair order, validation order, repeated attempts, or review-after-repair must be reconstructed.
- Select it with `ai-code-review-refactor` when prior review findings, latest-commit follow-up, or fragile paths change review scope.

# Technical Selection Criteria
Evaluate memory use by event boundedness, privacy class, projection determinism, source freshness, graph impact, validation impact, trajectory impact, promotion authority, and closure risk. A memory claim is usable only as accepted current evidence, rejected, stale, or not verified; unclassified memory cannot support implementation or completion.

# Proactive Professional Triggers
- **Signal:** The plan repeats the same patch path or command after two failures. **Hidden risk:** the agent loops without a verified cause. **Required professional action:** record the repeat-failure gate, route to diagnosis, and change hypothesis or stop as blocked. **Route to:** `failure-diagnosis`, `agent-execution-discipline`. **Evidence required:** prior attempts, failure class, changed route, validator or blocked reason.
- **Signal:** A file is called fragile based on memory but current source, owners, generated status, or tests were not inspected. **Hidden risk:** stale memory either overconstrains safe work or misses a new source-of-truth boundary. **Required professional action:** read current source, build a bounded graph/context slice, scan same-pattern files, and map validators. **Route to:** `repository-graph-analysis`, `validation-broker`. **Evidence required:** inspected paths, graph freshness, accepted/rejected memory, validator mapping.
- **Signal:** A previous validation pass, review approval, or report is reused after later edits or compaction. **Hidden risk:** closure overclaims stale evidence. **Required professional action:** compare command order to final material changes and mark validation current, stale, partial, or not run. **Route to:** `execution-trajectory-analysis`, `validation-broker`. **Evidence required:** validation ledger, later edits, freshness verdict, residual risk.
- **Signal:** Memory is proposed as a new skill rule, registry trigger, eval fixture, or documentation requirement. **Hidden risk:** unreviewed operational memory becomes durable policy. **Required professional action:** require maintainer approval, placement rationale, privacy review, and validation before promotion. **Route to:** `skill-authoring-expert`, `change-documentation-gate`. **Evidence required:** confirmed source pattern, approval status, target artifact, tests/evals, rollback note.
- **Signal:** A memory projection accepts a prior graph, validation, or trajectory claim but omits why contrary or excluded events were rejected. **Hidden risk:** deterministic retrieval becomes selective hindsight. **Required professional action:** name included events, excluded events, accepted/rejected/stale verdicts, and what each verdict can and cannot prove. **Route to:** `repository-graph-analysis`, `plan-execution-consistency`. **Evidence required:** event ids or bounded classes, exclusion reason, source reconciliation, evidence limit.

# Risk Escalation Rules
- Escalate when memory suggests repeat failure and the current plan repeats the same route, patch path, or validator.
- Escalate when a fragile file lacks preflight inspection, owner/source-of-truth check, graph slice, same-pattern scan, or targeted validation.
- Escalate when stale context or memory projection is being used as current source evidence.
- Escalate to `security-privacy-gate` when a proposed event may include secrets, raw prompts, personal data, environment variables, credentials, full command output, or private archives.
- Escalate to a maintainer before promoting memory into docs, tests, registries, eval fixtures, skills, or source rules.

# Critical Details
- Append-only memory events are bounded facts: id, kind, path or artifact family, failure class, validation result, timestamp/order, privacy boundary, projection version, retention policy, and promotion status.
- Memory projection names retrieval key, included events, excluded events, summary, confidence, freshness limit, determinism version, and source reconciliation result.
- Coupling decisions can only widen graph/context scope, require direct source refresh, strengthen validation freshness, require trajectory review, or defer source promotion.
- Load [references/memory-event-privacy-retention.md](references/memory-event-privacy-retention.md) for event field, privacy, exclusion, and retention rules.
- Load [references/memory-graph-trajectory-coupling.md](references/memory-graph-trajectory-coupling.md) for graph, execution trajectory, validation freshness, and context-pack coupling.
- Load [references/memory-validation-promotion-gates.md](references/memory-validation-promotion-gates.md) for validator mapping, human promotion, rollback, and evidence-limit templates.

# Failure Modes
- **Auto-learning claim:** Memory is described as automatically updating source policy or runtime skill behavior.
- **Source substitution:** A memory summary replaces reading current repository files, registry entries, tests, reports, or generated source-of-truth.
- **Private data retention:** Raw prompt, full command output, secret, credential, environment variable, or personal data is stored as memory.
- **Repeat retry loop:** A third same-path attempt proceeds without new diagnosis, route, validation, or blocked handoff.
- **Selective projection:** Accepted memory events are cited while rejected, stale, superseded, privacy-excluded, or contrary events are omitted.
- **Ungoverned coupling:** Memory expands graph, validation, trajectory, or closure claims without naming source evidence and limits.
- **Unreviewed promotion:** Memory becomes docs, tests, registries, evals, skills, or policy without maintainer approval.
- **Validation bypass:** A memory signal changes closure risk but is not mapped to a validator, reviewer, owner response, or explicit residual risk.

# Reference Loading Policy
The `SKILL.md` body carries selection, gates, output, and closure rules. Load only the reference needed for the active memory decision:
- [references/memory-event-privacy-retention.md](references/memory-event-privacy-retention.md) when drafting an event, classifying privacy, excluding sensitive fields, or deciding retention.
- [references/memory-graph-trajectory-coupling.md](references/memory-graph-trajectory-coupling.md) when reconciling memory with repository graph, context pack, execution trajectory, stale validation, or compaction evidence.
- [references/memory-validation-promotion-gates.md](references/memory-validation-promotion-gates.md) when mapping accepted memory to validators, reviewer/owner response, rollback, human promotion, or final handoff limits.

# Output Contract
Return a `project_memory_governance_record` with:
- `mode_selected` (memory projection, repeat failure gate, fragile file gate, stale context gate, or promotion review).
- `boundaries_inspected` (current source, registry/config/docs, tests, reports, generated artifacts, graph slice, trajectory ledger, and skipped boundaries with reason).
- `memory_event` (bounded event facts, privacy class, retention boundary, promotion status, and excluded sensitive material).
- `memory_projection` (retrieval key, included/excluded events, projection version, summary, confidence, accepted/rejected/stale/not-verified verdict).
- `source_check` (current repository evidence that confirms, refutes, or limits each memory claim).
- `coupling_decision` (graph/context scope change, validation freshness requirement, trajectory review requirement, promotion path, or no-op).
- `changed_memory_to_validation_map` (each accepted memory signal mapped to validator, review check, owner response, or residual risk).
- `promotion_and_risk` (none, proposed, approved, rejected, owner, rollback note, memory gaps, privacy limits, stale projection, and next gate).
- `evidence_limits` (what evidence proves, what evidence does not prove, not-run or stale checks, unsupported owner or adapter evidence, and residual risk).
- `handoff` (owner skill, reviewer or maintainer, required next action, blocked condition, and accepted memory limit).

# Evidence Contract
Close memory governance only when these answers are concrete:
- **Basis:** memory signal, current request, affected path or artifact, and why the signal changes risk.
- **Privacy and retention:** what is stored, what is excluded, retention class, and why the event is safe to retain.
- **Current evidence and boundaries inspected:** source files, registry/config/docs, tests, reports, generated artifact source-of-truth, graph slice, trajectory, or owner evidence inspected.
- **What evidence proves:** the bounded memory claim accepted for the current task, the source fact that confirms it, and the validator/review obligation it changes.
- **What evidence does not prove:** behavior outside inspected boundaries, owners not contacted, stale reports, unrun validators, generated artifacts not rebuilt, or promotion not approved.
- **Coupling and validation:** accepted/rejected graph-memory-trajectory judgment, freshness verdict, validator/review mapping, and what remains not verified.
- **Promotion and closure:** maintainer approval state, durable artifact path if any, rollback note, residual risk, and next owner.

# Benchmark Coverage
This capability covers event-sourced memory discipline, deterministic retrieval, incident learning without auto-policy mutation, privacy-minimized retention, fragile-file governance, stale-context rejection, repeat-failure loop prevention, graph-memory-trajectory reconciliation, validation freshness, and human promotion into durable source artifacts.

# Routing Coverage
Routes from `change-forge-router`, `quality-test-gate`, `ai-code-review-refactor`, `change-documentation-gate`, `agent-execution-discipline`, and `skill-authoring-expert` should arrive here when memory affects scope, review depth, validation freshness, repeat-failure handling, or promotion. Route away when the primary need is raw source discovery, graph extraction, validation command brokering, failure diagnosis, or code review without a memory signal.

# Quality Gate
1. Memory events are append-only, bounded, classified, and privacy-reviewed.
2. Projection is deterministic and names included and excluded events.
3. Memory is not treated as source fact.
4. Repeat failure, fragile file, stale context, validation freshness, and privacy gates are evaluated when signals exist.
5. Privacy boundary excludes raw prompts, secrets, personal data, environment variables, credentials, private archives, and full command output.
6. Memory findings are reconciled with current source, graph/context freshness, validation evidence, and trajectory evidence before closure.
7. Promotion into source artifacts is human-approved or explicitly deferred/rejected.
8. Coupling decisions name the downstream skill, evidence it must inspect, and the memory limit it must not exceed.
9. Every accepted memory signal maps to validation, review, owner response, or residual risk.
10. Handoff states inspected evidence, unknowns, validation limits, rollback note, and next owner.

# Used By
`change-forge-router`, `quality-test-gate`, `ai-code-review-refactor`, `change-documentation-gate`, `agent-execution-discipline`, `skill-authoring-expert`.

# Handoff
Hand off gated memory findings to the owner skill with current-source evidence requirements and explicit limits. Hand off promotion candidates to a maintainer; do not edit durable policy automatically.

# Completion Criteria
The capability is complete when memory events are bounded, projections are deterministic, repeat failure/fragile/stale/privacy gates are evaluated, memory is reconciled with current source and graph/trajectory/validation evidence, promotion is governed by humans, and residual risk is explicit.
