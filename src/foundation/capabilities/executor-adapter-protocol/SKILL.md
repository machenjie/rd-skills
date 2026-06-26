---
name: executor-adapter-protocol
description: Defines runtime adapter contracts for ChangeForge hook events, capability degradation, evidence ledgers, gate results, and closure contracts across supported agent executors.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "123"
changeforge_version: 0.1.0
---

# Mission
Normalize executor-specific hook and telemetry events into a bounded ChangeForge runtime protocol so professional skills can reason about lifecycle state, permission state, evidence, validation freshness, gate results, and closure without depending on one agent runtime's event shape. The adapter protocol is a runtime evidence contract: it records what the executor can and cannot observe, degrades unsupported evidence honestly, and prevents adapter gaps from becoming false completion claims.

# When To Use
- When adding, reviewing, validating, or comparing Codex, Claude, Copilot, OpenHands, Gemini, Goose, or other executor hook integration.
- When an executor event must become `AdapterCapabilities`, `NormalizedEvent`, `LifecycleState`, `EvidenceLedger`, `GateResult`, or `ClosureContract`.
- When an executor lacks a hook event, permission signal, validation outcome, file/config change event, stop callback, checkpoint, compaction phase, or worktree lifecycle signal that another runtime supports.
- When final closure depends on what the runtime can observe, what it cannot observe, and how fail-open or fail-closed policy is configured.
- When permission/sandbox, execution trajectory, validation broker, workflow state, project memory, or repository graph evidence must be coupled without leaking raw runtime payloads.

# Do Not Use When
- The task is only static skill text with no runtime adapter, hook, event, permission, validation, telemetry, or closure behavior.
- The runtime event is already normalized, adapter capability parity is current, and no degradation or closure decision is affected.
- The task needs LLM routing policy or professional skill selection; the adapter protocol is runtime plumbing, not the router or an agent brain.
- The primary need is tool risk classification, validation command brokerage, trajectory reconstruction, or workflow state review without an adapter capability question.

# Stage Fit
- **Design/coding:** define adapter capability fields, normalized event shape, privacy boundary, fail policy, and recovery owner before hook-runtime code or template changes.
- **Code-review/refactoring:** compare raw event producers, hook templates, and consumers so adapter changes do not become router logic, skill selection, or unbounded telemetry.
- **Testing/validation:** prove permission, command outcome, changed path, stop, compaction, and validation visibility with adapter fixtures or explicit unsupported evidence.
- **Release/handoff:** require closure contracts to separate supported, partial, stale, unsupported, fail-open, and fail-closed evidence before installation or runtime rollout.
- **Debugging/incident/compaction:** reconstruct event order, degradation, missing fields, and residual risk when a runtime warning, stop failure, or compacted handoff weakens evidence.

# Non-Negotiable Rules
- Treat `AdapterCapabilities` as the source of runtime feature availability before event normalization or policy evaluation.
- Convert executor payloads into `NormalizedEvent` before downstream gates consume them.
- Record lifecycle transitions in `LifecycleState`; do not infer workflow state from raw executor event names in downstream gates.
- Store only bounded evidence facts in `EvidenceLedger`; exclude raw prompts, secrets, personal data, environment variables, credentials, and full command output.
- Express each gate decision as `GateResult` with outcome, reason, evidence references, fail policy, and degradation status.
- Build `ClosureContract` from supported adapter events only; unsupported, stale, partial, or low-visibility closure evidence must be disclosed.
- Apply fail-open behavior for advisory hooks unless a maintainer explicitly configured fail-closed behavior with recovery path.
- Unknown or unsupported event handling must degrade capability and record residual risk rather than pretending full coverage exists.

# Industry Benchmarks
Anchor against adapter capability negotiation, stable event normalization, audit evidence integrity, graceful degradation, fail-safe policy design, least-privilege telemetry, CI freshness controls, incident timeline reconstruction, and closure contracts. Keep the body focused on route-time decisions; load the reference only when concrete event fields, capability matrices, or output templates are needed.

# Mode Matrix
| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities |
| --- | --- | --- | --- | --- |
| Capability negotiation | New executor, changed hook support, adapter comparison, or parity question. | Declare supported/unsupported events and visibility before policy use. | Adapter name, event list, field visibility, degradation mode. | `agent-tool-permission-sandbox` |
| Event normalization | Raw hook payload is converted for gates. | Produce bounded `NormalizedEvent` and redact sensitive data. | Event kind, phase, paths, command class, permission/validation status. | `security-privacy-gate` |
| Lifecycle state coupling | Runtime events drive stage, trajectory, or workflow state. | Map events into legal lifecycle transitions. | Previous/next state, order, stage signal, unsupported transition. | `agent-workflow-state-machine`, `execution-trajectory-analysis` |
| Gate result degradation | Hook is advisory, unsupported, partial, failed, or fail-closed. | Preserve negative evidence and prevent false pass. | Gate name, outcome, reason, fail policy, residual risk. | `validation-broker`, `agent-execution-discipline` |
| Closure contract review | Final handoff depends on adapter evidence. | Separate supported checks from unsupported checks. | Closure checks, stale/partial status, next owner, evidence limits. | `plan-execution-consistency` |
| Privacy and retention review | Runtime payload may include prompts, secrets, paths, output, or user data. | Minimize telemetry and classify retention. | Bounded fields retained, excluded sensitive fields, redaction marker. | `project-memory-governance`, `security-privacy-gate` |

# Selection Rules
- Select this capability for `executor adapter`, `runtime adapter`, `adapter capabilities`, `AdapterCapabilities`, `NormalizedEvent`, `LifecycleState`, `EvidenceLedger`, `GateResult`, `ClosureContract`, fail-open, fail-closed, or `unsupported runtime event` signals.
- Select it with `agent-tool-permission-sandbox` when tool execution, permission decision, command risk, sandbox state, or approval visibility is part of normalization.
- Select it with `agent-workflow-state-machine` and `execution-trajectory-analysis` when lifecycle events affect stage legality, event ordering, compaction, repair/re-review, or stop closure.
- Select it with `validation-broker` when command outcome, validation freshness, stale evidence, unsupported validation fields, or stop-closure validation status depends on adapter visibility.
- Select it with `project-memory-governance` when runtime evidence may become bounded memory, behavior fixtures, fragile-file signals, or repeated-failure records.

# Technical Selection Criteria
Evaluate adapter evidence by executor support, event family, field visibility, payload boundedness, privacy class, permission visibility, command outcome visibility, path visibility, validation outcome visibility, lifecycle order confidence, checkpoint/rollback support, compaction direction, fail policy, degradation behavior, closure consequence, and maintainer recovery path. Adapter evidence is usable only as supported-current, supported-partial, unsupported, stale, degraded-warning, fail-closed-blocking, or not verified.

# Proactive Professional Triggers
- **Signal:** A runtime claims parity with another executor without an `AdapterCapabilities` diff.
  **Hidden risk:** missing event support makes downstream gates rely on silent or wrong evidence the runtime cannot emit.
  **Required professional action:** record supported and unsupported events before policy evaluation.
  **Route to:** `agent-tool-permission-sandbox`, `agent-execution-discipline`.
  **Evidence required:** adapter matrix, missing events, degradation mode, closure consequence.
- **Signal:** Raw hook payload includes prompt text, environment values, command output, credentials, personal data, or broad file dumps.
  **Hidden risk:** telemetry leaks sensitive runtime data into reports, memory, or handoff.
  **Required professional action:** normalize to bounded fields and redact before ledger storage.
  **Route to:** `security-privacy-gate`, `project-memory-governance`.
  **Evidence required:** retained fields, excluded fields, redaction marker, retention class.
- **Signal:** Validation or permission closure uses an adapter that cannot observe command outcome, permission decision, or changed paths.
  **Hidden risk:** unsupported or stale evidence is reported as passed or current.
  **Required professional action:** downgrade to partial/unsupported and route to validation broker or manual evidence.
  **Route to:** `validation-broker`, `quality-test-gate`.
  **Evidence required:** missing field, fallback evidence, stale/not-verified status.
- **Signal:** Fail-open advisory hook warns but final handoff omits the warning.
  **Hidden risk:** degraded runtime support silently disappears before closure.
  **Required professional action:** preserve warning in `GateResult` and closure residual risk.
  **Route to:** `agent-execution-discipline`, `plan-execution-consistency`.
  **Evidence required:** warning, gate outcome, residual risk, next owner.
- **Signal:** Fail-closed behavior blocks commands, installs, release validation, or hook runtime use without recovery path.
  **Hidden risk:** missing recovery path can block operators or force unsafe rollback bypass.
  **Required professional action:** require configured gate, reason, owner, and recovery path.
  **Route to:** `delivery-release-gate`, `quality-test-gate`.
  **Evidence required:** fail-closed rule, blocked action, operator recovery, rollback.
- **Signal:** Unknown executor event aborts routing, review, or validation.
  **Hidden risk:** unsupported runtime shapes create brittle hooks and unverified closure state.
  **Required professional action:** normalize to `Unknown`, degrade gate result, and preserve residual risk.
  **Route to:** `agent-workflow-state-machine`, `execution-trajectory-analysis`.
  **Evidence required:** event family guess, unsupported fields, safe fallback.

# Risk Escalation Rules
- Escalate to `security-privacy-gate` when adapter payloads may expose secrets, raw prompts, credentials, personal data, environment variables, full command output, connector data, or external side effects.
- Escalate to `delivery-release-gate` when adapter fail-closed behavior blocks release, install, packaging, deployment automation, or rollback validation.
- Escalate to `quality-test-gate` and `validation-broker` when unsupported events reduce validation freshness, affected-path mapping, or stop-closure certainty.
- Escalate to `agent-workflow-state-machine` when adapter lifecycle events cannot represent a required stage transition.
- Escalate to a maintainer when supporting a required lifecycle state would change the runtime contract, retention boundary, or fail policy.

# Critical Details
- Canonical events normalize session, prompt, route, tool, permission, validation, file/config, worktree, subagent, task, compaction, stop, and unknown executor signals.
- `AdapterCapabilities` names supported and unsupported events, field visibility, permission/validation support, stop handling, checkpoint/rollback, mode/role, codebase-index, path observation, and fail policy.
- `NormalizedEvent` preserves bounded facts only: event kind, phase, adapter, timestamp/order, stage signal, tool category, command class, bounded paths, validation status, permission decision, privacy class, and redaction marker.
- `LifecycleState` is action-aware; planning, read, edit, review, repair, validation, release, compaction, stop, and handoff remain separate states.
- Runtime capability degradation is evidence, not failure by itself; closure may proceed only when residual risk and unsupported checks are explicit.
- Fail-open still requires warning evidence; fail-closed requires configured gate, reason, owner, and operator recovery path.
- Load [references/adapter-event-contract.md](references/adapter-event-contract.md) for event families, field matrices, degradation rules, closure checks, and the output template.

# Failure Modes
- **Assumed parity:** A Copilot, Claude, or generic event is treated like a Codex pre-tool event even though the adapter marks it unsupported.
- **Raw event leakage:** Prompt text, environment variables, credentials, personal data, or command output is copied into evidence, reports, memory, or handoff.
- **False closure:** Stop closure claims complete validation when the runtime cannot observe command outcome, changed paths, or validation freshness.
- **Silent fail-open:** Advisory hooks degrade but no warning, `GateResult`, or residual risk reaches final handoff.
- **Brittle unknown event:** Unknown events abort routing instead of degrading to a known unsupported outcome.
- **Router confusion:** Adapter protocol is described as selecting skills or making LLM policy decisions rather than normalizing runtime evidence.
- **Validation visibility overclaim:** Adapter output reports a command as seen but cannot expose exit code, covered paths, artifact freshness, or later edits.
- **Compaction state loss:** Pre-compact or post-compact support is missing, so final handoff treats retained summaries as full trajectory evidence.

# Reference Loading Policy
The `SKILL.md` body carries selection, gates, output, and closure rules. Load [references/adapter-event-contract.md](references/adapter-event-contract.md) when drafting a concrete adapter record, comparing executor support, normalizing event fields, deciding fail policy, reconciling validation/permission visibility, or building a closure contract.

# Output Contract
Return an `executor_adapter_protocol_record` with:
- `mode_selected` (capability negotiation, event normalization, lifecycle state coupling, gate result degradation, closure contract review, or privacy and retention review).
- `boundaries_inspected` (executor runtime, hook templates, adapter matrix, permission fields, validation fields, path visibility, stop/compaction support, reports, graph/memory/trajectory consumers, and skipped boundaries with reason).
- `adapter_capabilities` (supported events, unsupported events, field visibility, command/path/validation/permission support, stop handling, checkpoint/rollback, mode/role/codebase-index support, degradation mode, and fail policy).
- `normalized_events` (stable event kind, bounded payload fields, source adapter, timestamp/order, stage signal, command class, validation/permission outcome, bounded paths, privacy class, and redaction marker).
- `lifecycle_state` (previous state, next state, legal transition status, unsupported transition fields, trajectory order confidence, and workflow-state consequence).
- `evidence_ledger` (bounded fact refs, source event ids, retained fields, excluded sensitive fields, redaction status, retention class, and evidence freshness).
- `gate_results` (gate name, outcome, reason, fail-open/fail-closed policy, degraded capability flags, owner, and recovery path).
- `closure_contract` (supported checks, unsupported checks, stale/partial/not-verified evidence, fallback/manual evidence, residual risk, rollback note, and next owner).
- `validation_evidence` (adapter fixture, validator command, report, artifact, output summary, exit code when visible, covered paths, freshness after final edit, and not-verified fields).
- `evidence_limits` and `residual_risk` (what adapter evidence proves, what it cannot observe, and the next gate).

# Evidence Contract
Close adapter-protocol review only when these answers are concrete:
- **Basis:** executor, event family, runtime contract change, and why adapter visibility affects closure.
- **Boundaries inspected and current evidence:** adapter capability matrix, hook templates, normalized field set, validation/permission visibility, trajectory/workflow consumers, reports, generated hook runtime artifacts, and skipped boundaries with reason.
- **Privacy boundary:** retained bounded fields, excluded sensitive fields, retention class, and redaction marker.
- **Degradation and fail policy:** unsupported fields, degraded gate result, fail-open warning or fail-closed recovery, and maintainer owner.
- **Validation evidence and what evidence proves:** command, validator, fixture, report, artifact, output summary, exit code when visible, covered paths, freshness, and the adapter claim each proves.
- **What evidence does not prove:** unsupported event families, hidden command output, unseen changed paths, missing permission decisions, unavailable stop/compaction state, and uninspected executors remain outside proof.
- **Closure and handoff:** supported/unsupported closure checks, validation freshness effect, residual risk, rollback note, handoff target, and next owner.

# Benchmark Coverage
This capability covers adapter capability negotiation, stable event normalization, bounded evidence ledgers, privacy-minimized telemetry, permission and validation visibility, lifecycle state coupling, graceful degradation, fail-open/fail-closed policy, unsupported event handling, and closure contracts.

# Routing Coverage
Routes from `change-forge-router`, `security-privacy-gate`, `delivery-release-gate`, `quality-test-gate`, `ai-code-review-refactor`, `change-documentation-gate`, `skill-authoring-expert`, and `agent-execution-discipline` should arrive here when runtime adapter evidence changes permission, validation, lifecycle, telemetry, fail policy, or closure obligations. Route away when the primary need is LLM routing, source graph extraction, validation command selection, memory projection, or workflow-state review without adapter visibility.

# Quality Gate
1. Adapter capabilities are declared before event normalization or downstream policy use.
2. Unknown or unsupported events produce degraded `GateResult`, not unstructured failure or silent success.
3. Evidence ledger entries contain bounded facts only and exclude raw prompts, secrets, personal data, environment variables, credentials, and full command output.
4. Normalized events state adapter, event kind, phase/order, privacy class, visible fields, and missing fields.
5. Lifecycle state distinguishes supported transitions, unsupported transitions, stale evidence, and closure consequence.
6. Closure contract separates supported checks, unsupported checks, stale/partial/not-verified evidence, fallback/manual evidence, residual risk, and next owner.
7. Fail-open or fail-closed behavior is explicit, owner-reviewed, recoverable, and validation-covered for changed runtime behavior.
8. Permission/sandbox and validation broker visibility are reconciled when commands, tools, paths, or validation outcomes are involved.
9. Adapter protocol is not described as an LLM, router, professional skill selector, or automatic policy learner.
10. Validation evidence records command or fixture, outcome, exit code when visible, covered paths, generated report/artifact, freshness, and unsupported fields.
11. Handoff states inspected evidence, unknowns, validation limits, rollback note, residual risk, and next owner.

# Used By
`change-forge-router`, `security-privacy-gate`, `delivery-release-gate`, `quality-test-gate`, `ai-code-review-refactor`, `change-documentation-gate`, `skill-authoring-expert`, `agent-execution-discipline`.

# Handoff
Hand off unsupported events, degraded gates, privacy limits, fail-closed policy changes, or closure gaps to the owning runtime maintainer, reviewer, validator, security gate, release gate, or documentation owner with `AdapterCapabilities`, `GateResult`, `ClosureContract`, rollback note, and residual risk attached.

# Completion Criteria
The capability is complete when executor events normalize through stable bounded contracts, runtime capability degradation is visible, privacy-sensitive payloads are excluded, fail policy is explicit, validation and permission visibility are reconciled, closure is bounded by adapter capabilities, and no unsupported event is treated as full evidence.
