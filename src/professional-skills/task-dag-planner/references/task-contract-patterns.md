# Task Contract Patterns

Use this reference when a task node must be executable by a fresh agent without hidden context. Keep each task contract concise and scoped to one owner surface and one reviewable artifact.

## Node Contract
- **Scope:** one goal, one owner surface, one risk domain, and one expected artifact.
- **Inputs:** exact files, configs, docs, generated artifacts, callers, tests, or previous node outputs to inspect.
- **Mutation boundary:** exact files to create, modify, or delete, plus public/internal/private visibility and compatibility impact.
- **Reuse and placement:** existing pattern or helper considered first, rejected locations, dependency direction, and why new structure is or is not needed.
- **Validation:** literal command or validator, expected output, evidence artifact, freshness rule, and what the check does not prove.
- **Rollback:** revert command, rollback node, forward-fix decision, or manual owner when rollback is not immediate.
- **Review and handoff:** independent review gate, completion evidence, downstream unblock condition, and residual risk owner.

## Visible Markdown Plan Shape

Use normal Markdown for AI-visible L3+ full plans:

```markdown
# Implementation Plan

## Goal

...

## Design Summary

...

## Global Constraints

- ...

## Task 1: <reviewable task title>

Goal:
...

Files:
- Inspect: `<path>`
- Modify: `<path>`
- Test: `<path>`

Acceptance Criteria:
- ...

Verify:
- Command: `<literal command>`

Expected:
- ...

Review:
- ...

Stop Conditions:
- ...

Rollback:
- ...
```

For L1/L2 work, a minimal Plan Handoff is enough:

```markdown
# Plan Handoff

Files:
- Inspect: `<path>`
- Modify: `<path>`
- Test: `<path>`

Verify:
- Command: `<literal command>`

Residual Risk:
- ...
```

Maintainer tooling canonicalizes `Inspect:`, `Modify:`, `Create:`, `Delete:`, and
`Test:` file entries by stripping the role prefix, Markdown backticks, and
trailing explanations before comparing accepted plan files with changed files.
`Inspect:` and `Test:` entries count as inspection/test files; `Modify:`,
`Create:`, and `Delete:` entries count as changed-file intent.

Do not require ordinary agents to emit JSON metadata, task graph schemas,
ledger keys, hook event ids, internal node ids, or digest values. Maintainer,
CI, benchmark, doctor, or advisory hook tooling may derive those artifacts from
the visible plan, but the agent-facing task contract remains natural language.

## Placeholder Replacement Rules

Do not write tasks such as "TBD", "TODO", "handle edge cases", "write tests",
"add proper error handling", "validate it works", "similar to above",
"refactor as needed", or "update docs if necessary".

Replace vague text with exact behavior:

- "handle edge cases" -> list the exact edge cases.
- "write tests" -> name the test file, test case, behavior, and expected result.
- "proper error handling" -> name the error condition, error contract, and command that proves it.
- "similar to above" -> repeat the exact files, behavior, and validation for the task.

## Splitting Rules
- Split a node when it mixes migration, API contract, authorization, UI behavior, data backfill, release, or documentation evidence.
- Split a node when two owners, two mutable shared resources, or two validation commands are required to prove completion.
- Keep nodes together only when splitting would create artificial handoff overhead and the same reviewer can validate the full artifact in one pass.
