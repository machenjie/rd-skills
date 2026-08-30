# Engineering Artifact Review Checklist

Use for an independent review of an ordinary Engineering Brief, Task Plan, acceptance, or contract artifact before implementation. Do not load it for implementation-diff review, a bounded implementation task with no separate decision artifact, high-risk design, or release/deployment/migration readiness.

## Review Checklist

- Confirm artifact kind, scope, acceptance, non-goals, decision owner, and review authority.
- Verify each material claim against current source or explicit owner evidence.
- For an ordinary Engineering Brief, check outcome, boundaries, invariants, consumers, unknowns, and the first executable slice.
- For a Task Plan, check dependencies, write scopes, integration and conflict owners, stop conditions, and validation ownership.
- For an acceptance artifact, check falsifiable outcomes, rejection conditions, validator, evidence owner, freshness, and release consequence.
- For a contract artifact, check producers, consumers, versions, compatibility, null or default semantics, errors, rollout, and deprecation.
- Record high-risk Engineering Brief decisions as unreviewed specialist scope.
- Record release, deployment, or migration readiness as unreviewed approval scope.
- Establish implementation readiness from resolved blockers, owned dependencies, and one safe executable slice.
- Match validation and rollback evidence to artifact claims, failure boundaries, and proof limits.
- Mark security, privacy, money, destructive, privileged, irreversible, or public-contract decisions outside review authority unless their authoritative decisions are supplied.
- Return the verdict, severity-ranked findings, reviewed and unverified scope, downstream impact, residual risk, and next owner.
