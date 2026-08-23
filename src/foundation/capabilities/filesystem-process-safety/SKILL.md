---
name: filesystem-process-safety
description: "Use when code mutates files, resolves paths, applies file protection, or controls child processes. Skip uploads, shell syntax, build graphs, services, and host administration."
---

# filesystem-process-safety

## Registry Trigger

**Use when**

- Local create, temporary commit, replace, durability, cleanup, protection, ownership, path containment, link, or reparse behavior can change.
- Direct child-process executable, argv, environment, working directory, inherited-resource, stdio, exit, timeout, cancellation, descendant, cleanup, or unknown-result behavior can change.

**Do not use when**

- The decision concerns uploads or object storage, shell syntax, Linux host administration, build graphs or code generation, or service business logic.
- No task-local filesystem or child-process safety decision changes.

## Skill Role

Define portable application-runtime safety for local mutation and direct child processes from current platform, runtime, filesystem, trust, and consumer facts.

## Inputs

- supported platforms, filesystems, runtime APIs, path authority, who can write the path, whether any writer is less trusted, link policy, replacement, durability, protection, and cleanup owner
- executable identity, argv, environment, working directory, stdio, deadline, cancellation, descendants, exit meaning, and effect reconciliation

## High-Value Rules

- When local creation, replacement, durability, containment, link, permission, ownership, or cleanup semantics are active, load the `atomic-filesystem-commit-and-containment` Reference.
- When direct executable, argv, environment, working-directory, inherited-resource, stdio, exit, timeout, cancellation, descendant, result, or cleanup semantics are active, load the `child-process-invocation-and-completion` Reference.
- Stop when current platform, trust, path, executable, lifecycle, or consumer facts cannot select the active named decisions; shell-language semantics remain outside this owner.

## Anti-Patterns

- Reject API-name-only safety claims, check/open races, create-then-tighten exposure, pipe deadlocks, and kill-as-completion.

## Stop Conditions

- Stop when the trusted base, target, executable, platform guarantee, effective protection, descendant scope, or reconciliation owner cannot be bounded.
- Reject atomicity, durability, containment, termination, or result claims based only on an API name.
- Route uploads, shell behavior, Linux host operations, build graphs, and service rules to their existing owners.

## Output Contract

- Return a Filesystem/Process Safety Record covering platform, path/link, commit, durability, protection, cleanup, executable, argv, environment, working-directory, inherited-resource, and stdio decisions.
- Include exit, timeout, cancellation, descendants, unknown results, evidence, proof limits, and residual owners.

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [atomic filesystem commit and containment](references/atomic-filesystem-commit-and-containment.md) | targeted | Local creation, replacement, durability, containment, link, permission, ownership, or cleanup semantics remain open | No local filesystem mutation or path-authority decision changes | analysis-agent, task-agent, review-agent | boundary-decision, proof-limit, residual-risk |
| [child process invocation and completion](references/child-process-invocation-and-completion.md) | targeted | Executable selection, argv, environment, stdio, exit, timeout, cancellation, descendants, or result certainty remains open | No direct child-process execution contract changes | analysis-agent, task-agent, review-agent | boundary-decision, proof-limit, residual-risk |
