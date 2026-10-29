---
name: php-professional-usage
description: "For analysis/task/review agents: use for PHP conversion, dispatch, errors, or process lifetime; skip generic package work and edits without PHP semantics."
---

# php-professional-usage

## Registry Trigger

**Use when**

- PHP type conversion, comparison, autoloading, error propagation, or resource lifetime affects behavior.
- Request workers, long-running commands, or repeated jobs can retain application state.

**Do not use when**

- PHP appears only in dependency metadata, comments, or unchanged generated output.
- The decision concerns generic build policy or framework configuration without PHP runtime behavior.

## Skill Role

Protect PHP value semantics, class resolution, error handling, and request or process state.

## High-Value Rules

- Bind coercion and comparison behavior to the target PHP version and boundary types.
- Distinguish missing values, null, false, zero, and empty strings where the contract distinguishes them.
- Resolve the actual entrypoint, autoloader order, class identity, and case-sensitive deployment behavior.
- Preserve intended handling for exceptions, engine errors, and cleanup failures.
- Assign state lifetime from the actual process model, including static variables and retained objects.
- Release resources through explicit owner paths, including exceptional exits and repeated work.
- Verify affected behavior through the deployed SAPI or long-running execution model.

## Anti-Patterns

- Loose equality or implicit conversion turns invalid input into a valid identifier or amount.
- A successful local autoload hides case mismatches on the deployment filesystem.
- A worker assumes request teardown resets globals, caches, transactions, or subscriptions.
- Destructor timing is used as the sole proof that an external resource closed correctly.

## Targeted References

- No task-local Reference is indexed for this Skill.
