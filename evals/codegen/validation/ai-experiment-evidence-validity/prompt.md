# Benchmark Prompt

## Task

Implement deterministic evidence-validation functions for fixed RAG, trial, training, and product-experiment records. Apply the explicit contracts in task.md.

## Context

The Python starter currently returns optimistic defaults. The work is a standalone validation implementation. Read `task.md` for data fields and observable outcomes, and `plan.md` for the bounded approach.

## Requirements

- Retrieval misses differ from answer omissions and unsupported certainty.
- Actual terminal states, uncertainty, and explicit budgets govern trial acceptance.
- Training checks distinguish future targets from unavailable features or immature labels.
- Experiment checks reject SRM, unit mismatch, invalid peeking, and undeclared multiplicity.

## Constraints

- Treating a success statement as an actual successful terminal state.
- Rejecting every future prediction target as leakage.
- Fitting preprocessing or tuning on final heldout samples.
- Accepting a sequential label without the declared plan constraints.
- Use Python standard-library code and fixed records only.
- Do not add a model service, business runtime, generic state engine, or external dependency.

## Deliverables

- Implement the public functions in `evidence_checks.py`.
- Preserve input data and return the contracted diagnostics and values.
- Keep passing and rejecting neighboring cases distinguishable.

## Completion Evidence

- Eight executable assertion methods compare paired valid and invalid records.
- An independent Pearson calculation exposes sample-ratio mismatch.
- A single-mechanism control suppresses only future-feature detection.
- Passing, incomplete starter, and faulty control are run separately.
- Report the exact candidate and assertion results, including proof limits.
