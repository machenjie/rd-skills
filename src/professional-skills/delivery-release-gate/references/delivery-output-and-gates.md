# Delivery Output And Gates

Load only when assigned L3-L5 analysis, release-artifact implementation, or independent readiness review needs mode-specific closure plus targeted proof for a selected delivery risk.

## Do Not Load

Do not load for local-only work without a release decision or when the root contract or compact checklist is sufficient. Named Layer 3 Skills own specialized migration, compatibility, security, reliability, and tool mechanisms.

## Output Contract

Return exactly one mode closure, followed only by fields triggered by the selected risk:

1. **Analysis closure:**
   - Return the source-backed release plan, authority boundaries, selected rollout and recovery decisions, validation strategy, unknowns, residual risk, and recommended next step.
   - Make no claim of edits, production action, or approval.
2. **Task closure:**
   - Return the actual release-artifact diff, post-edit results, preserved behavior, unverified scope, residual risk, and next independent-review owner.
   - Obtain explicit authority before any production or privileged action.
   - Leave approval to an independent reviewer.
3. **Review closure:**
   - Return `Go`, `No-Go`, or `Blocked` with severity-ranked findings, reviewed and unreviewed scope, and proof limits.
   - Use `Blocked` for inaccessible required evidence, naming missing evidence, unblock condition, repair owner, and handoff.
   - Make no edit, deployment, or rollback.
4. **Release boundary and artifact:** State the target environment and affected pipeline, artifact, configuration, or secret boundary.
   - State build and promotion identity.
   - State material provenance or reproducibility needs and behavior-preservation evidence.
5. **Rollout, watch, and authority:** State blast radius, selected exposure strategy, and approval or authority boundary.
   - State stop and containment signals, owner, and required watch evidence.
   - Justify rolling, canary, blue-green, phased, or direct rollout from current risk.
6. **Compatibility, migration, and recovery:** When versions or data states can coexist, state ordering, skew or consumer behavior, reconciliation, and cleanup boundary. Rollback, restore, or forward-repair outcomes and rehearsal evidence apply only when reversibility, impact, change type, or policy triggers them.
7. **IaC, Helm, and GitOps:** When declarative infrastructure is affected, state its desired/effective or rendered change and resource/account/namespace boundary. Also state authority, state/sync/drift behavior, present hooks or CRDs, blast radius, and selected containment/recovery evidence for the actual toolchain.
8. **Hotfix, regulated, and limits:** When incident mitigation is involved, distinguish mitigation from resolution.
   - State the incident owner and validation signal.
   - For a policy-defined regulated release, state required approval, provenance or audit evidence, owner, retention, and exception.
   - Tie artifacts to claims.
   - Name unproven production, consumer, and data risks.

## Quality Gate

1. When promotion, provenance, or reproducibility risk requires stable artifact identity, prove non-drifting bytes and source or build identity.
   - Use an artifact-system control without universally banning mutable labels.
2. When environment differences can change affected behavior, require equivalence evidence only for material dimensions.
   - Material dimensions include configuration, dependency endpoint, identity, policy, topology, and data shape.
   - Select staging, ephemeral environments, rendered comparison, or production-safe checks from current risk.
3. When failure may require reversal or recovery, establish an evidenced outcome for rollback, restore, forward repair, disablement, or containment. Require execution or rehearsal only when risk, policy, prior failure, or change type warrants it; a documented command alone is not proof.
4. When blast radius or delivery policy warrants controlled exposure, require explicit authority and containment signals.
   - Require owned observation through a delivery mechanism selected from current capabilities and risk.
5. When migration, contract, or version skew can expose incompatible code/data/consumers, require coexistence, ordering, reconciliation, and cleanup proof. Expand/contract, dual operation, tolerant readers, coordinated cutover, or forward-only repair are candidates chosen from actual compatibility and recovery constraints.
6. When IaC, Helm, Kubernetes, or GitOps changes effective infrastructure, require an inspectable intended/effective diff, blast radius, authority, state/sync/drift behavior, and containment evidence. Plan, render, policy check, server-side dry run, GitOps preview, or targeted test are candidates supported by the toolchain.
7. When an incident hotfix or regulated release is triggered, require only the applicable outcomes. Incident evidence covers the mitigation or resolution boundary, owner, and validation signal; regulated-release evidence covers approval, provenance, audit, retention, and exceptions. Regulated artifacts and fixed incident roles remain conditional on policy or incident evidence.
