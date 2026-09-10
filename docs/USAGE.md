# Usage

Describe the engineering outcome you want. You do not need to choose a specialist,
name a workflow, or investigate the repository before asking.

The examples use Codex and `$engineering-control-plane`. Use the
[host invocation table](QUICKSTART.md#host-invocation) for other hosts. Cline has
Skills artifacts only; live invocation and the full workflow are not established.
OpenAI API packages need an API integration. Copilot CLI support does not extend
automatically to other Copilot surfaces.

## Describe the task

A useful request can be as short as:

```text
$engineering-control-plane

Payment callbacks sometimes create the same order twice.
Find the cause and fix it. Add the necessary regression test and verify the change.
```

State the outcome and important constraints. Add any facts you already know:

- observed and expected behavior, a reproducible input, or an error;
- likely files, modules, or a test command;
- public behavior that must stay compatible and files that must not change;
- relevant rollout, data, security, performance, or accessibility concerns; and
- a point where you want rd-skills to stop.

These are useful clues. The implementing agent still checks the current source,
owner, tests, and affected consumers before editing.

## Everyday requests

### Local change

```text
$engineering-control-plane

Keep the server validation error visible after a failed save in the billing settings form.
Preserve keyboard navigation and the existing API behavior.
Update the relevant component test and run it.
```

A local change can finish with inspection, editing, self-check, and targeted
validation. You may see no separate Analysis or independent Review.

### Refactor

```text
$engineering-control-plane

Remove the duplicate retry calculation shared by the invoice worker and webhook handler.
Keep public behavior unchanged and reuse the existing owner if one exists.
Run the focused tests for both consumers.
```

State the behavior a refactor must preserve. If current code reveals competing
rules or owners, rd-skills should resolve that specific question before making
the affected edit.

### Migration

```text
$engineering-control-plane

Split customer_name into given_name and family_name without breaking current clients.
Map readers and writers, propose a rollout and rollback sequence, then implement only the earliest reversible step.
Do not touch production data.
```

Compatibility, data recovery, and deployment order may need deeper Analysis or
an independent judgment. The request does not authorize production execution.

### Review only

```text
$engineering-control-plane

Review only. Do not edit files.
Inspect the current diff and every changed file for correctness, compatibility, security, and missing regression coverage.
Return blocking findings first with file and line evidence, then list what you could not verify.
```

Make the actual diff and changed files accessible. A summary alone is insufficient.
A review-only request ends with findings and limits; it does not authorize repairs.

## What to expect

The agent should explain what it is changing and validate after the final edit.
Extra investigation, multiple tasks, or independent Review should have a concrete
reason. You do not need to request every mechanism or follow a fixed sequence.

| Normal behavior | Behavior to question |
| --- | --- |
| A small change finishes after relevant checks, without another agent reviewing it. | Every change waits for Analysis, a design document, and independent Review. |
| The Task agent searches for files, tests, and callers itself. | Missing file paths alone cause a separate planning round or a request for you to research the repository. |
| An unresolved compatibility or authorization decision prompts a focused investigation or question. | Work stops for a vague risk label without a concrete missing fact or affected action. |
| The original Task repairs an ordinary review defect and reruns targeted validation. | Every repair automatically starts another Review. |
| An unavailable check is reported with the attempted operation and actual failure. | The result claims success for a check that did not run. |

rd-skills reuses existing authorization for bounded, reversible work. It asks when
a decision belongs to you: new scope, intended product behavior, a compatibility
break, or additional authority for a destructive, privileged, production, or
irreversible action. Host permissions still apply. If current source can answer
the question, it should inspect that source first.

## Understand the result

A completed implementation should report:

- **Changed:** the files and behavior that changed.
- **Verified:** checks run after the latest relevant edit and their actual results.
- **Reviewed, if selected:** the independently inspected scope and findings; this is separate from validation.
- **Limits:** skipped, unavailable, flaky, or partial checks, unverified behavior, and material residual risk.
- **Next, if needed:** a remaining user decision or follow-up.

Passing tests does not prove live deployment, host loading, provider behavior, or
production correctness. The result should state those limits when relevant.

## Common problems

| Problem | What to do |
| --- | --- |
| The host rejects the invocation | Check the [host invocation table](QUICKSTART.md#host-invocation). In Codex, use `$engineering-control-plane`, not a leading Slash command. |
| The tool ignores the request after installation | Restart it, confirm the installed tool and scope, then rerun doctor. Doctor checks installed files, not live loading. |
| The task stops for a decision | Answer the concrete scope, behavior, compatibility, or authority question. |
| The task edits too broadly | Restate the allowed scope and preserved behavior. |
| The same failure happens twice | Expect a changed hypothesis or new evidence before another attempt. |
| A validation command is unavailable | Supply the supported command if known; the result must state the gap and cannot claim that check passed. |
| A review cannot inspect the change | Make the actual diff and changed files accessible. |
| An installation or upgrade check fails | Use [Advanced Installation & Recovery](INSTALLATION.md#troubleshooting-and-recovery). |

For reproducible problems, include the command, host, scope, operating system,
Python version, and redacted output described in [Support](../SUPPORT.md).

Continue with [How it works](HOW_IT_WORKS.md) for the minimal mental model and
examples of when each mechanism is useful.
