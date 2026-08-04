---
name: shell-cli-professional-usage
description: "Use with task-agent, review-agent, or analysis-agent for task-local Shell/CLI safety and rerun behavior. Do not use without that decision or as task owner."
---

# shell-cli-professional-usage

## Registry Trigger

**Use when**

- Shell CLI script safety set euo pipefail quoting exit codes temp files destructive command dry run stdout stderr idempotency rerun safety

**Do not use when**

- no task-local shell cli professional usage decision is required

## Skill Role

Protect shell-language execution, failure propagation, argument boundaries, secrets, temporary resources, destructive targets, reruns, and interface evidence. Consume non-trivial CLI interface decisions from `cli-daemon-interface-design`.

## High-Value Rules

- Verify the actual shell/dialect and caller contract. Treat `set -e` and `pipefail` as partial controls: explicitly handle expected failures in conditions, pipelines, substitutions, subshells, and cleanup without losing the original status.
- Quote scalar expansions and preserve argument boundaries with arrays and `"$@"`; never rebuild commands with `eval`. Keep secrets out of argv, xtrace, stdout, errors, and process listings, using the tool's supported protected channel.
- Validate shell safety through `mktemp` resources, signal-safe cleanup, canonical destructive targets, explicit authority, fail-safe reruns, and separated stdout/stderr behavior.
- Verify the accepted CLI output and exit contract from current consumers.
- Require machine-readable stdout only for an automation consumer.
- Route grammar, help, configuration precedence, output schema/versioning, and exit-code design to `cli-daemon-interface-design`.

## Anti-Patterns

- `set -e` is suppressed in several control-flow contexts, while pipeline consumers can terminate producers normally; untested strict mode can exit incorrectly or hide failure.
- An empty, relative, symlinked, or environment-derived destructive target can bypass a superficial string check.
- Cleanup traps can overwrite the command's real exit status.

## Execution Checklist

1. Map interpreter, inputs and trust, argv/environment/files, stdout consumer, exit-code contract, privilege, and destructive scope.
2. Trace expansions, arrays, pipelines, failure contexts, secret exposure, temporary resources, traps, target canonicalization, and partial state.
3. Test only triggered risks among wrong target, interruption, partial failure, cleanup, rerun, no-op, secret exposure, and output behavior.

## Stop Conditions

- Escalate production/release, elevated privilege, destructive resources, secret-bearing commands, or attacker-controlled evaluation when authority, rollback, or safer language/tooling is unresolved.
- Route unresolved non-trivial command grammar, help, configuration precedence, output compatibility, and exit semantics to `cli-daemon-interface-design`.

## Output Contract

- Return a Shell execution review: cover interpreter safety, argument boundaries, temporary resources, destructive-target validation, dry-run/apply parity, rerun behavior, and evidence for the accepted output and exit contract

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | an accepted CLI interface leaves shell dialect error handling portability or representation-verification mechanisms open | the CLI interface decision is absent or shell constraints select one simple approach | task-agent, review-agent, analysis-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | script changes quoting failures temp resources destructive paths or exit behavior | no shell control-flow safety or CLI contract changes | task-agent, review-agent, analysis-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | idempotency argv cleanup or output-contract claims need fresh proof | current callers fixtures and safe command checks prove each claim | task-agent, review-agent, analysis-agent | evidence-record, proof-limit, residual-risk |
