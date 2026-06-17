# Expected Evidence

- read before plan: dependency manifest, lockfile, changelog for the upgraded dependency, affected imports, tests, and CI config.
- TDD: regression test or existing suite selection tied to the upgraded dependency behavior.
- validation evidence: dependency audit/validation command, targeted tests, build or lint command, and any lockfile integrity check.
- independent review: `ai-code-review-refactor` reviews assumption gaps and `quality-test-gate` reviews whether evidence proves the claimed completion.
- repair/re-review: missing evidence routes back to the original owner or `quality-test-gate`, then re-review repeats before handoff.
- residual risk: transitive runtime behavior not covered by local smoke tests.
- handoff: include route manifest, hook warning context, inspected files, command output summary, rollback note, residual risk, and next gate.
