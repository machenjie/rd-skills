# Regression Testing Checklist

- Link the guard to an accepted defect, incident, review finding, or escaped failure and state the causal mechanism.
- Preserve the triggering input, state, role, tenant, ordering, timing, dependency response, and wrong observable result that matter.
- Choose the narrowest boundary that still contains the causal storage, browser, provider, concurrency, or deployment behavior.
- Obtain safe unfixed failure evidence, targeted mutation/fault evidence, or an explicit counterfactual proof limit.
- Assert the allowed result, the prior forbidden result, and unauthorized, duplicate, or missing side effects where relevant.
- Scan same-pattern paths and map material matches to fresh guards, fixes, or residual owners.
- Own fixture redaction, drift, setup, and cleanup across pass, failure, timeout, and cancellation.
- Use deterministic seams and bounded observation; keep flake reruns or quarantine separate from closure evidence.
- Record the fresh scoped result, unproved variants, infeasible automation, compensating detection, owner, and revisit trigger.
