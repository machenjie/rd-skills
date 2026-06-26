---
name: agent-tool-permission-sandbox
description: Classifies agent tool, command, edit, permission, sandbox, destructive-action, secret-exposure, and external-side-effect risks before execution and handoff.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "120"
changeforge_version: 0.1.0
---

# Mission
Classify agent tool, shell command, file edit, MCP/connector, permission prompt, sandbox, and external side-effect risk before execution or closure. The capability turns tool use into a bounded professional record: what action is intended, what authority is available, what can mutate, what can leak, how rollback works, which gate owns the decision, and what evidence remains unsupported.

# When To Use
- Before shell commands, permission prompts, tool calls, apply patches, install/build scripts, deploy commands, migrations, cleanup commands, connector actions, or generated artifact writes.
- When a command can delete, overwrite, move, publish, deploy, push, install, change permissions, access secrets, use network, mutate external systems, or expose untrusted output.
- When sandbox mode, approval policy, MCP tool trust, runtime hook warning, bounded telemetry, final handoff, or validation freshness depends on tool behavior.
- When project memory, repository graph, executor adapter, workflow state, trajectory, or validation broker evidence references a risky action.

# Do Not Use When
- The work is purely read-only with ordinary file reads/searches and no secret-bearing output, network-write, external service, or mutation exposure.
- A deterministic local validation command writes only normal caches and a higher gate already produced an equivalent current permission, boundary, rollback, and residual-risk record.
- The primary question is CLI design, release sequencing, validation command selection, authentication policy, or secret rotation design without an agent tool/sandbox decision.

# Stage Fit
Use during read, planning, coding, debugging, bug-fix, code-review, refactoring, testing, release, repair, validation, stop, compaction, and handoff stages when the next action or closure claim depends on authority, sandboxing, side effects, output sensitivity, or rollback. Re-enter after a route change, sandbox/approval change, command argument change, target boundary change, failed risky command, or final material edit that invalidates previous permission evidence.

# Non-Negotiable Rules
- Classify every relevant tool/action before execution by write scope, destructive potential, external side effect, secret exposure, network behavior, privilege, target boundary, idempotency, rollback need, and closure consequence.
- Do not store raw prompts, secrets, personal data, environment values, credentials, full command arguments, or full command output in state, memory, telemetry, reports, or handoff.
- Use least-privilege execution and existing sandbox controls; do not bypass approval policy, tool policy, connector scope, or user intent.
- Destructive-local actions require target confirmation, preview or dry-run when available, restore path, and residual risk.
- External-write actions such as deploy, push, publish, send, migrate, rotate, delete, mutate issue/email/cloud/db, or package release require owner evidence plus security, release, or reliability gate alignment.
- Secret-sensitive and untrusted-output actions require redaction rules before output is viewed, summarized, stored, or passed to memory.
- Runtime hook warnings remain deterministic, bounded, and fail-open unless a maintainer explicitly configured stricter behavior with recovery path.
- Unsupported adapter, sandbox, permission, or connector visibility degrades evidence; it never proves that the action is safe.

# Industry Benchmarks
Anchor against least privilege, separation of duties, change-management approval, NIST SSDF credential protection, SRE release safety, supply-chain trust-boundary review, secure logging/redaction, incident rollback readiness, and audit-ready evidence retention. Keep the body focused on route-time decisions; load the reference only when a concrete risk matrix or closure record is needed.

# Mode Matrix
| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities |
| --- | --- | --- | --- | --- |
| Read-only inspection | File search/read, report parse, local metadata inspection, no secret-bearing output. | Bound scope and avoid overclaiming harmlessness. | Paths/classes inspected, output sensitivity, no-write statement. | `repository-graph-analysis` |
| Local-write/edit | Patch, format, generated report, build cache, dist artifact, hook support artifact. | Confirm source-of-truth boundary and rollback/revert path. | Target files, generated outputs, revert path, later validation need. | `plan-execution-consistency` |
| Destructive-local gate | Delete, clean, reset, overwrite, move, chmod, chown, force, broad glob. | Prevent wrong-target loss and repeated destructive attempts. | Target proof, dry-run/preview status, restore plan, owner. | `cleanup-deletion-governance` |
| External-read/connector gate | MCP/app/API/cloud/issue/email reads or untrusted data fetch. | Bound data access and retention. | Account/data boundary, query scope, redaction, retention class. | `security-privacy-gate` |
| External-write/release gate | Push, publish, deploy, send, migrate, rotate, mutate cloud/db/issue/email/package. | Require owner, release/security alignment, and compensation path. | Approval/result, target environment, rollback/compensation, gate owner. | `delivery-release-gate` |
| Secret-sensitive output gate | Env, token, key, credential, private data, raw tool output, prompt/tool transcript. | Exclude raw sensitive values from evidence and memory. | Retained fields, excluded fields, redaction marker, next owner. | `secret-configuration-security` |

# Selection Rules
- Select this capability for permission events, risky pre-tool warnings, release commands, destructive cleanup, migrations, install scripts, external writes, untrusted connectors, secret-bearing commands, broad filesystem edits, or missing sandbox evidence.
- Select it with `security-privacy-gate` when secrets, credentials, permissions, user data, prompt/tool output, connector data, untrusted output, auth context, or retention policy is involved.
- Select it with `delivery-release-gate` when deploy, push, publish, migration, package, build artifact, install, rollback, or environment mutation behavior is involved.
- Select it with `executor-adapter-protocol` when permission decisions, sandbox state, command outcome, changed paths, or validation visibility arrive through runtime hooks.
- Select it with `agent-workflow-state-machine` and `execution-trajectory-analysis` when the timing of tool use affects legal stage transition, repeated failure, repair, validation freshness, or closure.
- Select it with `validation-broker` when validation commands, generated reports, build outputs, or not-run/fail/stale status must be mapped to changed paths.
- Select it with `project-memory-governance` when bounded tool-risk facts may be retained as memory, fragile-file signal, repeated-failure fact, or future warning.

# Technical Selection Criteria
Evaluate action safety by executable/tool family, argument sensitivity, target boundary, write radius, external system authority, network direction, privilege level, sandbox mode, approval policy/result, connector trust, data classification, idempotency, dry-run support, rollback/restore path, owner confirmation, output retention, adapter visibility, validation freshness, and closure consequence. Classify evidence only as current-supported, current-partial, stale, not-run, denied, failed, unsupported, secret-redacted, rollback-unverified, or unsafe-to-run.

# Proactive Professional Triggers
- **Signal:** A command includes delete, remove, overwrite, reset, clean, force, chmod, chown, sudo, migrate, apply, deploy, push, publish, rotate, live endpoint, token, key, secret, credential, or broad glob language.
  **Hidden risk:** An agent mutates or destroys the wrong target.
  **Required professional action:** Classify risk, verify target, require preview/dry-run when available, and name rollback.
  **Route to:** `security-privacy-gate`, `delivery-release-gate` when external.
  **Evidence required:** Action class, target boundary, preview/dry-run status, rollback, residual risk.
- **Signal:** Sandbox is disabled, broad, unknown, or insufficient for the intended write.
  **Hidden risk:** Local action writes the wrong repository path or generated-output boundary.
  **Required professional action:** Narrow scope, record sandbox/approval state, or stop with blocked handoff.
  **Route to:** `agent-workflow-state-machine`, `plan-execution-consistency`.
  **Evidence required:** Sandbox mode, approval policy/result, affected path map, not-run/blocked decision.
- **Signal:** Tool output can contain prompts, environment values, credentials, personal data, private data, source-control tokens, cloud identifiers, or full command logs.
  **Hidden risk:** Evidence capture leaks sensitive data into reports, memory, or final notes.
  **Required professional action:** Require redaction before capture, classify retention, and retain bounded facts only.
  **Route to:** `secret-configuration-security`, `project-memory-governance`.
  **Evidence required:** Retained output fields, excluded fields, redaction marker, retention report.
- **Signal:** MCP/app/connector action has broad account access or unclear operation scope.
  **Hidden risk:** The agent leaks private data or mutates the wrong account beyond user intent.
  **Required professional action:** Classify and document data boundary, action boundary, operation class, and allowed write/read scope before use.
  **Route to:** `security-privacy-gate`.
  **Evidence required:** Connector scope map, account/data class, requested operation, disallowed operations, residual risk.
- **Signal:** Validation, report generation, build, or install writes files after earlier approval.
  **Hidden risk:** Closure cites stale permission or validation evidence.
  **Required professional action:** Compare command order, verify mapped validators, and disclose stale or partial closure when rerun is unavailable.
  **Route to:** `validation-broker`, `quality-test-gate`.
  **Evidence required:** Command order, changed outputs, validator coverage, freshness verdict.
- **Signal:** Runtime adapter cannot observe permission result, changed paths, command outcome, or stop callback.
  **Hidden risk:** Missing adapter visibility creates stale approval evidence.
  **Required professional action:** Document degraded visibility, require manual tool record, and verify closure wording stays partial.
  **Route to:** `executor-adapter-protocol`, `agent-execution-discipline`.
  **Evidence required:** Adapter support matrix, missing adapter field, fallback evidence report, closure consequence.

# Risk Escalation Rules
- Escalate to `security-privacy-gate` for secrets, credentials, auth context, user data, personal data, private data, untrusted output, connector data, prompt/tool transcript, raw command output, or broad read access.
- Escalate to `secret-configuration-security` for keys, tokens, env vars, cloud credentials, signing material, CI secrets, vault/KMS access, or config files that can carry secrets.
- Escalate to `delivery-release-gate` for deploy, publish, push, migration, package release, production config, feature flag, rollback, install, or generated runtime artifact behavior.
- Escalate to `reliability-observability-gate` when a command can stress production, change telemetry, alter capacity, affect incident response, or mutate live operational state.
- Escalate to `validation-broker` when command execution changes validation freshness, report outputs, generated artifacts, or test/build/install proof.
- Escalate to maintainer/user approval when target boundary, external account, production environment, destructive scope, or rollback path cannot be independently verified.

# Critical Details
- Shell command risk depends on both executable and arguments; record only bounded program/action classes when arguments can contain sensitive data.
- File edits can be risky without shell commands when they touch registries, hooks, release scripts, install scripts, security policy, generated/runtime artifacts, or distribution outputs.
- "Dry run available" is not the same as "dry run executed"; approval authorizes an action class but does not prove correctness.
- Read-only is a conclusion, not a default. A read can still be secret-sensitive if output contains credentials, private data, or full logs.
- Network access is not automatically external-write; classify direction, endpoint, data class, and mutation ability.
- Generated reports and dist outputs can be local-write evidence and may require freshness validation even when source markdown is the only manual edit.
- Fail-open runtime warnings provide advisory context and never mutate project source.
- Load [references/tool-risk-boundary-matrix.md](references/tool-risk-boundary-matrix.md) for detailed risk classes, controls, telemetry boundaries, and closure template.
- Load [references/connector-output-retention-boundary.md](references/connector-output-retention-boundary.md) when connector data, untrusted output, account scope, redaction, retention, or memory handoff is in scope.
- Load [references/permission-validation-freshness.md](references/permission-validation-freshness.md) when permission evidence, generated outputs, validation order, trajectory, or plan-execution consistency affects final closure.

# Failure Modes
- **Destructive command without target proof:** A cleanup, reset, overwrite, or broad glob removes files outside intended scope.
- **Secret exposure:** Full command output, env values, raw prompts, credentials, personal data, or connector payloads enter memory, reports, or final notes.
- **Approval bypass:** A tool runs an external write after policy denied permission, did not request approval, or exceeded the approved operation class.
- **Untrusted connector overreach:** A broad connector reads or writes account data outside the user-intended boundary.
- **Rollback gap:** A migration, deploy, publish, package, or cleanup action runs with no tested rollback, compensation, backup, or restore path.
- **Stale permission evidence:** Validation/build/report generation writes after approval, but final closure treats the earlier record as current.
- **Adapter overclaim:** Unsupported permission, sandbox, path, or command-outcome visibility is reported as full evidence.
- **Telemetry bloat:** Full commands or logs are retained instead of bounded action facts, making the capability unsafe and inefficient.

# Reference Loading Policy
The `SKILL.md` body carries routing, selection, gate, evidence, and closure rules. Load only the reference needed for the active decision:
- [references/tool-risk-boundary-matrix.md](references/tool-risk-boundary-matrix.md) when drafting a concrete tool record, classifying a risky command, comparing sandbox/approval states, reviewing connector scope, handling secret-sensitive output, or preparing a final handoff with residual risk.
- [references/connector-output-retention-boundary.md](references/connector-output-retention-boundary.md) when MCP/app/API connector data, untrusted output, account scope, redaction, retention, or project-memory handoff must be bounded.
- [references/permission-validation-freshness.md](references/permission-validation-freshness.md) when validation, build, report, dist, package, install, trajectory, or plan-execution evidence can become stale after tool use or generated writes.

# Output Contract
Return a `tool_permission_sandbox_record` with:
- `mode_selected` (read-only inspection, local-write/edit, destructive-local gate, external-read/connector gate, external-write/release gate, or secret-sensitive output gate).
- `action_summary` (bounded tool/program/action class, not full arguments when they may contain sensitive data).
- `risk_classification` (risk class, trigger signals, write radius, external side effect, secret sensitivity, privilege, connector trust, network direction, and production effect).
- `sandbox_and_approval` (sandbox mode, approval policy, permission result, denied/not-requested/not-needed reason, adapter visibility, and missing evidence).
- `target_boundary` (files, directories, generated outputs, services, environments, accounts, data classes, or external systems in scope and explicitly out of scope).
- `side_effect_inventory` (filesystem, network, database, source control, deploy, package, email, connector, cloud, telemetry, memory, or report effects).
- `controls_and_rollback` (dry-run/preview/backup/restore/rollback/compensation/idempotency/rate-limit/owner confirmation and whether each was available, executed, skipped, or not verified).
- `telemetry_boundary` (bounded facts retained, sensitive facts excluded, redaction marker, retention class, and memory/report policy).
- `validation_and_closure` (mapped validators, freshness status, not-run/failed/stale/partial commands, next gate, residual risk, and handoff owner).
- `evidence_limits` (boundaries inspected, what evidence proves, what evidence does not prove, unsupported adapter/tool visibility, and unknowns).
- `handoff` (approved, blocked, not-run, partial, or reroute decision; owner skill; reviewer gate; required next action).

# Evidence Contract
Close a tool-permission review only when these answers are concrete:
- **Basis:** requested action, risk trigger, target boundary, and why sandbox/approval affects execution or closure.
- **Current evidence:** command/tool class, inspected files, registry or route caller, sandbox mode, approval policy/result, connector scope, and adapter visibility.
- **Safety controls:** dry-run/preview/backup/rollback/idempotency/rate limit/owner confirmation and which controls were actually executed.
- **Privacy boundary:** retained bounded fields, excluded raw prompts/secrets/env/credentials/personal data/full arguments/full output, redaction marker, and retention class.
- **Boundaries inspected:** in-scope and out-of-scope files, generated outputs, accounts, connectors, services, data classes, route caller, and validation surfaces.
- **What evidence proves / does not prove:** current permission, sandbox, target, rollback, privacy, and validation claims supported by evidence, and the behavior, external state, production safety, or adapter visibility the evidence does not prove.
- **Closure:** validation freshness, unsupported evidence, rollback note, residual risk, and next gate or owner.

# Benchmark Coverage
This capability covers least-privilege execution, destructive-action confirmation, approval-policy adherence, sandbox boundary review, connector trust scoping, secret-safe telemetry, untrusted-output handling, rollback readiness, validation freshness coupling, runtime adapter degradation, and audit-ready handoff.

# Routing Coverage
Routes from `change-forge-router`, `security-privacy-gate`, `delivery-release-gate`, `reliability-observability-gate`, `quality-test-gate`, `ai-code-review-refactor`, `skill-authoring-expert`, and `agent-execution-discipline` should arrive here when tool execution, command risk, permission state, sandbox boundary, external side effect, secret-sensitive output, connector trust, or risky closure evidence is at issue. Route away when the primary need is designing the CLI itself, implementing auth policy, choosing validation commands, or modeling release sequence without an agent tool/sandbox decision.

# Quality Gate
1. Risk class is explicit before execution, validation, or handoff.
2. Sandbox and approval state are stated without bypassing policy.
3. Target boundary includes in-scope and out-of-scope files, services, accounts, data classes, or environments.
4. Destructive-local actions have target confirmation, preview/dry-run status, restore plan, and residual risk.
5. External-write actions have owner/gate evidence, rollback or compensation path, and release/security alignment.
6. Secret-sensitive actions exclude raw prompts, secrets, env values, credentials, personal data, full arguments, and full output.
7. Untrusted tools/connectors have data access boundary, action scope, allowed operations, and retention policy.
8. Runtime adapter or hook visibility gaps downgrade evidence rather than proving approval.
9. Validation freshness is recalculated after final material source, registry, report, dist, package, or install-output edits.
10. Final handoff states inspected evidence, unknowns, validation limits, rollback note, residual risk, and next owner.

# Used By
`change-forge-router`, `security-privacy-gate`, `delivery-release-gate`, `reliability-observability-gate`, `quality-test-gate`, `ai-code-review-refactor`, `skill-authoring-expert`, `agent-execution-discipline`.

# Handoff
Hand off the permission and sandbox record with any risky command, tool call, edit, release, cleanup, migration, connector, generated artifact, hook runtime change, or final closure claim. If the action is unsafe, overbroad, unsupported, denied, secret-sensitive without redaction, or missing rollback, hand off to the relevant security, release, reliability, validation, workflow-state, or maintainer owner before execution.

# Completion Criteria
The capability is complete when tool risk, sandbox and approval state, target boundary, side effects, secret boundaries, rollback controls, adapter visibility, validation freshness, telemetry limits, unknowns, next gate, and residual risk are explicit enough for an independent reviewer to approve, block, reroute, or accept partial evidence.
