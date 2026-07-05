# Benchmark Prompt

## Task

Create bounded evidence that ChangeForge professional routing and hook injection are active without leaking raw prompts or secrets.

## Context

The benchmark checks whether skills and hooks produce reviewable route context and bounded runtime signal rather than contaminating baseline output. This is an assertion-backed Codex live benchmark fixture for rd-skills core capability coverage. It is not a runtime content corpus and must not depend on network access, hidden archives, or user-specific state.

## Requirements

- Record bounded route context with task type, risk level, professional concerns, source/test context, validation focus, assumptions, and residual risk.
- Record at least one bounded hook injection signal such as SessionStart, UserPromptSubmit, PreToolUse, or Stop.
- Explain why baseline output must remain free of ChangeForge-specific contamination.
- State that hook evidence is bounded and excludes raw prompt text, full command output, secrets, and local absolute user paths.

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
