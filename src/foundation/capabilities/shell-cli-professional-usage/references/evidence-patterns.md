# Shell CLI Evidence Patterns
Use this reference when shell/CLI closure depends on current or prior evidence, validation freshness, destructive/output/secret proof, profile tool boundaries, or changed-surface-to-validation mapping. Keep it as an evidence map, not a shell tutorial.

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
- **Strong evidence**: current script/help/caller inspected, role-permitted command or existing artifact named when used, result/freshness recorded, and proof limits named.
- **Weak evidence:** ShellCheck alone for destructive behavior, or stale or manual output.
- **Missing evidence:** an unavailable accepted check without `planned` or `not_run` status, reason, and owner.
- **Invalid evidence:** apply argv that differs from the printed command, external input through `eval`, secret exposure, or inaccessible output.

## Tool Permission Boundary
- For installs, permission changes, service operations, and external mutations, name the exact target and authority.
- Use a dry-run or preview when supported.
- Define the stop condition and cleanup or rollback command.
- When closure relies on shell or CLI evidence, distinguish displayed commands from executed argv and record the run's shell and working directory. Retained output omits or redacts expanded secrets and credential-bearing environment values.

## Handoff Evidence Shape

```yaml
shell_cli_evidence_closure:
  profile: analysis-agent | task-agent | review-agent
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
      reason_if_planned_or_not_run: ""
      proves: ""
      does_not_prove: ""
      freshness: fresh | stale | partial | planned | not_run
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
