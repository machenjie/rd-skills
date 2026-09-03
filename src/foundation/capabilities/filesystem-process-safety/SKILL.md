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

- supported platforms, filesystems, runtime APIs, create or replace intent, commit point, durability, legitimate concurrency, and cleanup owner
- executable identity, argv, environment, working directory, stdio, deadline, cancellation, descendants, exit meaning, and result reconciliation
- current related trust evidence, less-trusted actor or writer, sensitive authority, reachable impact path, and any complete related `critical_unknown`

## High-Value Rules

- Preserve normal correctness whenever a current filesystem effect or direct child-process effect changes; a controlled same-trust environment does not remove correctness work.
- When local creation, replacement, durability, containment, link, permission, ownership, or cleanup semantics are active, load the `atomic-filesystem-commit-and-containment` Reference.
- When direct executable, argv, environment, working-directory, inherited-resource, stdio, exit, timeout, cancellation, descendant, result, or cleanup semantics are active, load the `child-process-invocation-and-completion` Reference.
- Load `trust-sensitive-filesystem-process-protection` only for current related concrete reachable trust evidence or a complete related `critical_unknown`.
- Ordinary mutability, path difference, future replacement, or generic unknown does not create a less-trusted writer or replace an independent concurrency, durability, retry, or recovery decision.

## Anti-Patterns

- Reject API-name-only correctness claims, blind retry after an unknown result, pipe deadlocks, and kill-as-completion.
- Reject trust-sensitive proof demands based only on mutability, path spelling, future possibility, or a disconnected generic unknown.

## Stop Conditions

- Stop when the target, executable, platform guarantee, commit, descendant scope, or reconciliation owner cannot be bounded.
- Stop trust-sensitive work when a complete related `critical_unknown` leaves actor, authority, or reachable impact unresolved; a generic unknown remains a Proof Limit.
- Reject atomicity, durability, containment, termination, or result claims based only on an API name.
- Route uploads, shell behavior, Linux host operations, build graphs, and service rules to their existing owners.

## Output Contract

- Return a normal Filesystem/Process Safety Record covering create or replace, atomicity, durability, legitimate concurrency, cleanup, wait and reap, stdout/stderr, timeout or cancellation, and result reconciliation.
- Add trust-sensitive protection only when its Reference loads, with separate actor or writer, privilege or sensitive asset, and reachable material impact decisions.

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [atomic filesystem commit and containment](references/atomic-filesystem-commit-and-containment.md) | targeted | Local creation, replacement, durability, containment, link, permission, ownership, or cleanup semantics remain open | No local filesystem mutation or path-authority decision changes | analysis-agent, task-agent, review-agent | boundary-decision, proof-limit, residual-risk |
| [child process invocation and completion](references/child-process-invocation-and-completion.md) | targeted | Executable selection, argv, environment, stdio, exit, timeout, cancellation, descendants, or result certainty remains open | No direct child-process execution contract changes | analysis-agent, task-agent, review-agent | boundary-decision, proof-limit, residual-risk |
| [trust sensitive filesystem process protection](references/trust-sensitive-filesystem-process-protection.md) | targeted | A current filesystem or direct child-process effect has concrete reachable trust evidence, or a complete related Core critical unknown remains | Only normal filesystem or process correctness applies, or trust evidence is generic, disconnected from the current effect, or unreachable | analysis-agent, task-agent, review-agent | boundary-decision, proof-limit, residual-risk |
