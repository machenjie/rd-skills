# Benchmark Prompt

## Task

Implement or describe the smallest correct change using existing helpers or native platform features while preserving validation and security.

## Context

The fixture includes an overbuild trap: a broad abstraction, dependency, or new file would be more complex than the requested behavior needs. This is an assertion-backed Codex live benchmark fixture for rd-skills core capability coverage. It is not a runtime content corpus and must not depend on network access, hidden archives, or user-specific state.

## Requirements

- Search for and reuse existing helper behavior when semantics match.
- Prefer standard library or native language features over a new dependency.
- Avoid new abstractions, new files, or generic helpers unless they remove real complexity.
- Keep required validation, error handling, security, and accessibility evidence intact.
- Record LOC, new file count, and dependency count as telemetry only.

## Constraints

- Keep all evidence bounded and repository-local.
- Do not add dependencies unless explicitly justified by the case.
- Do not store raw prompts, full command output, secrets, or local absolute user paths.
- Do not claim completion without validation evidence or residual risk.

## Deliverables

- Updated implementation or bounded evidence file in the starter repository.
- Focused tests or test plan evidence for the behavior under evaluation.
- A concise handoff note with changed files, validation evidence, and residual risk.

## Completion Evidence

The case passes only when assertions can inspect concrete files such as `CAPABILITY_EVIDENCE.md`, `process-trace.json`, `final.md`, `diff.patch`, or grading metadata and find the required capability evidence.
