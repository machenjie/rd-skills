Selected stage: debugging-diagnosis.
Selected professional skill: backend-change-builder.
Selected capabilities: senior-programming-judgment-core, failure-diagnosis, failure-contract-design, idempotency-retry-design, observability, validation-broker, agent-execution-discipline.

Hidden risks: timeout label is not a verified violated invariant; duplicate charge is a side effect; patch-first diagnosis may miss retry and failure-contract boundaries.
Senior programming judgment required: map symptom/root cause to violated fact, invariant, boundary, state transition, side effect, or failure contract.
Evidence required: reproduction; eliminated hypotheses; verified cause; idempotency invariant; retry/failure contract; side-effect ordering; validation proof limits.
Output obligations: symptom/root-cause-to-invariant map; failure contract and side-effect evidence map; validation evidence with proof limits; residual risk owner and next gate.
Inspected boundaries: reproduction notes, payment retry boundary, idempotency invariant, duplicate-charge side effect, failure contract, and observability handoff.
Validation command: not verified; fixture describes expected agent output only.
What evidence proves: debugging must not close from cause labels without invariant/failure mapping.
What evidence does not prove: the actual production cause.
Residual risk: payment gateway behavior needs source-backed confirmation; owner: backend-change-builder.
Next gate: quality-test-gate.
