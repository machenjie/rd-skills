# Repository Automation Contracts

**Load when:** An internal CLI, hook, monorepo automation path, maintenance mutation, subprocess, rerun, or cleanup contract can change the decision.

**Do not load when:** No repository automation interface or mutation behavior changes.

**Required by:** `task-agent`

**Required output:** `decision-record`, `failure-decision`, `proof-limit`

Sources accessed 2026-07-26.

## Decision Rules

- Name supported CLI, hook, build, monorepo, and CI callers and invocation contexts.
- Define argv, config/environment precedence, stdio, help, machine output, and exits.
- Resolve worktree, root, submodule, sparse checkout, generated tree, and dirty-state authority.
- Declare tool, file, locale, time, randomness, network, credential, cache, and host inputs.
- Resolve an authorized target allowlist once; use it for preview and apply and reject current-directory authority.
- Define concurrency, atomic commit or recovery, and rerun behavior.
- Define child executable, argv, environment, directory, stdio, timeout, cancellation, descendants, and exit mapping.
- Preserve the primary failure while reporting cleanup or rollback failure.
- Compare repeated clean runs when reproducibility is required.
- Inspect owner, consumer, tests, adjacent utilities, versions, reuse, and invalid, interrupted, and forbidden outcomes before the smallest complete change.

## Primary Sources

- [Git hooks](https://git-scm.com/docs/githooks); [Bazel](https://bazel.build/basics/hermeticity); Python [argparse](https://docs.python.org/3/library/argparse.html), [subprocess](https://docs.python.org/3/library/subprocess.html), and [tempfile](https://docs.python.org/3/library/tempfile.html).

## Proof Limits

Sources do not prove wrappers, platforms, hook installation, worktree layout, sandbox, credentials, or filesystem guarantees. Verify callers, invalid target, interruption, rerun, child failure, and cleanup; report unknown or partial recovery without widening APIs or unrelated tooling.
