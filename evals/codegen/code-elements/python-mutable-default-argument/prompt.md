# Benchmark Prompt

## Task

Fix a Python mutable default argument bug in request aggregation code.

## Context

The starter repo contains a function with `items=[]` as a default argument.
Requests can leak state into later calls.

## Requirements

- Replace the mutable default with explicit per-call initialization.
- Preserve the public function behavior for callers that pass a list.
- Add regression tests proving state does not leak across calls.
- Include a Code Element Professionalism Review for variable default semantics.

## Constraints

- Do not change the public function name.
- Do not introduce a new class or helper module for this local fix.
- Do not mutate caller-owned lists unless the old behavior explicitly did so.

## Deliverables

- Updated Python implementation.
- Regression tests for repeated calls and explicit list input.
- Evidence note with validation command output.

## Completion Evidence

- Tests fail on the mutable default version and pass after the fix.
- Handoff states whether caller-provided lists are copied or mutated.

