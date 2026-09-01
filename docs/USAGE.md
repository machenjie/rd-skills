# Usage

After installation, use rd-skills by describing the engineering outcome you want. You do not need to choose a specialist, name an internal workflow, or investigate the repository before asking.

Skill invocation is host-specific. The examples below use Codex, where Skills use `$skill-name`. The [host invocation table](QUICKSTART.md#host-invocation) distinguishes artifact delivery, live invocation, and full-workflow availability. Cline has Skills artifacts only; live invocation and the full workflow are not established. OpenAI API packages are used through an API integration. Copilot CLI facts do not apply automatically to other Copilot surfaces.

## Describe the task

A useful request can be as short as:

```text
$engineering-control-plane

Payment callbacks sometimes create the same order twice.
Find the cause and fix it. Add the necessary regression test and verify the change.
```

State the outcome and important constraints in normal language. rd-skills reads the repository to discover ownership, placement, consumers, and available checks before it edits.

## Helpful information

Add any facts you already know. None of these are mandatory:

- the behavior you observe and the behavior you expect;
- a reproducible input, error message, or failing test;
- likely files or modules;
- public behavior that must remain compatible;
- files or systems that must not change;
- the repository's test, lint, build, or migration command;
- rollout, security, data, performance, or accessibility concerns; and
- a point where you want rd-skills to stop and ask.

Paths and commands are useful clues, not proof. rd-skills still checks the current source before relying on them.

## What rd-skills handles

For implementation work, rd-skills normally:

1. reads the relevant source, tests, and repository rules;
2. identifies the owning code and nearby consumers;
3. decides whether it can safely edit or must investigate first;
4. applies the professional guidance needed for the concrete task;
5. makes the smallest complete change supported by current facts;
6. runs checks that cover the changed behavior and risk;
7. has a separate reviewer inspect the actual latest change; and
8. reports results, limits, remaining risk, and any next action.

It does not silently authorize destructive operations, production changes, privilege elevation, unmanaged-file replacement, or scope outside your request.

## Natural-language examples

### Bug

```text
$engineering-control-plane

The settings page crashes when a saved account has no display label.
Find the cause, fix the owning component, and add a regression test.
Keep the behavior for labeled accounts unchanged.
```

For intermittent or repeated failures, include timestamps, correlation IDs, or a minimal reproduction if available. rd-skills should prove the cause rather than repeat the same attempted fix.

### Feature

```text
$engineering-control-plane

Add validation, submitting, success, and failed-save states to the checkout address form.
Preserve keyboard navigation and existing design-system behavior.
Add the relevant component tests.
```

If interaction, accessibility, or ownership is unclear, rd-skills may inspect and plan the affected user flow before editing.

### Refactor

```text
$engineering-control-plane

Remove the duplicate retry calculation shared by the invoice worker and webhook handler.
Keep public behavior unchanged and reuse the existing owner if one exists.
Run the focused tests for both consumers.
```

A refactor should still state the invariant it preserves. “Clean this up” alone leaves correctness unclear.

### API change

```text
$engineering-control-plane

Add MFA enrollment status to the login response.
Check authentication and compatibility impact before changing the contract.
Update the contract tests and call out any consumer decision I need to make.
```

Public API work may pause for a compatibility, versioning, or rollout choice instead of guessing.

### Migration

```text
$engineering-control-plane

Split customer_name into given_name and family_name without breaking current clients.
Map all readers and writers, propose a safe rollout and rollback sequence, then implement only the earliest reversible step.
Do not touch production data.
```

Schema, data, and cross-service changes are planned around compatibility, recovery, and ordering. Production execution remains a separate authority boundary.

### Review

```text
$engineering-control-plane

Review only. Do not edit files.
Inspect the current diff and every changed file for correctness, compatibility, security, and missing regression coverage.
Return blocking findings first with file and line evidence, then list what you could not verify.
```

Provide the actual diff or make it accessible in the current workspace. A changed-file summary alone is not enough for an exact change review.

### High-risk change

```text
$engineering-control-plane

Design wallet-based subscription authorization.
Do not implement or perform a transaction.
Identify the human approval, key custody, idempotency, reconciliation, and rollback boundaries first.
```

Security, payments, irreversible actions, credentials, and production authority require explicit boundaries. Stopping for your decision is expected behavior.

## Understand the result

A completed implementation response should make these points easy to find:

- **Changed:** the files and behavior that changed.
- **Verified:** the commands that ran after the latest edit and their results.
- **Reviewed:** the independently checked change and any findings resolved.
- **Unverified:** behavior or environments the available checks did not prove.
- **Residual risk:** risk that remains after the completed checks.
- **Next:** a user decision, rollout step, or follow-up only when one is still necessary.

“Tests passed” is not proof of a live deployment, real host loading, provider behavior, or production correctness. The result should name those limits when they matter.

## When rd-skills asks you

Most repository-local, reversible work can proceed without repeated confirmation. rd-skills asks one focused question when the answer belongs to you, for example:

- whether to expand beyond the requested scope;
- whether a public compatibility break is acceptable;
- which of two unsupported product behaviors is intended;
- whether unmanaged content may be replaced;
- whether to perform a destructive, privileged, production, or data-changing action; or
- which external system or consumer is authoritative.

If current source can answer the question safely, rd-skills should investigate instead of asking you to do preliminary repository research.

## Common questions

### Do I need to learn the Skill names?

No. When the [host invocation table](QUICKSTART.md#host-invocation) gives a verified invocation, use it and describe the task. In Codex, that is `$engineering-control-plane`. Cline does not currently have a contract-backed live invocation or full workflow guarantee.

### Do I need to provide acceptance criteria?

No. State the observable outcome and constraints you know. Precise acceptance is helpful when the behavior is subtle or compatibility matters.

### Can I provide a file or test command?

Yes. rd-skills treats it as a useful candidate and verifies it against the repository rather than assuming it is authoritative.

### Why did rd-skills investigate before editing?

Ownership, impact, verification, or safety was not yet supported by current source. The goal is to avoid a fast change in the wrong place.

### Why did it stop after the same failure happened twice?

Repeating an unchanged attempt is unlikely to create new information. rd-skills requires a changed hypothesis, new evidence, or a different safe path before retrying.

### Can doctor say the AI tool loaded rd-skills?

No. Doctor verifies installed artifacts. Restart the tool and run a small real task to check the live experience.

## Common problems

| Problem | What to do |
| --- | --- |
| The host rejects the invocation | Check the [host invocation table](QUICKSTART.md#host-invocation). In Codex, use `$engineering-control-plane`, not a leading Slash command. |
| The tool ignores the request after installation | Restart it, confirm the tool and scope you installed, then rerun doctor. |
| The task stops before editing | Read the stated ownership, safety, compatibility, or scope gap and answer only the concrete question. |
| The task edits too broadly | Restate the allowed scope and preserved behavior; ask it to stop if ownership differs. |
| A validation command is unavailable | Provide the repository's supported command if known, or ask rd-skills to report the gap without claiming completion. |
| A review cannot inspect the change | Make the actual diff and changed files accessible; do not substitute a summary. |
| An installation or upgrade check fails | Use [Advanced Installation & Recovery](INSTALLATION.md#troubleshooting-and-recovery). |

For reproducible bugs, include the command, tool, scope, operating system, Python version, and redacted output described in [Support](../SUPPORT.md).

## Advanced documentation

- [Advanced Installation & Recovery](INSTALLATION.md) for paths, scopes, dry runs, conflicts, backups, upgrade, uninstall, packages, and recovery.
- [Migrating older installations](MIGRATING_TO_HOOKLESS.md) for historical installation cleanup and rollback.
- [System architecture](HOOKLESS_ARCHITECTURE.md) for how the product is structured internally.
- [AI control boundaries](AI_CONTROL_BOUNDARIES.md) for host capability and enforcement limits.
- [Documentation map](README.md) for maintainer, validation, benchmark, and release material.
