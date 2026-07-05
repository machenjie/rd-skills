# Shell CLI Evidence Patterns

Use this reference when shell/CLI closure depends on repository graph, project memory, execution trajectory, validation freshness, destructive-command proof, stdout/stderr contract evidence, secret-handling proof, tool permission boundaries, or changed-surface-to-validation mapping. Keep it as an evidence map, not a shell tutorial.

## Changed-Shell-Surface-To-Validation Map

| Shell/CLI claim | Minimum evidence | What it proves | What it does not prove |
| --- | --- | --- | --- |
| Destructive command is guarded | Current script path, target selector, dry-run output, apply flag/confirmation rule, rollback note, and target-guard test | The inspected command path blocks the named wrong-target case before mutation | Every production context, shell environment, or operator mistake is covered |
| Output contract is safe | stdout schema or sample, stderr diagnostic sample, exit-code table, and parser/golden-output test | The inspected consumer can distinguish data, diagnostics, and failures | All downstream parsers or historic output consumers are compatible |
| Quoting and path handling are robust | ShellCheck result, hostile filename fixture, null-delimiter or quoted-array proof, temp/trap cleanup, and rerun test | The inspected path handles representative whitespace/glob/temp/rerun hazards | Every filesystem, locale, or external command behavior is covered |
| Secret handling is contained | no-secret-in-argv review, tracing boundary, redacted log sample, temp-file mode, and retention statement | The named secret path avoids obvious process-list/log/artifact exposure | External tool logging, kernel audit, or third-party retention is fully proven |
| Command composition is injection-safe | argv array or safe API proof, rejected `eval`/`bash -c` path, input validation, and negative injection fixture | The inspected command boundary does not execute user text as shell syntax | Every callee option parser or environment variable is safe |
| Prior command evidence is fresh | current source/help/caller paths, cwd/env assumptions, accepted/rejected memory, command/report path, and final-edit freshness | The prior command claim still matches inspected current files | Later script edits, hidden aliases, shell startup files, or uninspected CI jobs remain covered |

## Evidence Quality Labels

- **Strong evidence**: current script/help/caller inspected, command or artifact named, exit code or review status recorded, final-edit freshness stated, and proof limits named.
- **Weak evidence**: ShellCheck alone for destructive/filesystem behavior, old runbook output, manual terminal success, style guide citation, or memory claim without current source.
- **Missing evidence**: no dry-run output, no target guard, no stdout/stderr sample, no hostile filename fixture, no secret-boundary review, no rollback path, or no owner for not-run validation.
- **Invalid evidence**: printed command that differs from apply argv, `eval` with external input, secret in argv/history/logs, stale command help, or inaccessible report.

## Tool Permission Boundary

| Action | Boundary record |
| --- | --- |
| Source reads, `--help`, dry-run commands, graph search, report review, and ShellCheck/shfmt diff-only checks | Read-only or non-mutating local action; cite searched paths and avoid full output dumps. |
| bats tests, fixture creation, formatter rewrites, generated reports, temp directory commands, and local sandbox scripts | State-mutating only for caches, reports, temp files, fixtures, or local artifacts; cite command, exit code, artifact path, and cleanup/rollback. |
| package install, chmod/chown, service restart, cloud/kube/terraform apply/delete, migration, release, rollback, or production-target command | High-risk state-mutating action; require explicit scope, dry-run proof, rollback/forward-fix path, redaction, stop condition, and permission record. |

## Handoff Evidence Shape

```yaml
shell_cli_evidence_closure:
  inspected_paths:
    - path: ""
      finding: ""
  accepted_prior_claims:
    - claim: ""
      current_evidence: ""
  rejected_or_stale_claims:
    - claim: ""
      reason: ""
  changed_shell_surface_to_validation_map:
    - surface: ""
      risk: destructive | output_contract | path_temp | secret | command_injection | freshness
      command_or_artifact: ""
      exit_code_or_status: ""
      proves: ""
      does_not_prove: ""
      freshness: fresh | stale | partial | not_run
      owner: ""
  tool_permission_boundary:
    action_class: ""
    sandbox: ""
    state_mutation: ""
    redaction: ""
  residual_risk:
    - risk: ""
      owner: ""
      next_gate: ""
```
