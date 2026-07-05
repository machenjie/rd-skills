# Expected Evidence

- read before plan: existing form component, submit handler, validation error component, design-system form controls, tests, and API client behavior.
- TDD: component or integration test covering dirty state, disabled submitting state, and failed-save server error persistence.
- validation evidence: targeted frontend test command plus browser or component-state verification when available.
- independent review: `quality-test-gate` reviews regression coverage and state matrix; `experience-impact-modeler` reviews user-visible states.
- repair/re-review: any missing state or inaccessible control returns to `frontend-change-builder`, then re-review repeats.
- residual risk: visual regressions outside tested viewport or design-system variants.
- handoff: include route manifest, inspected components/tests, state matrix, validation output, residual risk, and next gate.
