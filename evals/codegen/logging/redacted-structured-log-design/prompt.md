# Benchmark Prompt

## Task

Design bounded structured logging for sensitive request handling with redaction and security validation.

## Context

The benchmark verifies that logging-design and security-privacy gates trigger for raw request, token, cookie, auth header, and audit-log surfaces. This is an assertion-backed Codex live benchmark fixture for rd-skills core capability coverage. It is not a runtime content corpus and must not depend on network access, hidden archives, or user-specific state.

## Requirements

- Record log type, event, level, fields, redaction, correlation id, cardinality, and no-log rationale.
- Trigger logging-design-gate and security-privacy-gate evidence.
- Avoid logging raw request body, query, token, cookie, auth header, secret, or PII.
- Add or describe tests that cover redaction or no-log rationale.
- Use structured fields with bounded cardinality and an audit versus diagnostic boundary.
- When audit and diagnostic logs are both present, state separate sink and separate retention rationale.
- Security logs must include policy plus denial category, reason, or error category fields.

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
