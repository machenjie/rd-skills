---
name: cli-daemon-interface-design
description: "`analysis-agent`/`task-agent`/`review-agent`: use when CLI, TUI, or daemon commands, flags, config, streams, exit codes, signals, or dry-run behavior change; skip unrelated work."
---

# cli-daemon-interface-design

## Registry Trigger

**Use when**

- CLI TUI daemon command flags config precedence stdout stderr exit codes signals dry run background process scriptability

**Do not use when**

- no task-local cli daemon interface design decision is required

## Skill Role

Define explicit CLI and daemon behavior for human use, automation, side effects, reruns, signals, configuration, and supervision.

## High-Value Rules

- Define command grammar, configuration precedence, output and error contracts, and exit semantics from the affected human and automation consumers before implementation.
- When output is machine-consumed, separate stable requested data on stdout from diagnostics on stderr and select a versioned machine-readable representation appropriate to the consumer.
- For commands with remote, destructive, credential, or out-of-workspace effects, choose truthful preview, scoped confirmation, idempotency, or reconciliation controls from the effect and available authority; do not label a partial simulation as dry-run.
- Define non-idempotent rerun and partial-result behavior that prevents harmful silent repetition.
- When a process handles termination or reload, define cleanup, lock and child ownership, in-flight work, observable completion, and exit behavior from the supervisor and caller contracts.
- Require explicit production targets and credential input channels protected from history and process listings.

## Anti-Patterns

- A fixed precedence ladder copied from another tool can override the wrong authority; derive precedence from the actual configuration sources and document the winner.
- Interactive confirmation without non-interactive behavior can hang automation or silently choose a destructive default.
- A force flag without a scoped target, current-state evidence, or consequence preview does not establish intent.
- Progress mixed into structured output breaks consumers even when the command succeeds.

## Stop Conditions

- Escalate to `security-privacy-gate` for credential, IAM, secret, or sensitive-output boundaries.
- Escalate to `delivery-release-gate` for deploy, migration, publication, or production mutation.
- Escalate to `reliability-observability-gate` for supervised daemons, unattended execution, or operational signals.
- Escalate to `data-api-contract-changer` when machine output is a consumed contract and compatibility is unresolved.

## Output Contract

- Return a CLI or daemon decision: define command model, config precedence, output, exits, dry-run, signals, lifecycle, daemon behavior, and tests

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | Output, retry, destructive-action, or daemon lifecycle semantics remain open | No command or daemon interface contract changes | task-agent, review-agent, analysis-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | Interface changes span signals, exit codes, automation, or cleanup | Only internal implementation changes behind stable command behavior | task-agent, review-agent, analysis-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | Compatibility claims require fresh help, outputs, scripts, or tests | No interface-consumer claim awaits validation | task-agent, review-agent, analysis-agent | evidence-record, proof-limit, residual-risk |
