# Repeat Failure Checklist

- Name the exact repeated path, hypothesis, edit shape, and validation command.
- Preserve the latest failing output summary and changed-file evidence.
- Before another edit after a repeated failure, scan for occurrences of the verified or currently tested failure pattern and the consumers reachable from the affected owner; disclose any uninspected scope.
- Require one new falsifiable hypothesis and one materially different proof path.
- Stop after two same-path failures when neither new evidence nor a safer probe exists.
- At a repeated-failure handoff, return task-local source, command, diff, and result evidence for the next falsifiable hypothesis. Durable workflow history remains in its owning system, not an internal history or memory store.
