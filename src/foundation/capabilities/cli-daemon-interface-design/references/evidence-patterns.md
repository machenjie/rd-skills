# CLI Daemon Interface Evidence Patterns

Use this reference when closure depends on repository graph, project memory, execution trajectory, validation freshness, command output, generated help/docs, automation consumers, or a changed-interface-to-validation map. Keep it as an evidence map, not a second CLI design guide.

## Interface Claim To Evidence Map

| Interface claim | Minimum evidence | What it proves | What it does not prove |
| --- | --- | --- | --- |
| Command grammar is stable | Command tree, flags, positional args, aliases, deprecated forms, generated help, invalid-argument tests. | The inspected grammar and discoverability contract are defined. | Hidden scripts or external users do not rely on undocumented forms. |
| Machine output is parseable | Schema or golden output, stdout/stderr split, parser smoke command, compatibility window, consumer list. | The named output mode can be parsed without diagnostics contaminating stdout. | Every automation consumer or future field removal is safe. |
| Exit codes are actionable | Exit-code table, retry guidance, failure-class tests, signal mapping. | Automation can distinguish success, usage, validation, dependency, partial, timeout, and signal states. | All provider-specific failures or OS-specific signal timing are covered. |
| Config precedence is deterministic | Defaults, system/user/project config, env vars, flags, profile/target selectors, precedence tests. | The inspected invocation resolves configuration in the documented order. | All deployment environments or inherited config files are covered. |
| Destructive action is bounded | Scoped selector, confirmation token, dry-run no-write proof, idempotency/rerun behavior, rollback or repair path. | The inspected mutation path has a reviewed side-effect boundary. | Live production state, provider permissions, or every partial failure is reversible. |
| Daemon lifecycle is safe | Supervisor config, readiness/liveness distinction, signal tests, reload behavior, lock/PID behavior, shutdown timeout. | The inspected lifecycle has start, ready, reload, drain, and cleanup evidence. | Production orchestrator behavior, all OS variants, or real load timing is proven. |
| TUI/non-TTY behavior is safe | TTY/non-TTY tests, cancel/resize behavior, terminal restoration, progress stream, color policy. | The inspected terminal flow has an automation-safe path. | Every terminal emulator or screen reader behavior is covered. |
| Validation is fresh | Command, working directory, exit code/status, output summary, artifact path, covered interface surface, final-edit freshness. | Evidence was produced after the final material edit for the mapped interface risk. | Later source/help/docs/test/report edits or hidden consumers are covered. |

## Graph, Memory, And Execution Reconciliation

- Treat repository graph, project memory, generated help, docs, prior command output, and execution trajectory as selectors until current source and tests confirm them.
- Accept prior "flag exists", "output schema stable", "daemon reload safe", "consumer list complete", or "validation passed" claims only when current commands, docs, tests, generated help, scripts, and validators still match.
- Reject or downgrade memory that lacks date, owner, command scope, output artifact, validation command, consumer boundary, or residual-risk owner.
- Mark evidence stale after edits to command code, help/docs, config defaults, output schemas, exit codes, signal handlers, service units, examples, generated reports, or validation mappings.
- Map every final CLI/TUI/daemon confidence claim to a source path, generated help/doc artifact, command output, validator command, owner approval, or explicit not-run residual risk.

## Tool Permission Boundary

| Action | Boundary record |
| --- | --- |
| Local source reads, graph search, report inspection, help fixture inspection, and markdown validation | Read-only local shell action; cite searched paths and avoid full output dumps. |
| Local validators, builds, generated help refresh, and report generation | State-mutating only for reports, caches, temp files, dist/build artifacts, or local fixtures; cite log path, command, exit code, and rollback path. |
| Command execution that writes files, rotates credentials, deploys, deletes, publishes, migrates, or changes daemon state | High-risk local or external action; require dry-run or sandbox proof, scoped target, rollback/repair path, stop condition, and secret redaction. |

## Handoff Evidence Shape

```yaml
cli_daemon_interface_evidence_closure:
  inspected_surfaces:
    - surface: ""
      finding: ""
  accepted_prior_claims:
    - claim: ""
      current_evidence: ""
      freshness: ""
  rejected_or_stale_claims:
    - claim: ""
      reason: ""
  changed_interface_to_validation_map:
    - interface_surface: ""
      behavior_or_contract: ""
      validation_command_or_artifact: ""
      exit_code_or_status: ""
      proves: ""
      does_not_prove: ""
      owner: ""
      freshness: ""
  tool_permission_boundary:
    action_class: ""
    sandbox: ""
    state_mutation: ""
    redaction: ""
  residual_risks:
    - risk: ""
      owner: ""
      next_gate: ""
```
