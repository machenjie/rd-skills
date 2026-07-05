# Benchmark Prompt

## Task

Create bounded evidence that professional references are loaded by stage instead of loading every skill at once.

## Context

The benchmark distinguishes precise staged injection from broad over-routing. This is an assertion-backed Codex live benchmark fixture for rd-skills core capability coverage. It is not a runtime content corpus and must not depend on network access, hidden archives, or user-specific state.

## Requirements

- Record requirement or PDD stage evidence limited to clarification, problem definition, acceptance criteria, and non-goals.
- Record DDD evidence for domain objects, invariants, ownership, and side-effect boundaries.
- Record SDD evidence for module boundary, placement, reuse, error contract, and logging decision.
- Record TDD evidence for acceptance-to-test, invariant-to-test, failure-mode tests, and validation commands.
- Record review evidence for code review, plan consistency, repair, and re-review.
- Name at least one unrelated capability that must not be loaded for the fixture.

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
