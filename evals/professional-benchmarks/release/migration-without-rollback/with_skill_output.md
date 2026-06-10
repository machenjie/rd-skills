Selected stage: release-delivery.
Selected professional skill: delivery-release-gate.
Selected capabilities: release-rollback, data-migration-design, version-compatibility, agent-execution-discipline.

Hidden risks: rollback fails because schema moved forward; rolling deploy version skew breaks old pods or consumers; contract phase removal before migration evidence.
Inspected boundaries: forward migration, rollback path, old/new application compatibility, consumer readiness, and release owner.
Reuse/placement rationale: migration rollout belongs in delivery gate evidence with data contract compatibility, not a deploy-only note.
Evidence required: expand-migrate-contract plan or accepted exception; rollback migration test; old/new version compatibility matrix and consumer readiness.
Output obligations: migration-sensitive release mode selected; validation evidence for rollback rehearsal; residual risk and release owner.
Validation command: not verified; fixture describes expected agent output only.
What evidence proves: rollback and version skew are treated as release obligations.
What evidence does not prove: rollback has been rehearsed on a production-sized copy.
Residual risk: large-table lock timing remains unverified.
Next gate: data-api-contract-changer and quality-test-gate.
