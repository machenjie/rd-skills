# Adapter Event Contract

Use this reference when adding or reviewing executor adapter fields, unsupported event handling, event normalization, permission/validation visibility, fail-open/fail-closed policy, privacy retention, or closure contract behavior. The `SKILL.md` body remains the route-time contract; this file is loaded only for concrete adapter records or reviews.

# Adapter Capability Fields

| Field | Required content | Closure effect |
| --- | --- | --- |
| `adapter_name` | Runtime/executor name and version when available. | Identifies which event semantics apply. |
| `supported_events` | Canonical events the adapter can observe. | May support closure checks for those event families. |
| `unsupported_events` | Canonical events the adapter cannot observe. | Must degrade related gates and closure checks. |
| `field_visibility` | Which fields are full, partial, none, or unsupported. | Prevents overclaiming command, path, validation, or permission evidence. |
| `permission_support` | Permission request, decision, prompt, denial, or approval visibility. | Drives `agent-tool-permission-sandbox` evidence strength. |
| `validation_support` | Command outcome, validation status, exit code, artifact, or output summary visibility. | Drives `validation-broker` freshness and outcome confidence. |
| `path_visibility` | Read, changed, deleted, generated, config, worktree, or unknown path observation. | Drives repository graph and plan consistency. |
| `stop_support` | Stop, stop failure, closure package, and final handoff visibility. | Drives closure contract confidence. |
| `checkpoint_support` | Checkpoint, rollback, worktree lifecycle, or recovery marker support. | Drives rollback and release evidence limits. |
| `privacy_boundary` | Retained fields, excluded fields, redaction marker, retention class. | Prevents sensitive payload retention. |
| `fail_policy` | Fail-open advisory, fail-closed blocking, owner, and recovery path. | Defines whether degraded evidence warns or blocks. |

# Canonical Event Families

| Family | Events | Required normalization | Common missing evidence |
| --- | --- | --- | --- |
| Session and task | `SessionStart`, `SessionEnd`, `TaskCreated`, `TaskCompleted` | Session/task ids when available, bounded state, adapter name, timestamp/order. | Task lifecycle in lightweight runtimes. |
| Prompt and route | `UserPromptSubmit`, `UserPromptExpansion` | Route/stage signal only; no raw prompt body in evidence. | Prompt expansion or route metadata. |
| Tool and permission | `PreToolUse`, `PermissionRequest`, `PostToolUse`, `PostToolUseFailure`, `PostToolBatch` | Tool kind, command risk, sandbox/permission decision, bounded paths, exit/outcome when available. | Permission decision, batch contents, failed tool details. |
| Validation and command | `PostToolUse`, `PostToolUseFailure`, `Stop` | Command class, exit/outcome summary, validation status, artifacts, bounded output summary. | Exit code, command scope, freshness relation. |
| File and config | `FileChanged`, `ConfigChanged`, `WorktreeCreate`, `WorktreeRemove` | Path class, generated/source status, checksum/order or bounded path, no file dump. | Config drift, generated artifact changes, worktree lifecycle. |
| Subagent and compaction | `SubagentStart`, `SubagentStop`, `PreCompact`, `PostCompact`, `Compact` | Delegation/compaction phase, supported fields, degraded fields, retained bounded facts. | Direction-specific compaction, subagent result details. |
| Stop and unknown | `Stop`, `StopFailure`, `Unknown` | Closure checks, unsupported checks, residual risk, safe degradation. | Final validation state, residual risk, stop failure cause. |

# Normalization Pipeline

1. Identify executor adapter and raw event family.
2. Compare raw event against `AdapterCapabilities` before policy evaluation.
3. Classify field visibility as `full`, `partial`, `none`, or `unsupported`.
4. Extract only bounded fields needed by selected gates.
5. Redact or omit raw prompt body, secrets, personal data, environment variables, credentials, full command output, and broad file dumps.
6. Emit `NormalizedEvent` with event kind, phase/order, adapter, timestamp/order, stage signal, command class, bounded paths, validation status, permission decision, privacy class, and missing-field list.
7. Update `LifecycleState` only from normalized events and declared capability support.
8. Emit `GateResult` for supported, degraded, fail-open, fail-closed, failed, stale, or unsupported evidence.
9. Build `ClosureContract` from supported checks plus explicit unsupported checks and residual risk.

# Gate Result Outcomes

| Outcome | Meaning | Required fields |
| --- | --- | --- |
| `pass-current` | Supported evidence is current and covers the requested check. | Evidence refs, scope, freshness. |
| `pass-degraded` | Advisory hook permits progress with warning/residual risk. | Missing fields, warning, next owner. |
| `partial` | Some required fields are available but not all. | Available fields, missing fields, fallback evidence. |
| `unsupported` | Adapter cannot observe the needed event or field. | Unsupported event/field, closure consequence. |
| `stale` | Evidence predates later material changes. | Event order, later edits, next validator. |
| `fail-open-warning` | Fail-open policy allowed continuation. | Policy, warning text summary, residual risk. |
| `fail-closed-blocked` | Configured gate blocks continuation. | Gate, reason, owner, recovery path. |
| `not-verified` | Adapter evidence cannot prove the claim. | Required manual evidence or next gate. |

# Capability Degradation Rules

1. Declare supported and unsupported events before policy evaluation.
2. Unsupported events produce degraded `GateResult`, not silent success.
3. Partial field visibility downgrades proof even when the event itself is supported.
4. Fail-open needs warning evidence and residual risk in final handoff.
5. Fail-closed needs configured gate, reason, owner, and operator recovery path.
6. Closure can only claim evidence the adapter can observe or manual fallback evidence explicitly supplies.
7. Evidence ledgers store bounded facts, redaction state, and references, not raw prompts, secrets, personal data, environment variables, credentials, or full command output.

# Closure Checks

| Closure check | Supported evidence | Unsupported consequence |
| --- | --- | --- |
| Requirement/route state | Route/stage manifest event or bounded prompt signal. | Require manual route manifest in handoff. |
| Read-before-edit | Read path visibility and changed path visibility. | Require direct source-read summary and diff inventory. |
| Permission/sandbox | Permission request/decision, sandbox mode, command risk. | Mark permission evidence partial and route to sandbox record. |
| Validation freshness | Command outcome, covered paths, order after final edits. | Mark validation not verified or require manual command evidence. |
| Repair/re-review | Review finding, repair event, re-review event. | Require manual repair ledger. |
| Stop residual risk | Stop event with closure package or explicit handoff. | Require final handoff residual risk outside adapter. |
| Rollback/checkpoint | Checkpoint or rollback marker. | Require rollback note and owner. |

# Privacy and Retention Ledger

| Payload class | Keep | Exclude |
| --- | --- | --- |
| Prompt | Route/stage signal and bounded classification. | Raw prompt body and hidden instructions. |
| Command | Program/action class, risk class, outcome summary. | Full command output, secrets, environment values. |
| Paths | Bounded read/changed/generated path families. | Full file dumps or unrelated directory inventory. |
| Validation | Command class, exit/outcome, freshness, artifacts. | Full logs unless explicitly needed and redacted. |
| Connector/MCP | Connector class, operation class, approval state. | Personal data, broad mailbox/docs content, credentials. |
| Memory candidate | Structural bounded facts and promotion status. | Private archives, raw transcript, full command output. |

# Adapter Parity Review

When comparing executors, use this checklist:

1. List supported and unsupported canonical events per adapter.
2. Compare field visibility for command outcome, permission decision, changed paths, validation status, stop handling, and compaction direction.
3. Identify which professional gates degrade for each missing field.
4. State whether degradation is fail-open warning, fail-closed block, partial evidence, unsupported, or not verified.
5. Name manual fallback evidence needed for closure.
6. Confirm the adapter is not being used as a router, LLM, or automatic skill selector.

# Output Template

```yaml
executor_adapter_protocol_record:
  mode_selected: closure contract review
  boundaries_inspected:
    executor_runtime: codex
    hook_templates: [path/or/surface]
    adapter_matrix: current
    permission_fields: full|partial|none|unsupported
    validation_fields: full|partial|none|unsupported
    path_visibility: full|partial|none|unsupported
    stop_compaction_support: full|partial|none|unsupported
    skipped_boundaries: [boundary with reason]
  adapter_capabilities:
    adapter_name: codex
    supported_events: []
    unsupported_events: []
    field_visibility:
      command_outcome: partial
      permission_decision: partial
      changed_paths: partial
      validation_status: partial
    fail_policy: fail-open-warning
    owner: runtime-maintainer
  normalized_events:
    - event_kind: PreToolUse
      phase: before-action
      adapter: codex
      bounded_payload: [tool_kind, command_risk, path_family]
      missing_fields: []
      privacy_class: bounded
      redaction_marker: sensitive-fields-excluded
  lifecycle_state:
    previous_state: read
    next_state: edit
    legal_transition: allowed|blocked|not-verified
    unsupported_transition_fields: []
  evidence_ledger:
    retained_fields: [event_kind, path_family, command_class]
    excluded_fields: [raw_prompt, secrets, environment_variables, full_command_output]
    freshness: current|stale|partial|not-verified
  gate_results:
    - gate: permission-sandbox
      outcome: pass-degraded
      reason: permission decision partially visible
      fail_policy: fail-open-warning
      owner: agent-tool-permission-sandbox
      recovery_path: manual permission record
  closure_contract:
    supported_checks: []
    unsupported_checks: []
    fallback_manual_evidence: []
    status: ready|partial|needs-validation|blocked|not-verified
    rollback_note: [reversal path]
    residual_risk: [risk]
    next_owner: [owner]
```
