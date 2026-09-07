# Expected Evidence

- inspect: checkout, invoice, and refund calculations, existing order/domain modules, tests, import boundaries, and any other consumers found during the same-pattern scan.
- analysis result: evidence for shared and distinct rules, the owning module and dependency direction, and any unresolved rounding decision that blocks the affected extraction.
- validation evidence: the Task establishes characterization coverage before extraction and runs targeted tests after the final edit, preserving totals and rounding behavior for every affected path.
- independent review: not selected by default; an unresolved ownership or calculation judgment must be named before requesting a separate assessment.
- repair: an extraction that violates the established owner or calculation rule returns to the same implementation Task for reproduction, cause verification, same-pattern inspection, correction, and fresh validation. A changed design assumption warrants reconsidering only the affected decision.
- residual risk: additional consumers not established by source inspection; text-search matches alone do not prove complete coverage.
- result: actual changed files, placement rationale, preserved rule differences,
  validation results, unverified scope, and any material residual risk or
  unresolved user decision.
