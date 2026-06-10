Selected stage: debugging-diagnosis.
Selected professional skill: delivery-release-gate.
Selected capabilities: agent-execution-discipline, failure-diagnosis, data-migration-design, release-rollback.

Hidden risks: repeated same-path retry without route repair; migration lock impact on production writes; diagnosis claim without verified cause.
Inspected boundaries: two failed migration attempts, lock scope, write traffic impact, rollback boundary, and release retry conditions.
Reuse/placement rationale: the next action belongs in migration planning and release rollback evidence, not another local command retry.
Evidence required: route repair ledger with two failed attempts; lock diagnosis evidence and migration plan adjustment; rollback or safe retry boundary.
Output obligations: route repair decision and new hypothesis; validation evidence for safer migration path; residual release risk and owner.
Validation command: not verified; fixture describes expected agent output only.
What evidence proves: the same failed path is stopped and a new diagnosis path is required.
What evidence does not prove: the lock holder has been found in a real database.
Residual risk: production lock duration remains unknown.
Next gate: delivery-release-gate with quality-test-gate evidence.
