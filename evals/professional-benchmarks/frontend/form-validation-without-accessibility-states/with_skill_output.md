Selected stage: coding.
Selected professional skill: frontend-change-builder.
Selected capabilities: form-validation-design, frontend-testing, interaction-state-modeling, code-clarity-maintainability.

Hidden risks: inaccessible validation feedback; lossy form state after API failure; test coverage only verifies visual red text.
Inspected boundaries: field validation state, submit disabled state, loading state, API error state, success state, focus management, and test queries.
Reuse/placement rationale: validation state belongs with the form controller/component boundary; shared UI only receives accessible message props.
Evidence required: form state matrix including invalid, disabled, loading, API error, and success states; keyboard and screen reader validation evidence; behavior-oriented tests with accessibility queries.
Output obligations: accessibility obligations and focus management; validation evidence for a11y/user behavior; what tests prove and do not prove.
Validation command: not verified; fixture describes expected agent output only.
What evidence proves: visible, keyboard, and assistive-tech paths are covered by the expected output.
What evidence does not prove: real browser/screen reader behavior until run.
Residual risk: product copy for recoverable API errors still needs review; owner: frontend-change-builder.
Next gate: quality-test-gate.
