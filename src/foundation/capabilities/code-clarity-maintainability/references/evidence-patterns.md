# Code Clarity Evidence Patterns

Use this reference when closure depends on repository graph, project memory, execution trajectory, validation freshness, command output, review artifacts, or evidence limits.

## Evidence Map

| Evidence Type | Accept When | Reject When | Closure Wording |
| --- | --- | --- | --- |
| Current source read | Public entry point, changed files, tests, and relevant callers were read after the last edit | Source was read before later edits or only from memory | `current source inspected: ...` |
| Repository graph | Graph matches current imports/exports/callers and names affected ownership edges | Graph is stale, generated before moved files, or lacks dynamic caller limits | `graph accepted/rejected because ...` |
| Project memory | Memory states prior decisions and is reconciled with current source | Memory is treated as proof without source confirmation | `memory used as hint, verified by ...` |
| Execution trajectory | Trajectory explains edit/read/test order, failed commands, repairs, and route changes | Final diff is approved while failed path or repair remains unreviewed | `trajectory finding and re-review: ...` |
| Validation command | Command ran after final edit and can fail for the clarity risk or behavior boundary | Command predates final edit, is unrelated, or only proves formatting | `command, exit code, proves/does-not-prove` |
| Review artifact | Finding names path, line/area, impact, and required action | Review says "clean" without scope, files, or evidence limits | `review scope and limits: ...` |

## Graph, Memory, Execution Coupling

For L3+ clarity approval, answer these in order:

1. **Graph:** Which entry point, callers, imports/exports, tests, and split/merge paths define the current ownership graph?
2. **Memory:** Which prior decision, benchmark, report, or previous review is being reused, and what current source read confirms or rejects it?
3. **Execution:** Did implementation read before editing, avoid repeated same-path retries, repair findings, and re-run stale validators after the final edit?
4. **Validation:** Which command or review artifact can fail for the affected behavior, structure, or test readability risk?

If any answer is missing, close with an explicit residual risk instead of approval.

## Freshness Rules

- Re-run or disclose stale validation when `SKILL.md`, references, registry, generated reports, tests, fixtures, configs, or build scripts change after a command.
- Treat a full-suite pass as stale for this slice if target files changed afterward.
- Treat graph and memory as selectors, not proof, until current source paths are re-read.
- Treat formatter/linter success as insufficient for behavior-preserving refactors unless the change is formatting-only.
- Treat a single targeted eval as insufficient for skill-system handoff when AGENTS requires the full validation chain.

## What Evidence Proves

- A skill-body link validator proves linked references resolve; it does not prove the reference is professionally sufficient.
- A professionalism eval score proves current scoring dimensions; it does not prove runtime agent behavior on every task.
- A build profile proves emitted runtime artifacts can be generated for that profile; it does not prove source directories are safe to install directly.
- A unit or validation command proves only the paths it exercises; it does not prove dynamic callers, external integrations, or production scale.
- A review artifact proves inspected files and stated scope; it does not prove skipped files or stale sources.

## Closure Template

Use this compact closure for clarity changes:

```yaml
clarity_evidence:
  mode: main-flow | control-naming | split-merge | test-clarity | agent-ai-maintainability
  inspected:
    source_paths: []
    tests_or_validators: []
    graph_memory_trajectory: accepted | rejected | not_used
  decision: approved | blocked | route_to_next_gate
  evidence:
    command_or_review: ""
    proves: ""
    does_not_prove: ""
    freshness: fresh | stale | partial
  residual_risk: ""
  next_gate: ""
```
