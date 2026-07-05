# Business Semantic Pack Coupling

Use this reference when `domain-impact-modeler` owns Business Semantic Pack domain slices or must decide whether missing BSP evidence blocks implementation planning.

## BSP Output Fields
- `sections_written`: business_vocabulary, business_objects, business_rules, workflows, data_and_signal_semantics, code_mapping, validation_map, or context_control sections changed by the DDD work.
- `source_backed_facts`: each business claim marked `FACT` with current source, owner review, user-provided source, or validation evidence.
- `assumptions`: business claims that are not source-confirmed and must not be treated as FACT.
- `open_questions`: owner, vocabulary, rule authority, workflow, validation, or source freshness gaps that block implementation planning.
- `residual_business_risk`: semantic risks left after selected source reads, owner review, or validation.

## Coupling Rules
- When a business semantic trigger is present but no BSP exists, do not proceed directly to implementation planning; create the BSP slice or record structured skip rationale.
- Structured skip rationale belongs in `context_control.selected_references` or `skipped_references` with reference, reason, evidence limit, residual risk, and next owner.
- Domain model output must carry `evidence_class` for each material claim.
- Mark current-source, owner-review, user-source, or validation-backed claims as `FACT`.
- Mark graph-selected or memory-selected claims as `INFERENCE`, `ASSUMPTION`, `OPEN_QUESTION`, or `MEMORY_SIGNAL`.
- Project memory and repository graph are selectors only; they may choose files, owners, rules, or transitions to inspect, but they cannot prove a BSP `FACT` without current source, owner review, user-provided source, or validation result.
