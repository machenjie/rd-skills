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
- Classify blocks, ordinary Procs, and lambdas for arguments, return, break, and escaping lifetime.
- Inspect lazy enumeration and repeated traversal before moving side effects across iteration boundaries.
- Match rescue scope to the intended exception family and preserve cleanup through `ensure`.
- Define separate ownership for shared object state, thread variables, and fiber-local context.
- Observe thread failures and completion through the actual concurrency owner.
- Validate runtime-specific scheduling assumptions against the selected Ruby engine and version.

## Anti-Patterns

- An escaped Proc returns into an expired caller or changes a loop's exit behavior.
- Default rescue is treated as catching every exception.
- Fiber-local state is assumed to follow every thread execution path.
- A long-running worker retains request objects or silently loses a background failure.

## Stop Conditions

- Resolve receiver lookup, escaping block control, and concurrent-state ownership before changing their effects.

## Output Contract

- Return dispatch, block, exception, concurrency, and cleanup decisions with target-engine evidence.

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [dispatch blocks and concurrency](references/dispatch-blocks-and-concurrency.md) | targeted | dynamic receiver, nonlocal block control flow, cleanup, or concurrent Ruby state | unchanged Ruby code and package configuration without runtime consequences | analysis-agent, task-agent, review-agent | decision-record, failure-decision, validation-plan |
