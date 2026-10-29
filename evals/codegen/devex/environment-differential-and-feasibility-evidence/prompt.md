# Benchmark Prompt

## Task

Implement deterministic evidence-validation functions for environment comparisons and bounded feasibility records. Follow task.md.

## Context

The starter returns unsupported success. This task implements a standalone validator over fixed records. It does not diagnose the machine running the benchmark.

## Requirements

- Separate observed differences from verified causes.
- Distinguish application, toolchain, and configuration changes.
- Require controlled intervention or a linked minimal reproduction.
- Validate falsification, comparison, critical boundaries, versions, budgets, and stopping.
- Return explicit prototype limits.

## Constraints

- Use Python standard-library code.
- Do not scan environments, install dependencies, execute record text, or call external systems.
- Do not add an experiment platform or generic task engine.

## Deliverables

- Implement both public functions in evidence_checks.py.
- Preserve input records.
- Keep valid, inconclusive, and falsifying records distinguishable.

## Completion Evidence

Run real assertions against the passing candidate, incomplete starter, and faulty control. Run the existing smoke harness. Report proof limits.
