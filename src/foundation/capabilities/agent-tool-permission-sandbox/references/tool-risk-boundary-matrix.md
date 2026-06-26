# Tool Risk Boundary Matrix

Use this reference when a command, edit, connector action, migration, release step, generated artifact, or hook/runtime action needs detailed risk classification. Keep records compact: the goal is enough evidence for approval, reroute, or closure without retaining sensitive payloads.

## Record Fields

| Field | Required Content | Keep Out |
| --- | --- | --- |
| `mode_selected` | Read-only inspection, local-write/edit, destructive-local, external-read, external-write, or secret-sensitive output. | Long narrative. |
| `action_summary` | Bounded program/tool/action family and intent. | Full arguments if they may contain secrets or private data. |
| `risk_classification` | Risk class, trigger signals, write radius, external side effect, secret sensitivity, privilege, and production effect. | Raw command output. |
| `sandbox_and_approval` | Sandbox mode, approval policy/result, denied/not-needed rationale, adapter visibility, and missing evidence. | Policy bypass advice. |
| `target_boundary` | In-scope and out-of-scope paths, accounts, services, environments, data classes, generated outputs. | Personal data samples. |
| `side_effect_inventory` | Filesystem, network, source control, deploy, package, connector, cloud, DB, telemetry, memory, report effects. | Unbounded logs. |
| `controls_and_rollback` | Preview/dry-run/backup/restore/rollback/compensation/idempotency/rate limit/owner confirmation status. | "Trust me" approvals. |
| `telemetry_boundary` | Retained bounded facts, excluded fields, redaction marker, retention class. | Raw prompts, secrets, env values, credentials, full output. |
| `validation_and_closure` | Mapped validators, freshness, not-run/failed/stale/partial status, next gate, residual risk, owner. | Completion claims without evidence. |

## Risk Classes

| Risk Class | Trigger | Minimum Required Control | Escalate To |
| --- | --- | --- | --- |
| read-only | File search/read, metadata inspection, report parse, no mutation and no secret-bearing output. | Bounded paths, output sensitivity check, no-write statement. | `project-memory-governance` if retained. |
| local-write | Patch, format, generated report, dist artifact, local build/test cache, non-destructive config edit. | Target boundary, revert path, validation freshness plan. | `validation-broker` when outputs affect proof. |
| destructive-local | Delete, clean, reset, overwrite, move, chmod/chown, broad glob, force flag. | Target proof, preview/dry-run when available, restore plan, owner. | `security-privacy-gate`, `cleanup-deletion-governance`. |
| external-read | Connector/API/cloud/issue/email read, package metadata fetch, network read. | Account/data boundary, query scope, redaction, retention class. | `security-privacy-gate`. |
| external-write | Push, publish, deploy, send, mutate issue/email/cloud/db/package, rotate, migrate. | Owner approval, release/security gate, rollback or compensation. | `delivery-release-gate`, `reliability-observability-gate`. |
| secret-sensitive | Env, token, key, credential, private data, prompt/tool transcript, raw command output. | Redaction before capture, bounded facts only, retention limit. | `secret-configuration-security`. |
| production-affecting | Live endpoint, production config, capacity, telemetry, incident response, migration. | Reliability/release gate, rollback trigger, validation evidence. | `reliability-observability-gate`. |
| unsupported-visibility | Adapter/tool cannot observe permission result, command outcome, changed paths, or stop state. | Degraded evidence, manual record, closure residual risk. | `executor-adapter-protocol`. |

## Action Signal Matrix

| Signal | Default Concern | Required Question |
| --- | --- | --- |
| `rm`, `clean`, `reset`, `delete`, `remove`, broad glob | Wrong-target deletion. | What exact target is in scope, and how is it restored? |
| `overwrite`, `move`, `mv`, `chmod`, `chown`, `sudo`, `force` | Privilege or irreversible local mutation. | What authority is needed, and was a preview available/executed? |
| `deploy`, `publish`, `push`, `release`, `send` | External write or user-visible side effect. | Who owns approval, rollback, and post-action verification? |
| `migrate`, `apply`, `rotate`, `terraform`, `kubectl`, `helm` | Production or infrastructure mutation. | What environment is targeted, and what is the rollback/compensation path? |
| `token`, `key`, `secret`, `credential`, `env`, `password` | Secret exposure. | What fields are excluded before evidence capture? |
| connector/MCP/app action | Broad account or external data access. | What data and operation scopes are allowed and disallowed? |
| generated reports or dist outputs | Local writes after validation. | Which validators must rerun after the write? |

## Sandbox And Approval Interpretation

| State | Meaning For Closure |
| --- | --- |
| sandbox read-only and action read-only | Usually sufficient if output is not secret-sensitive and scope is bounded. |
| sandbox write-limited and target inside scope | Acceptable with revert path and fresh validation. |
| sandbox disabled or broad filesystem access | Requires explicit target boundary and residual risk; do not imply containment. |
| approval never and action is risky | Either avoid action, use safe read-only alternative, or disclose not-run/blocked. |
| approval granted | Authorization only; still requires target proof, rollback, and validation. |
| approval denied or not requested | Do not execute the action; hand off as blocked/not-run unless a safe alternative exists. |
| adapter unsupported | Downgrade evidence and attach manual record; unsupported visibility is not approval. |

## Required Controls By Mode

| Mode | Controls |
| --- | --- |
| Read-only inspection | Bound paths/query, check output sensitivity, summarize only bounded facts, disclose unknowns. |
| Local-write/edit | Name source-of-truth boundary, generated outputs, revert path, validator coverage, and later-edits freshness. |
| Destructive-local | Require target proof, preview/dry-run when available, backup/restore path, owner, and repeated-attempt stop rule. |
| External-read/connector | Scope account/data/query, forbid unneeded writes, redact sensitive output, state retention class. |
| External-write/release | Require owner approval, release/security gate, environment target, rollback/compensation, verification command, and residual risk. |
| Secret-sensitive output | Redact before storage, retain only bounded facts, exclude full arguments/output, route to secret/security owner. |

## Telemetry Boundary

Record bounded facts: program family, action family, risk class, target class, sandbox/approval state, outcome class, validation freshness, next gate, and residual risk. Exclude raw prompts, secrets, environment variables, credentials, personal data, private data, full arguments, full command output, connector payloads, and unbounded logs.

## Closure Template

```yaml
tool_permission_sandbox_record:
  mode_selected: local-write/edit
  action_summary: "apply markdown patch to target capability and reference"
  risk_classification:
    risk_class: local-write
    trigger_signals: [file edit, security-sensitive capability text]
    external_side_effect: none
    secret_sensitivity: redacted/no raw secrets requested
  sandbox_and_approval:
    sandbox_mode: "state current environment exactly"
    approval_policy: "state current policy exactly"
    permission_result: not_needed_or_not_available_or_granted
    adapter_visibility: manual_record
  target_boundary:
    in_scope: [target SKILL.md, target reference]
    out_of_scope: [registry changes, runtime code, unapproved content-ingestion structures]
  controls_and_rollback:
    preview_or_diff: executed
    rollback: "revert only the target files if validation regresses"
    validation: [targeted validators, full suite]
  telemetry_boundary:
    retained: [program family, risk class, paths, validator outcomes]
    excluded: [raw prompts, secrets, env values, credentials, full output]
  validation_and_closure:
    freshness: after_final_edit
    residual_risk: "state broad dirty worktree or unsupported evidence"
    next_gate: quality-test-gate
```
