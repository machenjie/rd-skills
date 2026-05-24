# Benchmark Prompt

## Task

Add order display-name formatting without creating a new generic helper or
duplicating existing formatter logic.

## Context

The starter repo already contains order and customer formatting helpers in
owner modules. The requested change is small, but an agent may be tempted to
add `formatOrderDisplayName()` to `shared/utils` without searching for reuse
candidates or explaining placement.

## Requirements

- Search for existing order and customer formatting helpers before adding code.
- Reuse or compose existing helpers when semantics match.
- Keep order business terminology inside the order module unless a real shared
  technical utility is justified.
- Add focused tests for display-name formatting through the public order API.
- Include an Execution Discipline Report with reuse search evidence and an
  Implementation Structure Plan.

## Constraints

- Do not add business logic to `shared`, `common`, or generic `utils` modules.
- Do not create a public export for code used only inside the order module.
- Do not change unrelated billing, customer, or inventory behavior.

## Deliverables

- Updated order display-name implementation.
- Tests covering normal, missing-customer, and archived-order display cases.
- Short structure note listing searched files, reuse candidates, rejected
  alternatives, validation command, and residual risk.

## Completion Evidence

- Test output proving the public order API formats display names correctly.
- Evidence inventory showing the search command or inspected files.
- Diff contains no new order business helper under shared/common/utils.