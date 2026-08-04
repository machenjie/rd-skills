# Repository Automation Contracts

**Load when:** An internal CLI, hook, monorepo automation path, maintenance mutation, subprocess, rerun, or cleanup contract can change the decision.

**Do not load when:** No repository automation interface or mutation behavior changes.

**Required by:** `task-agent`

**Required output:** `decision-record`, `failure-decision`, `proof-limit`

Official sources were accessed on 2026-07-26.

## One Decision

Select one repository automation contract that behaves consistently from supported entrypoints and leaves a known workspace state after success, failure, or interruption.

| Fact to establish | Required decision | Failure signal |
|---|---|---|
| Entrypoints and consumers | Name direct CLI, hook, build target, monorepo wrapper, CI caller, and supported invocation context | One caller receives different defaults or working-directory behavior |
| Interface | Define argv, config precedence, environment, stdin, stdout, stderr, exit, help, and machine-output stability | Human diagnostics corrupt automation output or failure exits zero |
| Repository identity | Resolve worktree, repository root, submodule, sparse checkout, generated tree, and dirty-state policy | The utility mutates another worktree or assumes one checkout layout |
| Hermetic inputs | Declare tool versions, files, locale, time, randomness, network, credentials, caches, and host executables | A clean or isolated host produces another result |
| Mutation | Define dry-run parity, target allowlist, concurrency, atomic commit, backup or recovery, and rerun behavior | Interruption exposes partial state or rerun duplicates changes |
| Subprocesses | Define executable, argv, environment, working directory, stdio, timeout, cancellation, descendants, and exit mapping | A child remains active or an unknown effect is reported as success |
| Cleanup | Preserve the primary failure while reporting temporary files, locks, processes, or rollback failure | Cleanup hides the cause or removes an unrelated path |

## Decision Rules

- Keep preview and apply selection over the same resolved target set.
- Reject implicit current-directory authority.
- Make hooks safe under their documented Git working directory and environment.
- Compare repeated clean runs when reproducibility is required.
- Return unknown or partial state when recovery cannot prove a final result.

## Primary Sources

- [Git hooks](https://git-scm.com/docs/githooks)
- [Bazel hermeticity](https://bazel.build/basics/hermeticity)
- [Python argument parsing](https://docs.python.org/3/library/argparse.html)
- [Python subprocess management](https://docs.python.org/3/library/subprocess.html)
- [Python temporary files](https://docs.python.org/3/library/tempfile.html)

## Proof Limits

These pages do not establish repository wrapper behavior, supported platforms, hook installation, worktree layout, sandbox enforcement, credential policy, or filesystem guarantees. Exercise current callers plus invalid target, interruption, rerun, subprocess failure, and cleanup paths before closure.
