# Benchmark Prompt

## Task

Refactor a Python comprehension that hides filtering, mapping, and defaulting logic.

## Context

The starter repo has a nested comprehension with inline `or` defaults and side
conditions. It is hard to review and has edge-case drift.

## Requirements

- Split or name the expression so filter, mapping, and default rules are explicit.
- Preserve current public behavior.
- Add tests for empty, missing, filtered, and normal records.
- Include code-element and behavior-preservation evidence.

## Constraints

- Do not add a class or shared helper for one local expression.
- Do not change returned record shape.
- Do not replace the logic with broad unrelated refactoring.

## Deliverables

- Updated Python implementation.
- Regression tests for expression branches.
- Handoff with before/after expression semantics.

## Completion Evidence

- Tests prove behavior preservation for all listed fixtures.
- Review note explains why the expression is now reviewable.

