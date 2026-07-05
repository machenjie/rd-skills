# Expected Evidence

- read before plan: checkout calculation, invoice calculation, refund calculation, order domain/model modules, tests, and import boundaries.
- TDD: characterization tests for all three calculation paths before extraction.
- validation evidence: same-pattern scan result and targeted test output proving all copied paths still match expected totals.
- independent review: `architecture-impact-reviewer` reviews ownership, over-abstraction, and placement; `quality-test-gate` reviews coverage.
- repair/re-review: if the extraction lands in a generic shared utility without ownership rationale, repair routes to `architecture-impact-reviewer`, then re-review repeats.
- residual risk: hidden fourth calculation path not found by text search.
- handoff: include route manifest, reuse ladder, rejected placements, inspected files, validation output, residual risk, and next gate.
