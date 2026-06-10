# Benchmark Prompt

## Task

Rewrite a reconciliation job that compares 10M ledger rows against provider rows using nested scans and load-all processing.

## Context

The starter repository reads both datasets into lists, loops over every pair, sorts entire intermediate collections, and then computes top unmatched accounts. It has no input-size statement or memory budget.

## Requirements

- State expected input size, distribution, hot-key/skew risk, average case, and worst case.
- Select data structures that match lookup, dedupe, grouping, ordering, top-K, and range needs.
- Use streaming, chunking, pagination, or indexed lookup where memory requires it.
- Justify sorting, grouping, and top-K complexity.
- Add tests or benchmark/profile evidence for the performance-sensitive path.

## Constraints

- Do not keep O(n squared) nested scans for 10M records.
- Do not load all unbounded input into memory without an explicit budget.
- Do not choose a complex structure without explaining the access pattern.
- Do not claim performance improvement without evidence.

## Deliverables

- Algorithm/Data Structure Decision.
- Complexity and memory budget.
- Streaming or chunking decision.
- Benchmark or profile evidence for the hot path.

## Completion Evidence

- Reconciliation is bounded by map/index/top-K/streaming/chunking behavior rather than full nested scans.
- Test data includes representative skew and large-input cases.
- Rejected alternatives explain why the simpler approach is insufficient.
