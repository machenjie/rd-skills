# Benchmark Prompt

## Task

Create evidence for a validation broker that marks old validation stale after material code changes.

## Context

The benchmark verifies that Stop closure and final handoff do not treat stale validation as fresh evidence. This is an assertion-backed Codex live benchmark fixture for rd-skills core capability coverage. It is not a runtime content corpus and must not depend on network access, hidden archives, or user-specific state.

## Requirements

- Record an initial validation pass before a material edit.
- Record a material code or fixture edit after that validation pass.
- Mark the previous validation stale and refuse to claim full completion from stale evidence.
- Record a fresh validation rerun or an explicit residual risk if no rerun occurs.

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
