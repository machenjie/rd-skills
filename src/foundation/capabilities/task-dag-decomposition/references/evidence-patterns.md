# Task DAG Evidence Patterns

Use this reference when a task DAG must close against current source, repository graph, project memory, execution trajectory, validation freshness, tool boundary, or plan-execution consistency evidence. Keep detailed examples here so `SKILL.md` remains efficient.

## Contents

- [Evidence Closure Matrix](#evidence-closure-matrix)
- [Graph, Memory, and Trajectory Judgment](#graph-memory-and-trajectory-judgment)
- [Validation Freshness Rules](#validation-freshness-rules)
- [Repair and Re-review Ledger](#repair-and-re-review-ledger)
- [Tool Boundary Record](#tool-boundary-record)
- [Plan Consistency Checks](#plan-consistency-checks)

## Evidence Closure Matrix

| DAG element | Minimum closure evidence | Does not prove |
| --- | --- | --- |
| Task node | Goal, allowed files, owner surface, dependency list, validator or review artifact, done condition. | Adjacent tasks are safe to start. |
| Dependency edge | Edge type, producer, consumer, reason, and source fact or owner decision behind the edge. | The graph is acyclic unless cycle check is recorded. |
| Parallel group | Allowed-file comparison plus shared-resource scan for generated files, configs, fixtures, tables, queues, flags, and public contracts. | Future scope changes remain collision-free. |
| Safety flag | Irreversible operation, approval owner, rollback or recovery path, and validation gate. | Data can be recovered without the named procedure. |
| Skipped scope | Non-goal, owner, reason, and not-present check or accepted residual risk. | The skipped surface is unaffected in production. |
| Repair route | Finding, changed files, repair owner, new validation, and independent re-review result. | Downstream work before re-review was safe. |

## Graph, Memory, and Trajectory Judgment

Record selector evidence as one of:

- `accepted`: current source, generated artifact, test, registry, report, or owner evidence confirms the claim.
- `rejected`: current evidence contradicts the graph, memory, or trajectory claim.
- `stale`: the claim may have been true, but edits, time, build output, or validation order make it unsafe for closure.
- `not_verified`: the claim is plausible but was not checked; map it to residual risk or a source-inspection task.

Repository graph may identify likely owners and dependents, project memory may widen review scope, and execution trajectory may add freshness or repair nodes. None of them proves behavior without current source or validation evidence.

## Validation Freshness Rules

Validation is fresh only when it runs after the final material edit to the source, fixture, config, generated input, migration, or reference it is meant to cover.

Mark validation stale or partial when:

- a task changed allowed files after the command ran;
- a repair changed a task node after review;
- generated reports were produced before the latest source edit;
- a build profile was skipped even though runtime installation depends on it;
- a command validated only one node but the handoff claims the whole DAG.

Each validation record should include command, exit code, artifact or report path, covered node, what it proves, what it does not prove, and residual risk owner.

## Repair and Re-review Ledger

Use this compact ledger for execution recovery:

```yaml
repair:
  finding: "T2 used stale generated client output"
  owner: "backend-change-builder"
  changed_files:
    - "src/api/generated/client.ts"
  validation:
    command: "npm test -- api/generated-client"
    result: "exit 0"
  independent_re_review:
    reviewer: "quality-test-gate"
    result: "approved after generated diff check"
  downstream_unblock: "T3 may start after re-review, not after repair commit"
```

## Tool Boundary Record

When a task or validator uses shell, connector, deployment, migration, scanner, cloud, production, or secret-bearing tools, record:

- tool/action class and exact command or connector action;
- permission state and sandbox boundary;
- read-only, dry-run, or state-mutating classification;
- write paths, network behavior, or production scope;
- rollback, cleanup, or revert path;
- redaction rule for secrets, environment values, raw prompts, and long output.

If the tool can mutate production, cloud, data, IAM, or secrets, add a safety prerequisite node before execution.

## Plan Consistency Checks

Before handoff, compare the accepted DAG to actual work:

- changed files are within `allowed_files` or the DAG is amended and re-reviewed;
- each changed node maps to validation, review evidence, owner response, or residual risk;
- skipped tasks and skipped scopes still have stated owners and not-present checks;
- parallel groups still have non-overlapping file and resource scopes after final edits;
- build, install, generated report, and runtime reference validations are fresh;
- residual risks name the owner, consequence, and next gate.
