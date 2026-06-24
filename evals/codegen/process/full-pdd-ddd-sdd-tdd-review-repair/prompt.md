# Benchmark Prompt

## Task

Create bounded evidence for an explicit PDD -> DDD -> SDD -> TDD -> Coding -> Review -> Repair -> Re-review -> Handoff flow.

## Context

The benchmark verifies that process evidence is explicit and assertion-backed rather than inferred from a good final answer. This is an assertion-backed Codex live benchmark fixture for rd-skills core capability coverage. It is not a runtime content corpus and must not depend on network access, hidden archives, or user-specific state.

## Requirements

- Record PDD problem, affected user or system, acceptance criteria, constraints, non-goals, and validation signal.
- Record DDD domain terms, objects, invariants, ownership decision, and side-effect boundaries.
- Record SDD modules, files, public API, data flow, error contract, failure modes, and logging decision.
- Record TDD acceptance-to-tests, invariant-to-tests or code, public API-to-tests, failure-mode tests, and validation commands.
- Record review coverage, at least one review finding or explicit no-finding rationale, repair, re-review, residual risk, and final diff coverage.

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
