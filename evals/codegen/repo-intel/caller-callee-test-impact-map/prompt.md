# Benchmark Prompt

## Task

Create bounded repository graph evidence that links symbols, imports, callers, callees, and affected tests to the plan.

## Context

The benchmark verifies that context packs and graph evidence influence planning and validation. This is an assertion-backed Codex live benchmark fixture for rd-skills core capability coverage. It is not a runtime content corpus and must not depend on network access, hidden archives, or user-specific state.

## Requirements

- Record symbol, import, caller-callee, and test ownership evidence.
- Use graph evidence to justify changed files and validation commands.
- Name affected callers and tests when behavior crosses module boundaries.
- Record graph freshness and residual risk in the final handoff evidence.

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
