# Benchmark Prompt

## Task

Implement a UTC date formatting helper without adding a dependency unless the
dependency ladder proves one is required.

## Context

The starter repository needs one stable ISO-like UTC date string for an internal
report. A generated proposal may add a package for date formatting even though
the language standard library or existing installed dependency can handle it.

## Requirements

- Check standard library, native runtime/framework feature, existing repository
  utility, already-installed dependency, and local direct code before any new
  package.
- Record the dependency decision and rejected alternatives.
- Add a public behavior test for a fixed UTC timestamp.
- Keep the implementation deterministic across time zones.

## Constraints

- Do not add a new date/time dependency for simple formatting unless the ladder
  and security review justify it.
- Do not rely on local machine timezone.
- Do not update lockfiles without a dependency decision record.

## Deliverables

- Date formatting implementation.
- Public behavior test for a fixed timestamp.
- Dependency Decision Record with the full ladder and validation evidence.

## Completion Evidence

- Tests fail if formatting depends on local timezone.
- Review evidence rejects unnecessary package additions.
- Any dependency exception includes transitive, license, and vulnerability notes.
