# Benchmark Prompt

## Task

Create evidence that a review finding leads to repair and re-review before final handoff.

## Context

The benchmark verifies that review is not a decorative step and that final diff coverage follows repairs. This is an assertion-backed Codex live benchmark fixture for rd-skills core capability coverage. It is not a runtime content corpus and must not depend on network access, hidden archives, or user-specific state.

## Requirements

- Record review coverage for the final diff or planned diff.
- Record at least one review finding or an explicit defect scenario.
- Record the repair performed to address the finding.
- Record re-review after repair and final residual risk.
- Show changed files and validation evidence in the handoff.

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
