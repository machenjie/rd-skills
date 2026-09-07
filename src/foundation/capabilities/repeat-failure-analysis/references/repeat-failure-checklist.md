# Repeat Failure Checklist

- Name the exact repeated path, hypothesis, edit shape, and validation command.
- Preserve the latest failing output summary and changed-file evidence.
- Before another edit after a repeated failure, scan for occurrences of the verified or currently tested failure pattern and the consumers reachable from the affected owner; disclose any uninspected scope.
- Require one new falsifiable hypothesis and one materially different proof path.
- Stop after two same-path failures when neither new evidence nor a safer probe exists.
- At a repeated-failure handoff, return task-local source, command, diff, and result evidence for the next falsifiable hypothesis. Durable workflow history remains in its owning system, not an internal history or memory store.

## Anti-Patterns

- Renaming the same patch is not a different approach.
- A green unrelated command does not disprove the observed failure.
- Previous conversation summaries are navigation hints, not source truth.

## Execution Checklist

1. List the failed attempts on the rejected path and the evidence each produced.
2. State why the prior path is rejected or still uncertain.
3. Inspect the owner and same-pattern occurrences.
4. Choose one falsifiable next hypothesis and a different proof path.
5. Return the bounded next action or a concrete blocker.
