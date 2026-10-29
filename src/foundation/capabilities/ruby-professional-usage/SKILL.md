---
name: ruby-professional-usage
description: "For analysis/task/review agents: use for Ruby dispatch, blocks, exceptions, or worker concurrency; skip generic tooling and changes without Ruby semantics."
---

# ruby-professional-usage

## Registry Trigger

**Use when**

- Ruby method lookup, dynamic dispatch, blocks, iteration, exceptions, or retained state changes behavior.
- Threads, fibers, or long-running workers affect ownership, error observation, or cleanup.

**Do not use when**

- Ruby is only a package label or unchanged framework dependency.
- The decision concerns generic build, release, or style without Ruby semantics.

## Skill Role

Protect Ruby control flow, dynamic calls, resource cleanup, and concurrent context.

## High-Value Rules

- Trace the real receiver, method lookup, visibility, and missing-method behavior before changing dynamic calls.
- Distinguish blocks, ordinary Procs, and lambdas for arguments, return, break, and escaping lifetime.
- Inspect lazy enumeration and repeated traversal before moving side effects across iteration boundaries.
- Match rescue scope to the intended exception family and preserve cleanup through `ensure`.
- Separate shared object state, thread variables, and fiber-local context.
- Observe thread failures and completion through the actual concurrency owner.
- Bind runtime-specific scheduling assumptions to the selected Ruby engine and version.

## Anti-Patterns

- An escaped Proc returns into an expired caller or changes a loop's exit behavior.
- Default rescue is treated as catching every exception.
- Fiber-local state is assumed to follow every thread execution path.
- A long-running worker retains request objects or silently loses a background failure.

## Targeted References

- No task-local Reference is indexed for this Skill.
