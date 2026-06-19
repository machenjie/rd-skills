---
name: executor-adapter-protocol
description: Defines runtime adapter contracts for ChangeForge hook events, capability degradation, evidence ledgers, gate results, and closure contracts across supported agent executors.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "123"
changeforge_version: 0.1.0
---

# Executor Adapter Protocol

## Mission
Normalize executor-specific hook events into a bounded ChangeForge runtime protocol so professional skills can reason about lifecycle state, evidence, gates, and closure without depending on one agent runtime's event shape.

## When To Use
- When adding or reviewing Codex, Copilot, Claude, or other executor hook integration.
- When an event must be converted into `NormalizedEvent`, `LifecycleState`, `EvidenceLedger`, `GateResult`, or `ClosureContract`.
- When an executor lacks a hook event, capability, permission signal, or stop callback that another runtime supports.
- When final closure depends on what the runtime can actually observe.

## Do Not Use When
- The change is only static skill text with no runtime adapter, hook, event, or closure behavior.
- The runtime event has already been normalized and no capability degradation or closure decision is affected.
- The task needs LLM routing policy; the adapter protocol is runtime plumbing, not the router.

## Non-Negotiable Rules
- Treat `AdapterCapabilities` as the source of runtime feature availability.
- Convert executor payloads into `NormalizedEvent` before policy evaluation.
- Record lifecycle transitions in `LifecycleState`; do not infer state from raw executor names in downstream gates.
- Store only bounded evidence facts in `EvidenceLedger`, never raw prompts, secrets, full command output, or environment dumps.
- Express each gate decision as `GateResult` with outcome, reason, evidence references, and degradation status.
- Build `ClosureContract` from supported adapter events only; unsupported closure evidence must be disclosed.
- Apply fail-open behavior for advisory hooks unless a maintainer explicitly configured fail-closed behavior.
- Unsupported event handling must degrade capability and record residual risk rather than pretending full coverage exists.

## Industry Benchmarks
- **Adapter capability negotiation**: Runtime behavior is selected from declared capabilities, not assumed parity.
- **Event normalization**: Downstream policy consumes stable event contracts instead of executor-specific payloads.
- **Audit evidence integrity**: Gate outcomes reference bounded evidence entries.
- **Graceful degradation**: Missing runtime support is explicit and does not create false completion claims.
- **Fail-safe policy design**: Fail-open and fail-closed choices are named, justified, and test-covered.

## Selection Rules
- Select this capability for `executor adapter`, `runtime adapter`, `adapter capabilities`, `normalized event`, `closure contract`, or `unsupported runtime event` signals.
- Select it with `agent-tool-permission-sandbox` when tool execution, permission, or sandbox state is part of normalization.
- Select it with `validation-broker` when closure depends on parsed validation outcomes.
- Select it with `execution-trajectory-analysis` when lifecycle transitions need sequence review.

## Risk Escalation Rules
- Escalate to `security-privacy-gate` when adapter events may expose secrets, raw prompts, credentials, personal data, or external side effects.
- Escalate to `delivery-release-gate` when fail-closed behavior blocks release, install, or deployment automation.
- Escalate to `quality-test-gate` when unsupported events reduce validation freshness or stop-closure certainty.
- Escalate to a maintainer when an adapter cannot represent a required lifecycle state without changing the runtime contract.

## Critical Details
- Canonical event names are `SessionStart`, `UserPromptSubmit`, `UserPromptExpansion`, `PreToolUse`, `PermissionRequest`, `PostToolUse`, `PostToolUseFailure`, `PostToolBatch`, `Stop`, `StopFailure`, `SessionEnd`, `SubagentStart`, `SubagentStop`, `TaskCreated`, `TaskCompleted`, `FileChanged`, `ConfigChanged`, `WorktreeCreate`, `WorktreeRemove`, `PreCompact`, `PostCompact`, `Compact`, and `Unknown`.
- `Compact` is backward-compatible; new adapters should prefer `PreCompact` and `PostCompact` when the runtime exposes direction-specific compaction phases.
- `AdapterCapabilities` must name supported/unsupported lifecycle hooks, permission fields, validation fields, stop handling, checkpoint/rollback support, mode/role support, codebase index support, visibility fields, and degradation modes.
- `NormalizedEvent` should preserve only bounded facts: event kind, lifecycle cadence, executor event name/phase, tool category, command risk/outcome, exit code, bounded read/changed/deleted/generated paths, validation status, permission decision, checkpoint/rollback signal, timestamp, stage signal, adapter name, and privacy redaction markers.
- `LifecycleState` is action-aware: planning, read, edit, review, repair, test, release, stop, compaction, and handoff are distinct states.
- Runtime capability degradation is evidence, not failure by itself; closure may proceed only with residual risk disclosure.
- Fail-open policy still requires warning evidence and must not be reported as a hard pass.
- Fail-closed policy requires an explicit configured gate, reason, and operator-facing recovery path.

## Failure Modes
- **Assumed parity**: A Copilot event is treated like a Codex pre-tool event even though the adapter marks it unsupported.
- **Raw event leakage**: Prompt text, environment variables, or command output is copied into the evidence ledger.
- **False closure**: Stop closure claims complete validation when the runtime cannot observe validation results.
- **Silent fail-open**: Advisory hooks degrade but no warning or residual risk reaches the handoff.
- **Unsupported event crash**: Unknown events abort routing instead of degrading to a known unsupported outcome.

## Output Contract
Return an `executor_adapter_protocol_record` with:
- **AdapterCapabilities**: supported events, unsupported events, explicit feature booleans, command/path/validation visibility, permission fields, stop handling, and degradation mode.
- **NormalizedEvent**: stable event kind, bounded payload fields, source adapter, timestamp, stage signal, validation outcome, permission outcome, rollback/checkpoint signal, and privacy redaction markers.
- **LifecycleState**: previous state, next state, legal transition status, and evidence reference.
- **EvidenceLedger**: bounded facts, source event ids, redaction status, and privacy boundary.
- **GateResult**: gate name, outcome, reason, fail-open/fail-closed policy, and degraded capability flags.
- **ClosureContract**: supported closure checks, unsupported checks, residual risk, and next owner.

## Quality Gate
1. Adapter capabilities are declared before event normalization.
2. Unknown or unsupported events produce a degraded `GateResult`, not unstructured failure.
3. Evidence ledger entries contain bounded facts only.
4. Closure contract distinguishes supported checks, unsupported checks, stale evidence, and residual risk.
5. Fail-open or fail-closed behavior is explicit and test-covered.
6. The adapter protocol is not described as an LLM, router, or professional skill selector.

## Used By
- `change-forge-router`
- `security-privacy-gate`
- `delivery-release-gate`
- `quality-test-gate`
- `ai-code-review-refactor`
- `change-documentation-gate`
- `agent-execution-discipline`

## Handoff
Hand off unsupported events, degraded closure, or fail-closed policy changes to the owning runtime maintainer, with `AdapterCapabilities`, `GateResult`, and residual risk attached.

## Completion Criteria
The capability is complete when executor events normalize through stable contracts, degraded runtime support is visible, closure is bounded by adapter capabilities, and no unsupported event is treated as full evidence.
