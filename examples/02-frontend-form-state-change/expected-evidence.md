# Expected Evidence

- inspect: existing form component, submit handler, validation error component, design-system form controls, tests, and API client behavior.
- validation evidence: component tests cover dirty state, disabled save during submission, failed-save error persistence, successful save, and preserved keyboard behavior; report the targeted command and results after the final edit, plus any browser checks actually performed.
- independent review: not selected; the existing owner, unchanged contract, and observable component behavior support local self-check and targeted validation.
- repair: if a check reveals a defect, the same Task reproduces it, verifies the cause, checks nearby states for the same pattern, repairs it, and reruns the relevant checks. No automatic Analysis or Review follows.
- residual risk: viewports or design-system variants not exercised by the available checks.
- result: actual changed files and behavior, validation results, unverified scope,
  and any material remaining risk. No formal handoff is needed for this local task.
