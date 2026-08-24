from __future__ import annotations

import hashlib
import json
import re
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import build as BUILD
import validation_utils as VALIDATION

G2_BASE_MANIFEST_DIGEST = (
    "43beb22720f6848259dfd28883e6cf52742de81660d78b53a65b87f0ffe9d08c"
)
G2_BASE_BATCHES = {
    "B0": (
        "logging-design-gate",
        "audit-evidence-integrity",
        "secret-configuration-security",
        "logging-error-handling",
    ),
    "B1": (
        "ai-code-review-refactor",
        "architecture-impact-reviewer",
        "change-documentation-gate",
        "data-api-contract-changer",
        "data-middleware-change-builder",
        "delivery-release-gate",
        "frontend-change-builder",
        "high-risk-design-review",
        "installed-client-change-builder",
        "integration-change-builder",
        "platform-infrastructure-change-builder",
        "quality-test-gate",
        "reliability-observability-gate",
        "repository-tooling-change-builder",
        "security-privacy-gate",
    ),
    "B2": (
        "authentication-authorization",
        "authentication-security",
        "cryptography-key-lifecycle",
        "dependency-vulnerability-scanning",
        "permission-boundary-modeling",
        "privacy-data-lifecycle",
        "tenant-isolation",
        "threat-modeling",
        "web-security",
    ),
    "B3": (
        "backup-recovery",
        "concurrency-control",
        "configuration-runtime-policy",
        "data-migration-design",
        "degradation-circuit-breaking",
        "distributed-workflow-consistency",
        "failure-contract-design",
        "idempotency-retry-design",
        "observability",
        "offline-sync-conflict-resolution",
        "release-rollback",
        "transaction-consistency",
    ),
    "B4": (
        "api-contract-design",
        "consumer-impact-analysis",
        "contract-testing",
        "design-pattern-selection",
        "domain-object-identification",
        "implementation-structure-design",
        "minimal-correct-implementation",
        "model-boundary-mapping",
        "module-boundary-design",
        "sdk-library-contract-design",
        "state-management-design",
        "technology-stack-selection",
        "version-compatibility",
    ),
    "B5": (
        "client-application-testing",
        "code-clarity-maintainability",
        "code-review",
        "documentation-generation",
        "refactoring",
        "regression-testing",
        "repeat-failure-analysis",
        "targeted-validation-selection",
        "test-data-management",
        "test-strategy",
    ),
    "B6": (
        "accessibility-inclusive-design",
        "build-tool-professional-usage",
        "client-lifecycle-state-restoration",
        "csharp-dotnet-professional-usage",
        "infrastructure-as-code-safety",
        "interaction-state-modeling",
        "kotlin-professional-usage",
        "powershell-professional-usage",
        "swift-professional-usage",
        "web-platform-professional-usage",
    ),
    "B7": (
        "android-platform-extension",
        "cross-platform-client-extension",
        "ios-ipados-platform-extension",
        "linux-desktop-platform-extension",
        "macos-platform-extension",
        "windows-platform-extension",
    ),
    "B8": (
        "ai-product-extension",
        "cloud-platform-extension",
        "iot-embedded-extension",
    ),
}
G2_BASE_EXPECTED_REFERENCE_COUNTS = {
    "B0": 12,
    "B1": 48,
    "B2": 26,
    "B3": 34,
    "B4": 30,
    "B5": 19,
    "B6": 20,
    "B7": 37,
    "B8": 7,
}
G2_PHASE8_OWNERS = {
    "payment-trading-extension",
    "web3-product-extension",
    "bigdata-product-extension",
    "low-level-systems-extension",
}
G2_BASE_SAFE_REFERENCES = {
    "ai-code-review-refactor/references/checklist.md",
    "api-contract-design/references/checklist.md",
    "change-documentation-gate/references/checklist.md",
    "code-clarity-maintainability/references/checklist.md",
    "code-review/references/checklist.md",
    "documentation-generation/references/checklist.md",
    "domain-object-identification/references/checklist.md",
    "engineering-artifact-review/references/review-checklist.md",
    "repeat-failure-analysis/references/repeat-failure-checklist.md",
    "routing-quality-review/references/routing-maintenance-checklist.md",
}
G2_BASE_COMPLETED_BATCHES: frozenset[str] = frozenset({"B0", "B1", "B2", "B3", "B4", "B5", "B6", "B7", "B8"})

ALL_ROLES = ("analysis-agent", "task-agent", "review-agent")
TASK_FIRST_ROLES = ("task-agent", "review-agent", "analysis-agent")


G2_BASE_B0_MOVE_SPECS = (
    (
        "logging-design-gate",
        """- Log only for a named diagnostic, audit, security, or operational question; prefer another signal or no new signal when it answers better.
- Place one event at the boundary owning the outcome; do not duplicate intermediate retries, wrappers, and terminal failures.
- Select level and stable schema from current logger policy, event meaning, and reachable failure states.
- Allow only purpose-required fields; omit or transform secrets, credentials, sensitive payloads, and unnecessary personal data under current policy.
- Preserve only the correlation needed across affected request, trace, message, or job boundaries without exposing raw identity.
- Bound material rate, value-space, retention, access, sink, cost, cardinality, and audit risk with measured/platform evidence and an owner.""",
        "a4475062a80f1a0449fbab1eef97e3c39af9b79f3ba99ecae4aed0fa915fea88",
        "src/professional-skills/logging-design-gate/references/logging-selection-criteria.md",
        ("task-agent", "review-agent"),
        ("selected-approach", "residual-risk"),
    ),
    (
        "logging-design-gate",
        """- Raw payload logging creates a durable privacy incident.
- Intermediate retry errors can create false incidents before the terminal outcome is known.
- High-cardinality fields, hot-path events, or an error without useful context can make the signal unusable.""",
        "195ff74d472e83251f4facdeca2b80377631d22600dec5584bb902a6ef70c961",
        "src/professional-skills/logging-design-gate/references/logging-selection-criteria.md",
        ("task-agent", "review-agent"),
        ("selected-approach", "residual-risk"),
    ),
    (
        "logging-design-gate",
        """1. Trace the named operational question to one owning event boundary and consumer action.
2. Choose level, schema, fields, redaction, correlation, and sink from current policy.
3. Verify failure visibility, duplicate emission, cardinality, rate, retention, and sensitive-data behavior.
4. **Task mode:** apply the logging decision at the owning event boundary.
5. **Review mode:** judge every changed event path against safe-logging criteria.
6. Stop when event purpose, owner, or data classification is unproven.""",
        "0f4642ed8b6248f6b19b0ba9530ccec5dae995bc6bcf243a23c761b316a86622",
        "src/professional-skills/logging-design-gate/references/checklist.md",
        ("task-agent", "review-agent"),
        ("checklist-result", "validation-plan"),
    ),
    (
        "audit-evidence-integrity",
        """- Define the audit question, critical outcomes and sources, expected records, time window, and completeness reconciliation.
- Preserve authoritative human/service identity, effective actor, delegation, session, tenant, purpose, and stable causation/correlation identities.
- Record occurrence, commit, and receipt time with source, offset, sync health, precision, uncertainty, and no unsupported global order.
- A critical event is missing without a coverage alarm.
- Shared actor identity hides who acted.
- Clock skew is misrepresented as reliable order.
- Broken correlation severs cause from outcome.
- Generate normal, denied, failed, delegated, administrative, and partial paths; reconcile expected records.""",
        "b582b29b1e3b34ce0774c7e82fc1a60f2e276eadb626581a889976926efc494d",
        "src/foundation/capabilities/audit-evidence-integrity/references/completeness-identity-and-time.md",
        ("analysis-agent", "task-agent", "review-agent"),
        ("decision-record", "boundary-decision", "proof-limit"),
    ),
    (
        "audit-evidence-integrity",
        """- Preserve canonical records and schema versions while treating views and transformations as derived evidence with lineage.
- Separate administration from producers and subjects, protecting records, integrity metadata, keys, policy, validation configuration, and privileged-use evidence.
- Select one composition-specific verification contract and bind what sequences, checkpoints, signatures, hashes, storage controls, and reconciliation each cover. An isolated hash proves only its bound bytes and cannot by itself prove deletion, truncation, replay, or reordering.
- A mutable admin path alters protected evidence.
- Delete, alter, replay, duplicate, reorder, skew clocks, break correlation, and exercise privileged access.""",
        "629a575291a67eca441d3d8c6e8e9e5ceaa343ac780d6ec6babcaa51ab74d0dd",
        "src/foundation/capabilities/audit-evidence-integrity/references/tamper-evidence-storage-and-access.md",
        ("analysis-agent", "task-agent", "review-agent"),
        ("evidence-record", "validation-plan", "proof-limit"),
    ),
    (
        "audit-evidence-integrity",
        """- Enforce retention and hold policy across records, indexes, replicas, backups, exports, and verification material without legal conclusions.
- Bind access, export, and custody to selector, time range, schema, counts, integrity proof, actor, purpose, transfer, receipt, and verification.
- A retention gap silently removes evidence.
- Export transformation changes meaning or integrity.
- A custody gap leaves a handoff unverifiable.
- Verify exports across transformation/handoff; exercise retention, hold, expiry, and custody transitions.""",
        "c02d861edfacf6d3449c6466b255910efb10c3ddb45b2d1274c1567e7d582f35",
        "src/foundation/capabilities/audit-evidence-integrity/references/retention-export-and-chain-of-custody.md",
        ("analysis-agent", "task-agent", "review-agent"),
        ("boundary-decision", "decision-record", "residual-risk"),
    ),
    (
        "secret-configuration-security",
        """- Trace changed values through source and history, CI variables and logs, build cache and image layers, client bundles and source maps, runtime manifests, observability sinks, support exports, backups, and offline consumers.
- Treat a plausibly exposed credential as compromised according to its authority and policy: contain access, rotate or revoke, verify consumer adoption, then decide whether history or artifact cleanup is also required.
- Design rotation as a state transition across known consumers. Define overlap or dual-read behavior when required, adoption evidence, revoke criteria, failure recovery, and a forward-safe rollback that does not revive compromised material.
- Deleting a committed value, masking a CI setting, or removing one log line does not revoke copies already present in history, caches, artifacts, or external sinks.
- Public build prefixes, client-side config, serialized request objects, crash reports, and support exports can cross the intended audience boundary without an obvious “secret” field name.
- Rollback to an old compromised value is re-exposure, not recovery.""",
        "8d58ae6a1b6d93f7743a2fb33e5d0dbb79fc17c3ee64287ac734246f930df8ab",
        "src/foundation/capabilities/secret-configuration-security/references/benchmarks-and-patterns.md",
        ("analysis-agent", "task-agent", "review-agent"),
        ("option-comparison", "selected-approach"),
    ),
    (
        "secret-configuration-security",
        """- Scope storage and decrypt authority by principal, purpose, operation, environment, tenant, and lifetime; include audit, break-glass, deletion recovery, and inaccessible-consumer ownership where material.
- Separate sensitivity from mechanism: environment variables, encryption, masking, or a managed store do not by themselves prove least privilege, non-exposure, rotation safety, or recovery.
- Escalate security-sensitive defaults or config changes that weaken authentication, transport, authorization, isolation, rate control, or data protection; general config semantics remain with `configuration-runtime-policy`.""",
        "101aedc8cfb0e2f2eb529283745e0719f9a316e778bca4eac222f7ea8b0e1e09",
        "src/foundation/capabilities/secret-configuration-security/references/checklist.md",
        ("analysis-agent", "task-agent", "review-agent"),
        ("checklist-result", "residual-risk"),
    ),
    (
        "secret-configuration-security",
        "- Keep raw values out of prompts, commands, diffs, fixtures, screenshots, reports, and retained scanner output. Validate transformation-aware redaction with representative secret-bearing shapes and downstream sinks.",
        "d41c9a716f50faacc9cb1133774675fe3a99c92a79d0f18d5db99efae7f12680",
        "src/foundation/capabilities/secret-configuration-security/references/evidence-patterns.md",
        ("analysis-agent", "task-agent", "review-agent"),
        ("evidence-record", "proof-limit", "residual-risk"),
    ),
    (
        "logging-error-handling",
        """- **Define error ownership and external meaning.** Preserve causal context across layers while translating only at owned boundaries; distinguish user, domain, dependency, transient, permanent, cancellation, and unexpected outcomes relevant to caller action.
- **Log an owned diagnostic event, not arbitrary data.** Name audience, decision enabled, event point, stable identity, outcome, and retention need before selecting fields or severity.
- **Preserve correlation across attempts and effects.** Carry request, operation, trace, job, message, tenant-safe, and real or effective actor identity needed to reconstruct a causal path without confusing retries with distinct business operations.
- **Classify terminal outcome accurately.** Avoid reporting handled intermediate retries, expected denial, cancellation, or fallback as terminal errors, and avoid hiding exhausted or partially applied work behind informational success.
- **Minimize sensitive and unbounded content.** Exclude secrets and raw bodies by default, transform personal or regulated fields according to current policy, and bound message, stack, collection, key, and payload expansion.
- **Control volume and cardinality at the source.** Derive event rate, level, sampling, aggregation, dynamic labels, and hot-path detail from current diagnostic need, cost, and incident consequence.
- **Separate diagnostics from audit records.** Identify the security-relevant outcome, accepted audit dependency, unresolved semantics, integrity, retention, access, sink, or durability, named specialist handoff, and gap without claiming protected-record closure.
- Log the same exception at each layer, producing duplicate noise without additional ownership or action.
- Store raw requests, tokens, personal data, stack detail, or dynamic high-cardinality values because they might help later.
- Treat a fallback or retry as success while the original failure, final disposition, or lost effect cannot be reconstructed.""",
        "a99373326f967f07ffb72713f0a19039a89913295b1c607e8d21418802f34a61",
        "src/foundation/capabilities/logging-error-handling/references/benchmarks-and-patterns.md",
        ("task-agent", "review-agent"),
        ("option-comparison", "selected-approach"),
    ),
    (
        "logging-error-handling",
        "- **Prove failure reconstruction and redaction.** Exercise representative normal, denied, retry, timeout, cancellation, partial, and unexpected paths, then verify correlation, terminal classification, sensitive-field handling, and proof limits.",
        "df3cd80422caf34cbff3d6bc4468a63e0144e40f7ebdc26ef9fa9bb3f1ba3986",
        "src/foundation/capabilities/logging-error-handling/references/evidence-patterns.md",
        ("task-agent", "review-agent"),
        ("evidence-record", "proof-limit", "residual-risk"),
    ),
)

G2_BASE_B1_MOVE_SPECS = (
    (
        "ai-code-review-refactor",
        """## Professional Decision Rules

- Judge every changed path in the actual latest diff within the fixed boundary.
- Apply fixed review-risk selection and Core relation, severity, evidence, repair, and re-review rules without mutation, rerouting, or inferred approval.

## High-Value Gotchas

- A summary or self-review is not an independent review of the actual diff.

## Execution Checklist

1. Inspect the actual diff, affected contracts, tests, and fixed review-risk selection.
2. Return reachable findings or an explicit no-finding result with proof limits.""",
        "72bd65befa341a90947eae3fa21ad1180c91adf1b702fdc77bb85ce94838593e",
        "src/professional-skills/ai-code-review-refactor/references/checklist.md",
        ("review-agent",),
        ("checklist-result", "residual-risk"),
    ),
    (
        "architecture-impact-reviewer",
        """## Professional Decision Rules

- When new structure or a boundary is proposed, place behavior with the owner of its reason to change and preserve the affected dependency direction.
- Reuse an abstraction only when its contract and ownership match current evidence.
- Similarity alone does not justify reuse.
- Skip reuse proof for owner-internal edits without structural change.
- Compare the smallest local design with broader alternatives using only material change-locality, coupling, compatibility, operability, and deletion constraints.
- Require placement and ownership rationale only for proposed files, services, shared helpers, dependencies, public surfaces, or moved responsibilities that change structure.

## High-Value Gotchas

- Orphaned shared abstractions accumulate coupling.

## Execution Checklist

1. Trace current owner, consumers, and dependency direction.
2. Compare the smallest local placement with material alternatives.""",
        "0c8779881d6836249467104b5618eef866852330505791a552363bb4eab9644b",
        "src/professional-skills/architecture-impact-reviewer/references/placement-and-ownership.md",
        ("analysis-agent", "review-agent"),
        ("boundary-decision", "selected-approach", "residual-risk"),
    ),
    (
        "architecture-impact-reviewer",
        "3. Verify compatibility, reversibility, deletion cost, and enforcement boundaries.",
        "9ed8ffa4c392a1eee242b25de8b4096e8388cbfc0e926ec635a7956a46af1a7a",
        "src/professional-skills/architecture-impact-reviewer/references/reversibility-evolution-and-proof-limits.md",
        ("analysis-agent", "review-agent"),
        ("decision-record", "validation-plan", "proof-limit", "residual-risk"),
    ),
    (
        "architecture-impact-reviewer",
        "4. **Analysis mode:** select placement and rejected alternatives.",
        "667fa0168e34f29abf2a06d9c440f62aa2b4b9c5f8808647cb3ed6b1d1605d0f",
        "src/professional-skills/architecture-impact-reviewer/references/placement-and-ownership.md",
        ("analysis-agent", "review-agent"),
        ("boundary-decision", "selected-approach", "residual-risk"),
    ),
    (
        "architecture-impact-reviewer",
        "5. **Review mode:** judge placement, dependency direction, and enforcement.",
        "2e37a76c1f97b3c6f938646ec6460d6118a29fa121df692c68d74546192dda7e",
        "src/professional-skills/architecture-impact-reviewer/references/dependency-topology-and-enforcement.md",
        ("analysis-agent", "review-agent"),
        ("boundary-decision", "gate-decision", "validation-plan", "residual-risk"),
    ),
    (
        "architecture-impact-reviewer",
        "6. Stop when evidence cannot support one placement.",
        "1cb2950573cf74af472d9e994ada8cdf5802ecf644e7f0003ad5b9fd00ecb150",
        "src/professional-skills/architecture-impact-reviewer/references/placement-and-ownership.md",
        ("analysis-agent", "review-agent"),
        ("boundary-decision", "selected-approach", "residual-risk"),
    ),
    (
        "change-documentation-gate",
        """## Professional Decision Rules

- Update documentation when behavior, public contract, configuration, operations, migration, deprecation, or user workflow changes.
- Keep examples executable and consistent with current names, defaults, errors, and version behavior.
- Place facts in the owning source document and link rather than duplicate unstable details.
- Validate links, commands, generated outputs, and migration instructions against the final implementation.

## High-Value Gotchas

- Stale examples are worse than missing examples.
- Generated docs must be changed at their source.
- A migration guide without rollback and version boundaries is incomplete.

## Execution Checklist

1. Trace the behavior delta to its audience, owning document, generated origin, and version boundary.
2. Choose update, migration note, deprecation guidance, or evidence-backed no-docs treatment.
3. Verify examples, commands, links, rollback guidance, and safe-disclosure boundaries.
4. **Task mode:** update the owning source for the accepted behavior delta.
5. **Review mode:** judge examples, commands, links, and migration guidance.
6. Stop closure when source behavior and published guidance cannot be reconciled.""",
        "0f4f8369f379c6114f0b77210db923e0b9eb303a9ab198ab2bf6cf04f85f3d6f",
        "src/professional-skills/change-documentation-gate/references/checklist.md",
        ("task-agent", "review-agent"),
        ("checklist-result", "residual-risk"),
    ),
    (
        "data-api-contract-changer",
        """## Professional Decision Rules

- Treat the accepted API, event, schema, error, or data-format delta as one producer-to-consumer transition; load the named Reference for compatibility, migration, null/default, version, generated-surface, replay, or rollback decisions.""",
        "3c741fa05ad72f7752076b54635030d0d8b2e5fbec0c2e27d22fe3192aacfd30",
        "src/professional-skills/data-api-contract-changer/references/checklist.md",
        ("analysis-agent", "task-agent"),
        ("checklist-result", "residual-risk"),
    ),
    (
        "data-middleware-change-builder",
        """## Professional Decision Rules

- Name the source of truth, consistency model, transaction boundary, and ownership for every stateful change.
- Design migrations for version coexistence, backfill idempotency, restartability, verification, and rollback.
- For caches and queues, define invalidation, ordering, duplication, replay, poison-message, and degradation behavior.
- Use realistic data volume and concurrency evidence for query, index, lock, and partition choices.

## High-Value Gotchas

- Cache invalidation without a source-of-truth rule serves stale data.
- A migration that cannot resume safely turns failure into manual recovery.
- Queue acknowledgement order can lose or duplicate work.

## Execution Checklist

1. **Analysis mode:** select consistency and recovery behavior from sink evidence.
2. **Task mode:** apply the accepted boundary with replay and reconciliation behavior.
3. Stop when state ownership or reconciliation remains implicit.""",
        "279f9328e5523877785f910d6679adf73a1164927b2f49bca43e5f9715a35689",
        "src/professional-skills/data-middleware-change-builder/references/checklist.md",
        ("analysis-agent", "task-agent"),
        ("checklist-result", "residual-risk"),
    ),
    (
        "delivery-release-gate",
        """## Professional Decision Rules

- Prove material artifact/configuration/compatibility/migration/rollout/observability/recovery dimensions.
- Select rollout, watch, approval, and containment from blast radius, reversibility, controls, and policy.
- When triggered, test old/new coexistence or recovery against the artifact and material environment.
- Destructive, production, privileged, or irreversible action needs explicit user authority.

## High-Value Gotchas

- A rollback command does not prove recovery.
- Clean deployment can miss version skew.
- Early cleanup can remove recovery.

## Execution Checklist

1. Trace artifact identity, configuration, migration, compatibility, blast radius, and recovery owner.
2. Choose rollout/watch/containment/rollback from reversibility and policy.
3. Verify mixed-version behavior, promotion provenance, stop signals, and recovery.
4. **Analysis mode:** select the release controls.
5. **Task mode:** produce the release metadata.
6. **Review mode:** judge the release evidence.
7. Stop if authority, artifact identity, or recovery proof is implicit.""",
        "9da039ec8ca7de916432367f6ab14de56787446743193b6c2272a5c60859f906",
        "src/professional-skills/delivery-release-gate/references/delivery-output-and-gates.md",
        ("analysis-agent", "task-agent", "review-agent"),
        ("gate-decision", "residual-risk"),
    ),
    (
        "frontend-change-builder",
        """## Professional Decision Rules

- Keep state in the narrowest correct owner and derive rather than duplicate state.
- Handle loading, empty, error, success, disabled, permission, cancellation, retry, and stale-response behavior for async work.
- Reuse design-system components and preserve keyboard, focus, semantic, responsive, and screen-reader behavior.
- Map UI acceptance to component, integration, accessibility, and visual validation proportional to risk.

## High-Value Gotchas

- Duplicated derived state drifts.
- Unmount, cancellation, and out-of-order responses create race defects.
- Automated accessibility checks do not prove keyboard and screen-reader flows.

## Execution Checklist

1. Trace the affected interaction states, API outcomes, focus path, and responsive behavior.
2. Choose state ownership and component reuse from current design-system and lifecycle evidence.
3. Implement the bounded behavior with explicit cancellation, denial, failure, and recovery paths.
4. Stop closure when an affected state lacks accessibility or behavior proof.""",
        "1f20122f1d748c1d8e6912ca2ecde6d1638d49621024db31c621f59ea452cc39",
        "src/professional-skills/frontend-change-builder/references/checklist.md",
        ("task-agent",),
        ("checklist-result", "residual-risk"),
    ),
    (
        "high-risk-design-review",
        """## Professional Decision Rules

- Test the brief as four connected dimensions: problem and acceptance; ownership and invariants; placement, contract, and failure design; acceptance-to-validation mapping.
- Require decisions only when they change downstream work, risk, rollback, or user-visible behavior.
- Confirm the First Executable Slice remains safe, verifiable, and reversible.
- Reject dependency cycles, conflicting writes, unowned shared contracts, and rollback claims without an executable path.

## High-Value Gotchas

- More artifacts do not improve accuracy when they repeat the same facts.
- A complete-looking brief can still name the wrong owner or omit version skew and failure behavior.
- Review breadth must remain proportional to the concrete risk.

## Execution Checklist

1. Verify source evidence and acceptance.
2. Check owner, invariants, reuse, and rejected placements.
3. Check public contract, data, failure, compatibility, and rollback effects.
4. Check dependencies, workspace requirements, integration, review, and validation boundaries.""",
        "1ed187bf3187d10cd7ad53075a8a0cf8c71e2fa4fa334385f35eb3b508cacc92",
        "src/professional-skills/high-risk-design-review/references/design-review-checklist.md",
        ("review-agent",),
        ("checklist-result", "residual-risk"),
    ),
    (
        "installed-client-change-builder",
        """## Professional Decision Rules

- Load only the active native-platform and framework References.
- Load a Domain decision's evidence companion only through the accepted carrier.
- Preserve the accepted route and narrowest current source seam.
- Do not infer a target from a framework.
- Do not select a new Professional, Domain, or Layer3.

## High-Value Gotchas

- Shared or framework checks do not prove native lifecycle, packaging, or final
  artifact behavior.

## Execution Checklist

1. Inspect the accepted owner, minimum consumer, tests, targets, and package facts.
2. Implement the smallest complete change at the current seam.
3. Validate each affected target and report unavailable checks and proof limits.""",
        "87414f34a8acf4f2cac4358d1910767297d28fc5d8375d8d5c37c47f00975768",
        "src/professional-skills/installed-client-change-builder/SKILL.md",
        ("task-agent",),
        ("proof-limit", "selected-approach", "validation-plan"),
    ),
    (
        "integration-change-builder",
        """## Professional Decision Rules

- Align affected producer and consumer contracts before resolving implementation conflicts.
- Define triggered timeout, retry, idempotency, ordering, authentication, version-skew, and partial-failure behavior at the boundary.
- Derive the exact signed representation and permitted transformation or canonicalization from the current provider contract.
- Preserve raw bytes only when the current provider contract defines raw bytes as the signed representation.
- Complete verification, freshness, and replay checks before an operation changes the signed representation or causes effects.
- Keep integration ownership explicit; do not hide a shared contract inside a local adapter.
- Validate the integrated diff and changed cross-boundary behavior, not only isolated components.

## High-Value Gotchas

- Passing component tests does not prove the integrated contract.
- Retries across a non-idempotent boundary amplify failures.
- Conflict resolution can silently choose one owner’s incompatible assumption.

## Execution Checklist

1. Trace producer, consumer, authority, timeout, duplicate, and partial-failure behavior across the boundary.
2. Choose retry, idempotency, reconciliation, and version-skew controls from provider semantics.
3. Derive the exact signed representation and permitted transformation or canonicalization from the current provider contract.
4. Prove verification, freshness, and replay checks precede representation-changing operations and effects.
5. Verify credential containment, recovery, and integrated consumer behavior.
6. **Analysis mode:** select timeout, duplicate, and reconciliation behavior from provider evidence.
7. **Task mode:** apply the accepted boundary across producer and consumer paths.
8. Stop when provider authority or reconciliation ownership remains unknown.""",
        "1ed64b7e982ae1d85fa3d93e8a2c0cef9328a8c51d4bc36bf2aacfdb24b7fe3c",
        "src/professional-skills/integration-change-builder/references/checklist.md",
        ("analysis-agent", "task-agent"),
        ("checklist-result", "validation-plan"),
    ),
    (
        "platform-infrastructure-change-builder",
        """## Professional Decision Rules

- Separate state layers; change the smallest owner; bind secret-free non-mutating proposal evidence to target/versions.

## High-Value Gotchas

- Proposal evidence is neither execution authority nor convergence proof.""",
        "f0eb19d6866b31cbd4e5dc0b1e1ab79d5af5dd271d9e546734332c40384fdb66",
        "src/professional-skills/platform-infrastructure-change-builder/references/iac-source-contracts.md",
        ("task-agent",),
        ("proof-limit", "selected-approach", "validation-plan"),
    ),
    (
        "quality-test-gate",
        """## Professional Decision Rules

- Own proof strategy and acceptance-to-signal mapping before command selection.
- Use `targeted-validation-selection` only after strategy selection, and only for repository-defined command and coverage selection.
- Leave evidence timing and refresh decisions to Core Guard G and the validation-freshness contract.
- Map scoped acceptance and material risk to the smallest test levels that exercise the regression and negative mechanisms under deterministic controls.

## High-Value Gotchas

- A broad green suite can miss the changed mechanism.
- A result becomes stale after a material source, test, fixture, schema, or config edit.
- Lint, type checks, and manual inspection do not substitute for behavior proof.

## Execution Checklist

1. Select strategy before commands.
2. **Analysis mode:** Map acceptance to proof.
3. **Task mode:** Add the smallest proving test.
4. **Review mode:** Judge coverage and freshness.
5. Stop when changed behavior or acceptance remains unverified.""",
        "22ba77cd90166a20d0e0bdb6bcf8812e9eef496e90290c741aea2fd033fc5a66",
        "src/professional-skills/quality-test-gate/references/checklist.md",
        ("analysis-agent", "task-agent", "review-agent"),
        ("checklist-result", "validation-plan"),
    ),
    (
        "reliability-observability-gate",
        """## Professional Decision Rules

- Define affected failure modes, user impact, recovery owner, and any decision-relevant operating objective.
- Require an SLI or SLO only when an owned objective has a decision consequence.
- Apply timeouts, backpressure, retry budgets, circuit breaking, and degradation only where latency or load risk triggers them.
- Select only actionable signals, alerts, and runbook links justified by current risk.
- Validate triggered restart, failover, replay, rollback, and capacity assumptions proportionally.

## High-Value Gotchas

- Retries can worsen overload.
- An alert without an operator action is noise.
- Average latency hides tail failure.

## Execution Checklist

1. Trace the failure mode through user impact, dependency pressure, telemetry, and recovery ownership.
2. Choose objectives, timeouts, retry budgets, degradation, and alerts only when current risk triggers them.
3. Verify restart, failover, replay, rollback, capacity, and operator-action assumptions where material.
4. **Analysis mode:** select objectives and recovery controls from failure evidence.
5. **Task mode:** apply accepted controls at the affected runtime boundary.
6. **Review mode:** judge restart, failover, capacity, and operator-action evidence.
7. Stop when a material objective or recovery action lacks evidence and ownership.""",
        "54c54124598e49f602a21f5be5b17290c2741802190eff102a066be80b1a6aba",
        "src/professional-skills/reliability-observability-gate/references/checklist.md",
        ("analysis-agent", "task-agent", "review-agent"),
        ("checklist-result", "residual-risk"),
    ),
    (
        "repository-tooling-change-builder",
        """## Professional Decision Rules

- Inspect the owner, minimum consumer, tests, adjacent utilities, and reuse before adding structure.
- Declare behavior-affecting inputs and environment; reject ambient workstation or cache state as proof.
- Validate the selected generator, plugin, harness, or automation mechanism through its named Reference.
- Stay within the accepted owner; do not widen public APIs or refactor unrelated tooling for tests.

## High-Value Gotchas

- Ambiguous generated authority, ambient state, or a false-green harness invalidates proof.

## Execution Checklist

1. Inspect owner, consumer, invocation, tests, generated surfaces, versions, and reuse.
2. Map normal, invalid, interrupted, rerun, and forbidden outcomes.
3. Make the smallest complete change.
4. Validate after the latest edit and report limits.""",
        "6dcb9aa2d6e495be39a66ffa0ba7f8024cbe1d2649a9730cfd8c95165dcb4f8f",
        "src/professional-skills/repository-tooling-change-builder/references/repository-automation-contracts.md",
        ("task-agent",),
        ("decision-record", "failure-decision", "proof-limit"),
    ),
    (
        "security-privacy-gate",
        """## Professional Decision Rules

- Trace the accepted trust-boundary delta from controlled source or authority to the protected asset and reachable sink, then select controls at the effective path.
- Mutability, future replacement, or bounded same-principal non-sensitive local access without privilege elevation or a less-trusted writer does not prove a material abuse path.

## High-Value Gotchas

- Authentication is not object-level authorization; redaction after serialization is late.
- A security claim without negative-path evidence remains unverified.

## Execution Checklist

1. **Analysis mode:** select controls from the reachable abuse path.
2. **Task mode:** apply controls at the effective trust boundary.
3. **Review mode:** judge denied paths, containment, and residual exposure.
4. Stop when trust boundaries, policy, or exploit-relevant evidence remain unknown.""",
        "126cb0fe32efb3db86e2ce9dbf92b84dc5d126d6e0a39223fa765570a4023985",
        "src/professional-skills/security-privacy-gate/references/security-output-and-gates.md",
        ("analysis-agent", "task-agent", "review-agent"),
        ("gate-decision", "residual-risk"),
    ),
)

G2_BASE_B1_NEW_ANCHORS = {
    "installed-client-change-builder": """## Professional Decision Rules

- Preserve the accepted route/targets through active named References and carriers.
- Inspect owner, consumers, tests, and target/package facts before the smallest complete change.
- Record target checks, unavailable evidence, proof limits, and residual risk.""",
    "repository-tooling-change-builder": (
        "Inspect owner, consumer, tests, adjacent utilities, versions, reuse, and "
        "invalid, interrupted, and forbidden outcomes before the smallest complete "
        "change."
    ),
}

G2_BASE_B1_FINGERPRINT_NEW_ANCHORS = {
    "0c8779881d6836249467104b5618eef866852330505791a552363bb4eab9644b": """## Professional Decision Rules

- When new structure or a boundary is proposed, place behavior with the owner of its reason to change and preserve the affected dependency direction.
- Reuse an abstraction only when its contract and ownership match current evidence.
- Similarity alone does not justify reuse.
- Skip reuse proof for owner-internal edits without structural change.
- When placement remains open, compare the smallest local design with broader alternatives against material change-locality, coupling, compatibility, operability, and deletion constraints.
- Require placement and ownership rationale only for proposed files, services, shared helpers, dependencies, public surfaces, or moved responsibilities that change structure.

## High-Value Gotchas

- Orphaned shared abstractions accumulate coupling.

## Execution Checklist

1. Trace current owner, consumers, and dependency direction.
2. Compare the smallest local placement with material alternatives.""",
    "1ed64b7e982ae1d85fa3d93e8a2c0cef9328a8c51d4bc36bf2aacfdb24b7fe3c": """# Integration Checklist

- Name provider, owner, environment, producer/consumer contracts, version skew, authority, and partial-failure behavior.
- Define timeout, retry/backoff, circuit breaking, aggregate budget, idempotency, duplicates, unknown outcomes, ordering, compensation, and reconciliation.
- Derive the exact signed representation and permitted transformation or canonicalization from the current provider contract.
- Preserve raw bytes only when the provider contract defines raw bytes as the signed representation.
- Prove signature verification, freshness, and replay checks finish before representation-changing operations or effects.
- Keep payload, signature, token, cookie, authorization, secret, and credential data out of logs, source, images, configuration, and generated artifacts; own credential storage, rotation, and least privilege.
- Keep provider and generated models inside the adapter unless version, null, and default mappings are explicit.
- Validate sandbox/production and rate-limit differences, recovery, the integrated diff, consumers, and contract/failure/replay/monitoring behavior.
- Record provider/version, credential, artifact, consumer, log, reconciliation, release, skipped boundaries, command/result, freshness, proof limit, rollback, residual risk, next owner, and handoff.""",
    "9da039ec8ca7de916432367f6ab14de56787446743193b6c2272a5c60859f906": """# Delivery Output And Gates

Use this targeted Reference only when extended release-risk closure needs a gate decision.

## Gate Record

1. **Boundary and artifact:** target plus affected pipeline, artifact, configuration, or secret; immutable build/promotion identity; triggered provenance, reproducibility, and behavior proof.
2. **Rollout and authority:** blast radius, exposure, permission, stop/containment signals, and owned observation selected from consequence and reversibility.
3. **Compatibility and recovery:** coexisting version/data order, skew, consumer behavior, reconciliation, cleanup, and the recovery mechanism with fresh proof.
4. **Infrastructure:** desired/effective diff, authority, state/sync/drift, hooks/CRDs, blast radius, and containment/recovery for IaC, Helm, Kubernetes, or GitOps.
5. **Hotfix or regulated release:** mitigation/resolution owner and signal plus policy-triggered approval, provenance/audit, retention, exception, claim binding, and unproven risk.

## Decision Gates

1. Bind artifact bytes to source/build identity; mutable labels alone cannot establish identity.
2. Prove material environment equivalence across configuration, endpoints, identity, policy, topology, and data shape.
3. Select rollback, restore, repair, disablement, or containment from actual recovery constraints; commands alone are not proof.
4. Give controlled exposure explicit authority, containment signals, and owned observation.
5. Prove coexistence, ordering, reconciliation, cleanup, and rollback readability for triggered migration, contract, or version skew.
6. For effective infrastructure change, inspect diff, state/drift, blast radius, and containment.
7. Carry triggered incident/regulatory evidence; require source evidence for fixed roles or artifacts.

## Proof Limits

- Treat a clean deployment, rollback command, or early cleanup as insufficient for version-skew and recovery claims.
- Before a destructive, production, privileged, or irreversible action, require explicit user authority.""",
    "f0eb19d6866b31cbd4e5dc0b1e1ab79d5af5dd271d9e546734332c40384fdb66": """## Professional Decision Rules

- Separate state layers; change the smallest owner; bind secret-free non-mutating proposal evidence to target and versions.

## High-Value Gotchas

- Proposal evidence is neither execution authority nor convergence proof.""",
}

G2_BASE_B4_FINGERPRINT_NEW_ANCHORS = {
    "60d03130eb0ede742ed11124b55e050d1b32e9b187aa8b85499a4f898bfdc37e": (
        "- Do not assume consumers upgrade together, call behavior-changing additions "
        "safe, or remove a bridge by calendar without usage, stored-data, queue, and "
        "rollback evidence."
    ),
}

C1_FRAMEWORK_MOVE_SPECS = (
    (
        "installed-client-change-builder",
        "- Keep shared widget or state ownership separate from platform-channel ownership.",
        "5ac7e9f76ddbf7895ac8665c1d7a3d527eda5c96848696a794e0480ee3d1e30b",
        "src/professional-skills/installed-client-change-builder/references/flutter-framework-contracts.md",
        "- Keep shared widget or state ownership separate from platform-channel ownership.",
    ),
    (
        "installed-client-change-builder",
        "- Test restoration, links, plugins, and packaging on every affected release target.",
        "1cbbfaf237090f06645a51703c9d3bfca2a2b31e2bb4c849298ef58a68ab24e3",
        "src/professional-skills/installed-client-change-builder/references/flutter-framework-contracts.md",
        "- Test restoration, links, plugins, and packaging on each affected release target in the accepted target set.",
    ),
    (
        "installed-client-change-builder",
        "Pin the repository SDK, plugins, and native projects before deciding behavior.",
        "568e194ba4fe55ad56630e658d2c659d53cc7908e44156444ce7f3d20aae551e",
        "src/professional-skills/installed-client-change-builder/references/flutter-framework-contracts.md",
        "- Pin the repository SDK, plugins, and native projects before deciding behavior.",
    ),
    (
        "installed-client-change-builder",
        "- Distinguish JavaScript state from native application state and process recreation.",
        "960204d050aaffd31265b07b3d0159fe2d5bc96ac598f84f6a4c4e56cb75d0fb",
        "src/professional-skills/installed-client-change-builder/references/react-native-framework-contracts.md",
        "- Distinguish JavaScript state from native application state and process recreation.",
    ),
    (
        "installed-client-change-builder",
        "- Keep platform-specific behavior in the narrowest existing platform seam.",
        "fe522d7c571289793c909bcb7572fe4a091a412e983eb60ebdcca0cef9ba6e19",
        "src/professional-skills/installed-client-change-builder/references/react-native-framework-contracts.md",
        "- Keep platform-specific behavior in the narrowest existing platform seam.",
    ),
    (
        "installed-client-change-builder",
        "- Keep lifecycle and privileged operating-system work in the main-process owner.",
        "76da04f14ac7959ed72c1c67a12d8d5b521d59e38fa7a9ff165d8904e2715697",
        "src/professional-skills/installed-client-change-builder/references/electron-framework-contracts.md",
        "- Keep lifecycle and privileged operating-system work in the main-process owner.",
    ),
    (
        "installed-client-change-builder",
        "- Validate renderer-to-main boundaries, deep-link entry, and the packaged artifact.",
        "2279c22a3871e2f7720c035cf3a41f3c0351521d9af70199c52f8459591cb011",
        "src/professional-skills/installed-client-change-builder/references/electron-framework-contracts.md",
        "- Validate renderer-to-main boundaries, deep-link entry, and the packaged artifact.",
    ),
    (
        "installed-client-change-builder",
        "- Keep commands, plugins, capabilities, and webview callers inside their declared authority.",
        "867799315787341e86cba77a70f67b2e94d4e94bbb252d8575302307f77b7516",
        "src/professional-skills/installed-client-change-builder/references/tauri-framework-contracts.md",
        "- Keep commands, plugins, capabilities, and webview callers inside their declared authority.",
    ),
    (
        "installed-client-change-builder",
        "- Validate deep-link registration and the platform-specific bundle output.",
        "04096c94e95628761f7c2a36355439c7e2bd5ffe05a9742d725c471b2e67a386",
        "src/professional-skills/installed-client-change-builder/references/tauri-framework-contracts.md",
        "- Validate deep-link registration and the platform-specific bundle output.",
    ),
    (
        "installed-client-change-builder",
        "- Preserve top-level window ownership and platform-specific window-manager behavior.",
        "94d494533409826dea5fbcf46ac881cc9690644d3c8012de6ccf83a8768055d6",
        "src/professional-skills/installed-client-change-builder/references/qt-framework-contracts.md",
        "- Preserve top-level window ownership and platform-specific window-manager behavior.",
    ),
    (
        "installed-client-change-builder",
        "- Validate runtime libraries, plugins, QML modules, and platform package contents.",
        "bf240a1e6b011eed630c1fbaca49c865b9f820003448abac7b1dee1527e0c911",
        "src/professional-skills/installed-client-change-builder/references/qt-framework-contracts.md",
        "- Validate runtime libraries, plugins, QML modules, and platform package contents.",
    ),
    (
        "installed-client-change-builder",
        "- Map cross-platform window events to the affected native lifecycle.",
        "a9f947741f42530aafe3573266bcc152e11f4fc8ac621ceb939f96cc8f0ba265",
        "src/professional-skills/installed-client-change-builder/references/dotnet-maui-framework-contracts.md",
        "- Map cross-platform window events to the affected native lifecycle.",
    ),
    (
        "installed-client-change-builder",
        "- Validate platform lifecycle hooks, restored state, permissions, and each package target.",
        "94aec34444d5dae0e837bc08eed2d5f451952cd24f2df9238d25fad1f463b9af",
        "src/professional-skills/installed-client-change-builder/references/dotnet-maui-framework-contracts.md",
        "- Validate platform lifecycle hooks, restored state, permissions, and each package target.",
    ),
    (
        "installed-client-change-builder",
        "- Put shared behavior only in source sets whose declared targets support it.",
        "f122e0fbb6feba644bf72cce0287be317fa02ee322787ff5dc463ca38d03a7c5",
        "src/professional-skills/installed-client-change-builder/references/kotlin-multiplatform-framework-contracts.md",
        "- Put shared behavior only in source sets whose declared targets support it.",
    ),
    (
        "installed-client-change-builder",
        "- Validate each target compilation and final binary or host-application integration.",
        "1dccc73f2d3ee59cf28535a1692b54059a0b9cda1df77be6b710e2b5094ca099",
        "src/professional-skills/installed-client-change-builder/references/kotlin-multiplatform-framework-contracts.md",
        "- Validate each target compilation and final binary or host-application integration.",
    ),
)

C1_LANGUAGE_MOVE_SPECS = (
    ("csharp-dotnet-professional-usage", "- Preserve async ownership, `CancellationToken` propagation, context/dispatcher needs, observed exceptions, and caller-visible cancellation.", "b037ae80361d4b1f89f3cf2fcd1d0b6520fd7cf66f8ce8c54a8ac74588e85f18", "src/foundation/capabilities/csharp-dotnet-professional-usage/references/async-resource-and-iterator-contracts.md", "- **Async owner:** identify the returned/observed task, caller token, deadline, synchronization/dispatcher requirement, exception path, progress/result cardinality, and shutdown behavior."),
    ("csharp-dotnet-professional-usage", "- Define one owner and ordered cleanup for each disposable resource, including partial construction, repeated disposal, and cleanup failure.", "949596d426055ff432cf8b7d1aa17af1f63f9610306393e0f6c140fb1506293b", "src/foundation/capabilities/csharp-dotnet-professional-usage/references/async-resource-and-iterator-contracts.md", "- **Resource lifetime:** assign `IDisposable` and `IAsyncDisposable` ownership, construction order, reverse cleanup order, repeated cleanup, concurrent use, and primary-versus-cleanup exception behavior."),
    ("csharp-dotnet-professional-usage", "- Define iterator and LINQ execution plans by enumeration count, deferred effects, provider translation, cancellation, and resource lifetime.", "96f116b095dc4178afe2814e14811b30bda4feb56b3a8f1fcf0e02b6da44babf", "src/foundation/capabilities/csharp-dotnet-professional-usage/references/async-resource-and-iterator-contracts.md", "- **Iterator:** identify when code first executes, each enumeration and disposal site, partial enumeration, source mutation, failure timing, and resource held across `yield`."),
    ("csharp-dotnet-professional-usage", "- Validate nullable compiler contracts across reflection, serialization, interop, generated, and disabled-context runtime boundaries.", "e727c2e9c9b57c80bc07228bc1ca0e8d5a570a35ea74267c21ec77c7770b83bf", "src/foundation/capabilities/csharp-dotnet-professional-usage/references/async-resource-and-iterator-contracts.md", "- **Nullable boundary:** record nullable context and warnings plus runtime validation for reflection, serialization, interop, generated code, oblivious libraries, and collection elements."),
    ("csharp-dotnet-professional-usage", "- Choose class, struct, record, or `ValueTask` from identity, copy, equality, boxing, consumption, and compatibility evidence.", "a3f43ca6daf2ef2404fd95c53976d4ae4b57cb288f1d69ef52ee56989d38c7e3", "src/foundation/capabilities/csharp-dotnet-professional-usage/references/async-resource-and-iterator-contracts.md", "- Supply runtime null from an oblivious boundary, mutate a nested record member, box/copy a struct, and resolve a scoped service through each real owner."),
    ("csharp-dotnet-professional-usage", "- Enforce DI lifetime ownership against shorter-lived capture, service location, and disposal of container-owned instances.", "86257927decdfd7b125cf23be3cdf155b8d3b2c8846ee03e9024869a071ff0ad", "src/foundation/capabilities/csharp-dotnet-professional-usage/references/async-resource-and-iterator-contracts.md", "- **Type/DI:** verify class/struct/record equality and copy graph, `ValueTask` consumption constraints, service lifetime, captured dependencies, scope creation/disposal, and container ownership."),
    ("csharp-dotnet-professional-usage", "- Prove trim/AOT reachability for reflection, serialization, DI, dynamic code, and plugins in the actual publish mode.", "2f793a275183a5812625fb99e72553bb11cf06d58fdad17cfb2258835242f0f0", "src/foundation/capabilities/csharp-dotnet-professional-usage/references/runtime-deployment-and-interop-contracts.md", "| Trimming | Actual publish options, reflection/serialization/DI roots, annotations or descriptors, warning ownership, plugin policy, and smoke entry points | Warnings are suppressed or a dynamically reached member disappears only after publish |"),
    ("csharp-dotnet-professional-usage", "- Define load context, native/COM ABI and apartment, UI dispatcher, target, RID, and framework-dependent/self-contained deployment.", "46a88d8388321e79acd3f9d61d744ea980e2ab755260391a6859988f141f0aac", "src/foundation/capabilities/csharp-dotnet-professional-usage/references/runtime-deployment-and-interop-contracts.md", "- Record the runtime and publish target, reachability/loading owner, ABI/apartment/dispatcher contract, exercised target artifact, proof limits, and residual risk."),
    ("kotlin-professional-usage", "- Give every coroutine a lifecycle owner, parent, dispatcher rationale, cancellation outcome, cleanup path, and observed failure.", "30a04afb0543720ae719fe77ce1105fd66edd674f752468f654352126d680a41", "src/foundation/capabilities/kotlin-professional-usage/references/coroutine-flow-state-contracts.md", "| Coroutine owner | Launch site, parent job, scope lifetime, dispatcher, child-failure policy, cancellation translation, cleanup, and shutdown | Detached work outlives its owner, cancellation becomes success, or a child failure is unobserved |"),
    ("kotlin-professional-usage", "- Decide whether a stream is cold, shared, or state-bearing; specify collection lifetime, replay/conflation, backpressure, failure, and slow-consumer behavior.", "bec5a84e1b5b585e51192ed207483f06ac0d65926b36e632492eef5c24faaffb", "src/foundation/capabilities/kotlin-professional-usage/references/coroutine-flow-state-contracts.md", "- Choose cold, shared, or state-bearing flow from producer lifetime and consumer guarantees, not from convenience."),
    ("kotlin-professional-usage", "- Expose `StateFlow` as current state with an explicit mutation owner and atomic transition rule; do not use it as an unbounded event queue.", "172150031616df0a342084d2ddd61365db2a6389ddbf01a7df07da0a8b5e46e4", "src/foundation/capabilities/kotlin-professional-usage/references/coroutine-flow-state-contracts.md", "| `StateFlow` | Single mutation owner, initial/current value meaning, atomic update, equality conflation, and terminal-error representation | Concurrent writers lose transitions or an equal value is expected to emit |"),
    ("kotlin-professional-usage", "- Treat Java platform types and generated/reflection boundaries as unproven null contracts; validate or narrow them before Kotlin assumptions escape.", "7135d1e68cf74beb942e12bb2f974b580144a07d5a33ba3e497bb0ca7af904ea", "src/foundation/capabilities/kotlin-professional-usage/references/type-interop-and-dsl-contracts.md", "- **Nullability:** record platform types, flexible generic arguments, collection elements, reflection, serialization, persistence, generated surfaces, and the runtime validation or narrowing location."),
    ("kotlin-professional-usage", "- Use sealed hierarchies, variance, and reified APIs only after proving closure, compatibility, and generated/reflective behavior.", "03c4c534cb0d68c0e3e0312388df62419e43e3a89668b58b98a40d5a47eaa502", "src/foundation/capabilities/kotlin-professional-usage/references/type-interop-and-dsl-contracts.md", "- **Sealed hierarchy:** establish the module/package closure, external implementor contract, serialization tags, and how new variants reach compiled consumers."),
    ("kotlin-professional-usage", "- Check data/value-class equality, copy depth, boxing, mangling, and Java-callable ABI at every identity or interop boundary.", "85002ac279ec90f71ae5ff2da4f3b2fae34de4e98bf1c03b8c12f97ca53754b7", "src/foundation/capabilities/kotlin-professional-usage/references/type-interop-and-dsl-contracts.md", "- Add an allowed sealed subtype, box a value class through generic/interface/nullable use, and copy a data class with mutable nested state."),
    ("kotlin-professional-usage", "- Define each delegated property's owner, `getValue`/`setValue` effects, lifecycle, interop failure, and verification output.", "ed44961fc36b7442449dd5ec8ff86ddb0023fb0f36ed016ad242540b90af024e", "src/foundation/capabilities/kotlin-professional-usage/references/type-interop-and-dsl-contracts.md", "- **Delegated property:** define the property/delegate owner, `getValue`/`setValue` state semantics, delegate lifecycle/threading, Java/reflection exposure, invalid read/write behavior, and verification output."),
    ("kotlin-professional-usage", "- In Compose, locate state at its mutation/sharing owner; prove observability, identity, lifecycle-aware collection, and one-way events.", "c9d62b948fcff26f21853f6ade5393abed4147012c0581285790379d408f8730", "src/foundation/capabilities/kotlin-professional-usage/references/coroutine-flow-state-contracts.md", "| Compose bridge | State holder owner, snapshot-observable value, collector lifecycle, stable item identity, event path, and disposal | Collection outlives the screen, mutable non-state data stays stale, or recomposition repeats effects |"),
    ("swift-professional-usage", "- Choose value/reference and copy-on-write semantics from identity, aliasing, mutation isolation, copy cost, concurrency, and nested-reference evidence.", "1a857497b8b49bedad43ec0de4fa4e60e9ba6fab17bfc1f401fd4bfb906bab9b", "src/foundation/capabilities/swift-professional-usage/references/value-memory-and-type-contracts.md", "- **Value versus reference:** define semantic identity, mutation owner, copy independence and cost, and any stored references shared after copying."),
    ("swift-professional-usage", "- Prove ARC teardown ownership across closures, delegates, callbacks, tasks, Objective-C edges, and cycle-breaking edges.", "3e3e8d31d5073263f36e1185b40101b06f55dfc8a2cd7d5c3cbfecdf59b03c7e", "src/foundation/capabilities/swift-professional-usage/references/value-memory-and-type-contracts.md", "- **ARC graph:** trace strong edges through closures, delegates, async work, timers, notifications, Objective-C objects, and caches; assign the edge that breaks each cycle."),
    ("swift-professional-usage", "- Treat actor isolation and `Sendable` as access contracts; identify hops, unsafe escapes, inherited isolation, and UI owner.", "e730e5e27b933e49a3b241c04fdacd3ae768dd84ca74ded7b347302840d2aa39", "src/foundation/capabilities/swift-professional-usage/references/concurrency-interop-and-ui-contracts.md", "| Actor or global actor | Isolated mutable state, synchronous and asynchronous entry points, hop sites, reentrancy invariant, `nonisolated` surface, and UI owner | State changes between suspension points or an unsafe escape bypasses isolation |"),
    ("swift-professional-usage", "- Preserve caller-visible cancellation semantics across task groups, unstructured tasks, continuations, and cleanup.", "384d9c79e5578a96aa37e9d9ed8f5734f83785dd72a53e11e03230771aa95f14", "src/foundation/capabilities/swift-professional-usage/references/concurrency-interop-and-ui-contracts.md", "- Exercise normal completion, cancellation before and during suspension, owner teardown, and each callback outcome."),
    ("swift-professional-usage", "- Choose generics, `some`, or `any` from identity, storage, dispatch, associated-type, and compatibility needs.", "c67379d6adc0e93256ba9e75b884bd39b9b4128b26373aac71eef5cbf93ce342", "src/foundation/capabilities/swift-professional-usage/references/value-memory-and-type-contracts.md", "- **Protocol/generic:** establish associated types, `Self` requirements, specialization needs, storage and heterogeneous collection needs, and the public compatibility surface."),
    ("swift-professional-usage", "- Define each Optional's absent-state meaning, safe unwrapping/defaulting, API exposure, and Objective-C import behavior.", "830765ceea5721623632a2378a4b527bb88b22bd384d889f6ad6e494681b5e01", "src/foundation/capabilities/swift-professional-usage/references/value-memory-and-type-contracts.md", "- **Optional:** define `nil` as a named state, safe binding/chaining or defaulting, forced-unwrapping preconditions, nested Optional behavior, and public/Objective-C API representation."),
    ("swift-professional-usage", "- At Objective-C boundaries, inspect nullability, selector exposure, ownership, bridging copies, availability, and exception limits.", "efb585e1aacdf62aa4e941450bf331915bd184cb8779298b1d816ff52d945661", "src/foundation/capabilities/swift-professional-usage/references/concurrency-interop-and-ui-contracts.md", "| Objective-C boundary | Imported nullability, selector/name, ownership convention, block lifetime, bridging copy, error convention, availability, and caller | An implicitly unwrapped optional, copied collection, or retained callback changes meaning |"),
    ("swift-professional-usage", "- In SwiftUI, bind state identity and lifetime to the correct view/model owner; prove observation, main-actor mutation, task cancellation, restoration, and package visibility.", "61bf7ec5e5c7c9b4dac1072d48626e2300c267fa01c53299c04872925383d95c", "src/foundation/capabilities/swift-professional-usage/references/concurrency-interop-and-ui-contracts.md", "| SwiftUI state | View/model identity, state creation owner, observation mechanism, main-actor mutation, task key/cancellation, restoration, and disposal | Model recreation, stale non-observable mutation, repeated effect, or off-owner update |"),
)

FG_C1K_LANGUAGE_NEW_ANCHORS = {
    "b037ae80361d4b1f89f3cf2fcd1d0b6520fd7cf66f8ce8c54a8ac74588e85f18": "| Async owner | Observed task, caller token/deadline, context/dispatcher, exception, result cardinality, shutdown. |",
    "949596d426055ff432cf8b7d1aa17af1f63f9610306393e0f6c140fb1506293b": "| Resource | `IDisposable`/`IAsyncDisposable` owner, construction/reverse cleanup, repeated cleanup, concurrent use, primary-versus-cleanup failure. |",
    "96f116b095dc4178afe2814e14811b30bda4feb56b3a8f1fcf0e02b6da44babf": "| Iterator | First execution, enumeration/disposal sites, partial enumeration, mutation, failure timing, resource across `yield`. |",
    "e727c2e9c9b57c80bc07228bc1ca0e8d5a570a35ea74267c21ec77c7770b83bf": "| Nullable | Context/warnings plus runtime checks for reflection, serialization, interop, generated/oblivious code, collection elements. |",
    "a3f43ca6daf2ef2404fd95c53976d4ae4b57cb288f1d69ef52ee56989d38c7e3": "| Type/value | Class/struct/record equality/copy graph and `ValueTask` consumption. |",
    "86257927decdfd7b125cf23be3cdf155b8d3b2c8846ee03e9024869a071ff0ad": "| DI | Service lifetime/capture, scope/disposal, and container owner. |",
    "2f793a275183a5812625fb99e72553bb11cf06d58fdad17cfb2258835242f0f0": "| Trimming | Publish options; reflection/serialization/DI roots; annotations/descriptors; warning owner; plugins; smoke entry. | Suppressed warning or publish-only missing member. |",
    "46a88d8388321e79acd3f9d61d744ea980e2ab755260391a6859988f141f0aac": "- Record target, loading owner, ABI/apartment/dispatcher, exercised artifact, limits, residual risk.",
    "1a857497b8b49bedad43ec0de4fa4e60e9ba6fab17bfc1f401fd4bfb906bab9b": "| Value/reference | Identity, mutation owner, copy independence/cost, shared references; copy then mutate across identity. |",
    "3e3e8d31d5073263f36e1185b40101b06f55dfc8a2cd7d5c3cbfecdf59b03c7e": "| ARC | Strong edges through closure, delegate, task, timer, notification, Objective-C, cache; release owners, prove teardown/retention. |",
    "e730e5e27b933e49a3b241c04fdacd3ae768dd84ca74ded7b347302840d2aa39": "| Actor | Mutable state, sync/async entry, hops, reentrancy invariant, `nonisolated`, UI owner. | Suspension invalidates state or unsafe escape bypasses isolation. |",
    "384d9c79e5578a96aa37e9d9ed8f5734f83785dd72a53e11e03230771aa95f14": "- Exercise completion, cancellation before/during suspension, owner teardown, and callback outcomes.",
    "c67379d6adc0e93256ba9e75b884bd39b9b4128b26373aac71eef5cbf93ce342": "| Protocol/generic | Associated type, `Self`, specialization, storage, heterogeneous collection, compatibility; cross affected type boundary. |",
    "830765ceea5721623632a2378a4b527bb88b22bd384d889f6ad6e494681b5e01": "| Optional | Named `nil`, binding/chaining/default, force precondition, nesting, public/Objective-C representation; exercise absent/present/invalid paths. |",
    "efb585e1aacdf62aa4e941450bf331915bd184cb8779298b1d816ff52d945661": "| Objective-C | Nullability, selector, ownership, block lifetime, bridging copy, error, availability, caller. | IUO, copied collection, or retained callback changes meaning. |",
    "61bf7ec5e5c7c9b4dac1072d48626e2300c267fa01c53299c04872925383d95c": "| SwiftUI | View/model identity, state owner, observation, main-actor mutation, task cancellation, restoration, disposal. | Recreation, stale mutation, repeated effect, off-owner update. |",
}

G2_BASE_B2_MOVE_SPECS = (
    (
        "authentication-authorization",
        """## Anti-Patterns

- Treat an authenticated session, signed assertion, embedded role, or internal caller as sufficient authorization for a protected action.
- Trust caller-supplied subject, tenant, delegation, role, group, or scope, or propagate identity context whose authority and freshness cannot be reconstructed downstream.
- Expand this Skill into credential/session/token control selection, or generalize one successful login or API path to workers, callbacks, recovery, support, and external identity mappings.""",
        "f64b5abfd7bfc7c2ae46fe2e07d141572c8c11db8c3a0f4854d145a05b738add",
        "src/foundation/capabilities/authentication-authorization/references/evidence-patterns.md",
        ("task-agent", "analysis-agent", "review-agent"),
        ("evidence-record", "proof-limit", "residual-risk"),
    ),
    (
        "authentication-security",
        """## Anti-Patterns

- Clearing a client cookie is not revocation when a refresh token or server session remains valid.
- Recovery, email change, federation, or account linking can bypass stronger controls on the primary login path.

## Execution Checklist

1. Map actors, credentials, IdP trust, session/token families, privilege transitions, recovery paths, and compromise events.
2. Verify current provider capabilities, signing/key policy, browser cookie model, revocation store, performance/UX constraints, and applicable organizational policy before choosing controls.
3. Prove reachable attack paths and record untested paths, evidence limits, and residual takeover risk.""",
        "2606583d895ac4fdea03323e2248899afcf81150921ff448482cbef94b745e48",
        "src/foundation/capabilities/authentication-security/references/checklist.md",
        ("analysis-agent", "task-agent", "review-agent"),
        ("checklist-result", "residual-risk"),
    ),
    (
        "permission-boundary-modeling",
        """## Anti-Patterns

- Treat a role, hidden UI control, gateway scope, authenticated caller, or internal workload as the authoritative permission decision for object- or tenant-sensitive work.
- Let caller-controlled owner, tenant, role, status, purpose, or mutable privilege fields establish entitlement, or filter a broad result after protected data has crossed its disclosure boundary.
- Generalize one endpoint’s denial response, one policy placement, or one happy-path fixture to unrelated resources, entry points, bulk behavior, delegated actors, or deployed policy state.""",
        "148caab768e7ff19fc8f6b5a52c31ee0c6f2ef656626cb4fb95d4adb2b881973",
        "src/foundation/capabilities/permission-boundary-modeling/references/evidence-patterns.md",
        ("analysis-agent", "task-agent", "review-agent"),
        ("evidence-record", "proof-limit", "residual-risk"),
    ),
    ("cryptography-key-lifecycle", """- Nonce handling violates the selected construction's uniqueness, reuse, or misuse-resistance contract.
- An unauthenticated mode permits undetected modification.
- Wrong AAD or context accepts data across boundaries.
- Key and data versions mismatch.""", "19b9da31c24b894d71e587a4c995448a68fb2d753fd41d7b1a3be220ed3a6657", "src/foundation/capabilities/cryptography-key-lifecycle/references/primitives-nonces-and-envelopes.md", ("analysis-agent", "task-agent", "review-agent"), ("selected-approach", "boundary-decision", "proof-limit")),
    ("cryptography-key-lifecycle", """- Rotation removes the only decrypt path.
- Recovery material is inaccessible when required.
- A revoked key remains usable or retained unexpectedly.""", "82d8831fa317150abef5d949b4d7cece9a7a3d2f22f02a4e6583fb7ee75c7052", "src/foundation/capabilities/cryptography-key-lifecycle/references/rotation-versioning-and-recovery.md", ("analysis-agent", "task-agent", "review-agent"), ("boundary-decision", "validation-plan", "proof-limit")),
    ("cryptography-key-lifecycle", """- Destruction causes irreversible data loss.
- Algorithm deprecation leaves an unknown consumer.""", "2df7c13e51e24103397b912656abd338acfea2dbadd355f2996bf2b1066ddabf", "src/foundation/capabilities/cryptography-key-lifecycle/references/compromise-destruction-and-agility.md", ("analysis-agent", "task-agent", "review-agent"), ("failure-decision", "boundary-decision", "residual-risk")),
    ("cryptography-key-lifecycle", "- Test valid decrypt and altered ciphertext, tag, AAD, nonce, key identity, and version.", "b9d57bd95736c2fb12f17a88144d2244c3a7f8b0c64f1eaa8a46cb5cdb091060", "src/foundation/capabilities/cryptography-key-lifecycle/references/primitives-nonces-and-envelopes.md", ("analysis-agent", "task-agent", "review-agent"), ("selected-approach", "boundary-decision", "proof-limit")),
    ("cryptography-key-lifecycle", "- Rehearse recovery, compromise, revocation, destruction safeguards, re-protection, and deprecation migration.", "c6457c6f5ef57b0c3883208eb0d7c2980580c7d217d33dbf93809eb23f1b44ae", "src/foundation/capabilities/cryptography-key-lifecycle/references/compromise-destruction-and-agility.md", ("analysis-agent", "task-agent", "review-agent"), ("failure-decision", "boundary-decision", "residual-risk")),
    ("tenant-isolation", """- Missing tenant predicate exposes another tenant's row.
- Attacker-controlled tenant key selects another tenant.
- Cache key collision returns another tenant's value.""", "1f5a18981057804d7b64c9520d111aa7de770b0be85532050de40382db7e01ce", "src/foundation/capabilities/tenant-isolation/references/data-storage-cache-and-search-isolation.md", ("analysis-agent", "task-agent", "review-agent"), ("boundary-decision", "validation-plan", "residual-risk")),
    ("tenant-isolation", "- Async context loss uses no tenant or the previous tenant.", "0358526c5280fdda699863c4632d6a5e6e1702085baf5d09578a84f61d4d7d66", "src/foundation/capabilities/tenant-isolation/references/async-queue-and-execution-context-isolation.md", ("analysis-agent", "task-agent", "review-agent"), ("boundary-decision", "validation-plan", "proof-limit")),
    ("tenant-isolation", "- Shared admin or support tooling bypasses isolation.", "70c8589a5a50f2681d8ab9695d0a5f75486acf8009eb7014000333523c8c1efc", "src/foundation/capabilities/tenant-isolation/references/operations-telemetry-and-lifecycle-isolation.md", ("analysis-agent", "task-agent", "review-agent"), ("boundary-decision", "validation-plan", "residual-risk")),
    ("tenant-isolation", "- Mixed-tenant batch or migration applies one scope to all items.", "98ec35aa634bea34e857ccd8d30a7c9a6e4660d3c1be770c2ed867f258e05c4c", "src/foundation/capabilities/tenant-isolation/references/async-queue-and-execution-context-isolation.md", ("analysis-agent", "task-agent", "review-agent"), ("boundary-decision", "validation-plan", "proof-limit")),
    ("tenant-isolation", """- Delete or restore leaks or resurrects another tenant's data.
- Telemetry exposes cross-tenant data.""", "0b3f8065600b8d680762e7d7803050fdd85a156a0e922f6b559dd1f37d530f99", "src/foundation/capabilities/tenant-isolation/references/operations-telemetry-and-lifecycle-isolation.md", ("analysis-agent", "task-agent", "review-agent"), ("boundary-decision", "validation-plan", "residual-risk")),
)

G2_BASE_B2_NEW_ANCHORS = {
    """- Rotation removes the only decrypt path.
- Recovery material is inaccessible when required.
- A revoked key remains usable or retained unexpectedly.""": """- When the affected rotation drops its last readable version: Rotation removes the only decrypt path.
- Recovery material is inaccessible when required.
- A revoked key remains usable or retained unexpectedly.""",
    "- Mixed-tenant batch or migration applies one scope to all items.": "- If mixed-tenant items would share one tenant scope, reject the work as an isolation failure.",
}

G2_BASE_B2_FINGERPRINT_NEW_ANCHORS = {
    "1f5a18981057804d7b64c9520d111aa7de770b0be85532050de40382db7e01ce": """- Tenant filtering occurs after read, list, count, or facet computation.
- Cache, object, or search scope can be selected from caller-controlled identity.
- Privileged paths bypass tenant predicates without explicit scope and audit.""",
    "0358526c5280fdda699863c4632d6a5e6e1702085baf5d09578a84f61d4d7d66": "- Async context loss uses no tenant or the prior tenant.",
}

G2_BASE_B3_MOVE_SPECS = (
    (
        "backup-recovery",
        """## Anti-Patterns

- Treating snapshot freshness, replication, or a successful restore command as proof that the product is usable.
- Restoring a database while omitting objects, keys, configuration, queue position, identity state, or compatible code.
- Prescribing one copy topology, rehearsal cadence, runbook form, approval chain, or recovery objective for unrelated consequences.
- Claiming production-scale, cross-region, or incident-time recovery from a small local exercise.""",
        "4f5f9de6ff165bb67dad350eb99dc688072bb3d21390a89e5c18b7ea8ae1009f",
        "src/foundation/capabilities/backup-recovery/references/evidence-patterns.md",
        ("task-agent", "review-agent"),
        ("evidence-record", "proof-limit", "residual-risk"),
    ),
    (
        "concurrency-control",
        """## Anti-Patterns

- A `read → decide → act` sequence is unsafe unless the store enforces the decision atomically.
- Enqueue deduplication does not make consumer side effects exactly once.

## Execution Checklist

1. Identify resources, invariants, overlap, and atomicity gaps.
2. Specify mechanism, conflict response, retry/idempotency, lock order, and fencing.
3. Verify deterministic race outcomes and the forbidden stale or duplicate effect.""",
        "88b3a28c5cadbbf2ad3b502f938d1b7b01a4463694c116df88b0bc9f3329bc19",
        "src/foundation/capabilities/concurrency-control/references/checklist.md",
        ALL_ROLES,
        ("checklist-result", "residual-risk"),
    ),
    (
        "configuration-runtime-policy",
        """## Anti-Patterns

- Treating build-, deploy-, and runtime-time configuration as interchangeable hides when behavior can change.
- Leaving precedence implicit makes code, file, environment, CLI, remote, tenant, experiment, and operator values nondeterministic.
- Using test-friendly defaults in production silently changes safety behavior.
- Publishing hot reloads before validation exposes partial or invalid state.
- Creating untyped or ownerless flags leaves obsolete branches and unverifiable rollout state.
- Packing unrelated strategies into one mode parameter creates an unbounded policy registry.""",
        "b92c0a5b7107e71b67344ad22c2832821f5f9863105ef3f5b989f4b811d6bef8",
        "src/foundation/capabilities/configuration-runtime-policy/references/checklist.md",
        ("task-agent", "review-agent", "analysis-agent"),
        ("checklist-result", "residual-risk"),
    ),
    (
        "data-migration-design",
        """## Anti-Patterns

- Couple schema change, full backfill, consumer cutover, and destructive cleanup into one irreversible mutation.
- Treat successful statements, copied row counts, or absence of errors as proof that business invariants survived.
- Retry non-idempotent conversion blindly or let backfill and live writers race without an authority rule.""",
        "ec0ac0b32411e3c4b8163826b65b9c2a5071deb07f28d15b1346f7f5908257ed",
        "src/foundation/capabilities/data-migration-design/references/evidence-patterns.md",
        ALL_ROLES,
        ("evidence-record", "proof-limit", "residual-risk"),
    ),
    (
        "degradation-circuit-breaking",
        """## Anti-Patterns

- Nested timeouts can exceed the caller deadline unless budgets flow downstream.
- Allow layered retries because they multiply dependency load.
- Skip jitter when concurrent callers can synchronize retries.
- Continue ordinary attempts while the circuit breaker is open.
- A stale or empty fallback is user-visible behavior, not a neutral implementation detail.

## Execution Checklist

1. Map dependency criticality, caller deadline, immutable gateway ceilings or out-of-chain local ceilings, resource pool, and fallback authority.
2. Record dependency connection/read/phase timeouts and the actual retry policy beneath those ceilings, plus fallback, bulkhead, breaker states, probes, and recovery criteria.
3. Verify timeout exhaustion, amplification, fallback, isolation, and half-open recovery.""",
        "6c5b60d7c5c76086cc82ab27590857431870a0d285c82521ded2c232ebef0351",
        "src/foundation/capabilities/degradation-circuit-breaking/references/checklist.md",
        ALL_ROLES,
        ("checklist-result", "residual-risk"),
    ),
    ("distributed-workflow-consistency", """- Duplicate delivery commits an effect twice.
- Lost completion leaves a committed effect unfinished.""", "4a1f4d3e1af97b87a093fe6b10abde1176b10e422854e8b4b57b0ebc2a0cd357", "src/foundation/capabilities/distributed-workflow-consistency/references/identity-state-and-unknown-outcomes.md", ALL_ROLES, ("boundary-decision", "failure-decision", "proof-limit")),
    ("distributed-workflow-consistency", """- Wrong compensation violates current business state.
- Partial ordering advances a dependency early.""", "db49e1e55d92769e3f00b0b336501b48beaa36f18d84f9eea34b58b56e980b70", "src/foundation/capabilities/distributed-workflow-consistency/references/compensation-convergence-and-reconciliation.md", ALL_ROLES, ("failure-decision", "selected-approach", "residual-risk")),
    ("distributed-workflow-consistency", """- Poison or stuck work loops or blocks progress.
- Old-version execution misreads state or commands.
- Manual repair changes state without audit evidence.""", "8352f7a04decbe407ea51514ede8fe82203aae6706d5257522043e2ee95a36a0", "src/foundation/capabilities/distributed-workflow-consistency/references/stuck-manual-repair-and-versioning.md", ALL_ROLES, ("failure-decision", "validation-plan", "proof-limit")),
    ("distributed-workflow-consistency", "- Fault before/after dispatch and effect, before result persistence, and during compensation.", "7a5c534c7566a2e891aec38878f54d77712961bb18469e6955b412e79d3a49be", "src/foundation/capabilities/distributed-workflow-consistency/references/compensation-convergence-and-reconciliation.md", ALL_ROLES, ("failure-decision", "selected-approach", "residual-risk")),
    ("distributed-workflow-consistency", "- Exercise duplicate, reordered, delayed, poison, lost-response, stuck, repair, and participant-drift cases.", "1f4c76c48ef37e3d279de84b53e1799c9dd52ff3a0c2996273cb7a8793aca814", "src/foundation/capabilities/distributed-workflow-consistency/references/identity-state-and-unknown-outcomes.md", ALL_ROLES, ("boundary-decision", "failure-decision", "proof-limit")),
    ("distributed-workflow-consistency", "- Replay representative old/new definitions against histories and mixed participant versions.", "35cdbdf0520a2f4cdbe4e7d42edf5e9c7a9ae402177c17a57eb1411afac04cc3", "src/foundation/capabilities/distributed-workflow-consistency/references/stuck-manual-repair-and-versioning.md", ALL_ROLES, ("failure-decision", "validation-plan", "proof-limit")),
    ("failure-contract-design", """## Anti-Patterns

- Reject null/generic success, collapsed categories, raw dependency errors, unsafe retryability, hidden partials, and cancellation-as-failure.""", "aa1c6bcce47571c61c3796884a360c4fb646cb14495e69d90fcf2828857da571", "src/foundation/capabilities/failure-contract-design/references/evidence-patterns.md", TASK_FIRST_ROLES, ("evidence-record", "proof-limit", "residual-risk")),
    (
        "observability",
        """## Anti-Patterns

- Unbounded labels can exhaust the metrics backend and destabilize alerts.
- Correlation without privacy controls creates a cross-system data leak.
- A signal that cannot change an operator action is noise, not release evidence.

## Execution Checklist

1. Name the material impact or invariant, failure mode, operator question, and signal gap.
2. Select bounded fields, correlation, retention/access, and actionable signals.
3. Verify signal emission, joins, label bounds, privacy, alert action, and SLI semantics.""",
        "38f1873fa5447e9924d0f7dae90841b4d1c7b15426bc188127cfbfa70e612776",
        "src/foundation/capabilities/observability/references/checklist.md",
        ALL_ROLES,
        ("checklist-result", "residual-risk"),
    ),
    ("offline-sync-conflict-resolution", """## Anti-Patterns

- Replay every queued request after reconnect without operation identity or authoritative status.
- Drop tombstones before every replica and offline client has crossed the deletion horizon.
- Resolve conflicts by device time while clock skew, account changes, or field-level intent remains material.""", "9a62e0819ddd92f4a9d9df3d3a7537d910c11561f59172a934031f0ad283f226", "src/foundation/capabilities/offline-sync-conflict-resolution/references/sync-reconciliation-contracts.md", ALL_ROLES, ("selected-approach", "proof-limit", "residual-risk")),
    ("release-rollback", """## Anti-Patterns

- Calling the previous binary a rollback while schema, config, jobs, routes, provider, or visible state remains changed.
- Treating canary, blue-green, rolling, flags, approvals, or incident roles as universal.
- Inventing traffic, metric, watch, or deadline thresholds without baseline and consequence evidence.
- Deleting old artifacts or compatibility paths before the exposure and recovery windows that need them have closed.""", "737dd0e1bf250d05eca72cbdcf5d686fbd1b19a220a8ac6d995bb2761c6b12a3", "src/foundation/capabilities/release-rollback/references/evidence-patterns.md", ALL_ROLES, ("evidence-record", "proof-limit", "residual-risk")),
    (
        "transaction-consistency",
        """## Anti-Patterns

- An ORM annotation does not prove the effective isolation, autocommit, connection reuse, or replica-read behavior.
- A rollback-only test can hide committed interleavings, serialization failures, write skew, stale replicas, and event-before-commit defects.

## Execution Checklist

1. Map the invariant, read/write/side-effect order, concurrency actors, and exact partial-failure point.
2. Verify effective datastore and ORM semantics.
3. Define the relevant anomaly reproduction and expected outcome.
4. Map fresh reproduction results to the selected mechanism, retry behavior, proof limits, and residual risk.""",
        "251122efee9a01e4d311f72384f53fada3a0ddd6b1b69d42fce4a18cf0b88fa7",
        "src/foundation/capabilities/transaction-consistency/references/checklist.md",
        ("analysis-agent", "task-agent"),
        ("checklist-result", "residual-risk"),
    ),
)

G2_BASE_B3_FINGERPRINT_NEW_ANCHORS = {
    "8352f7a04decbe407ea51514ede8fe82203aae6706d5257522043e2ee95a36a0": """| Stuck detection | Query, threshold authority, false-positive handling, alert owner, and response deadline. | Poison work loops below alerts. |
| Quarantine | Isolation, retained evidence, live-work protection, and disposition. | One item blocks an ordered population. |
| Repair authority | Actor, workflow/step/effect target, purpose, permission, and approval. | A generic console edits state. |
| Repair command | Preconditions, dry run, repeat identity, allowed transition, participant check, and stop. | Repair repeats an unknown effect. |
| Audit | Before/after state, actor, evidence, command, outcome, and reconciliation. | Manual repair lacks attribution. |
| Definition version | Persisted version, command/event compatibility, participant support, and replay behavior. | Old history runs under incompatible code. |""",
    "35cdbdf0520a2f4cdbe4e7d42edf5e9c7a9ae402177c17a57eb1411afac04cc3": """- Replay representative histories under compatible and incompatible definitions.
- Exercise mixed old/new workers or participants where supported.""",
    "4f5f9de6ff165bb67dad350eb99dc688072bb3d21390a89e5c18b7ea8ae1009f": """- Reject snapshot, replication, or command success as product usability proof.
- Reject a restore that omits dependent state.
- Reject a universal copy, cadence, or objective.
- Reject production-scale or incident-time claims from a small local exercise.""",
}


G2_BASE_B4_MOVE_SPECS = (
    ("api-contract-design", """## Anti-Patterns

- Do not expose internal representations or call a contract additive without consumer-semantic proof.""", "367b3d44bef6dbd7c123be1bae9bada9499091a89c5d421cd7843fb6d0fa0f59", "src/foundation/capabilities/api-contract-design/references/evidence-patterns.md", ALL_ROLES, ("evidence-record", "proof-limit", "residual-risk")),
    ("consumer-impact-analysis", """## Anti-Patterns

- A provider-only green test does not prove downstream compatibility.
- A public export, package, stream, webhook, or copied example can have consumers outside repository search scope.
- Calendar expiry without usage or owner evidence can remove a still-live contract.
- Generated output treated as incidental hides source-schema and compatibility drift.""", "ad23b2a84a02dbd5f195e9cde96005228d94c7ec971c625e37e7ec9664d476ef", "src/foundation/capabilities/consumer-impact-analysis/references/evidence-patterns.md", ("task-agent", "analysis-agent", "review-agent"), ("evidence-record", "proof-limit", "residual-risk")),
    ("contract-testing", """## Anti-Patterns

- Declaring compatibility from schema shape alone while semantic meaning, error behavior, or consumer tolerance changed.
- Inventing a vendor or consumer mock from memory, or treating one captured response as the provider's complete behavior.
- Applying one broker, registry mode, versioning style, or consumer-driven workflow to every boundary.
- Replacing integration, journey, consumer discovery, or rollout proof with contract tests.""", "3b79b8b3bedb3a6603b453746697ff3b109177aec953441172647cd4f02c5df0", "src/foundation/capabilities/contract-testing/references/evidence-patterns.md", ALL_ROLES, ("evidence-record", "proof-limit", "residual-risk")),
    ("design-pattern-selection", """## Anti-Patterns

- Reject one-variant wrappers, hidden global/I/O work, code-sharing bases, and pattern names without current force evidence.""", "2ce1e7b19d97a76bbce2773c58278696e45d7be658e14076acc27933178009b3", "src/foundation/capabilities/design-pattern-selection/references/pattern-evidence-record.md", ALL_ROLES, ("evidence-record", "proof-limit", "residual-risk")),
    ("domain-object-identification", """## Anti-Patterns

- Reject table/DTO/UI names, nesting, joins, proximity, or repository search as domain ownership proof.""", "e0bf2a835ca72e438882854c46e7156260bad8984ac3f66b3698c062f903db40", "src/foundation/capabilities/domain-object-identification/references/evidence-patterns.md", ALL_ROLES, ("evidence-record", "proof-limit", "residual-risk")),
    ("implementation-structure-design", """## Anti-Patterns

- Reject convention-, size-, utility-, or test-only exports as ownership or placement proof.""", "89e24bab8dc55edc51988425ed8028add16defdd7149f8e3d194bd3cb43996a2", "src/foundation/capabilities/implementation-structure-design/references/evidence-patterns.md", TASK_FIRST_ROLES, ("evidence-record", "validation-plan", "proof-limit", "residual-risk")),
    ("minimal-correct-implementation", """## Anti-Patterns

- Reject speculative scaffolding, pass-through abstractions, duplicate packages/code, and shortcuts without a bounded exit.""", "274f7273aaf1fbe92fe18a0292fc53f6f4c6374f52372b01dcf7830ca808cfc6", "src/foundation/capabilities/minimal-correct-implementation/references/simplicity-ladder.md", ALL_ROLES, ("option-comparison", "selected-approach", "residual-risk")),
    ("model-boundary-mapping", """## Anti-Patterns

- Do not cross a representation boundary without owned mapping and semantic-preservation proof.""", "8e5cb1f0b053484f7e96e4f0f235f7b5ab97965f36fc56a03413a7dbddbd55bf", "src/foundation/capabilities/model-boundary-mapping/references/evidence-patterns.md", TASK_FIRST_ROLES, ("evidence-record", "proof-limit", "residual-risk")),
    ("module-boundary-design", """## Anti-Patterns

- Treating a framework, layer name, directory layout, file count, or coupling score as sufficient boundary proof.
- Moving business policy into `shared`, `common`, or `utils` to avoid choosing its owner.
- Publishing a facade that re-exports internals or mirrors another module without owning semantics.
- Renaming a cycle as a callback or event while state, ordering, failure, or retry ownership stays circular.""", "a11d8ad1bb604a788375871d6222de7456974d1138ce0b38e3fc08a5d3fcfa4c", "src/foundation/capabilities/module-boundary-design/references/split-merge-and-move-decisions.md", ("analysis-agent", "review-agent"), ("boundary-decision", "selected-approach", "residual-risk")),
    ("sdk-library-contract-design", """## Anti-Patterns

- Do not infer compatibility or adoption from a declaration diff or source-only fixture.""", "080d3bfef11492f8390df4b4b3f9c11f7b7cd941e44568dd7518ab33fc8e8347", "src/foundation/capabilities/sdk-library-contract-design/references/evidence-patterns.md", TASK_FIRST_ROLES, ("evidence-record", "proof-limit", "residual-risk")),
    ("state-management-design", """## Anti-Patterns

- Promote state globally because prop flow is inconvenient, or duplicate server state without an invalidation owner.
- Key cache or persisted state without tenant, account, resource, or query identity needed to prevent cross-context reuse.
- Let a stale response, optimistic failure, logout, or navigation leave durable or sensitive state under the wrong owner.""", "433d1828f6dd7f726f9658cee5516cb393c7af55d19fecdf0e20ad3ebcec3403", "src/foundation/capabilities/state-management-design/references/checklist.md", ("task-agent",), ("checklist-result", "residual-risk")),
    ("technology-stack-selection", """## Anti-Patterns

- A weighted score lets a hard compatibility, security, ownership, or migration gap disappear inside a total.
- Fashion or generic reputation substitutes for current constraints and workload evidence.
- Entry price excludes on-call, upgrade, incident, coexistence, data movement, or exit work.
- A prototype or vendor benchmark is extrapolated across different scale, topology, failure modes, versions, or data shapes.""", "6ff4039fe84435c74eaff9c91528fb9d060a68ab0a555ed6707da94056f8309f", "src/foundation/capabilities/technology-stack-selection/references/benchmarks-and-patterns.md", ALL_ROLES, ("option-comparison", "selected-approach")),
    ("version-compatibility", """## Anti-Patterns

- Assuming consumers upgrade together or deriving their window from producer speed.
- Calling added fields non-breaking despite changed defaults, validation, matching, or behavior.
- Removing a bridge by calendar without usage, stored-data, queue, and rollback evidence.""", "60d03130eb0ede742ed11124b55e050d1b32e9b187aa8b85499a4f898bfdc37e", "src/foundation/capabilities/version-compatibility/references/evidence-patterns.md", ALL_ROLES, ("evidence-record", "proof-limit", "residual-risk")),
)

G2_BASE_B5_MOVE_SPECS = (
    ("client-application-testing", """## Anti-Patterns

- Reject recreation-as-process-death, one-target-as-supported-matrix, and screenshot/tree-only oracles.""", "44e42f4052aaec59a875b929e2244a6f2906fabbd083753e0f9b58f0c59022bc", "src/foundation/capabilities/client-application-testing/references/client-test-matrix.md", ALL_ROLES, ("validation-plan", "residual-risk")),
    ("code-clarity-maintainability", """## Anti-Patterns

- A guard or early return bypasses cleanup, audit, rollback, or response work.
- A boolean, mode, negated condition, or magic value hides authority or state semantics at the call site.
- Tiny helpers or files force traversal across vague wrappers to understand one decision.
- A shorter diff or lower metric is treated as clarity proof while behavior, ownership, or test intent becomes harder to see.""", "3d51acffeffb63c2c18e7c54843c86a7d3ea40386907aab24eada5f2232b23ef", "src/foundation/capabilities/code-clarity-maintainability/references/checklist.md", ALL_ROLES, ("checklist-result", "residual-risk")),
    ("code-review", """## Anti-Patterns

- Edited-line-only review, speculative findings, or mock/retry/suppression-only proof cannot close a consequential path.""", "978e70ed93633f3c5b45b67eff7171da0074f68a5b0f96007c1e2bee9feada72", "src/foundation/capabilities/code-review/references/evidence-patterns.md", ("review-agent", "analysis-agent", "task-agent"), ("evidence-record", "proof-limit", "residual-risk")),
    ("documentation-generation", """## Anti-Patterns

- Treating repository discovery or prior summaries as factual proof.
- Keeping stale docs because code validation passes.
- Publishing generated examples without checking their compatibility promise.
- Claiming no documentation impact without naming considered audiences.""", "76a3cf529acb204581af3f42127407acc9b64e9220b35d8929e4d69db6887a00", "src/foundation/capabilities/documentation-generation/references/evidence-patterns.md", ("task-agent", "review-agent"), ("evidence-record", "proof-limit", "residual-risk")),
    ("refactoring", """## Anti-Patterns

- Reject behavior changes labeled refactoring, causally hidden broad moves, and local-search-only deletion.""", "60e670ba3f0f03e65519c66b43965ab712fb7684382c32261fef409edaca3507", "src/foundation/capabilities/refactoring/references/behavior-preservation-evidence.md", ("review-agent", "analysis-agent"), ("evidence-record", "proof-limit", "residual-risk")),
    ("regression-testing", """## Anti-Patterns

- A green-only guard, wrong-boundary test, trigger-erasing fixture, stale evidence, incomplete current-task repair, or indiscriminate sibling fix does not prove non-recurrence.""", "a3aacdab0dcb1d1bceab54f686192fcfc449aa635de6184fb9cf1136d2852dac", "src/foundation/capabilities/regression-testing/references/evidence-patterns.md", ALL_ROLES, ("evidence-record", "proof-limit", "residual-risk")),
    ("repeat-failure-analysis", """## Anti-Patterns

- Renaming the same patch is not a different approach.
- A green unrelated command does not disprove the observed failure.
- Previous conversation summaries are navigation hints, not source truth.

## Execution Checklist

1. List the failed attempts on the rejected path and the evidence each produced.
2. State why the prior path is rejected or still uncertain.
3. Inspect the owner and same-pattern occurrences.
4. Choose one falsifiable next hypothesis and a different proof path.
5. Return the bounded next action or a concrete blocker.""", "2579e0bdb093233326918026886178c0e27eb8e7bd3ac14281e30a15ac586b24", "src/foundation/capabilities/repeat-failure-analysis/references/repeat-failure-checklist.md", ALL_ROLES, ("checklist-result", "residual-risk")),
    ("targeted-validation-selection", """## Anti-Patterns

- Reject invented commands, name-only coverage, framework-habit entrypoints, and freshness facts used as timing verdicts.""", "5d4501157283af4e8b9bb22c7665255d3f561a2f80dbb2891bc7f845703b6729", "src/foundation/capabilities/targeted-validation-selection/references/repository-command-entry-evidence.md", ALL_ROLES, ("evidence-record", "proof-limit", "residual-risk")),
    ("test-data-management", """## Anti-Patterns

- Share mutable fixture state across cases or depend on execution order, machine time, or uncontrolled identifiers.
- Use a large production-like snapshot that hides which records and relationships cause the behavior.
- Rely on rollback cleanup when effects commit separately, run asynchronously, or leave external resources behind.""", "bdf0969d1474a039c2a4722a05d1f2a4f26aa99c587f8fc6afe957bfb341ca22", "src/foundation/capabilities/test-data-management/references/checklist.md", ALL_ROLES, ("checklist-result", "residual-risk")),
    ("test-strategy", """## Anti-Patterns

- Reject catalog-, coverage-, broad-suite-, mock-, or manual-only proof without a task-specific failure mechanism and oracle.""", "1baca81dba632f8004f57d2276192ddbe74d7024f319a97603093775fb16119a", "src/foundation/capabilities/test-strategy/references/evidence-patterns.md", ALL_ROLES, ("evidence-record", "proof-limit", "residual-risk")),
)

G2_BASE_B6_MOVE_SPECS = (
    ("accessibility-inclusive-design", """## Anti-Patterns

- Add an accessibility label while leaving the control's role, state, focus behavior, or action inaccessible.
- Treat passing automation, a screenshot, or one screen reader as proof of accessibility conformance.
- Remove visible focus, error text, or non-color cues because a mouse path still works.""", "4d4edc7f84da14532fa96b8d2a8973be2bae1f46294c62b7e66c1586e83c2fde", "src/foundation/capabilities/accessibility-inclusive-design/references/accessibility-verification-evidence.md", ALL_ROLES, ("evidence-record", "validation-plan", "proof-limit", "residual-risk")),
    ("build-tool-professional-usage", """## Anti-Patterns

- Rely on command order, undeclared files, local caches, host-installed tools, or mutable shared output for a green build.
- Hand-edit generated artifacts or accept broad regeneration churn without source-to-output explanation.
- Treat local command success as proof of hosted enforcement, cross-platform reproducibility, or deployed artifact identity.""", "9c9ce3c039484e84782b84f6fec2ce44645c1a1316176084823897ad93621a95", "src/foundation/capabilities/build-tool-professional-usage/references/evidence-patterns.md", TASK_FIRST_ROLES, ("evidence-record", "proof-limit", "residual-risk")),
    ("client-lifecycle-state-restoration", """## Anti-Patterns

- Treat an in-memory resume, process recreation, and cold launch as the same path.
- Restore captured credentials, permissions, server responses, or completed commands as current truth.
- Use one global startup flag while multiple scenes, windows, activations, or tests can initialize independently.""", "7a140e05395295d70b5db860cd355680b1216421e6c482213c2a0d095ea76afc", "src/foundation/capabilities/client-lifecycle-state-restoration/references/restoration-boundaries.md", ALL_ROLES, ("selected-approach", "proof-limit")),
    ("csharp-dotnet-professional-usage", """- `async void`, fire-and-forget tasks, or sync-over-async hides failure, cancellation, context deadlock, or owner teardown.
- A `using`, finalizer, DI container, GC, or `await using` is assumed to establish the required cleanup order without failure-path proof.""", "4a615efeba2a29994252707b4af6394bbe987548c19d90239f9332e299759210", "src/foundation/capabilities/csharp-dotnet-professional-usage/references/async-resource-and-iterator-contracts.md", TASK_FIRST_ROLES, ("decision-record", "residual-risk")),
    ("csharp-dotnet-professional-usage", """- Nullable-clean compilation, a record, or a struct is treated as runtime null safety, deep immutability, or cheap copying.
- Build success is treated as reflection, native loading, trimming, AOT, UI-affinity, or deployment proof.""", "559698ee3bd20f9b734426701b471339ab5fdf889d40d54ae771b7660b2db466", "src/foundation/capabilities/csharp-dotnet-professional-usage/references/runtime-deployment-and-interop-contracts.md", TASK_FIRST_ROLES, ("selected-approach", "proof-limit", "residual-risk")),
    ("infrastructure-as-code-safety", """## Anti-Patterns

- Proposals are not execution/convergence proof; source rollback may leave effects.""", "9edb1a8e97964f0a5e8ffa383d3235d0938bf9743fb717abef0832e959c83320", "src/foundation/capabilities/infrastructure-as-code-safety/references/state-plan-and-drift-contracts.md", ALL_ROLES, ("decision-record", "proof-limit", "residual-risk")),
    ("interaction-state-modeling", """## Anti-Patterns

- Show success from request acceptance, optimistic mutation, or local completion before the authoritative effect is known.
- Collapse permission denial, absence, filtering, and load failure into a single empty or error treatment that leaks or misstates state.
- Disable an action without an owned reason or recovery path, or let a late response overwrite newer user intent.""", "87338dcb17207a35acb3aca2b31d0fb9be0ca9460b1ae17a4a641a4c8ceec380", "src/foundation/capabilities/interaction-state-modeling/references/state-transition-and-backend-evidence.md", ALL_ROLES, ("evidence-record", "validation-plan", "proof-limit", "residual-risk")),
    ("kotlin-professional-usage", """- `GlobalScope`, an unowned scope, or a default dispatcher hides cancellation, failure, or shutdown.
- A cold `Flow` is assumed to cache work, or `StateFlow`/`SharedFlow` is assumed to preserve every event.""", "55cd12a192b8f88566ed0c79bb73e0dbf5cfa684d5f59e4293eded61239a24ba", "src/foundation/capabilities/kotlin-professional-usage/references/coroutine-flow-state-contracts.md", TASK_FIRST_ROLES, ("selected-approach", "proof-limit", "residual-risk")),
    ("kotlin-professional-usage", """- `!!`, a platform type, or a generated annotation is treated as runtime null proof.
- Data-class `copy`, a value wrapper, sealed `when`, or `remember` is treated as deep immutability, stable ABI, future exhaustiveness, or durable state.""", "b2f528556e7e934eab896c580419535770e747dc8a03f315155d431517ea406e", "src/foundation/capabilities/kotlin-professional-usage/references/type-interop-and-dsl-contracts.md", TASK_FIRST_ROLES, ("decision-record", "residual-risk")),
    ("powershell-professional-usage", """## Anti-Patterns

- Success flags, text conversion, command strings, syntax portability, and blind reruns do not prove contracts.""", "78d91d41d2743b011146c34b587421c3541151c3d395cff9923389f863a1fa0f", "src/foundation/capabilities/powershell-professional-usage/references/pipeline-error-and-native-contracts.md", TASK_FIRST_ROLES, ("decision-record", "residual-risk")),
    ("swift-professional-usage", """- A `struct`, `let`, protocol, or `Sendable` conformance is treated as deep immutability or race-freedom proof.
- `weak`, `unowned`, or `[weak self]` is applied mechanically without proving lifetime and required work completion.""", "f594d7b89b8802a5d81e62ac72240c765b819a4cd4e288809e688b6eb90e18cf", "src/foundation/capabilities/swift-professional-usage/references/value-memory-and-type-contracts.md", TASK_FIRST_ROLES, ("decision-record", "residual-risk")),
    ("swift-professional-usage", """- `@MainActor` is treated as proof that every synchronous caller runs on the main thread.
- A detached task, continuation, or SwiftUI task hides cancellation, double resume, retention, or repeated effects.""", "470795b6f733dcb2defbe5312713628edf4cb6f4b5ba3965633416adf8bb491e", "src/foundation/capabilities/swift-professional-usage/references/concurrency-interop-and-ui-contracts.md", TASK_FIRST_ROLES, ("selected-approach", "proof-limit", "residual-risk")),
    ("web-platform-professional-usage", "- Replace semantic HTML with generic elements and assume ARIA restores native behavior automatically.", "83f47d904bfa1d93341422dcf2fc5561cae2b698535ee9c518a072770ffbb1f6", "src/foundation/capabilities/web-platform-professional-usage/references/document-semantics-and-accessibility-tree-contracts.md", ALL_ROLES, ("selected-approach", "boundary-decision", "proof-limit")),
    ("web-platform-professional-usage", """- Treat `load` or component mount as the only entry path despite history traversal, BFCache, restored storage, or an active service worker.
- Infer browser support from a specification, one compatibility table, or one engine without testing the supported version matrix.""", "e05e53dae1af8df0278261517a222d070bf54e44bdfeb7644d209c08d288a8ca", "src/foundation/capabilities/web-platform-professional-usage/references/browser-compatibility-and-verification-evidence.md", ALL_ROLES, ("evidence-record", "validation-plan", "proof-limit", "residual-risk")),
)

G2_BASE_B6_NEW_ANCHORS = {
    "4d4edc7f84da14532fa96b8d2a8973be2bae1f46294c62b7e66c1586e83c2fde": "- Do not infer native-client certification from WCAG or usability from an accessibility tree, automated scan, contrast result, screenshot, or one screen-reader run.",
    "4a615efeba2a29994252707b4af6394bbe987548c19d90239f9332e299759210": "- Reject hidden async failure, sync-over-async, or cleanup-order claims without failure-path proof.",
    "559698ee3bd20f9b734426701b471339ab5fdf889d40d54ae771b7660b2db466": "- Reject build or nullable/type syntax as runtime, immutability, loading, AOT, UI, or deployment proof.",
    "f594d7b89b8802a5d81e62ac72240c765b819a4cd4e288809e688b6eb90e18cf": "- Reject value syntax, ARC, `weak`/`unowned`, protocol, or `Sendable` as immutability, lifetime, or race-freedom proof.",
    "470795b6f733dcb2defbe5312713628edf4cb6f4b5ba3965633416adf8bb491e": "- Reject annotations, detached tasks, continuations, or SwiftUI tasks as thread, cancellation, resume, retention, or effect proof.",
    "87338dcb17207a35acb3aca2b31d0fb9be0ca9460b1ae17a4a641a4c8ceec380": "Reject local or optimistic completion before the authoritative effect and any late response that overwrites newer intent.",
    "83f47d904bfa1d93341422dcf2fc5561cae2b698535ee9c518a072770ffbb1f6": "Reject generic elements that assume ARIA restores native behavior.",
    "e05e53dae1af8df0278261517a222d070bf54e44bdfeb7644d209c08d288a8ca": "- Specification presence, WPT coverage, one compatibility table, or one engine does not prove deployed product support.",
}

G2_BASE_B7_MOVE_SPECS = (
    (
        "cross-platform-client-extension",
        """## High-Value Gotchas

- Shared or compile-time success can hide target-specific lifecycle, permission, accessibility, packaging, or runtime failure.

## Execution Checklist

- Verify ownership, compatibility, normal, failure, upgrade, and artifact behavior per affected target.
- Report the target matrix, source freshness, untested targets, non-inferences, and residual risk.""",
        "2b60d79f71cf52a942203fb06a6f1c1eb158f21183ee48598b05109b7a9f938a",
        "src/domain-extensions/cross-platform-client-extension/references/framework-target-evidence-contracts.md",
        ALL_ROLES,
        ("evidence-record", "proof-limit", "residual-risk"),
    ),
)

G2_BASE_B8_MOVE_SPECS = (
    (
        "ai-product-extension",
        """- **Trace consequential claims**: distinguish source evidence, model inference, uncertainty, and abstention according to user harm.
- **Keep low-impact output proportional**: do not impose universal citations on creative or low-impact output.
- **Preserve retrieval authorization**: prove retrieved data honors source permissions, tenant scope, and revocation.
- **Contain untrusted prompt content**: prove user or retrieved content cannot override trusted policy or authorize action.
- **Bound tool authority**: prove least privilege, valid arguments, confirmation, auditability, and recovery for side-effecting calls.
- **Evaluate probabilistic changes**: compare baseline and treatment on representative success, refusal, adversarial, and boundary cases.
- **Calibrate evaluation effort**: derive datasets, metrics, and thresholds from product harm and observed variance.
- **Distrust model output downstream**: validate model output independently at data, execution, rendering, API, and policy boundaries.
- **Minimize context data**: include only authorized data needed for the task.
- **Prove sensitive-data lifecycle**: verify redaction and retention when sensitive data reaches providers or logs.""",
        "99f0ba478984d25883f0785b5a7d88b814f5b6c5d064a4270af72d7939312245",
        "src/domain-extensions/ai-product-extension/references/checklist.md",
        ALL_ROLES,
        ("checklist-result", "residual-risk"),
    ),
    (
        "ai-product-extension",
        """- permission-blind retrieval leaks another tenant's chunks even when the source UI is secure
- indirect prompt injection turns retrieved content into unauthorized tool instructions
- evaluation averages hide severe failures in a small, consequential cohort
- provider or model changes alter refusal, token cost, or structured-output behavior without an application code change
- plausible output bypasses validation because downstream code treats model confidence as trust""",
        "3c2a7ac9396f021a015fa1fcb027d13866df9dfca230360ddfd32258145c1a88",
        "src/domain-extensions/ai-product-extension/references/checklist.md",
        ALL_ROLES,
        ("checklist-result", "residual-risk"),
    ),
    (
        "ai-product-extension",
        """1. Identify the AI risk signal, affected invariant, and evidence available for this change.
2. Choose controls from the current permission model, harm, reversibility, and measured behavior.
3. Define representative failure tests, fallback, observability, escalation, and residual risk.""",
        "1100ee4f2835ee446622dde0d5eb8de4d4f4384d739c87e243009d7cd69b6da5",
        "src/domain-extensions/ai-product-extension/references/checklist.md",
        ALL_ROLES,
        ("checklist-result", "residual-risk"),
    ),
)

G2_BASE_B8_NEW_ANCHORS = {
    "99f0ba478984d25883f0785b5a7d88b814f5b6c5d064a4270af72d7939312245": """- Define user-facing evidence authority across source evidence, model inference, uncertainty, abstention, independent verification, and human review. The contract covers unavailable evidence, fallback, appeal, correction, and explicit degraded decisions.
- Keep low-impact output proportional without universal citations for creative or low-impact output.
- Govern retrieval data and indexes by source permission, tenant, retention, redaction, deletion, ownership, version, namespace, refresh, and freshness. Verify revocation across active and fallback serving indexes, with a bounded lag.
- Separate trusted policy, user input, retrieved content, tool output, stored memory, and generated output. Exercise direct and indirect injection and poisoned tool results against instruction priority, data access, and future decisions.
- Bind tool calls to identity, principal, argument schema, data scope, side-effect class, confirmation, retry, recovery, and audit evidence. Approved authority excludes excess model fields and call sequences.
- Authorize durable memory reads and writes as product effects. Bind provenance, principal, tenant, purpose, policy version, trust, deletion, and revocation while preventing cross-actor poisoning or retrieval.
- Record evaluation-set source, owner, collection window, labels, transformations, version, and intended population. Detect overlap with training, tuning, retrieval, prompt development, and prior evaluation outputs before claiming independent evidence.
- Record judge identity or assignment, model version, rubric, calibration, scoring direction, disagreement, overrides, and adjudication. Independent or blinded review applies when variance or automation bias can change consequential decisions.
- Compare baseline and treatment across representative success, boundary, refusal, hallucination-prone, adversarial, and regression cases by consequential cohort.
- Derive evaluation thresholds and sample effort from harm, prevalence, and observed variance.
- Record deployable lineage for applicable behavior-bearing prompts, models, providers, retrievers, embeddings, indexes, tool schemas, safety policies, data snapshots, and evaluators.
- Bind prompt and response cache identity to principal, tenant, visibility, and behavior-bearing versions. Invalidate affected cache entries and proof when those inputs change.
- Exercise reachable timeout, rate-limit, retrieval, tool, refusal, unsafe-output, truncation, and configured fallback failures. Verify compatible refusal, structured output, tool authority, required evidence, and safety behavior.
- Treat model output as untrusted at parsing, rendering, storage, query, API, policy, and authorization boundaries. Validate structure and business authority independently of model confidence.
- Segment quality, retrieval, tool, refusal, latency, cost, drift, and safety signals by deployable lineage and consequential cohort. Bound labels and sensitive payloads, with named alert ownership.
- Minimize authorized context data to the task need.
- Map provider-bound and retained AI data across providers, logs, traces, caches, evaluation stores, and human-review queues. Applicable consent, purpose, region, fallback, residency, retention, deletion, and access rules govern each copy.""",
}

G2_BASE_B0_COMPACTIONS = (
    (
        "logging-design-gate",
        "src/professional-skills/logging-design-gate/SKILL.md",
        "d956cf732021e9c4a13d432b2982708daa1e73703439932ada9795949ad6b42c",
        "221679944eb1df243492bc89ac444e3f8b2cd938939ffbdaa2ac933e731a46fa",
        ("Support `task-agent` and `review-agent` for bounded logging decisions.", "Stop without a named question", "logging verdict"),
    ),
    (
        "audit-evidence-integrity",
        "src/foundation/capabilities/audit-evidence-integrity/SKILL.md",
        "20ec8601bcc751e82eb30851686766dd71b6e64be218594e8a7b390d067a35f9",
        "5721828949dde8d21535ff0b2dcf20b180a32f6834941c6fd20e3187e059e327",
        ("Define audit coverage, identity/time/causality, integrity/storage/access, lifecycle/export/custody, and verification.", "Load only the Reference for the active attribution, integrity, or lifecycle/custody decision.", "audit-evidence decision with analysis or implementation owner"),
    ),
    (
        "secret-configuration-security",
        "src/foundation/capabilities/secret-configuration-security/SKILL.md",
        "3991f39ba992e2a9a40f2185764d08dc5a0c3e5947b31bc94c4027c8e143ed67",
        "40e92045d2137d2de50fa4293d094aa0c7afc4c40fdccb5733e1fc1a203d6616",
        ("Own secret exposure, lifecycle, redaction, and recovery.", "Load named lifecycle/redaction/access/recovery References; exclude raw evidence.", "Return a secret-configuration decision: map exposure, access scope, rotation, revocation, redaction, recovery, owner, and residual exposure"),
    ),
    (
        "logging-error-handling",
        "src/foundation/capabilities/logging-error-handling/SKILL.md",
        "7e2efe1c7503ea6bf2e286a6962d814cd1afe70fe64ef82bfea442c36e8937d0",
        "76f867385ec4cbc28cd2b882bec0469a4b927e265168ec2162060e218ea11d4c",
        ("Define owned error translation/outcome and diagnostic event/correlation/redaction/volume/reconstruction; consume but do not own protected audit contracts.", "Load only the Reference for unresolved sensitive content, volume/cardinality, or audit ownership.", "logging and error decision with ownership, external meaning"),
    ),
)

G2_BASE_B1_COMPACTIONS = (
    ("ai-code-review-refactor", "src/professional-skills/ai-code-review-refactor/SKILL.md", "2df1ba4fb910c602d5915900da27617ecb30f5661e92f25ca40af8d05ddc74ee", "cf548e3bc362edc9f5d5f8f488c88d2ae37e522dbf1f0ef9695a5d6601ddd213", ("independently reviewing", "cannot reroute", "reviewed/unreviewed scope")),
    ("architecture-impact-reviewer", "src/professional-skills/architecture-impact-reviewer/SKILL.md", "422a9f496f9894e430b3db99f13f0b61ef5a8c3cf9213f399e8504b187b1ae99", "fa3fb22c7898106d1defeb7afae6743b3d52bcad8ce7a2710a1f90fccab417cc", ("select a source-backed placement", "Stop structural decisions", "architecture verdict, boundary findings")),
    ("change-documentation-gate", "src/professional-skills/change-documentation-gate/SKILL.md", "c1fadd53b06088dbb0e21ec1da38a5e2ab2f9989a8da3fb32c0033061a3563b4", "426d98046ff139c5cab312acf59abc2e54396e74ce3f451acf9d293930a13407", ("source-owned documentation accuracy", "Stop release", "documentation changes")),
    ("data-api-contract-changer", "src/professional-skills/data-api-contract-changer/SKILL.md", "fae6390621baa0c3081f9d63f908a8b285326ba4944161fd166be6313f1391ba", "c0a371b449b95793909b7ae1349c0084833385038909926356bc7c96dd5f73ed", ("Own evidenced data", "Stop on unresolved compatibility", "producer and consumer changes")),
    ("data-middleware-change-builder", "src/professional-skills/data-middleware-change-builder/SKILL.md", "605b1faa0069e848f428540746f13aac43012451c2d0e021fdc270a6a9932769", "51af820aededb532f57198975c6290b76e6c65b20e9c0ae2817171a9980c5db1", ("Map ownership, failure, recovery, and proof.", "Load one Reference for its open output.", "replay and reconciliation evidence")),
    ("delivery-release-gate", "src/professional-skills/delivery-release-gate/SKILL.md", "02e96a5daea2d9a390314eae547f86e61ed5528fec3eb3c043c6019e75112e2b", "aaf5c2ea8078a3c794725303f2ce7c3372dd96569a4a0d5dc88bc82024fa1fda", ("select rollout", "Block stale artifact/environment, authority, containment, compatibility/migration, infrastructure-state, or recovery evidence.", "go/no-go verdict")),
    ("frontend-change-builder", "src/professional-skills/frontend-change-builder/SKILL.md", "e69b53e752c8faba5e5e47e5e5f2200767abcf0b8eb6e369a9e71f1035276b6a", "72b501379de4feb495528125132c2cf50120a9cdfad704da5f9e48b2b039ad8b", ("frontend interaction states", "Stop implementation", "residual UX risk")),
    ("high-risk-design-review", "src/professional-skills/high-risk-design-review/SKILL.md", "89755cd877dcf8b55bee60a3da9d450e13cc7cf8c5056222ef773c8e213845b2", "cef593ac51134204e4b05992664ac38d6f61ff80362b4ffd8c67f8f06507f1d7", ("high-risk Engineering Brief", "Stop when source evidence", "First Executable Slice assessment")),
    ("installed-client-change-builder", "src/professional-skills/installed-client-change-builder/SKILL.md", "c2ae0c2737397ada23ff0460603bdb78782e12fc8c20dad0841343790ac93b09", "40b877e360ef3e6dfb793d13a3a5def396b53c77b177366946a8c7391bf7659c", ("Preserve the accepted route/targets through active named References and carriers.", "Stop on unresolved target, owner, client contract, artifact, or environment.", "Changed placement, framework/version, native owner/behavior")),
    ("integration-change-builder", "src/professional-skills/integration-change-builder/SKILL.md", "d7b87f093953c972fbf68cf0141678c0daaea60396d60ba247c30ea844e66766", "617d1818769c1b0fd35289cef58fa998eff25bb47302a9a240e6160afbf5628b", ("external integration change", "Block unknown provider/environment/credential/reconciliation authority", "unresolved provider risk")),
    ("platform-infrastructure-change-builder", "src/professional-skills/platform-infrastructure-change-builder/SKILL.md", "a679dc02672433337f8a7788454ed5b704744a3debcbcda97adf745cd00740ed", "4d43548f48103571f863dc798d5023ae7ad18bd9a674cc74ec14557ee7a74d0a", ("Begin by inspecting target/state/recovery.", "Stop while authority, state/writer/recovery, or effects remain unresolved.", "owner/source, target/version, proposal/effects/recovery, proof limits, release boundary")),
    ("quality-test-gate", "src/professional-skills/quality-test-gate/SKILL.md", "a306349facf66a2c973f5ac3dd98ddfdb9def99de6d454cf27eccdee2c20a33c", "1e694bd93dddec4dd1f6a57ee5400257bd6fe8b82da76485b5898ebf627018cb", ("Map acceptance and failure paths to proving signals.", "**Analysis mode (`analysis-agent`):** Select the proof strategy.", "**Task mode (`task-agent`):** Implement the smallest proving test.", "**Review mode (`review-agent`):** Judge coverage and freshness.", "Stop before production mutation or authority overrun.", "coverage verdict")),
    ("reliability-observability-gate", "src/professional-skills/reliability-observability-gate/SKILL.md", "07ac48ea867816d74e165acfef1ba27018056b724c8fddc940a29b128eea80a9", "8215ee6931408d9742fbf303e1dc04f5cb60763fd832fa8edb015c182f618fb8", ("Bind each objective to consequence, indicator, owner, and action.", "Stop when required reliability closure evidence is incomplete.", "reliability verdict")),
    ("repository-tooling-change-builder", "src/professional-skills/repository-tooling-change-builder/SKILL.md", "edb3823166821757f65b4034a6c6989e4465bdcac4f64f098abd2df5383b6d4f", "5667183572a85ddde75b9caca9d6d07cdbe0c480b580e1fa7a7ae824bdb75d9b", ("Support `task-agent` in changing bounded repository tooling", "Stop on unresolved authority, bootstrap, compatibility, oracle, recovery, or validation.", "cleanup/rollback, proof limits")),
    ("security-privacy-gate", "src/professional-skills/security-privacy-gate/SKILL.md", "69f357e4e7e8e4949dd83a34c1f853e9636b949b5c355fd4bd48c9f069bfd3c2", "f11d7bdde385a27584a4b22e07cd389adc4c59d8933597433238c4ecc5ba7ae5", ("Trace paths.", "Stop on incomplete security closure evidence.", "residual exposure")),
)

G2_BASE_SUCCESSOR_CONTENT_HASHES = {
    path: (old_sha256, new_sha256)
    for _owner, path, old_sha256, new_sha256, _facets in G2_BASE_B1_COMPACTIONS
} | {
    "src/professional-skills/platform-infrastructure-change-builder/references/iac-source-contracts.md": (
        "66e25bbe199f8e7ca2062fe4aa525d574f5eacb40a829e20c91e05b56add90dd",
        "ac76ff616b46e89bc3fbe32c02bb270161ae132d97162b38ba36866ae2148b29",
    ),
    "src/professional-skills/security-privacy-gate/references/security-output-and-gates.md": (
        "067ac9a3ae149ca3fc2572b1473ebbf5678e5eb3fc634267081a54c70968850a",
        "05129afaa245591be03b05cd5c2edc5dcfd5b494002d2dd70a9891b2d253f81e",
    ),
    "src/foundation/capabilities/dependency-vulnerability-scanning/SKILL.md": (
        "936703222d41977c6ba50f5832b729acc778a36f610f38cde7070206abe346c1",
        "25594c05073a5363d6e5084ed43afdfa5a7d6586a3a6f46fe17c6349c8982dda",
    ),
    "src/foundation/capabilities/code-review/SKILL.md": (
        "8cc752ce9f23822e9b7eaab20e10eff995fb738965eaed9892b7384942913073",
        "857b917228633d91dbf101a5446ed8a50ef64f004ddf0e812e9da0a0a55ef47d",
    ),
    "src/foundation/capabilities/regression-testing/SKILL.md": (
        "4c267275fad6956335102a12ac2066986459a0f8bd7b0c37da8c054d58507cbb",
        "683e2ee82844f3d49b62bb8c53c57190088cd284c323f19d7ae0598b81344186",
    ),
    "src/foundation/capabilities/infrastructure-as-code-safety/SKILL.md": (
        "ece9b4accd40549bf15895779777262449a3846fdc3923d5ac1d3a5178b3e5c1",
        "30c8a48b94f411059bb8e17e1670d1b5ca79db1c27b06394d5818f14de10c21c",
    ),
    "src/foundation/capabilities/powershell-professional-usage/SKILL.md": (
        "3d852f13fe931fff6cdabe7f6e0a157ac116d60bf5fbad855ae759d43fd8f329",
        "cd32328dda6ccaa431388c220cac38b08988ad220eb2a8a29b8b2a69224ff27c",
    ),
}

C1D_CONTENT_HASHES = {
    "src/professional-skills/data-middleware-change-builder/SKILL.md": "51af820aededb532f57198975c6290b76e6c65b20e9c0ae2817171a9980c5db1",
    "src/foundation/capabilities/data-migration-design/SKILL.md": "8b3651ba9b7a7a97203fe2dee1806a74a34f74e2250c573e9cd786b0932cc8fa",
    "src/foundation/capabilities/data-migration-design/references/benchmarks-and-patterns.md": "2b46b6b6480cc0afb931df255730a143988a76d944ab9244a26ff02e0d633005",
    "src/foundation/capabilities/release-rollback/SKILL.md": "738e04c280576f5392d91f822c605e2eed1916444aef7bf99b0aae48e2f4d453",
    "src/foundation/capabilities/permission-boundary-modeling/SKILL.md": "7c522d072a783f995f195be77cc33496ca69d4720bc8335d40f595d784a9b9ff",
}

C1D_UNCHANGED_REFERENCE_HASHES = {
    "src/professional-skills/data-middleware-change-builder/references/checklist.md": "7913ab5061bcc773b799077d47a02e5f0fee9e66dbe386c4c1bdb5c5d0b9473f",
    "src/professional-skills/data-middleware-change-builder/references/evidence-patterns.md": "c9f9f5090e759139a549b8f2d21bb47c18740d55dbea095686ea6530966b0569",
    "src/professional-skills/data-middleware-change-builder/references/recovery-patterns.md": "ccd256b2616f32f673419a7452c1b1b47ac23f85485ccfd4a52f5559d614c9aa",
    "src/foundation/capabilities/data-migration-design/references/checklist.md": "17161f751bca0a79e5cb56d07ce3af3ba889feba2437f8429e5934c5b158ed8d",
    "src/foundation/capabilities/data-migration-design/references/evidence-patterns.md": "b868feeb34a6b3e3399403c1b96608a6baa46f8768945768c02ff1a517f3ea65",
    "src/foundation/capabilities/permission-boundary-modeling/references/benchmarks-and-patterns.md": "9b0cd77ef56ec36c379a5eef6a3f7beadbe17fe99a563ad0a57dbad9f6462533",
    "src/foundation/capabilities/permission-boundary-modeling/references/checklist.md": "2a74584d536871e5c510ac7dc64791878bf6a503fa1da7d6eab9ad2ac635cebc",
    "src/foundation/capabilities/permission-boundary-modeling/references/evidence-patterns.md": "f876b57f88901fa11afcbbf60a549a0af4ca884a4b05df338534b85b49346d38",
    "src/foundation/capabilities/release-rollback/references/benchmarks-and-patterns.md": "52bbecd74a4ef1a0dc599855dbbd38d4ba08563e2a5fd60e3a27d4bd10dc74c6",
    "src/foundation/capabilities/release-rollback/references/checklist.md": "e8a45f93dcb38522492d252a295e5a6dcd61f9899bada1f5001aededf85c4096",
    "src/foundation/capabilities/release-rollback/references/evidence-patterns.md": "c0081ac454f9f9fa8a7ebd30b30a41cffdf41db26d3140f9e694672c3c109e58",
}

POST_B_TASK_CONTENT_HASHES = {
    "src/professional-skills/installed-client-change-builder/SKILL.md": "40b877e360ef3e6dfb793d13a3a5def396b53c77b177366946a8c7391bf7659c",
    "src/foundation/capabilities/client-lifecycle-state-restoration/SKILL.md": "fed428bb4a00aef941f2387398915c1ed4bf719eb4fa1c3cc5620ec5e9f8caf5",
    "src/foundation/capabilities/offline-sync-conflict-resolution/SKILL.md": "9503b7167d0ecbe22c11443217eb1c00340840e477e2ad3f99dcf8bad0ea53d6",
    "src/foundation/capabilities/state-management-design/SKILL.md": "01b485ff00c43de9cae0095f723aa531d82edaece53f7de4c3f7bc7ff75ac305",
    "src/foundation/capabilities/offline-sync-conflict-resolution/references/sync-reconciliation-contracts.md": "12fb8e46272ee7194b1526e97f967589156b15c8b38aae60ccc13d8691b63992",
}

POST_B_TASK_BUILT_TOKENS = {
    "src/professional-skills/installed-client-change-builder/SKILL.md": 216,
    "src/foundation/capabilities/client-lifecycle-state-restoration/SKILL.md": 183,
    "src/foundation/capabilities/offline-sync-conflict-resolution/SKILL.md": 207,
    "src/foundation/capabilities/state-management-design/SKILL.md": 187,
    "src/foundation/capabilities/offline-sync-conflict-resolution/references/sync-reconciliation-contracts.md": 466,
}

POST_B_TASK_PROTECTED_HASHES = {
    "src/professional-skills/installed-client-change-builder/references/dotnet-maui-framework-contracts.md": "a2443e016ae5e270f6e3f625cc9de4c580b4d5419031c092f9212284539a5baa",
    "src/professional-skills/installed-client-change-builder/references/electron-framework-contracts.md": "7bae06a3fb6f23031c79f86595d45f5d34b01606d4ad73cbf3a0897bf7f6b8d9",
    "src/professional-skills/installed-client-change-builder/references/flutter-framework-contracts.md": "0be7ae0cb79cff1634139be1586fb31b275a4a95ff5cc4f6114ad5be1f9cc504",
    "src/professional-skills/installed-client-change-builder/references/kotlin-multiplatform-framework-contracts.md": "68b9008c125e5ee0181b9cdd81c677ef29a3803ff0ef3b645e36752eb0069cdd",
    "src/professional-skills/installed-client-change-builder/references/native-platform-source-contracts.md": "7e1fb286caf5638028fbd06f840fe4ce4bcf5a4a5c4e7773df50c43a35ec56d4",
    "src/professional-skills/installed-client-change-builder/references/qt-framework-contracts.md": "a00a0182e8f05ba85ba4f923928ffab9350e19e1ce471255d4fccc7b6e85b4ed",
    "src/professional-skills/installed-client-change-builder/references/react-native-framework-contracts.md": "daa5958b7065ce843c175e4470b487d26dda17f4e2e430edd23f1f1632863cd2",
    "src/professional-skills/installed-client-change-builder/references/tauri-framework-contracts.md": "365093157fc5bf006d0ee9a29bf4991d8f4e35867f54288e4780246335b131f1",
    "src/foundation/capabilities/client-lifecycle-state-restoration/references/restoration-boundaries.md": "f28f0ebbef53471cea1df5c350111eba08471398179937386059da34b36fdeda",
    "src/foundation/capabilities/state-management-design/references/benchmarks-and-patterns.md": "8b6c5db4c225be49ffd4fefa84949d0c39f110a2e261bfa821261afa008cec2b",
    "src/foundation/capabilities/state-management-design/references/checklist.md": "f7f65d3edfc03cbc87e681f6cf58ca05a2adc7486fb2e1601ff853840614e7fb",
    "src/foundation/capabilities/state-management-design/references/evidence-patterns.md": "68999e5126cfbe56e9cd453d8399223fb1087268bb85f5542578439cc4edfc7f",
}

POST_B_TASK_SELECTED_REFERENCES = (
    ("installed-client-change-builder", "references/native-platform-source-contracts.md"),
    ("installed-client-change-builder", "references/flutter-framework-contracts.md"),
    ("installed-client-change-builder", "references/react-native-framework-contracts.md"),
    ("installed-client-change-builder", "references/electron-framework-contracts.md"),
    ("installed-client-change-builder", "references/tauri-framework-contracts.md"),
    ("installed-client-change-builder", "references/qt-framework-contracts.md"),
    ("installed-client-change-builder", "references/dotnet-maui-framework-contracts.md"),
    ("installed-client-change-builder", "references/kotlin-multiplatform-framework-contracts.md"),
    ("client-lifecycle-state-restoration", "references/restoration-boundaries.md"),
    ("offline-sync-conflict-resolution", "references/sync-reconciliation-contracts.md"),
    ("state-management-design", "references/benchmarks-and-patterns.md"),
    ("state-management-design", "references/checklist.md"),
    ("state-management-design", "references/evidence-patterns.md"),
)

POST_B_TASK_RULE_RELOCATIONS = (
    (
        "src/foundation/capabilities/client-lifecycle-state-restoration/SKILL.md",
        "- **Model lifecycle states by allowed effects.** Distinguish visible, obscured, background-capable, suspended, terminated, and relaunched states according to the repository's actual runtime contract.",
        (("src/foundation/capabilities/client-lifecycle-state-restoration/references/restoration-boundaries.md", ("| Visibility | Which UI instance is visible", "| Process lifetime | Whether the runtime can suspend")),),
    ),
    (
        "src/foundation/capabilities/client-lifecycle-state-restoration/SKILL.md",
        "- **Classify restorable state before serialization.** Preserve only user continuity that is safe to reconstruct while durable business truth remains with its authoritative owner.",
        (("src/foundation/capabilities/client-lifecycle-state-restoration/references/restoration-boundaries.md", ("| Snapshot scope | Which values reconstruct user intent",)),),
    ),
    (
        "src/foundation/capabilities/client-lifecycle-state-restoration/SKILL.md",
        "- **Make initialization repeat-safe.** Give launch, activation, and restoration work explicit ownership so duplicate entry cannot register handlers or commit effects twice.",
        (("src/foundation/capabilities/client-lifecycle-state-restoration/references/restoration-boundaries.md", ("| Initialization | Activation identity, instance ownership",)),),
    ),
    (
        "src/foundation/capabilities/client-lifecycle-state-restoration/SKILL.md",
        "- **Bind snapshots to identity and compatibility.** Reject or migrate snapshots when account, session, schema, application version, or required source data no longer matches.",
        (("src/foundation/capabilities/client-lifecycle-state-restoration/references/restoration-boundaries.md", ("| Compatibility | Snapshot schema, application version", "| Identity | Account, session, workspace, tenant")),),
    ),
    (
        "src/foundation/capabilities/client-lifecycle-state-restoration/SKILL.md",
        "- **Require lifecycle generation for asynchronous completion.** Cancel disposable work and prevent stale results from mutating a newer screen, session, or account.",
        (("src/foundation/capabilities/client-lifecycle-state-restoration/references/restoration-boundaries.md", ("| Async work | Operation owner, lifecycle generation",)),),
    ),
    (
        "src/foundation/capabilities/client-lifecycle-state-restoration/SKILL.md",
        "- **Restore intent without replaying effects.** Reconstruct navigation, drafts, and selections while reconciling consequential operations through their authoritative status.",
        (("src/foundation/capabilities/client-lifecycle-state-restoration/references/restoration-boundaries.md", ("| Consequential effects | Operation identity and current authoritative status",)),),
    ),
    (
        "src/foundation/capabilities/client-lifecycle-state-restoration/SKILL.md",
        "- **Define reset behavior for destructive transitions.** Specify what survives crash or upgrade and what must clear on logout, account switch, corruption, or incompatible restoration.",
        (("src/foundation/capabilities/client-lifecycle-state-restoration/references/restoration-boundaries.md", ("Clear or partition restoration when identity changes", "Migrate, partially restore, or discard through an explicit branch", "Return the affected lifecycle states, last reliable persistence point")),),
    ),
    (
        "src/foundation/capabilities/offline-sync-conflict-resolution/SKILL.md",
        "- **Choose authority per data and operation.** Declare local-first, server-authoritative, or explicitly merged behavior before selecting queues or caches.",
        (("src/foundation/capabilities/offline-sync-conflict-resolution/references/sync-reconciliation-contracts.md", ("| Read | Name authority/freshness per mode",)),),
    ),
    (
        "src/foundation/capabilities/offline-sync-conflict-resolution/SKILL.md",
        "- **Persist pending intent with reconciliation identity.** Record the business operation, target identity, base revision, payload version, and user-visible status needed after restart.",
        (("src/foundation/capabilities/offline-sync-conflict-resolution/references/sync-reconciliation-contracts.md", ("| Write | Choose online-only, queued, or local-first", "| Pending | Persist business/target identity")),),
    ),
    (
        "src/foundation/capabilities/offline-sync-conflict-resolution/SKILL.md",
        "- **Resolve unknown results before replay.** Query authoritative status or use proven duplicate suppression whenever a timeout or disconnect can hide a committed effect.",
        (("src/foundation/capabilities/offline-sync-conflict-resolution/references/sync-reconciliation-contracts.md", ("| Unknown | Reconcile authoritative status",)),),
    ),
    (
        "src/foundation/capabilities/offline-sync-conflict-resolution/SKILL.md",
        "- **Separate optimistic presentation from confirmed truth.** Represent pending, accepted, rejected, conflicted, and abandoned outcomes so rollback cannot erase unrelated changes.",
        (("src/foundation/capabilities/offline-sync-conflict-resolution/references/sync-reconciliation-contracts.md", ("| Optimistic | Separate confirmed base/overlay",)),),
    ),
    (
        "src/foundation/capabilities/offline-sync-conflict-resolution/SKILL.md",
        "- **Use semantic revisions instead of client wall clocks.** Detect conflicts from authoritative versions or domain intent unless the contract explicitly tolerates clock skew and last-writer behavior.",
        (("src/foundation/capabilities/offline-sync-conflict-resolution/references/sync-reconciliation-contracts.md", ("| Conflict | Use authoritative version, field semantics",)),),
    ),
    (
        "src/foundation/capabilities/offline-sync-conflict-resolution/SKILL.md",
        "- **Advance cursors only with applied state.** Commit page results, deletion markers, and checkpoint progress together so partial synchronization cannot skip or resurrect records.",
        (("src/foundation/capabilities/offline-sync-conflict-resolution/references/sync-reconciliation-contracts.md", ("| Incremental | Apply pages, tombstones, checkpoint atomically",)),),
    ),
    (
        "src/foundation/capabilities/offline-sync-conflict-resolution/SKILL.md",
        "- **Bind resumable transfer state to one upload.** Verify resource identity, processed offset, representation length, response completeness, current limits, expiry, and cancellation before appending bytes.",
        (("src/foundation/capabilities/offline-sync-conflict-resolution/references/sync-reconciliation-contracts.md", ("| Transfer | Bind upload identity, processed offset",)),),
    ),
    (
        "src/foundation/capabilities/offline-sync-conflict-resolution/SKILL.md",
        "- **End blocked work in an owned recovery state.** Expose retry, discard, replace, merge, or support escalation according to consequence and user authority.",
        (("src/foundation/capabilities/offline-sync-conflict-resolution/references/sync-reconciliation-contracts.md", ("Return authority, pending schema, retry/unknown result",)),),
    ),
    (
        "src/foundation/capabilities/state-management-design/SKILL.md",
        "- **Classify state by authority and lifetime.** Distinguish local interaction, form draft, server-owned, cached, derived, navigation, authentication context, optimistic, and persisted state before choosing storage or sharing scope.",
        (("src/foundation/capabilities/state-management-design/references/benchmarks-and-patterns.md", ("2. **Classify:** distinguish server, local UI",)),),
    ),
    (
        "src/foundation/capabilities/state-management-design/SKILL.md",
        "- **Keep one authoritative owner per state meaning.** Store durable business truth at its server or domain owner, derive redundant views where feasible, and define synchronization when copies are unavoidable.",
        (("src/foundation/capabilities/state-management-design/references/benchmarks-and-patterns.md", ("3. **Source of truth:** name the authoritative writer",)),),
    ),
    (
        "src/foundation/capabilities/state-management-design/SKILL.md",
        "- **Scope state to the narrowest consumer set.** Use component, feature, route, request, session, account, tenant, or application scope according to actual coordination and cleanup needs, not convenience.",
        (("src/foundation/capabilities/state-management-design/references/benchmarks-and-patterns.md", ("8. **Local versus global:** keep state at the lowest owner",)),),
    ),
    (
        "src/foundation/capabilities/state-management-design/SKILL.md",
        "- **Bind identity and freshness.** Include user, tenant, resource, query, version, and relevant policy context in keys and invalidation so account switching or late responses cannot cross boundaries.",
        (("src/foundation/capabilities/state-management-design/references/benchmarks-and-patterns.md", ("4. **Cache key:** derive response-varying resource", "5. **Freshness:** tie stale/retention/revalidation", "6. **Invalidation:** name mutations", "7. **Auth reset:** on logout")),),
    ),
    (
        "src/foundation/capabilities/state-management-design/SKILL.md",
        "- **Coordinate async and optimistic transitions.** Define operation identity, supersession, cancellation, stale arrival, server rejection, conflict, rollback or reconciliation, and forbidden duplicate effects.",
        (("src/foundation/capabilities/state-management-design/references/benchmarks-and-patterns.md", ("12. **Optimistic mutation:** snapshot affected views", "13. **Concurrency:** define stale response")),),
    ),
    (
        "src/foundation/capabilities/state-management-design/SKILL.md",
        "- **Treat persistence as a privacy and compatibility boundary.** Apply current classification, expiry, encryption, clear-on-logout or account change, migration, corruption, and backup behavior before storing sensitive or long-lived client state.",
        (
            ("src/foundation/capabilities/state-management-design/references/benchmarks-and-patterns.md", ("11. **Persistence:** choose URL, cookie, local/session storage",)),
            ("src/foundation/capabilities/state-management-design/references/checklist.md", ("For each persisted browser value, record privacy sensitivity",)),
        ),
    ),
    (
        "src/foundation/capabilities/state-management-design/SKILL.md",
        "- **Prove ownership and cleanup paths.** Exercise navigation, refresh, account switch, concurrent requests, failure, recovery, and unmount or shutdown behavior with explicit limits on uninspected surfaces.",
        (
            ("src/foundation/capabilities/state-management-design/references/checklist.md", ("Define auth expiry, sign-out, 401, role change", "Name handoff boundaries, validation evidence")),
            ("src/foundation/capabilities/state-management-design/references/evidence-patterns.md", ("## State Surface-To-Validation Map",)),
        ),
    ),
)


POST_B_REVIEW_CONTENT_HASHES = {
    "src/domain-extensions/cross-platform-client-extension/SKILL.md": "9a7c8b21bf06711c2b4a54a1e6b977ef31492cbd68ea709c24042077c4ebb449",
    "src/professional-skills/ai-code-review-refactor/references/review-output-and-gates.md": "d0009b17c8d3e57f97806ad846347a0da31f2df2032ce4c5387cd552633f6553",
}

POST_B_REVIEW_BUILT_TOKENS = {
    "src/domain-extensions/cross-platform-client-extension/SKILL.md": 265,
    "src/professional-skills/ai-code-review-refactor/references/review-output-and-gates.md": 533,
}

POST_B_REVIEW_PROTECTED_HASHES = {
    "src/professional-skills/ai-code-review-refactor/SKILL.md": "cf548e3bc362edc9f5d5f8f488c88d2ae37e522dbf1f0ef9695a5d6601ddd213",
    "src/domain-extensions/cross-platform-client-extension/references/shared-and-target-ownership-contracts.md": "6008e74909c0f468d031a6c26b9a0471d489c0564443bc27baaf25be90e55c4e",
    "src/domain-extensions/cross-platform-client-extension/references/bridge-plugin-and-ffi-contracts.md": "b54a12489713708c037235ac13b9225f8bbc2c8a8d1ee410fa3cade5c6bb776a",
    "src/domain-extensions/cross-platform-client-extension/references/parity-and-regression-contracts.md": "2514e35e59c10cdc21b5ba9b9bad56b5c95b820af1ed0a656e574107858ca36e",
    "src/domain-extensions/cross-platform-client-extension/references/framework-target-evidence-contracts.md": "3885f2f5c3f01b84ea18b3eef4c1a21d09be0f0540621ba8a346a061ec29603c",
}

POST_B_REVIEW_SELECTED_REFERENCES = (
    ("ai-code-review-refactor", "references/ai-review-pattern-catalog.md"),
    ("ai-code-review-refactor", "references/review-output-and-gates.md"),
    ("ai-code-review-refactor", "references/solution-optimality.md"),
    (
        "cross-platform-client-extension",
        "references/shared-and-target-ownership-contracts.md",
    ),
    (
        "cross-platform-client-extension",
        "references/bridge-plugin-and-ffi-contracts.md",
    ),
    (
        "cross-platform-client-extension",
        "references/parity-and-regression-contracts.md",
    ),
    (
        "cross-platform-client-extension",
        "references/framework-target-evidence-contracts.md",
    ),
    ("design-pattern-selection", "references/pattern-evidence-record.md"),
    (
        "implementation-structure-design",
        "references/object-module-decomposition.md",
    ),
    ("implementation-structure-design", "references/reuse-and-placement.md"),
    ("implementation-structure-design", "references/evidence-patterns.md"),
)

POST_B_REVIEW_RULE_RELOCATIONS = (
    (
        "src/domain-extensions/cross-platform-client-extension/SKILL.md",
        "- If targets remain unknown after that inspection, do not load this modifier and ask one bounded target question.",
        "- Unknown targets after source inspection prohibit loading and require one bounded target question.",
    ),
    (
        "src/domain-extensions/cross-platform-client-extension/SKILL.md",
        "- Load only the active ownership, bridge, parity, or target-evidence Reference and every confirmed concrete platform Domain.",
        "- Load only active ownership, bridge, parity, or target-evidence References and confirmed platform Domains.",
    ),
    (
        "src/domain-extensions/cross-platform-client-extension/SKILL.md",
        "- Keep cohesive targets together; use Analysis when ownership, dependency, validation, release, rollback, or integration boundaries split execution.",
        "- Keep cohesive targets together; use Analysis when ownership, dependency, validation, or integration splits execution.",
    ),
    (
        "src/domain-extensions/cross-platform-client-extension/SKILL.md",
        "- Route signing, store/channel rollout, release approval, and rollback authority to `delivery-release-gate`.",
        "- Return signing, rollout, release, and rollback authority to `delivery-release-gate`.",
    ),
    (
        "src/professional-skills/ai-code-review-refactor/references/review-output-and-gates.md",
        "1. **Findings:** Put Critical, High, Medium, and Low findings first.",
        "1. **Findings:** list Critical/High/Medium/Low findings first; give path/line or symbol, reachable failure, evidence, impact, severity, required outcome, and non-implementing correction direction. State explicitly when none exist.",
    ),
    (
        "src/professional-skills/ai-code-review-refactor/references/review-output-and-gates.md",
        """2. **Review decision:**
   - Record specification compliance before code quality, then `Approved`, `Returned for remediation`, or `Blocked`.
   - Use `Blocked` only for unavailable required evidence or unverifiable scope, naming the missing evidence, unverified scope, and unblock condition.
   - Number remediation actions and state exactly what an approval covers and excludes.""",
        "2. **Review decision:** assess specification before quality; choose `Approved`, `Returned for remediation`, or evidence-blocked `Blocked`; number remediation and bound approval/exclusions.",
    ),
    (
        "src/professional-skills/ai-code-review-refactor/references/review-output-and-gates.md",
        "3. **Reviewed scope:** Name the actual diff, every changed file inspected, relevant source and tests read, and any changed or reachable boundary left unreviewed. Record implementer/reviewer separation.",
        "3. **Reviewed scope:** name actual diff, inspected changed files/source/tests, unreviewed reachable boundaries, and implementer/reviewer separation.",
    ),
    (
        "src/professional-skills/ai-code-review-refactor/references/review-output-and-gates.md",
        "4. **Source-to-impact evidence:** Tie current evidence to the affected acceptance criterion or reachable impact path.",
        "4. **Source-to-impact evidence:** connect each finding to acceptance/invariant through current diff, source, tests, contracts, validation, or authoritative metadata; separate fact, assumption, and unverified behavior.",
    ),
    (
        "src/professional-skills/ai-code-review-refactor/references/review-output-and-gates.md",
        "5. **Behavior preservation:** For a refactor or repair, state which affected invariants and observable behavior remain unchanged.",
        "5. **Behavior preservation:** for repair/refactor, state invariant/observable preservation, proof and changed-code coverage, intentional delta, and warranted same-pattern/reuse/placement scope.",
    ),
    (
        "src/professional-skills/ai-code-review-refactor/references/review-output-and-gates.md",
        "6. **Repair and re-review:** Map each blocking finding to its required repair.",
        "6. **Repair and re-review:** map blocking findings to repair and re-review stage; close only against latest repair diff plus fresh validation.",
    ),
    (
        "src/professional-skills/ai-code-review-refactor/references/review-output-and-gates.md",
        "7. **Evidence limits and next action:** Record each validation or command actually run with its outcome, plus stale, skipped, or unavailable checks. The same evidence states its proof limits, residual risk, and recommended next owner and action.",
        "7. **Evidence limits and next action:** record each run and result, stale/skipped/unavailable checks, proof limits, residual risk, and next owner/action.",
    ),
    (
        "src/professional-skills/ai-code-review-refactor/references/review-output-and-gates.md",
        "1. Report a finding only when current diff, source, test, contract, validation, or authoritative dependency evidence supports an acceptance gap or reachable source-to-impact path. Otherwise, record the uncertainty as an evidence limit or request the missing proof.",
        "1. Report findings only from current evidence of an acceptance gap or reachable impact; otherwise record an evidence limit or missing proof.",
    ),
    (
        "src/professional-skills/ai-code-review-refactor/references/review-output-and-gates.md",
        "2. Calibrate severity from credible impact, reachability, affected scope, reversibility, and acceptance or release risk; do not promote style preference into a blocking defect.",
        "2. Calibrate severity by credible impact, reachability, scope, reversibility, and release risk; style alone is non-blocking.",
    ),
    (
        "src/professional-skills/ai-code-review-refactor/references/review-output-and-gates.md",
        "3. When generated code depends on an API, symbol, dependency, or contract that may be invented or version-sensitive, require proof against the declared version. Repository search, typecheck, build output, or authoritative package metadata are candidate mechanisms; cite why the selected evidence is sufficient.",
        "3. For possibly invented/version-sensitive API or contract use, require sufficient version-bound search, typecheck, build, or authoritative metadata.",
    ),
    (
        "src/professional-skills/ai-code-review-refactor/references/review-output-and-gates.md",
        "4. When a refactor or repair may alter observable behavior, require bounded equivalence evidence.",
        "4. When repair/refactor may change behavior, require bounded characterization, regression, contract, or semantic-diff evidence and name uncovered paths.",
    ),
    (
        "src/professional-skills/ai-code-review-refactor/references/review-output-and-gates.md",
        "5. When the failure mechanism provides a credible recurrence signal, require a same-pattern search scope tied to that mechanism and explain exclusions. Sibling implementations, call sites, or analogous contracts form evidence when warranted; an isolated finding without recurrence evidence does not trigger the scan.",
        "5. When recurrence evidence is credible, bind required same-pattern scope and exclusions to its mechanism.",
    ),
    (
        "src/professional-skills/ai-code-review-refactor/references/review-output-and-gates.md",
        "6. When a finding blocks approval, require repair and fresh relevant validation.",
        "6. Blocking findings require repair, fresh relevant validation, and independent re-review of the latest diff.",
    ),
    (
        "src/professional-skills/ai-code-review-refactor/references/review-output-and-gates.md",
        "7. When specialized risk exceeds assigned skills or evidence, return a handoff naming the triggered owner and required proof.",
        "7. When assigned expertise or evidence is insufficient, hand off the triggered owner and proof; never load a gate by default.",
    ),
    (
        "src/professional-skills/ai-code-review-refactor/references/review-output-and-gates.md",
        "8. Define approval by the inspected diff, files, contracts, and exercised paths.",
        "8. Bound approval to inspected diff/files/contracts/paths; list partial scope and exclude unsupported production-safety or broad-equivalence claims.",
    ),
)


FRONTEND_JIT_OWNER_SPECS = {
    "frontend-change-builder": {
        "root": "src/professional-skills/frontend-change-builder/SKILL.md",
        "registry": "professional",
        "cap": 270,
        "removed": ("references/frontend-output-and-gates.md",),
        "references": {
            "references/component-placement-and-reuse-gates.md": ("targeted", ("task-agent",), ("boundary-decision", "selected-approach", "residual-risk"), "route-or-material-unknown", ("acceptance", "scope", "material-risk-floor")),
            "references/state-ownership-and-api-failure-gates.md": ("targeted", ("task-agent",), ("decision-record", "failure-decision", "residual-risk"), "route-or-material-unknown", ("acceptance", "scope", "material-risk-floor")),
            "references/accessibility-closure-gates.md": ("targeted", ("task-agent",), ("gate-decision", "validation-plan", "proof-limit"), "route-or-material-unknown", ("acceptance", "scope", "material-risk-floor")),
            "references/frontend-security-closure-gates.md": ("targeted", ("task-agent",), ("gate-decision", "validation-plan", "residual-risk"), "route-or-material-unknown", ("acceptance", "scope", "material-risk-floor")),
            "references/frontend-quality-and-validation-evidence.md": ("evidence-pattern", ("task-agent",), ("evidence-record", "validation-plan", "proof-limit", "residual-risk"), "repo-resolvable-fact", ()),
            "references/same-pattern-scan-and-handoff-evidence.md": ("evidence-pattern", ("task-agent",), ("evidence-record", "validation-plan", "proof-limit", "residual-risk"), "repo-resolvable-fact", ()),
        },
    },
    "interaction-state-modeling": {
        "root": "src/foundation/capabilities/interaction-state-modeling/SKILL.md",
        "registry": "foundation",
        "cap": 290,
        "removed": ("references/benchmarks-and-patterns.md", "references/evidence-patterns.md"),
        "references": {
            "references/state-semantics-benchmark-anchors.md": ("benchmark-pattern", ALL_ROLES, ("option-comparison", "selected-approach"), "route-or-material-unknown", ("acceptance", "scope", "material-risk-floor")),
            "references/state-distinction-and-outcome-patterns.md": ("benchmark-pattern", ALL_ROLES, ("option-comparison", "selected-approach"), "route-or-material-unknown", ("acceptance", "scope", "material-risk-floor")),
            "references/state-derivation-and-recovery-decisions.md": ("targeted", ALL_ROLES, ("decision-record", "failure-decision", "residual-risk"), "route-or-material-unknown", ("acceptance", "scope", "material-risk-floor")),
            "references/state-transition-and-backend-evidence.md": ("evidence-pattern", ALL_ROLES, ("evidence-record", "validation-plan", "proof-limit", "residual-risk"), "repo-resolvable-fact", ()),
            "references/state-accessibility-evidence.md": ("evidence-pattern", ALL_ROLES, ("evidence-record", "validation-plan", "proof-limit", "residual-risk"), "repo-resolvable-fact", ()),
            "references/state-evidence-freshness-and-tool-boundary.md": ("evidence-pattern", ALL_ROLES, ("evidence-record", "validation-plan", "proof-limit", "residual-risk"), "repo-resolvable-fact", ()),
        },
    },
    "accessibility-inclusive-design": {
        "root": "src/foundation/capabilities/accessibility-inclusive-design/SKILL.md",
        "registry": "foundation",
        "cap": 330,
        "removed": ("references/inclusive-interaction-contracts.md",),
        "references": {
            "references/semantic-keyboard-and-focus-contracts.md": ("targeted", ALL_ROLES, ("selected-approach", "boundary-decision", "proof-limit"), "route-or-material-unknown", ("acceptance", "scope", "material-risk-floor")),
            "references/announcements-and-form-recovery-contracts.md": ("targeted", ALL_ROLES, ("selected-approach", "failure-decision", "proof-limit"), "route-or-material-unknown", ("acceptance", "scope", "material-risk-floor")),
            "references/visual-adaptation-and-direct-manipulation-contracts.md": ("targeted", ALL_ROLES, ("selected-approach", "boundary-decision", "proof-limit"), "route-or-material-unknown", ("acceptance", "scope", "material-risk-floor")),
            "references/accessibility-verification-evidence.md": ("evidence-pattern", ALL_ROLES, ("evidence-record", "validation-plan", "proof-limit", "residual-risk"), "repo-resolvable-fact", ()),
        },
    },
    "web-platform-professional-usage": {
        "root": "src/foundation/capabilities/web-platform-professional-usage/SKILL.md",
        "registry": "foundation",
        "cap": 340,
        "removed": ("references/document-event-rendering-contracts.md", "references/navigation-network-background-contracts.md"),
        "references": {
            "references/document-semantics-and-accessibility-tree-contracts.md": ("targeted", ALL_ROLES, ("selected-approach", "boundary-decision", "proof-limit"), "route-or-material-unknown", ("acceptance", "scope", "material-risk-floor")),
            "references/event-dispatch-and-default-action-contracts.md": ("targeted", ALL_ROLES, ("decision-record", "failure-decision", "proof-limit"), "route-or-material-unknown", ("acceptance", "scope", "material-risk-floor")),
            "references/layout-paint-and-compositing-contracts.md": ("targeted", ALL_ROLES, ("selected-approach", "validation-plan", "proof-limit"), "route-or-material-unknown", ("acceptance", "scope", "material-risk-floor")),
            "references/navigation-and-restoration-contracts.md": ("targeted", ALL_ROLES, ("decision-record", "failure-decision", "proof-limit"), "route-or-material-unknown", ("acceptance", "scope", "material-risk-floor")),
            "references/origin-storage-and-fetch-policy-contracts.md": ("targeted", ALL_ROLES, ("boundary-decision", "failure-decision", "proof-limit", "residual-risk"), "route-or-material-unknown", ("layer3", "acceptance", "scope", "material-risk-floor")),
            "references/service-worker-and-cache-contracts.md": ("targeted", ALL_ROLES, ("decision-record", "failure-decision", "validation-plan", "residual-risk"), "route-or-material-unknown", ("layer3", "acceptance", "scope", "material-risk-floor")),
            "references/worker-and-persistent-channel-contracts.md": ("targeted", ALL_ROLES, ("decision-record", "failure-decision", "validation-plan", "residual-risk"), "route-or-material-unknown", ("layer3", "acceptance", "scope", "material-risk-floor")),
            "references/browser-compatibility-and-verification-evidence.md": ("evidence-pattern", ALL_ROLES, ("evidence-record", "validation-plan", "proof-limit", "residual-risk"), "repo-resolvable-fact", ()),
        },
    },
}

C1F_FINAL_SOURCE_HASHES = {
    "src/professional-skills/repository-tooling-change-builder/SKILL.md": "5667183572a85ddde75b9caca9d6d07cdbe0c480b580e1fa7a7ae824bdb75d9b",
    "src/professional-skills/repository-tooling-change-builder/references/generator-and-plugin-contracts.md": "8762b282517f3e3c715a9c39150bf014e92314d533f37698de613d3f58b784d9",
    "src/professional-skills/repository-tooling-change-builder/references/harness-validity-contracts.md": "99e4f40187b5f77be2f986223d24f3e1ad830d3e4bd9744e91f5c0c9ff135a07",
    "src/professional-skills/repository-tooling-change-builder/references/repository-automation-contracts.md": "a46fda66e387de044e6b125908fab917d642df0c5d8ff756436e6920d217b392",
    "src/foundation/capabilities/design-pattern-selection/SKILL.md": "a4c8c36b57089fc079fadefcb576f832be424054c5155bbfc20e1aeea1725e5a",
    "src/foundation/capabilities/design-pattern-selection/references/pattern-evidence-record.md": "a67c93ecbf9cc270218467cd91cf186b167906db42d9b6c94f8db2f9a3f98fc0",
    "src/foundation/capabilities/build-tool-professional-usage/SKILL.md": "50f4817aa12afbe1da520e415f54c8823d2f3ae0adf1e36d227503900c2724cf",
    "src/foundation/capabilities/targeted-validation-selection/SKILL.md": "db53a393fa8ca8fa452bc942a594fa242bfbcd457834a9c9f0f87267d0ac490b",
    "src/foundation/capabilities/degradation-circuit-breaking/SKILL.md": "a0ec08520738b707f43cba45cf0dc9492b76b879a81f3aff51ba2dcba438f0a4",
    "src/foundation/capabilities/observability/SKILL.md": "129ba43ca05b88b4481e192f18fd1f37ed6043de3f94c7e70993f30995d06d97",
    "src/foundation/capabilities/backup-recovery/SKILL.md": "9ec6f32cae9c546a1e2059a4846bf7bf85e72e7d2cf62088366424575dcbc6f0",
    "src/professional-skills/reliability-observability-gate/SKILL.md": "8215ee6931408d9742fbf303e1dc04f5cb60763fd832fa8edb015c182f618fb8",
}

C1F_BUILT_PROJECTION_SPECS = {
    "src/professional-skills/repository-tooling-change-builder/SKILL.md": ("repository-tooling-change-builder", 261, "475a286d7143dba32bdab259bc4b121b8d769070b14641c8a12b12287507451b"),
    "src/foundation/capabilities/design-pattern-selection/SKILL.md": (None, 222, "4def12ed23d185b7c07cc0752b08ac3bf54d2fc226c194439eb958a1045bcf9b"),
    "src/foundation/capabilities/build-tool-professional-usage/SKILL.md": (None, 269, "69dc38e431ef7bcbd52bcf46c6ae7095419f88a7f7774c0e38128ffb0c472f04"),
    "src/foundation/capabilities/targeted-validation-selection/SKILL.md": (None, 223, "33361cbcacb5926d779a486126acb5d4f5edb211655effedee3b6053aa763730"),
    "src/professional-skills/reliability-observability-gate/SKILL.md": ("reliability-observability-gate", 341, "4b83912c8d1a6b97443e914407e2caeed34c0dc31a84244f4e8561000026961d"),
    "src/foundation/capabilities/degradation-circuit-breaking/SKILL.md": (None, 209, "b51e91ee25cdacff81c852603e10b1762dea62d8619357a982912854964a919b"),
    "src/foundation/capabilities/observability/SKILL.md": (None, 180, "e4ef41f730af8764196ca00ac1fb70771f9c637814e77b155393ed72b7589e2a"),
    "src/foundation/capabilities/backup-recovery/SKILL.md": (None, 224, "bf473845a5b6d130ca9197b5c8c1810fc5fb9519114178f22a1c335810553582"),
}

C1F_RULE_OWNER_ANCHORS = {
    "src/professional-skills/repository-tooling-change-builder/SKILL.md": ("Keep the tooling decision within its owner, inputs, stops, and output contract.", "Stop on unresolved authority, bootstrap, compatibility, oracle, recovery, or validation."),
    "src/professional-skills/repository-tooling-change-builder/references/generator-and-plugin-contracts.md": ("Name schemas, templates, source, generator code, flags, versions, and the sole editable owner.", "Prove a clean checkout can obtain or build the generator without its own absent output.", "Define destinations, ownership markers, stable order and format, stale deletion, and partial-write recovery.", "Bind plugin host API, ABI/protocol, versions, loading, options, and rejection.", "Preserve diagnostic identity, location, severity, message, fix applicability, and idempotence."),
    "src/professional-skills/repository-tooling-change-builder/references/harness-validity-contracts.md": ("Name the changed mechanism, boundary, and smallest representative fixture.", "Bind expected output or state to an independent oracle.", "Make the valid case pass and an invalid case fail for the intended reason.", "Distinguish test failure, infrastructure loss, skip, timeout, crash, and malformed output."),
    "src/professional-skills/repository-tooling-change-builder/references/repository-automation-contracts.md": ("Define argv, config/environment precedence, stdio, help, machine output, and exits.", "Resolve an authorized target allowlist once; use it for preview and apply and reject current-directory authority.", "Define child executable, argv, environment, directory, stdio, timeout, cancellation, descendants, and exit mapping.", "Preserve the primary failure while reporting cleanup or rollback failure."),
    "src/foundation/capabilities/design-pattern-selection/SKILL.md": ("Define the current force, reachable consumers, and direct alternative.", "Define construction, lifecycle, effect, concurrency, and failure ownership.", "Preserve visible I/O, latency, failure, cancellation, cleanup, and results; sharing is not a force.", "Route public/cross-module surfaces and specialist proof."),
    "src/foundation/capabilities/design-pattern-selection/references/pattern-evidence-record.md": ("Compare a direct call, constructor, function, composition, or existing relationship.", "Record initialization, synchronization, reset, unsubscribe or drain, shutdown, and failure ownership.", "Keep I/O, latency, timeout, retry, cancellation, cleanup, transaction, and partial failure visible.", "Record public, generated, serialized, and cross-module compatibility and deletion paths."),
    "src/foundation/capabilities/build-tool-professional-usage/SKILL.md": ("Define graph, generated authority, cache/action identity, and affected-test proof.", "Prove clean, incremental, parallel, and hermetic behavior.", "Compare source-bound artifacts rather than command success.", "Validate missing, stale, corrupt, partial, interrupted, and clean rebuild outcomes."),
    "src/foundation/capabilities/targeted-validation-selection/SKILL.md": ("Map acceptance and risk to the smallest-sufficient evidenced commands and coverage.", "Record target, directory, effects, authority, stop, recovery, cleanup, and retained output before execution.", "Preserve unsupported coverage, proof limits, and residual risk."),
    "src/foundation/capabilities/degradation-circuit-breaking/SKILL.md": ("Consume gateway ceilings without redefining them.", "Bind phase timeouts and retry to current ceiling and failure evidence.", "Select fallback, isolation, and breaker behavior from product invariants, capacity, and recovery."),
    "src/foundation/capabilities/observability/SKILL.md": ("Select signals from material impact.", "Propagate correlation only across evidence-bearing boundaries.", "Bind every alert to an owner and response."),
    "src/foundation/capabilities/backup-recovery/SKILL.md": ("Derive recovery objectives from consequence, scope, scale, dependencies, and owner.", "Map artifacts to capture, key/schema lineage, target, and restore order.", "For the named recovery, validate restored invariants.", "For the named recovery, reconcile side effects."),
    "src/professional-skills/reliability-observability-gate/SKILL.md": ("Bind each objective to consequence, indicator, owner, and action.", "Match each resilience control to reachable failure and recovery behavior.", "- **Review mode (`review-agent`):** reliability verdict; failure findings; current reviewed evidence and freshness; proof limits; unproven recovery behavior; residual risk."),
}

C1G_FINAL_SOURCE_HASHES = {
    "src/professional-skills/delivery-release-gate/SKILL.md": "aaf5c2ea8078a3c794725303f2ce7c3372dd96569a4a0d5dc88bc82024fa1fda",
    "src/professional-skills/delivery-release-gate/references/delivery-output-and-gates.md": "e76f8bcbd7b0ae6a0b5aa27afd603fe49b7def9c240bad0eda4da1c336527db4",
    "src/foundation/capabilities/version-compatibility/SKILL.md": "008bb557182e152938008b0f5e7175f5c2fb32eb44b9a7352b2a28e7591cfd75",
    "src/foundation/capabilities/version-compatibility/references/checklist.md": "28af459587f9e62605d26021e65a7473ce105db007c22ea47e9a74147f62ed32",
    "src/foundation/capabilities/version-compatibility/references/compatibility-benchmarks.md": "af7766cecc9f29fad1063a16234c6bf69cc7fb62148a6934c7b498de7d5eb893",
    "src/foundation/capabilities/version-compatibility/references/evidence-patterns.md": "ccb0ce11c7e7cf4006a9f9b7f898eb2bd2922d846b02bd35d9a9470308dce96c",
    "src/foundation/capabilities/configuration-runtime-policy/SKILL.md": "a0c6c4b122e76426256bc5deac35b741b32a406255992ac4c958ff10cfb2f9c6",
    "src/foundation/capabilities/configuration-runtime-policy/references/benchmarks-and-patterns.md": "9ef96a4caa8a66abad659cd04a1dbe7fced550efcf94907f1bd143eb2f94a53b",
    "src/foundation/capabilities/configuration-runtime-policy/references/evidence-patterns.md": "11db23aaedf78b0f5629b894c25bf3725b38559e6a216219bd63f3018aadfca4",
}

C1G_PROTECTED_HASHES = {
    "src/professional-skills/delivery-release-gate/references/checklist.md": "9f103563d839016ca66f86aef9a6679584a2dcadceea553964e01ceccb7a65ce",
    "src/professional-skills/delivery-release-gate/references/release-evidence-patterns.md": "b87635cc9fec6209239e4d0458a09acded3d97a2438fe8367dceb447b549add6",
    "src/foundation/capabilities/release-rollback/SKILL.md": "738e04c280576f5392d91f822c605e2eed1916444aef7bf99b0aae48e2f4d453",
    "src/foundation/capabilities/release-rollback/references/benchmarks-and-patterns.md": "52bbecd74a4ef1a0dc599855dbbd38d4ba08563e2a5fd60e3a27d4bd10dc74c6",
    "src/foundation/capabilities/release-rollback/references/checklist.md": "e8a45f93dcb38522492d252a295e5a6dcd61f9899bada1f5001aededf85c4096",
    "src/foundation/capabilities/release-rollback/references/evidence-patterns.md": "c0081ac454f9f9fa8a7ebd30b30a41cffdf41db26d3140f9e694672c3c109e58",
    "src/foundation/capabilities/configuration-runtime-policy/references/checklist.md": "55406df248bce907803dffd55d3473109d149526cea056a4d5f7c9113954275d",
    "src/registry/professional-skills.yaml": "32a3b49da13930f3baccf54dbd8de12064b1f07d273b2948dfaeb12586eaf49a",
    "src/registry/foundation-skills.yaml": "385843496634f9e9ef4426790cacff211858cab4f73c6c15f521fc2732b5b8fd",
}

C1G_BUILT_PROJECTION_SPECS = {
    "src/professional-skills/delivery-release-gate/SKILL.md": (
        "delivery-release-gate",
        310,
        "58d88e71ba05ce0b36336ac8ef70f3f13ded845a842ac99fcdc01a5911ae7e5c",
    ),
    "src/foundation/capabilities/release-rollback/SKILL.md": (
        None,
        229,
        "3e2150a21b3997726207b6ac9317c8077856708c87a481ac818898779c78229a",
    ),
    "src/foundation/capabilities/version-compatibility/SKILL.md": (
        None,
        250,
        "989a93e84c8ba897bdc8ba69113da520c11207996f1d64b7ad59b4810284ae91",
    ),
    "src/foundation/capabilities/configuration-runtime-policy/SKILL.md": (
        None,
        183,
        "f91cb26ad5c184d9505fec203a388ee461fda50f6a9c1684abc83bda5bfb8237",
    ),
}

C1G_RULE_OWNER_ANCHORS = {
    "src/professional-skills/delivery-release-gate/SKILL.md": (
        "Name the release decision owner.",
        "Load the named Reference for the open output.",
        "Require authority before action.",
        "Block stale artifact/environment, authority, containment, compatibility/migration, infrastructure-state, or recovery evidence.",
        "Refuse destructive, privileged, irreversible, or secret-bearing production action absent authority, sandbox/preview, recovery, and redaction.",
    ),
    "src/professional-skills/delivery-release-gate/references/delivery-output-and-gates.md": (
        "Bind artifact bytes to source/build identity; mutable labels alone cannot establish identity.",
        "Prove coexistence, ordering, reconciliation, cleanup, and rollback readability for triggered migration, contract, or version skew.",
        "Before a destructive, production, privileged, or irreversible action, require explicit user authority.",
    ),
    "src/foundation/capabilities/version-compatibility/SKILL.md": (
        "Inventory evidence-backed consumers, retained state/messages, and version skew.",
        "Load the named benchmark, checklist, or evidence Reference according to the open output.",
    ),
    "src/foundation/capabilities/version-compatibility/references/checklist.md": (
        "Route field semantics to `dto-schema-design`, consumer inventory to `consumer-impact-analysis`, executable contracts to `contract-testing`, migration execution to `data-migration-design`, and rollout/rollback to `release-rollback`.",
    ),
    "src/foundation/capabilities/version-compatibility/references/compatibility-benchmarks.md": (
        "Choose additive change, bridge/alias, expand-migrate-contract, version, adapter/upcaster, opt-in, dual publish/write, or config bridge from the failing path.",
        "Old producer → new consumer",
        "New producer → old consumer",
    ),
    "src/foundation/capabilities/version-compatibility/references/evidence-patterns.md": (
        "For telemetry, registry, flag, migration, notification, or rollback actions, record owner, scope, permission, dry-run/staging proof, stop, recovery, and redaction.",
        "Do not assume consumers upgrade together, call behavior-changing additions safe, or remove a bridge by calendar without usage, stored-data, queue, and rollback evidence.",
    ),
    "src/foundation/capabilities/configuration-runtime-policy/SKILL.md": (
        "Bind typed source, values, owner, default, precedence, apply boundary, and effective state.",
        "Load only the named output Reference.",
    ),
    "src/foundation/capabilities/configuration-runtime-policy/references/benchmarks-and-patterns.md": (
        "When current source does not match a generic precedence order, do not copy that order.",
        "Unowned strategy registry.",
    ),
    "src/foundation/capabilities/configuration-runtime-policy/references/evidence-patterns.md": (
        "For staging or production config/flag actions, record environment, data class, permission, owner, blast radius, stop, rollback/kill switch, and redaction.",
    ),
}

C1G_SELECTED_REFERENCES = [
    ("delivery-release-gate", "references/checklist.md"),
    ("delivery-release-gate", "references/delivery-output-and-gates.md"),
    ("delivery-release-gate", "references/release-evidence-patterns.md"),
    ("release-rollback", "references/benchmarks-and-patterns.md"),
    ("release-rollback", "references/checklist.md"),
    ("release-rollback", "references/evidence-patterns.md"),
    ("version-compatibility", "references/checklist.md"),
    ("version-compatibility", "references/compatibility-benchmarks.md"),
    ("version-compatibility", "references/evidence-patterns.md"),
    ("configuration-runtime-policy", "references/benchmarks-and-patterns.md"),
    ("configuration-runtime-policy", "references/checklist.md"),
    ("configuration-runtime-policy", "references/evidence-patterns.md"),
]

C1J_SOURCE_SPECS = (
    ("src/foundation/capabilities/concurrency-control/SKILL.md", "2999d19eee8d9afbbcd079fffb8dbf89f21befc1ceeb96735e57e66ce3835ae6", "f733486d49e368ddc40c284d1fe5c29e9e18b38da13cf2ca63ae98dd1f757fe3", 467, ("Select the narrowest current-store control", "Define conflict outcomes, retry and idempotence", "Prove allowed and forbidden concurrent outcomes.")),
    ("src/foundation/capabilities/concurrency-control/references/benchmarks-and-patterns.md", "8a1967636fa369772f71c321af03f568fb80d86d4efc7894af5c3f409c6b7b69", "b27c0673508eb78233bf04a175d787636256779c4490570b2ecb49c770a23300", 520, ("| Unique creation |", "| Lost update |", "| Read-modify-write |", "| Multi-resource invariant |", "| Cross-store workflow |", "| Lease ownership |", "| Queue overlap |", "| Hot aggregate |", "| Collaborative edit |", "| Cache stampede |", "| Pool or fan-out |", "The checklist owns lock order, cancellation, ABA, time and lifecycle decisions")),
    ("src/foundation/capabilities/transaction-consistency/references/benchmarks-and-patterns.md", "6a9b82e5703046828ab0b1b602c0e9032d1ee1b4aa364185d26a2c34b04bcd0c", "99a9f2e244e3083030ebd9b64a89be758208f1380787c0824236c4a83244518a", 608, ("| Remote call while locked |", "| Commit before remote |", "| Remote success before commit |", "| Cross-participant mechanism |", "| Outbox/inbox |", "| Saga/compensation |", "| Reconciliation |", "| 2PC/XA |", "The checklist owns transaction, retry, and failure-path selection.")),
    ("src/foundation/capabilities/transaction-consistency/references/evidence-patterns.md", "09c4e001ed1501058bbe77335f8cf23edcf52f28cda941d6cc72be36da9da147", "150e1fe62bd88659fe7ebc2a6bdbdbf6153894340460264c518be871736bc6c5", 548, ("| Local atomicity |", "| Lost-update control |", "| Set/range control |", "| Remote-effect ordering |", "| Outbox/inbox durability |", "| Compensation safety |", "| Reconciliation |", "| Evidence freshness |", "Record inspected and skipped writers, stores, side effects, recovery, tests, signals, and runbooks")),
    ("src/foundation/capabilities/distributed-workflow-consistency/SKILL.md", "e58c0ba89022e24f0c11e8f637e9f810e3b382035f02b09da4b027b99f7188aa", "df3a7d24a62d3aabc74405abeb7ce98376da7a049c3ec8b36c43c25694a98b2e", 569, ("Persist workflow, step, command, effect, attempt, tenant, version, and authoritative state before dispatch.", "Preserve command and effect correlation plus unknown outcomes", "Define idempotent forward, compensation, reconciliation, repair, stuck handling, audit, versioning, replay, and terminal evidence.")),
    ("src/foundation/capabilities/distributed-workflow-consistency/references/stuck-manual-repair-and-versioning.md", "59c50f408dd5d83e0d48a1657ee2ebeb4355c1ef0114bada5a393984eda283c1", "e07c57d14b47fef508030c9469abf96d163fcafb9478a3e7c93e47b1511f101a", 606, ("| Stuck detection |", "| Quarantine |", "| Repair authority |", "| Repair command |", "| Audit |", "| Definition version |", "| Evolution |", "Exercise quarantine, authorized/repeated/failed repair, and reconciliation.", "Replay representative histories under compatible and incompatible definitions.", "https://docs.temporal.io/visibility", "https://docs.aws.amazon.com/step-functions/latest/dg/redrive-executions.html")),
)

C1J_PROTECTED_HASHES = {
    "src/professional-skills/data-middleware-change-builder/SKILL.md": "51af820aededb532f57198975c6290b76e6c65b20e9c0ae2817171a9980c5db1",
    "src/professional-skills/data-middleware-change-builder/references/checklist.md": "7913ab5061bcc773b799077d47a02e5f0fee9e66dbe386c4c1bdb5c5d0b9473f",
    "src/professional-skills/data-middleware-change-builder/references/evidence-patterns.md": "c9f9f5090e759139a549b8f2d21bb47c18740d55dbea095686ea6530966b0569",
    "src/professional-skills/data-middleware-change-builder/references/recovery-patterns.md": "ccd256b2616f32f673419a7452c1b1b47ac23f85485ccfd4a52f5559d614c9aa",
    "src/foundation/capabilities/concurrency-control/references/checklist.md": "012f1c6db93c813abe0dd0eb710132d810d96dcb08fb21dd654e817a8456715d",
    "src/foundation/capabilities/concurrency-control/references/evidence-patterns.md": "ad0dadf8d15be705a17f62a2844b5295cb0047efa4b87e7851e2b785978765c6",
    "src/foundation/capabilities/transaction-consistency/SKILL.md": "076dff13a9468d13713ec106f5a96586f44635855f9600998209d197a8fb5308",
    "src/foundation/capabilities/transaction-consistency/references/checklist.md": "e588a5f3bd0ee1709ae90944bcdee804c9c243ee61f3c5b96ce1b28154802e9a",
    "src/foundation/capabilities/distributed-workflow-consistency/references/identity-state-and-unknown-outcomes.md": "7a0e547eee5e8b179d2d173058dc46bea0be9191858b6b810e475bbc3d7322d6",
    "src/foundation/capabilities/distributed-workflow-consistency/references/compensation-convergence-and-reconciliation.md": "4b8f50abb517dad40a6092b351e245b0db9ae9f0511189c8c7a625a4c1dcd104",
    "src/registry/professional-skills.yaml": "32a3b49da13930f3baccf54dbd8de12064b1f07d273b2948dfaeb12586eaf49a",
    "src/registry/foundation-skills.yaml": "385843496634f9e9ef4426790cacff211858cab4f73c6c15f521fc2732b5b8fd",
    "src/registry/domain-skills.yaml": "2d53ccc4206c94d9850e007d21603f04ba1f06f7721de5da1cd47dcfe6e16129",
    "scripts/build.py": "2543ed2c2cb7498babeae20d1f7bd244f968522f116c90b8b08c4106a25efcf1",
    "scripts/validation_utils.py": "a76092b2d24cdfaec66eb44e1f8d4e48a9f76d9dda8a875a3b5602771649f995",
    "dist/universal/skills/dev/data-middleware-change-builder/SKILL.md": "22a41125147da43b01da304168205b8840d7ec6649a16c7727bd7719943696f3",
}

C1J_BUILT_PROJECTION_SPECS = {
    "src/foundation/capabilities/concurrency-control/SKILL.md": (214, "3472b6ca5145616987527880780a6debd998414b3554cf85a6c43c1431ae3e5d"),
    "src/foundation/capabilities/transaction-consistency/SKILL.md": (283, "e8c916c5260c27787c8ac9da1ce9b0f4eebe2972360ea6779f050721a2bd5c75"),
    "src/foundation/capabilities/distributed-workflow-consistency/SKILL.md": (246, "c8d8f21a9a60dfe588db5a8157791781715b8293758a6d730ee38ad1dc3f65c6"),
}

C1J_REFERENCE_TOKENS = {
    ("data-middleware-change-builder", "references/checklist.md"): 359,
    ("data-middleware-change-builder", "references/evidence-patterns.md"): 374,
    ("data-middleware-change-builder", "references/recovery-patterns.md"): 291,
    ("transaction-consistency", "references/benchmarks-and-patterns.md"): 608,
    ("transaction-consistency", "references/checklist.md"): 451,
    ("transaction-consistency", "references/evidence-patterns.md"): 548,
    ("concurrency-control", "references/benchmarks-and-patterns.md"): 520,
    ("concurrency-control", "references/checklist.md"): 544,
    ("concurrency-control", "references/evidence-patterns.md"): 317,
    ("distributed-workflow-consistency", "references/identity-state-and-unknown-outcomes.md"): 592,
    ("distributed-workflow-consistency", "references/compensation-convergence-and-reconciliation.md"): 607,
    ("distributed-workflow-consistency", "references/stuck-manual-repair-and-versioning.md"): 606,
}
C1J_SELECTED_REFERENCES = list(C1J_REFERENCE_TOKENS)

C1I_FINAL_SOURCE_HASHES = {
    "src/professional-skills/quality-test-gate/SKILL.md": "1e694bd93dddec4dd1f6a57ee5400257bd6fe8b82da76485b5898ebf627018cb",
    "src/professional-skills/quality-test-gate/references/test-output-and-gates.md": "c1bf533e04443976a6bbe8ee77121a9117e88ffb868c39402311e9aa016c3409",
    "src/foundation/capabilities/test-data-management/SKILL.md": "0fc3f54334d7981b86d6a417953744869448765b02a63c0176048667c07b73dc",
    "src/foundation/capabilities/test-data-management/references/benchmarks-and-patterns.md": "146f17f6b108c73f2452bb363678dbe9a15f3fb87d5f961bc41edf64ee6b89b9",
    "src/foundation/capabilities/test-data-management/references/evidence-patterns.md": "b482b7c27c1528195b61077bad9c401cf08c62b3435e9072152b608b1a83b623",
    "src/foundation/capabilities/test-strategy/SKILL.md": "b8eb1d95138e72aaeecb2c5d5e389a6e6c7c1d5537a063581f01d504fddc01a4",
    "src/foundation/capabilities/test-strategy/references/benchmarks-and-patterns.md": "b47521c4c96bc46257707e7d56bce7140fddd44fc5f35762063dfed13eb6b7c2",
    "src/foundation/capabilities/test-strategy/references/evidence-patterns.md": "4dd4cf01fe1ee9e2f4a8d2d5a487799a7cbc72edd4867cb105b40f4d6d0f703a",
}

C1I_PRE_SOURCE_HASHES = {
    "src/professional-skills/quality-test-gate/SKILL.md": "32acb7696f42ff468bf9eeb522361e0b28f1e3c5f7c8c385f6ff554ad0858132",
    "src/professional-skills/quality-test-gate/references/test-output-and-gates.md": "81021b4ddd922976f5cf55a6d0b264826afb6b81b4389b8eb381260eb1631864",
    "src/foundation/capabilities/test-data-management/SKILL.md": "47b68ef1465bb408bd7b9b278e41d58c52c0b0c414031075d99cbe2b48fc7b21",
    "src/foundation/capabilities/test-data-management/references/benchmarks-and-patterns.md": "2d1af98bd0f20c72f798d2b0c56a2c6e36ac1a1fab6bdaa47c2ab4c3f36cda34",
    "src/foundation/capabilities/test-data-management/references/evidence-patterns.md": "26bfaa6df30942dbbbd6a146c4b90ee36eba901cfc3986b5bf6b808845606ea6",
    "src/foundation/capabilities/test-strategy/SKILL.md": "ba6fdb828fd4c04a87263b488bdcbbd521a29ab0048895774cb5b6200a6727e8",
    "src/foundation/capabilities/test-strategy/references/benchmarks-and-patterns.md": "ae78d671969677914a204b1fb491079b1a238bf3475aea2e81ac23ad33fa0393",
    "src/foundation/capabilities/test-strategy/references/evidence-patterns.md": "a6daddb7c8eedd07dfd25411bff3db2590e72d1907809c183ac8330c80303d96",
}

C1I_SOURCE_TOKENS = {
    "src/professional-skills/quality-test-gate/SKILL.md": 740,
    "src/professional-skills/quality-test-gate/references/test-output-and-gates.md": 565,
    "src/foundation/capabilities/test-data-management/SKILL.md": 508,
    "src/foundation/capabilities/test-data-management/references/benchmarks-and-patterns.md": 539,
    "src/foundation/capabilities/test-data-management/references/evidence-patterns.md": 476,
    "src/foundation/capabilities/test-strategy/SKILL.md": 494,
    "src/foundation/capabilities/test-strategy/references/benchmarks-and-patterns.md": 529,
    "src/foundation/capabilities/test-strategy/references/evidence-patterns.md": 537,
}

C1I_PROTECTED_HASHES = {
    "src/professional-skills/quality-test-gate/references/checklist.md": "c208301c6abaa0f47cb90826ae23420b9bef3c57facdeec932b9bc036eb7b19e",
    "src/professional-skills/quality-test-gate/references/test-structure-boundaries.md": "86038eeaa916ead150b505246f0308619f21a85e191cf1b772dcb2859a567d95",
    "src/foundation/capabilities/targeted-validation-selection/SKILL.md": "db53a393fa8ca8fa452bc942a594fa242bfbcd457834a9c9f0f87267d0ac490b",
    "src/foundation/capabilities/targeted-validation-selection/references/repository-command-entry-evidence.md": "86d1260cacf6bfa207a326e118239cf1f78363faf06f7c8e48a7631ca0d964e1",
    "src/foundation/capabilities/test-data-management/references/checklist.md": "e23b833747c26a46ae1935a6ec48a6ff78efc5d7e28eb7315c4f7e73e1b76771",
    "src/foundation/capabilities/test-strategy/references/checklist.md": "04883de9a1f8b1c3509a67a32c3720dcc88fafe10b525f74d0a03c96e07cf6f9",
    "src/professional-skills/ai-code-review-refactor/SKILL.md": "cf548e3bc362edc9f5d5f8f488c88d2ae37e522dbf1f0ef9695a5d6601ddd213",
    "src/foundation/capabilities/refactoring/references/split-merge-cleanup-patterns.md": "96b49d2084c6c8834a044ce4700ea6135db4fede99f70a9a6a559c8dba10b2db",
    "src/registry/professional-skills.yaml": "32a3b49da13930f3baccf54dbd8de12064b1f07d273b2948dfaeb12586eaf49a",
    "src/registry/foundation-skills.yaml": "385843496634f9e9ef4426790cacff211858cab4f73c6c15f521fc2732b5b8fd",
    "scripts/build.py": "2543ed2c2cb7498babeae20d1f7bd244f968522f116c90b8b08c4106a25efcf1",
    "tests/scripts/test_build_safety.py": "8a360b4ee64710130beb8ee3cb456cb54437a518fd0f07d7d58b496f0e7c50cd",
    "tests/test_hookless_build_install.py": "612e97a13a1601b48f3f3a5163d3f57e933e24e025183759dc3230b816f1bd23",
}

C1I_BUILT_PROJECTION_SPECS = {
    "src/professional-skills/quality-test-gate/SKILL.md": (
        "quality-test-gate",
        309,
        "a1b284bddfd1cdf9fed94e175d603e2db962ab597ba443ab58d3e1a8c3d543b6",
    ),
    "src/foundation/capabilities/test-data-management/SKILL.md": (
        None,
        257,
        "535ce74d430ee2cf20f237d416d8f0ec8b8f2c498cc7b262d2ab16624af16e65",
    ),
    "src/foundation/capabilities/test-strategy/SKILL.md": (
        None,
        232,
        "eb3ff8d61501d0a450aa9f72d60f5f96248791b06fb3b0cae7a57792d6780750",
    ),
}
C1I_RULE_OWNER_ANCHORS = {
    "src/professional-skills/quality-test-gate/SKILL.md": (
        "Map acceptance and failure paths to proving signals.",
        "**Analysis mode (`analysis-agent`):** Select the proof strategy.",
        "**Task mode (`task-agent`):** Implement the smallest proving test.",
        "**Review mode (`review-agent`):** Judge coverage and freshness.",
        "Map each acceptance and material failure to one signal.",
        "Select the lowest level exercising the real boundary.",
        "Record stale, flaky, skipped, or partial evidence as limited.",
        "Stop before production mutation or authority overrun.",
        "Escalate unowned flaky, skipped, or partial evidence.",
        "Flag uncovered changed files or acceptance.",
    ),
    "src/professional-skills/quality-test-gate/references/test-output-and-gates.md": (
        "| Authorization/tenancy |",
        "| Money/irreversible state |",
        "| Schema/migration |",
        "| Public API/event |",
        "| External integration |",
        "| Concurrent/distributed state |",
        "| Frontend/accessibility |",
        "| Release/configuration |",
        "| Performance/scale |",
        "Core Guard G decides refresh; Task runs only accepted commands afterward.",
        "Review reports stale or missing evidence without setting timing.",
        "Show a regression assertion fails when the repaired branch is removed, inverted, or bypassed.",
        "Use real infrastructure or contract-calibrated doubles when its behavior is the risk.",
        "Control or isolate time, randomness, IDs, data, concurrency, network behavior, and shared state.",
        "Keep release readiness unverified without built-artifact and rollback evidence.",
    ),
    "src/foundation/capabilities/test-data-management/SKILL.md": (
        "Build the smallest fixture for the named failure mechanism and oracle.",
        "Define controls for oracle-affecting time, randomness, IDs, order, locale, and external responses.",
        "Define namespace and cleanup ownership across commit, asynchronous, and parallel effects.",
        "Select synthetic or approved minimized data that excludes production secrets and personal records.",
        "Bind schema, fixture, dependency, and environment versions; refresh after oracle-affecting changes.",
    ),
    "src/foundation/capabilities/test-data-management/references/benchmarks-and-patterns.md": (
        "| Factory/default/trait |",
        "| Shared seed |",
        "| Golden/snapshot |",
        "| Load/parallel set |",
        "| External sandbox record |",
        "Inventory created rows, documents, keys, queue/DLQ items, files, notifications, sessions, and external records;",
        "Use synthetic reserved-domain identities and provider-approved values.",
        "Label inert secret/cookie fixtures and preserve tested parsing, expiry, signature, `SameSite`, domain, or path semantics.",
        "Keep usable credentials and production samples out.",
        "bind schema version, regeneration command, semantic diff, freshness, and redaction.",
    ),
    "src/foundation/capabilities/test-data-management/references/evidence-patterns.md": (
        "| Owned fixture |",
        "| Isolated effects |",
        "| Privacy-safe data |",
        "| Determinism |",
        "| Parallel/volume partition |",
        "| Fresh evidence |",
        "Protected exports/scans need approved source, minimization/redaction, retention/deletion, and cross-namespace proof.",
    ),
    "src/foundation/capabilities/test-strategy/SKILL.md": (
        "Map each risk to its mechanism, consequence, surface, oracle, and cheapest exercising level.",
        "Define mechanism-sensitive assertions and signals without taking entrypoint, coverage, or fallback ownership from `targeted-validation-selection`.",
        "Route release evidence to",
        "Route release evidence to `delivery-release-gate`.",
        "Stop on unresolved acceptance, consequence, surface, environment/fixture, oracle, or high-risk evidence owner.",
    ),
    "src/foundation/capabilities/test-strategy/references/benchmarks-and-patterns.md": (
        "| Calculation, validation, mapping, state |",
        "| Orchestration with ports/adapters |",
        "| API/event/SDK/export |",
        "| Migration/backfill/destruction |",
        "| Frontend behavior |",
        "| Provider/queue/file/email |",
        "| Security/payment/tenant/export |",
        "| Performance/concurrency/SLO |",
        "Name the mechanism and make the assertion fail for its relevant removal/inversion/omission/order/error-swallow mutation;",
    ),
    "src/foundation/capabilities/test-strategy/references/evidence-patterns.md": (
        "| Behavior covered |",
        "| Failure covered |",
        "| Compatibility covered |",
        "| Migration integrity covered |",
        "| Affected scope bounded |",
        "| Evidence fresh |",
        "| Omitted level owned |",
        "External, deploy, migration, restore, or rollback commands need authority, bounded effects, sandbox/dry-run where available, recovery, redaction, and stop.",
    ),
}

C1I_SELECTED_REFERENCES = [
    ("quality-test-gate", "references/checklist.md"),
    ("quality-test-gate", "references/test-output-and-gates.md"),
    ("quality-test-gate", "references/test-structure-boundaries.md"),
    ("targeted-validation-selection", "references/repository-command-entry-evidence.md"),
    ("test-data-management", "references/benchmarks-and-patterns.md"),
    ("test-data-management", "references/checklist.md"),
    ("test-data-management", "references/evidence-patterns.md"),
    ("test-strategy", "references/benchmarks-and-patterns.md"),
    ("test-strategy", "references/checklist.md"),
    ("test-strategy", "references/evidence-patterns.md"),
]


REVIEW_JIT_OWNER_SPECS = {
    "architecture-impact-reviewer": {
        "root": "src/professional-skills/architecture-impact-reviewer/SKILL.md",
        "registry": "professional",
        "cap": 415,
        "removed": ("references/architecture-output-and-gates.md",),
        "references": {
            "references/placement-and-ownership.md": ("targeted", ("analysis-agent", "review-agent"), ("boundary-decision", "selected-approach", "residual-risk"), "route-or-material-unknown", ("acceptance", "scope", "material-risk-floor"), 650),
            "references/consumer-and-data-impact.md": ("targeted", ("analysis-agent", "review-agent"), ("boundary-decision", "validation-plan", "residual-risk"), "route-or-material-unknown", ("acceptance", "scope", "material-risk-floor"), 650),
            "references/dependency-topology-and-enforcement.md": ("targeted", ("analysis-agent", "review-agent"), ("boundary-decision", "gate-decision", "validation-plan", "residual-risk"), "route-or-material-unknown", ("acceptance", "scope", "material-risk-floor"), 650),
            "references/reversibility-evolution-and-proof-limits.md": ("targeted", ("analysis-agent", "review-agent"), ("decision-record", "validation-plan", "proof-limit", "residual-risk"), "route-or-material-unknown", ("acceptance", "scope", "material-risk-floor"), 650),
            "references/checklist.md": ("decision-checklist", ("analysis-agent", "review-agent"), ("checklist-result", "residual-risk"), "route-or-material-unknown", ("acceptance", "scope", "material-risk-floor"), 650),
            "references/solution-optimality.md": ("targeted", ("analysis-agent", "review-agent"), ("selected-approach", "residual-risk"), "route-or-material-unknown", ("acceptance", "scope", "material-risk-floor"), 650),
        },
    },
    "module-boundary-design": {
        "root": "src/foundation/capabilities/module-boundary-design/SKILL.md",
        "registry": "foundation",
        "cap": 290,
        "removed": ("references/module-decomposition.md",),
        "references": {
            "references/boundary-kind-and-authority.md": ("targeted", ("analysis-agent", "review-agent"), ("boundary-decision", "decision-record", "residual-risk"), "route-or-material-unknown", ("acceptance", "scope", "material-risk-floor"), 600),
            "references/split-merge-and-move-decisions.md": ("targeted", ("analysis-agent", "review-agent"), ("boundary-decision", "selected-approach", "residual-risk"), "route-or-material-unknown", ("acceptance", "scope", "material-risk-floor"), 600),
            "references/benchmarks-and-enforcement.md": ("benchmark-pattern", ("analysis-agent", "review-agent"), ("option-comparison", "selected-approach"), "route-or-material-unknown", ("acceptance", "scope", "material-risk-floor"), None),
        },
    },
    "implementation-structure-design": {
        "root": "src/foundation/capabilities/implementation-structure-design/SKILL.md",
        "registry": "foundation",
        "cap": None,
        "removed": (),
        "references": {
            "references/object-module-decomposition.md": ("targeted", ("task-agent", "review-agent", "analysis-agent"), ("decision-record", "validation-plan", "proof-limit", "residual-risk"), "route-or-material-unknown", ("acceptance", "scope", "material-risk-floor"), None),
            "references/reuse-and-placement.md": ("targeted", ("task-agent", "review-agent", "analysis-agent"), ("selected-approach", "validation-plan", "proof-limit", "residual-risk"), "route-or-material-unknown", ("acceptance", "scope", "material-risk-floor"), None),
            "references/evidence-patterns.md": ("evidence-pattern", ("task-agent", "review-agent", "analysis-agent"), ("evidence-record", "validation-plan", "proof-limit", "residual-risk"), "repo-resolvable-fact", (), None),
        },
    },
    "technology-stack-selection": {
        "root": "src/foundation/capabilities/technology-stack-selection/SKILL.md",
        "registry": "foundation",
        "cap": 270,
        "removed": (),
        "references": {
            "references/benchmarks-and-patterns.md": ("benchmark-pattern", ALL_ROLES, ("option-comparison", "selected-approach"), "route-or-material-unknown", ("acceptance", "scope", "material-risk-floor"), 800),
        },
    },
}

REVIEW_JIT_IMMUTABLE_HASHES = {
    "src/professional-skills/architecture-impact-reviewer/references/checklist.md": "e88eda288d2e2e300babdc5be2c34032c747ca12615e63ea9bdfc1c5bdcd978b",
    "src/professional-skills/architecture-impact-reviewer/references/solution-optimality.md": "4fd71ca732ea3b54cf9fa0cb23c99abf9c6fe0e0a832f8a6d4689da3c22ce3fb",
    "src/foundation/capabilities/module-boundary-design/references/benchmarks-and-enforcement.md": "9c3d70a0f9318a339cf53692a6e9945d291a3bf71405ecdb1fc13be1da6065ca",
    "src/foundation/capabilities/implementation-structure-design/SKILL.md": "e17bfe7ccc8240fa4ffc805590b82716741fd661a7bbb8cf5ce3ecbc92fe210d",
    "src/foundation/capabilities/implementation-structure-design/references/evidence-patterns.md": "216cb05b63a44da250ce9fdd5c0a94f1d193d1441158bb534cb318d9d40d4adf",
    "src/foundation/capabilities/implementation-structure-design/references/object-module-decomposition.md": "a75359f90ae8e7ae4324ae3ad62ca1f04f1c2c79f94c3e2cccbe383e25dc92f5",
    "src/foundation/capabilities/implementation-structure-design/references/reuse-and-placement.md": "a4e44d8b22c5511b5f016297c6101fdd00295f3701d0b18e7c3beab3cde7d530",
}

REVIEW_JIT_FRAGMENT_DESTINATIONS = {
    "Only when structure or responsibility moves, state the owning module/service and public/private surface.": "src/professional-skills/architecture-impact-reviewer/references/placement-and-ownership.md",
    "Only when public or indirect consumers or authoritative data ownership can change, state known/unknown consumers.": "src/professional-skills/architecture-impact-reviewer/references/consumer-and-data-impact.md",
    "When dependency direction changes, state the effective source edge and evidence against the repository's ownership or model.": "src/professional-skills/architecture-impact-reviewer/references/dependency-topology-and-enforcement.md",
    "state the deletion or reversal boundary, coexistence, rollback or forward-migration outcome, accepted tradeoff, and revisit trigger supported by current policy and impact evidence.": "src/professional-skills/architecture-impact-reviewer/references/reversibility-evolution-and-proof-limits.md",
    "A directory name, proximity, team name, or framework layer is insufficient evidence of the semantic owner.": "src/foundation/capabilities/module-boundary-design/references/boundary-kind-and-authority.md",
    "Select keep, split, move, or merge and name the responsibility and authority preserved by that outcome.": "src/foundation/capabilities/module-boundary-design/references/split-merge-and-move-decisions.md",
    "Screen candidates against hard product, data, protocol, identity, compliance, deployment, offline, integration, and recovery constraints before comparing preferences.": "src/foundation/capabilities/technology-stack-selection/references/benchmarks-and-patterns.md",
    "Treat an approved existing stack as a candidate with known integration and operating evidence, not as an automatic winner; a new stack states the concrete gap it closes.": "src/foundation/capabilities/technology-stack-selection/references/benchmarks-and-patterns.md",
    "Before commitment, name owners for the deployment, on-call diagnosis, upgrade, security-response, recovery, capacity, and retirement duties that the selected stack actually creates.": "src/foundation/capabilities/technology-stack-selection/references/benchmarks-and-patterns.md",
    "Inspect stack-level support, end-of-life, continuity, and supply-chain exposure using dated findings from the named package-mechanics and package-risk owners.": "src/foundation/capabilities/technology-stack-selection/references/benchmarks-and-patterns.md",
    "Compare total-change cost across the accepted decision horizon using dated assumptions, ranges, and sensitivity for implementation, migration, coexistence, operation, incidents, upgrades, and exit.": "src/foundation/capabilities/technology-stack-selection/references/benchmarks-and-patterns.md",
    "Define migration and coexistence across data, protocols, generated artifacts, package managers, build/deploy lanes, observability, rollback, and old/new consumer compatibility.": "src/foundation/capabilities/technology-stack-selection/references/benchmarks-and-patterns.md",
    "Classify reversibility from the actual exit unit and information movement; prototypes and public benchmarks establish scoped feasibility rather than production readiness.": "src/foundation/capabilities/technology-stack-selection/references/benchmarks-and-patterns.md",
}


def _fingerprint(text: str) -> str:
    normalized = " ".join(text.split()).casefold()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _g2_owner_root(owner: str) -> Path:
    candidates = (
        ROOT / "src/professional-skills" / owner / "SKILL.md",
        ROOT / "src/foundation/capabilities" / owner / "SKILL.md",
        ROOT / "src/domain-extensions" / owner / "SKILL.md",
    )
    matches = [path for path in candidates if path.is_file()]
    if len(matches) != 1:
        raise AssertionError(f"expected one root for {owner}, got {len(matches)}")
    return matches[0]


def _g2_task_review_active_references(owner: str) -> set[str]:
    root = _g2_owner_root(owner)
    references: set[str] = set()
    for line in root.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|") or "(references/" not in line:
            continue
        cells = [cell.strip() for cell in line.split("|")]
        if len(cells) < 7:
            continue
        required_by = {
            role.strip("` ")
            for role in cells[5].split(",")
            if role.strip()
        }
        if not required_by & {"task-agent", "review-agent"}:
            continue
        marker = "(references/"
        relative = "references/" + line.split(marker, 1)[1].split(")", 1)[0]
        logical_id = f"{owner}/{relative}"
        if logical_id.endswith("/index.md"):
            continue
        if logical_id not in G2_BASE_SAFE_REFERENCES:
            references.add(logical_id)
    return references


# ERPAR-05C2B's task-local visible relocation ledger.  Every entry retains the
# pre-edit contiguous source phrase and the complete disposition fields needed
# to review a lossless move.  Registry validators remain the authority for the
# unchanged Reference contract; this test binds each ledger entry to the same
# required roles and outputs exposed by its source root.
MOVES = (
    ("quality-test-gate", "Add broader validation only for a concrete shared boundary or escape risk.", "src/professional-skills/quality-test-gate/references/test-output-and-gates.md"),
    ("quality-test-gate", "Mock-heavy tests can prove the mock instead of the real boundary.", "src/professional-skills/quality-test-gate/references/test-structure-boundaries.md"),
    ("quality-test-gate", "Map each acceptance criterion and material failure path to one proving signal.", "src/professional-skills/quality-test-gate/references/checklist.md"),
    ("repository-tooling-change-builder", "Bind generated output to authoritative inputs, generator version, destination, drift check, sole editable source, and a non-circular clean-checkout bootstrap.", "src/professional-skills/repository-tooling-change-builder/references/generator-and-plugin-contracts.md"),
    ("repository-tooling-change-builder", "Prove harness oracle and regression mechanism with positive and negative controls.", "src/professional-skills/repository-tooling-change-builder/references/harness-validity-contracts.md"),
    ("repository-tooling-change-builder", "Preserve internal CLI argv, environment, working directory, stdio, exit, cancellation, rerun, and cleanup.", "src/professional-skills/repository-tooling-change-builder/references/repository-automation-contracts.md"),
    ("ai-code-review-refactor", "A summary is not the diff.", "src/professional-skills/ai-code-review-refactor/references/ai-review-pattern-catalog.md"),
    ("ai-code-review-refactor", "Verify reachable failure mechanisms.", "src/professional-skills/ai-code-review-refactor/references/checklist.md"),
    ("backend-change-builder", "When the change affects untrusted input, identity, resource scope, or tenant scope, preserve validation and server-side authorization before disclosure or mutation.", "src/professional-skills/backend-change-builder/references/proactive-triggers.md"),
    ("backend-change-builder", "Trace each affected invariant through authorization, mutation, side effects, and failure outcomes.", "src/professional-skills/backend-change-builder/references/checklist.md"),
    ("backend-change-builder", "Stop repair work without an accepted finding or verified failure mechanism.", "src/professional-skills/backend-change-builder/references/professional-modes.md"),
    ("iot-embedded-extension", "Make updates recoverable", "src/domain-extensions/iot-embedded-extension/references/checklist.md"),
    ("cross-platform-client-extension", "Prove targets from repository, build targets, release configuration, or published artifacts without framework inference.", "src/domain-extensions/cross-platform-client-extension/references/framework-target-evidence-contracts.md"),
    ("cross-platform-client-extension", "Assign shared, adapter, plugin, and native owners", "src/domain-extensions/cross-platform-client-extension/references/shared-and-target-ownership-contracts.md"),
    ("cross-platform-client-extension", "Version bridge, FFI, plugin, and generated interfaces", "src/domain-extensions/cross-platform-client-extension/references/bridge-plugin-and-ffi-contracts.md"),
    ("cross-platform-client-extension", "Define behavior parity separately from UI parity.", "src/domain-extensions/cross-platform-client-extension/references/parity-and-regression-contracts.md"),
    ("package-dependency-management", "Justify capability before package choice.", "src/foundation/capabilities/package-dependency-management/references/checklist.md"),
    ("package-dependency-management", "Follow the repository's package authority.", "src/foundation/capabilities/package-dependency-management/references/ecosystem-command-map.md"),
    ("package-dependency-management", "Treat lifecycle code as executable supply chain.", "src/foundation/capabilities/package-dependency-management/references/evidence-patterns.md"),
    ("bigdata-product-extension", "Prove consumer compatibility", "src/domain-extensions/bigdata-product-extension/references/consumer-and-schema-contracts.md"),
    ("targeted-validation-selection", "Inspect repository guidance and command definitions for test/build/schema/lint/static/generator entrypoints.", "src/foundation/capabilities/targeted-validation-selection/references/repository-command-entry-evidence.md"),
    ("test-strategy", "Test-level escalation excludes risk-label-only layering.", "src/foundation/capabilities/test-strategy/references/benchmarks-and-patterns.md"),
    ("test-strategy", "Model negative and nondeterministic outcomes.", "src/foundation/capabilities/test-strategy/references/checklist.md"),
    ("test-strategy", "Flag stale or partial results, flaky retries, and skipped tests", "src/foundation/capabilities/test-strategy/references/evidence-patterns.md"),
    ("implementation-structure-design", "Place code with the owner of its change reason", "src/foundation/capabilities/implementation-structure-design/references/object-module-decomposition.md"),
    ("implementation-structure-design", "Reuse only when semantics, authority, failure, lifecycle, and evolution match", "src/foundation/capabilities/implementation-structure-design/references/reuse-and-placement.md"),
    ("implementation-structure-design", "Trace generated placement as", "src/foundation/capabilities/implementation-structure-design/references/evidence-patterns.md"),
    ("minimal-correct-implementation", "Compare delete or omit, existing repository behavior, standard or native behavior, installed dependencies, direct local code, and new structure", "src/foundation/capabilities/minimal-correct-implementation/references/simplicity-ladder.md"),
    ("filesystem-process-safety", "Define exclusive temporary creation in the destination directory", "src/foundation/capabilities/filesystem-process-safety/references/atomic-filesystem-commit-and-containment.md"),
    ("filesystem-process-safety", "Execute a selected program directly with structured argv.", "src/foundation/capabilities/filesystem-process-safety/references/child-process-invocation-and-completion.md"),
    ("domain-object-identification", "Classify each candidate as entity, value object, aggregate root, child entity, resource, policy, boundary model, or read model", "src/foundation/capabilities/domain-object-identification/references/benchmarks-and-patterns.md"),
    ("domain-object-identification", "Record relationships, cardinality, optionality", "src/foundation/capabilities/domain-object-identification/references/checklist.md"),
    ("domain-object-identification", "Confirm business owner, data owner, source of truth, tenant scope, mutation authority, and writer entry points from current evidence.", "src/foundation/capabilities/domain-object-identification/references/evidence-patterns.md"),
    ("refactoring", "Inventory observable behavior before movement.", "src/foundation/capabilities/refactoring/references/behavior-preservation-evidence.md"),
    ("refactoring", "Choose reviewable reversible steps.", "src/foundation/capabilities/refactoring/references/checklist.md"),
    ("refactoring", "Honor accepted deletion readiness.", "src/foundation/capabilities/refactoring/references/split-merge-cleanup-patterns.md"),
    ("client-application-testing", "Derive the matrix from the changed client risk.", "src/foundation/capabilities/client-application-testing/references/client-test-matrix.md"),
    ("failure-contract-design", "Define a machine-distinguishable failure contract at each changed material boundary", "src/foundation/capabilities/failure-contract-design/references/benchmarks-and-patterns.md"),
    ("failure-contract-design", "Represent partial and degraded outcomes explicitly", "src/foundation/capabilities/failure-contract-design/references/checklist.md"),
    ("failure-contract-design", "Treat repository inspection, generated contracts, and prior task evidence as leads", "src/foundation/capabilities/failure-contract-design/references/evidence-patterns.md"),
    ("design-pattern-selection", "A familiar repository pattern is copied without proving the same force, lifetime, and failure boundary.", "src/foundation/capabilities/design-pattern-selection/references/pattern-evidence-record.md"),
)

SECURITY_FRONTIER_MOVES = (
    (
        "security-privacy-gate",
        "Trace attacker-controlled data and authority from entry point to asset, sink, and disclosure path.",
        "src/professional-skills/security-privacy-gate/references/security-output-and-gates.md",
    ),
    (
        "security-privacy-gate",
        "Choose authorization, validation, containment, and lifecycle controls from the reachable abuse path.",
        "src/professional-skills/security-privacy-gate/references/security-output-and-gates.md",
    ),
    (
        "security-privacy-gate",
        "Verify denied cases, tenant isolation, secret handling, and residual exposure where triggered.",
        "src/professional-skills/security-privacy-gate/references/security-output-and-gates.md",
    ),
    (
        "privacy-data-lifecycle",
        "Classify data by meaning and flow. Name direct, derived, inferred, linked, and sensitive elements with subjects, producers, consumers, stores, regions, and accountable owners.",
        "src/foundation/capabilities/privacy-data-lifecycle/references/data-lifecycle-controls.md",
    ),
    (
        "privacy-data-lifecycle",
        "Bind processing to an accepted purpose. Reject collection, derivation, sharing, or retention that lacks a necessary product or operational outcome and authorized policy source.",
        "src/foundation/capabilities/privacy-data-lifecycle/references/data-lifecycle-controls.md",
    ),
    (
        "privacy-data-lifecycle",
        "Reject unnecessary representation. Bound fields, precision, granularity, frequency, population, access, and lifetime across primary data, telemetry, exports, and support artifacts.",
        "src/foundation/capabilities/privacy-data-lifecycle/references/data-lifecycle-controls.md",
    ),
    (
        "privacy-data-lifecycle",
        "Apply lifecycle policy to every reachable copy. Cover caches, indexes, logs, queues, analytics, replicas, archives, and backups with deletion propagation and non-resurrection behavior.",
        "src/foundation/capabilities/privacy-data-lifecycle/references/data-lifecycle-controls.md",
    ),
    (
        "privacy-data-lifecycle",
        "Make export, correction, and deletion observable. Define identity binding, scope, asynchronous progress, partial failure, completion evidence, and unavailable-copy disclosure.",
        "src/foundation/capabilities/privacy-data-lifecycle/references/data-lifecycle-controls.md",
    ),
    (
        "privacy-data-lifecycle",
        "Constrain third-party and regional handling. Record provider purpose, data classes, location, onward sharing, retention, deletion, incident, and exit obligations before transfer.",
        "src/foundation/capabilities/privacy-data-lifecycle/references/de-identification-and-provider-controls.md",
    ),
    (
        "privacy-data-lifecycle",
        "Treat telemetry as data processing. Remove unnecessary identifiers and payloads before collection instead of relying on sampling, access restriction, or later redaction.",
        "src/foundation/capabilities/privacy-data-lifecycle/references/data-lifecycle-controls.md",
    ),
    (
        "privacy-data-lifecycle",
        "Evaluate de-identification against linkage. Name direct and quasi-identifiers, recipient knowledge, release model, utility tradeoff, and re-identification testing before reducing controls.",
        "src/foundation/capabilities/privacy-data-lifecycle/references/de-identification-and-provider-controls.md",
    ),
    (
        "threat-modeling",
        "Bound the changed security graph. Name the protected asset or authority, changed entry point, trust transition, data or control flow, and downstream effect. Out-of-scope or unknown edges introduced or altered by the task remain explicit.",
        "src/foundation/capabilities/threat-modeling/references/benchmarks-and-patterns.md",
    ),
    (
        "threat-modeling",
        "Model capability and preconditions, not actor labels alone. Include only behaviors with graph-backed access, knowledge, timing, and control prerequisites.",
        "src/foundation/capabilities/threat-modeling/references/benchmarks-and-patterns.md",
    ),
    (
        "threat-modeling",
        "Trace a reachable abuse path. Follow source, attacker-controlled or stale values, transformations, policy or parser decisions, storage or transport, sink, and resulting effect; distinguish evidenced edges from assumptions and unreachable branches.",
        "src/foundation/capabilities/threat-modeling/references/benchmarks-and-patterns.md",
    ),
    (
        "threat-modeling",
        "Define the protected outcome before severity. State the confidentiality, integrity, availability, safety, financial, privacy, tenant, or authority invariant at risk. Current exposure and consequences determine likelihood, impact, and blast radius rather than a threat label.",
        "src/foundation/capabilities/threat-modeling/references/benchmarks-and-patterns.md",
    ),
    (
        "threat-modeling",
        "Select and place controls from the path. Compare candidate controls by protected outcome, intercepted edge, authority and owner, failure behavior, compatibility, and bypass surface. A mechanism remains undecided until the reachable path is known.",
        "src/foundation/capabilities/threat-modeling/references/benchmarks-and-patterns.md",
    ),
    (
        "threat-modeling",
        "Map the threat to fresh verification and detection. Connect the changed path and control to an abuse test, source/policy proof, monitoring, and final-edit freshness. The evidence limit remains explicit; scanner output alone cannot close business abuse.",
        "src/foundation/capabilities/threat-modeling/references/evidence-patterns.md",
    ),
    (
        "threat-modeling",
        "Own residual risk and reopening. Record the unclosed path or consequence, compensating or containment evidence, accountable owner, release consequence, and the scope, incident, exposure, data, actor, or control change that requires review.",
        "src/foundation/capabilities/threat-modeling/references/evidence-patterns.md",
    ),
    (
        "web-security",
        "Trace changed routes from source to sink. Identify attacker-controlled values, browser or server transformations, framework defaults, trust transitions, reachable sinks, and alternate encoded or nested paths before selecting a control.",
        "src/foundation/capabilities/web-security/references/benchmarks-and-patterns.md",
    ),
    (
        "web-security",
        "Match rendering protection to context. Preserve contextual escaping, sanitization, trusted-template boundaries, URL and style handling, and script or markup policy for the actual sink; avoid decoding or concatenation after validation.",
        "src/foundation/capabilities/web-security/references/benchmarks-and-patterns.md",
    ),
    (
        "web-security",
        "Protect state-changing requests at the authority boundary. Combine authenticated context with current request-integrity, origin, cookie, method, and object-authorization controls without treating browser UI or route guards as enforcement.",
        "src/foundation/capabilities/web-security/references/benchmarks-and-patterns.md",
    ),
    (
        "web-security",
        "Constrain server-side fetching and navigation. Validate destinations against owned policy, re-check redirects and resolved addresses, block credential forwarding and internal reachability, and preserve safe recovery for rejected targets.",
        "src/foundation/capabilities/web-security/references/benchmarks-and-patterns.md",
    ),
    (
        "web-security",
        "Treat uploads and downloads as active content boundaries. Bound type, size, name, path, archive expansion, scanning, storage authority, rendering disposition, and retrieval authorization according to reachable abuse.",
        "src/foundation/capabilities/web-security/references/benchmarks-and-patterns.md",
    ),
    (
        "web-security",
        "Define cross-origin and embedding behavior narrowly. Derive origin, credential, header, method, framing, opener, and message-channel policy from current consumers and reject ambient wildcard trust.",
        "src/foundation/capabilities/web-security/references/benchmarks-and-patterns.md",
    ),
    (
        "web-security",
        "Prove denial and bypass paths. Exercise alternate encodings, redirects, stale sessions, direct routes, nested payloads, mixed content, unauthorized objects, and deployment policy relevant to the changed sink.",
        "src/foundation/capabilities/web-security/references/evidence-patterns.md",
    ),
)

NEW_ANCHOR_OVERRIDES = {
    """## Anti-Patterns

- Replay every queued request after reconnect without operation identity or authoritative status.
- Drop tombstones before every replica and offline client has crossed the deletion horizon.
- Resolve conflicts by device time while clock skew, account changes, or field-level intent remains material.""": """## Anti-Patterns

- Replay without identity or authoritative status.
- Drop tombstones before replica horizons.
- Resolve conflicts by device time.""",
    "Classify data by meaning and flow. Name direct, derived, inferred, linked, and sensitive elements with subjects, producers, consumers, stores, regions, and accountable owners.": "source-backed inventory",
    "Bind processing to an accepted purpose. Reject collection, derivation, sharing, or retention that lacks a necessary product or operational outcome and authorized policy source.": "compatible accepted purpose",
    "Reject unnecessary representation. Bound fields, precision, granularity, frequency, population, access, and lifetime across primary data, telemetry, exports, and support artifacts.": "purpose and minimization decisions",
    "Apply lifecycle policy to every reachable copy. Cover caches, indexes, logs, queues, analytics, replicas, archives, and backups with deletion propagation and non-resurrection behavior.": "silently resurrecting deleted active data",
    "Make export, correction, and deletion observable. Define identity binding, scope, asynchronous progress, partial failure, completion evidence, and unavailable-copy disclosure.": "explicitly partial outcome",
    "Constrain third-party and regional handling. Record provider purpose, data classes, location, onward sharing, retention, deletion, incident, and exit obligations before transfer.": "provider flows and regions",
    "Treat telemetry as data processing. Remove unnecessary identifiers and payloads before collection instead of relying on sampling, access restriction, or later redaction.": "Minimize telemetry before emission",
    "Evaluate de-identification against linkage. Name direct and quasi-identifiers, recipient knowledge, release model, utility tradeoff, and re-identification testing before reducing controls.": "release and recipient model",
    "Bound the changed security graph. Name the protected asset or authority, changed entry point, trust transition, data or control flow, and downstream effect. Out-of-scope or unknown edges introduced or altered by the task remain explicit.": "| Security delta |",
    "Model capability and preconditions, not actor labels alone. Include only behaviors with graph-backed access, knowledge, timing, and control prerequisites.": "| Actor capability |",
    "Trace a reachable abuse path. Follow source, attacker-controlled or stale values, transformations, policy or parser decisions, storage or transport, sink, and resulting effect; distinguish evidenced edges from assumptions and unreachable branches.": "| Path reachability |",
    "Define the protected outcome before severity. State the confidentiality, integrity, availability, safety, financial, privacy, tenant, or authority invariant at risk. Current exposure and consequences determine likelihood, impact, and blast radius rather than a threat label.": "| Protected outcome and impact |",
    "Select and place controls from the path. Compare candidate controls by protected outcome, intercepted edge, authority and owner, failure behavior, compatibility, and bypass surface. A mechanism remains undecided until the reachable path is known.": "| Control placement |",
    "Map the threat to fresh verification and detection. Connect the changed path and control to an abuse test, source/policy proof, monitoring, and final-edit freshness. The evidence limit remains explicit; scanner output alone cannot close business abuse.": "| Validation and detection cover the claim |",
    "Own residual risk and reopening. Record the unclosed path or consequence, compensating or containment evidence, accountable owner, release consequence, and the scope, incident, exposure, data, actor, or control change that requires review.": "| Residual risk is accountable |",
    "Trace changed routes from source to sink. Identify attacker-controlled values, browser or server transformations, framework defaults, trust transitions, reachable sinks, and alternate encoded or nested paths before selecting a control.": "Select from the current browser/server path, boundary, authority, and failure contract.",
    "Match rendering protection to context. Preserve contextual escaping, sanitization, trusted-template boundaries, URL and style handling, and script or markup policy for the actual sink; avoid decoding or concatenation after validation.": "| Render |",
    "Protect state-changing requests at the authority boundary. Combine authenticated context with current request-integrity, origin, cookie, method, and object-authorization controls without treating browser UI or route guards as enforcement.": "| State change |",
    "Constrain server-side fetching and navigation. Validate destinations against owned policy, re-check redirects and resolved addresses, block credential forwarding and internal reachability, and preserve safe recovery for rejected targets.": "| Server connection |",
    "Treat uploads and downloads as active content boundaries. Bound type, size, name, path, archive expansion, scanning, storage authority, rendering disposition, and retrieval authorization according to reachable abuse.": "| Upload/publication |",
    "Define cross-origin and embedding behavior narrowly. Derive origin, credential, header, method, framing, opener, and message-channel policy from current consumers and reject ambient wildcard trust.": "| Navigation/policy |",
    "Prove denial and bypass paths. Exercise alternate encodings, redirects, stale sessions, direct routes, nested payloads, mixed content, unauthorized objects, and deployment policy relevant to the changed sink.": "Re-run applicable hostile and denied cases",
    "Bind generated output to authoritative inputs, generator version, destination, drift check, sole editable source, and a non-circular clean-checkout bootstrap.": "Name schemas, templates, source, generator code, flags, versions, and the sole editable owner.",
    "Prove harness oracle and regression mechanism with positive and negative controls.": "Bind expected output or state to an independent oracle.",
    "Preserve internal CLI argv, environment, working directory, stdio, exit, cancellation, rerun, and cleanup.": "Define child executable, argv, environment, directory, stdio, timeout, cancellation, descendants, and exit mapping.",
    """## Anti-Patterns

- Reject one-variant wrappers, hidden global/I/O work, code-sharing bases, and pattern names without current force evidence.""": """## Anti-Patterns

- Reject one-variant wrappers, hidden global or I/O work, code-sharing bases, and pattern names without current-force evidence.""",
}

# Frozen source authority.  These are intentionally literal rather than
# derived from the current anchors, so an anchor and its expected fingerprint
# cannot drift together.
FROZEN_SOURCE_FINGERPRINTS = (
    "1ae0b3ba47c63c573eb804a40bd8bfdbe7faff88d97ab6aa97b408bf948cfdad",
    "42f0898dad61eb42c1386572e8c3c0972d4235d6d2ff9c958f86996c131b3384",
    "b5fb0a2702cf4a7fcc6bf304f11dd1193fd179e800c9d574aedfae0c3407f305",
    "3e11d61a89d462f685c1d59547b4a9718f799fca3e60c2baec212d2717ba32f1",
    "3972b103d844e520a54bf0992be6c3b1ff9e97de56f96f0ac5febdc74f02886e",
    "f8171e390d1bb3b3c3cd746a13f3b1577c85d66f5dca8e4d6a3222fabeb92f66",
    "019fa5a09bb03cf810246db0bae6d4b8f22e8e5d6818f16b262d607b635b1128",
    "91856b8913515c46e15c9e7373232f83eb998a863f0bcefb5019a95a5f8dd2ce",
    "f35eb976fc2f532cbf8d176fc57fb659cb372c64de9b9ca5f30b1d0d0541f9db",
    "cc963f3921a29f2cdfda0838b1db4f0197fd80df8db2a50b7daa2d0683162398",
    "de89a13bf51aa82fa77e155f0e4869bd3ea5edecd3260cd250c3065534a6bce9",
    "090161109e5fafe86319cd760118fc6f3b390c91f8ef9e2f828d460d63a4922f",
    "a037e096a64210862ed3901f2261d39d72c48c06b9e64ad0722f4ed5b6f74127",
    "2d94526f912402764b447a2b8f3403acaaa1c06ff0db548a188028d9be10f454",
    "4874025e438237b64cb59d35416d063dfc0ef7b9bd4bfb81b85f312ce6606886",
    "6ff64e7bb28b50bb07362018d18a4f6bc0f9acf546ac9f94c549f798b0f2b57f",
    "975804de03ec0211f398c4282efdecd4eb182a472665f513e3283f6c22ad2852",
    "e79f5fdff55c497eda67de3c49517afe1188daedb5052da0392542bbb718fd4e",
    "508532d2b7fec2be6b8b7f6bf937deb8bc2b66e928d60757d78af3be8b5b41c3",
    "a693cfd967d13c0f165b88b744cf6599673d937e48b37fb972afe7233957b485",
    "686842a511a7718ee864859cf1fdeaeed9f3ccf0ec47430be82d205bd7cb9595",
    "d4d5a5ae1512e87a04f1fc3f106d887daa187698b3a2091df7930be155f0d7bf",
    "52a185fe79288dbd22d1fe3f2dde3d65cb17dbee4968dad42b13d1fac87ab2a1",
    "e3f309e234b073063dd57be201596e23e8ad111fc81556ba5a3c3f75aaa847a7",
    "435087bea46c91e5ed0a5590ced49cc4b6fcd58331c310c756c4627910e419f0",
    "c5986b29f98be8b9579571ae922ec168da591ce469c22dbd8efba0aa28a2d282",
    "04aa6394af84c3ff28767621ff1c69d8f7704e95c16fa040cc961b3ed808db60",
    "e99028181e7140b86fa8b1fae45652fa9eb4576c0776e6c11ee0a519e084d535",
    "b05827400bca28e1df0b07046892d6e4a261efc8769a739e5c2ff3d05fb6f67a",
    "edce5c6caf146fc2af3d53e5f9163b4f6cd875fb41cab4cd3ace62fbdf9bbc3f",
    "815b0b2b6c7f7f3fc0d7093ac8f86bc679a563c97222fb0fff88eab50713790b",
    "bfab3d7411540a4559d4213f63887ce05d4c46c5e823faa576edad601b75cb8a",
    "2b4f5071f0412f805eb2a52b56a79fab8380d170c2594f07be7670a89353174b",
    "9a38e1afa7d6840e4b63b8600461cf200386cf7a5110315a4f79e3e3ad0d5194",
    "3999219ca27f03d510fe760c4d7fe7b3db0817103eeafd6697db7190991e164d",
    "1cc39c5dc7341bdf56d5a0e2fd33e91490011a3c74c21d1cb2f4d8d5584bbdb1",
    "695bd3592647a61218d5f041b3c3ceb933753406b54929694601712ecb511ef7",
    "a8ff81e72be595bfabe669516c3e2139d3fa28781021bd26d5550e45dc2d38c5",
    "8c331b54e3eb92a8bc58eb9e055c9608c9e8996a0601e8e8c074eaeaea66b0e7",
    "80c9b1be4837a3cd3d92626499b40490760c60057ccdecdf1ef125c73e502e25",
    "82ed0afe0d4e3123a96d4d08aa24bb1837b517813f01429dc6090fe3523f5049",
    "863e777471295b4f19e16b3e394cc18793a88a70b17e463ec9dfa1ede1efa0bd",
    "e1c6b207154c35f220eea5cc49d0780231d63b3bea214053591fd52d0e488b64",
    "1095970bc94f176247b880e65737f9261728dbb4810b01163de6b9596725abbd",
    "930b2002e805199983f0f910c76c29b960851792c6733210c591d28f4cfba2c4",
    "ce9640ddec58107bdcbaa88060e1d3489f35add846b0b7d56738bceb5d3c1d7a",
    "595b1cc279a2c6fe67bb7ee57402ee379c24f722fc93de2ebe1a6bd766dc8205",
    "06a53eae7a161134afc1bdf1530d49ef3a651d4d938d3229becc09eca64df901",
    "0079dadc35e735915291bf1449d30b7e947a69b2c45489942407c06658f099b6",
    "14c744665b195d8eb1d312da54618f5e69fb601cf295fc8d141b515047f560c2",
    "0d1d7fb714a0e19b7b8d9068b7dc8ba0659c9b3aee1334b7428956d1367b24b6",
    "847f8f720f16d5d6fdee5a7e00c354a1514de790f8c4ea65f6f24988112d9b8f",
    "c8c42223421eda73183250762e39a7edc376422e44e1cb1b1353434ac7841477",
    "1ccdb6d9f10a245add948afdf6b33044b48b13b636fec8870dd3a3f11563ed62",
    "7c81ecb5331fd4496e9711fba0e80e169a1f229b0992cd487d619a3fc8e66d45",
    "33f72941fc41dec64619c6a6fe4e749d0d83a15cf6a3c558c8a0261798d796b6",
    "f677a68fc61e0d5c79435ec1e5e0392da12d423e3993eef2e1eec107fea998c7",
    "9d4a0f0fc9f6fe04e0f1adfe3ee3fde39732e84ced6ad8436d784538a31c520c",
    "a1ddac7a9c77f84c2daf5d552826a0fda0a6299f4e7eaa705fbab648e64876e5",
    "25d110c8970ae5abaea9e49748b9bb01fcce2e7c832d3132a77e107527a9d7a3",
    "69dc3a803bd7a3a25adc0bb465b4315d940e1e6c7f49bf3dff628068f635a599",
    "efe3b9c3af24a89a5206b35d6fa3fd2dbe1e4878e070f732ecbdd981e54f5833",
    "9b4244c0ee9ae9c424aae01f83b2bd7981f3ef2a3511eac851630f9a437c1ee8",
    "c3cb715c73f5946972c9d74770be2e4b76453caa4d00925df7709b64925e314a",
    "65ad2f361d501ea8e450c5fe85a8cc51c7c350ac07fc218947c9a3ffa307006d",
    "316b367c7b4bcd90595e6987be6ddd73c6327fbe954b1e0d152fd21116577582",
)

ROOT_PATHS = {
    "logging-design-gate": "src/professional-skills/logging-design-gate/SKILL.md",
    "audit-evidence-integrity": "src/foundation/capabilities/audit-evidence-integrity/SKILL.md",
    "secret-configuration-security": "src/foundation/capabilities/secret-configuration-security/SKILL.md",
    "logging-error-handling": "src/foundation/capabilities/logging-error-handling/SKILL.md",
    "architecture-impact-reviewer": "src/professional-skills/architecture-impact-reviewer/SKILL.md",
    "change-documentation-gate": "src/professional-skills/change-documentation-gate/SKILL.md",
    "data-middleware-change-builder": "src/professional-skills/data-middleware-change-builder/SKILL.md",
    "delivery-release-gate": "src/professional-skills/delivery-release-gate/SKILL.md",
    "frontend-change-builder": "src/professional-skills/frontend-change-builder/SKILL.md",
    "high-risk-design-review": "src/professional-skills/high-risk-design-review/SKILL.md",
    "installed-client-change-builder": "src/professional-skills/installed-client-change-builder/SKILL.md",
    "integration-change-builder": "src/professional-skills/integration-change-builder/SKILL.md",
    "reliability-observability-gate": "src/professional-skills/reliability-observability-gate/SKILL.md",
    "authentication-authorization": "src/foundation/capabilities/authentication-authorization/SKILL.md",
    "authentication-security": "src/foundation/capabilities/authentication-security/SKILL.md",
    "cryptography-key-lifecycle": "src/foundation/capabilities/cryptography-key-lifecycle/SKILL.md",
    "permission-boundary-modeling": "src/foundation/capabilities/permission-boundary-modeling/SKILL.md",
    "tenant-isolation": "src/foundation/capabilities/tenant-isolation/SKILL.md",
    "engineering-change-analysis": "src/professional-skills/engineering-change-analysis/SKILL.md",
    "quality-test-gate": "src/professional-skills/quality-test-gate/SKILL.md",
    "repository-tooling-change-builder": "src/professional-skills/repository-tooling-change-builder/SKILL.md",
    "ai-code-review-refactor": "src/professional-skills/ai-code-review-refactor/SKILL.md",
    "backend-change-builder": "src/professional-skills/backend-change-builder/SKILL.md",
    "security-privacy-gate": "src/professional-skills/security-privacy-gate/SKILL.md",
    "data-api-contract-changer": "src/professional-skills/data-api-contract-changer/SKILL.md",
    "iot-embedded-extension": "src/domain-extensions/iot-embedded-extension/SKILL.md",
    "ai-product-extension": "src/domain-extensions/ai-product-extension/SKILL.md",
    "cross-platform-client-extension": "src/domain-extensions/cross-platform-client-extension/SKILL.md",
    "bigdata-product-extension": "src/domain-extensions/bigdata-product-extension/SKILL.md",
    "package-dependency-management": "src/foundation/capabilities/package-dependency-management/SKILL.md",
    "targeted-validation-selection": "src/foundation/capabilities/targeted-validation-selection/SKILL.md",
    "test-strategy": "src/foundation/capabilities/test-strategy/SKILL.md",
    "implementation-structure-design": "src/foundation/capabilities/implementation-structure-design/SKILL.md",
    "minimal-correct-implementation": "src/foundation/capabilities/minimal-correct-implementation/SKILL.md",
    "filesystem-process-safety": "src/foundation/capabilities/filesystem-process-safety/SKILL.md",
    "domain-object-identification": "src/foundation/capabilities/domain-object-identification/SKILL.md",
    "refactoring": "src/foundation/capabilities/refactoring/SKILL.md",
    "client-application-testing": "src/foundation/capabilities/client-application-testing/SKILL.md",
    "failure-contract-design": "src/foundation/capabilities/failure-contract-design/SKILL.md",
    "design-pattern-selection": "src/foundation/capabilities/design-pattern-selection/SKILL.md",
    "privacy-data-lifecycle": "src/foundation/capabilities/privacy-data-lifecycle/SKILL.md",
    "threat-modeling": "src/foundation/capabilities/threat-modeling/SKILL.md",
    "web-security": "src/foundation/capabilities/web-security/SKILL.md",
    "model-boundary-mapping": "src/foundation/capabilities/model-boundary-mapping/SKILL.md",
    "sdk-library-contract-design": "src/foundation/capabilities/sdk-library-contract-design/SKILL.md",
    "api-contract-design": "src/foundation/capabilities/api-contract-design/SKILL.md",
    "payment-trading-extension": "src/domain-extensions/payment-trading-extension/SKILL.md",
    "web3-product-extension": "src/domain-extensions/web3-product-extension/SKILL.md",
    "cloud-platform-extension": "src/domain-extensions/cloud-platform-extension/SKILL.md",
    "idempotency-retry-design": "src/foundation/capabilities/idempotency-retry-design/SKILL.md",
    "platform-infrastructure-change-builder": "src/professional-skills/platform-infrastructure-change-builder/SKILL.md",
    "dependency-vulnerability-scanning": "src/foundation/capabilities/dependency-vulnerability-scanning/SKILL.md",
    "infrastructure-as-code-safety": "src/foundation/capabilities/infrastructure-as-code-safety/SKILL.md",
    "powershell-professional-usage": "src/foundation/capabilities/powershell-professional-usage/SKILL.md",
    "low-level-systems-extension": "src/domain-extensions/low-level-systems-extension/SKILL.md",
    "code-review": "src/foundation/capabilities/code-review/SKILL.md",
    "regression-testing": "src/foundation/capabilities/regression-testing/SKILL.md",
    "backup-recovery": "src/foundation/capabilities/backup-recovery/SKILL.md",
    "concurrency-control": "src/foundation/capabilities/concurrency-control/SKILL.md",
    "configuration-runtime-policy": "src/foundation/capabilities/configuration-runtime-policy/SKILL.md",
    "data-migration-design": "src/foundation/capabilities/data-migration-design/SKILL.md",
    "degradation-circuit-breaking": "src/foundation/capabilities/degradation-circuit-breaking/SKILL.md",
    "distributed-workflow-consistency": "src/foundation/capabilities/distributed-workflow-consistency/SKILL.md",
    "observability": "src/foundation/capabilities/observability/SKILL.md",
    "offline-sync-conflict-resolution": "src/foundation/capabilities/offline-sync-conflict-resolution/SKILL.md",
    "release-rollback": "src/foundation/capabilities/release-rollback/SKILL.md",
    "transaction-consistency": "src/foundation/capabilities/transaction-consistency/SKILL.md",
    "consumer-impact-analysis": "src/foundation/capabilities/consumer-impact-analysis/SKILL.md",
    "contract-testing": "src/foundation/capabilities/contract-testing/SKILL.md",
    "module-boundary-design": "src/foundation/capabilities/module-boundary-design/SKILL.md",
    "state-management-design": "src/foundation/capabilities/state-management-design/SKILL.md",
    "technology-stack-selection": "src/foundation/capabilities/technology-stack-selection/SKILL.md",
    "version-compatibility": "src/foundation/capabilities/version-compatibility/SKILL.md",
    "code-clarity-maintainability": "src/foundation/capabilities/code-clarity-maintainability/SKILL.md",
    "documentation-generation": "src/foundation/capabilities/documentation-generation/SKILL.md",
    "repeat-failure-analysis": "src/foundation/capabilities/repeat-failure-analysis/SKILL.md",
    "test-data-management": "src/foundation/capabilities/test-data-management/SKILL.md",
    "accessibility-inclusive-design": "src/foundation/capabilities/accessibility-inclusive-design/SKILL.md",
    "build-tool-professional-usage": "src/foundation/capabilities/build-tool-professional-usage/SKILL.md",
    "client-lifecycle-state-restoration": "src/foundation/capabilities/client-lifecycle-state-restoration/SKILL.md",
    "csharp-dotnet-professional-usage": "src/foundation/capabilities/csharp-dotnet-professional-usage/SKILL.md",
    "interaction-state-modeling": "src/foundation/capabilities/interaction-state-modeling/SKILL.md",
    "kotlin-professional-usage": "src/foundation/capabilities/kotlin-professional-usage/SKILL.md",
    "swift-professional-usage": "src/foundation/capabilities/swift-professional-usage/SKILL.md",
    "web-platform-professional-usage": "src/foundation/capabilities/web-platform-professional-usage/SKILL.md",
}

V7_ACTIVE_REFERENCE_FACETS = {
    "src/professional-skills/platform-infrastructure-change-builder/references/iac-source-contracts.md": (
        "Terraform",
        "OpenTofu",
        "Pulumi",
        "CloudFormation",
        "state",
        "locking",
        "identity",
        "unknown",
        "target",
        "recovery",
        "secret",
        "Version Limit",
        "Required Record",
    ),
    "src/foundation/capabilities/code-review/references/finding-taxonomy.md": (
        "reachable consequence",
        "reversibility",
        "current policy",
        "Critical",
        "High",
        "Medium",
        "Low",
        "Non-finding",
        "API / Hallucination",
        "Security",
        "Concurrency",
        "Dependencies",
        "Resource lifecycle",
        "Config / Infra",
        "specialist",
        "confidence",
        "evidence gap",
    ),
}

SECURITY_RESTORED_RULES = (
    "Request-integrity proof is required only when ambient browser authority has not been excluded.",
    "Set severity from exploitability and current release policy, not scanner labels.",
    "Risky tool execution requires authority, isolation, recovery, and redaction evidence.",
    "Do not assume a universal legal basis or exception for privacy or compliance processing.",
    "A Critical or High dependency finding requires a repair, remediation, exception, or block decision.",
    "Secret work requires an owner, policy, containment, and rotation path.",
    "Enforce server-side authorization; UI hiding is not authorization.",
    "When dynamic proof is unavailable, record explicit residual exposure.",
)

LEDGER_FIELDS = {
    "owner",
    "source_path",
    "old_anchor",
    "source_rule_fingerprint",
    "classification",
    "decision_problem",
    "destination",
    "required_by",
    "required_output",
    "new_anchor",
    "disposition",
    "preserved_facets",
    "co_trigger_effect",
    "route_effect",
    "validation",
    "proof_limit",
}

COMPACTION_FIELDS = {
    "owner",
    "path",
    "old_content_sha256",
    "new_content_sha256",
    "classification",
    "disposition",
    "required_by",
    "required_output",
    "new_anchor",
    "preserved_facets",
    "co_trigger_effect",
    "route_effect",
    "validation",
    "proof_limit",
}

# Frozen Reference projection authority.  `_reference_binding` below reads the
# current root only to compare it with these fixed expected values.
FROZEN_REFERENCE_BINDINGS = {
    "src/professional-skills/logging-design-gate/references/logging-selection-criteria.md": (("task-agent", "review-agent"), ("selected-approach", "residual-risk")),
    "src/professional-skills/logging-design-gate/references/checklist.md": (("task-agent", "review-agent"), ("checklist-result", "validation-plan")),
    "src/foundation/capabilities/audit-evidence-integrity/references/completeness-identity-and-time.md": (ALL_ROLES, ("decision-record", "boundary-decision", "proof-limit")),
    "src/foundation/capabilities/audit-evidence-integrity/references/tamper-evidence-storage-and-access.md": (ALL_ROLES, ("evidence-record", "validation-plan", "proof-limit")),
    "src/foundation/capabilities/audit-evidence-integrity/references/retention-export-and-chain-of-custody.md": (ALL_ROLES, ("boundary-decision", "decision-record", "residual-risk")),
    "src/foundation/capabilities/secret-configuration-security/references/benchmarks-and-patterns.md": (ALL_ROLES, ("option-comparison", "selected-approach")),
    "src/foundation/capabilities/secret-configuration-security/references/checklist.md": (ALL_ROLES, ("checklist-result", "residual-risk")),
    "src/foundation/capabilities/secret-configuration-security/references/evidence-patterns.md": (ALL_ROLES, ("evidence-record", "proof-limit", "residual-risk")),
    "src/foundation/capabilities/logging-error-handling/references/benchmarks-and-patterns.md": (("task-agent", "review-agent"), ("option-comparison", "selected-approach")),
    "src/foundation/capabilities/logging-error-handling/references/evidence-patterns.md": (("task-agent", "review-agent"), ("evidence-record", "proof-limit", "residual-risk")),
    "src/professional-skills/architecture-impact-reviewer/references/placement-and-ownership.md": (("analysis-agent", "review-agent"), ("boundary-decision", "selected-approach", "residual-risk")),
    "src/professional-skills/architecture-impact-reviewer/references/consumer-and-data-impact.md": (("analysis-agent", "review-agent"), ("boundary-decision", "validation-plan", "residual-risk")),
    "src/professional-skills/architecture-impact-reviewer/references/dependency-topology-and-enforcement.md": (("analysis-agent", "review-agent"), ("boundary-decision", "gate-decision", "validation-plan", "residual-risk")),
    "src/professional-skills/architecture-impact-reviewer/references/reversibility-evolution-and-proof-limits.md": (("analysis-agent", "review-agent"), ("decision-record", "validation-plan", "proof-limit", "residual-risk")),
    "src/professional-skills/change-documentation-gate/references/documentation-output-and-gates.md": (("task-agent", "review-agent"), ("gate-decision", "residual-risk")),
    "src/professional-skills/data-middleware-change-builder/references/checklist.md": (("analysis-agent", "task-agent"), ("checklist-result", "residual-risk")),
    "src/professional-skills/delivery-release-gate/references/delivery-output-and-gates.md": (ALL_ROLES, ("gate-decision", "residual-risk")),
    "src/professional-skills/frontend-change-builder/references/frontend-output-and-gates.md": (("task-agent",), ("gate-decision", "residual-risk")),
    "src/foundation/capabilities/accessibility-inclusive-design/references/accessibility-verification-evidence.md": (ALL_ROLES, ("evidence-record", "validation-plan", "proof-limit", "residual-risk")),
    "src/foundation/capabilities/interaction-state-modeling/references/state-transition-and-backend-evidence.md": (ALL_ROLES, ("evidence-record", "validation-plan", "proof-limit", "residual-risk")),
    "src/foundation/capabilities/web-platform-professional-usage/references/document-semantics-and-accessibility-tree-contracts.md": (ALL_ROLES, ("selected-approach", "boundary-decision", "proof-limit")),
    "src/foundation/capabilities/web-platform-professional-usage/references/browser-compatibility-and-verification-evidence.md": (ALL_ROLES, ("evidence-record", "validation-plan", "proof-limit", "residual-risk")),
    "src/professional-skills/high-risk-design-review/references/design-review-checklist.md": (("review-agent",), ("checklist-result", "residual-risk")),
    "src/professional-skills/installed-client-change-builder/SKILL.md": (("task-agent",), ("proof-limit", "selected-approach", "validation-plan")),
    "src/professional-skills/installed-client-change-builder/references/flutter-framework-contracts.md": (("task-agent",), ("proof-limit", "selected-approach", "validation-plan")),
    "src/professional-skills/installed-client-change-builder/references/react-native-framework-contracts.md": (("task-agent",), ("proof-limit", "selected-approach", "validation-plan")),
    "src/professional-skills/installed-client-change-builder/references/electron-framework-contracts.md": (("task-agent",), ("proof-limit", "selected-approach", "validation-plan")),
    "src/professional-skills/installed-client-change-builder/references/tauri-framework-contracts.md": (("task-agent",), ("proof-limit", "selected-approach", "validation-plan")),
    "src/professional-skills/installed-client-change-builder/references/qt-framework-contracts.md": (("task-agent",), ("proof-limit", "selected-approach", "validation-plan")),
    "src/professional-skills/installed-client-change-builder/references/dotnet-maui-framework-contracts.md": (("task-agent",), ("proof-limit", "selected-approach", "validation-plan")),
    "src/professional-skills/installed-client-change-builder/references/kotlin-multiplatform-framework-contracts.md": (("task-agent",), ("proof-limit", "selected-approach", "validation-plan")),
    "src/professional-skills/integration-change-builder/references/checklist.md": (("analysis-agent", "task-agent"), ("checklist-result", "validation-plan")),
    "src/professional-skills/reliability-observability-gate/references/reliability-output-and-gates.md": (ALL_ROLES, ("gate-decision", "residual-risk")),
    "src/professional-skills/change-documentation-gate/references/checklist.md": (("task-agent", "review-agent"), ("checklist-result", "residual-risk")),
    "src/professional-skills/frontend-change-builder/references/checklist.md": (("task-agent",), ("checklist-result", "residual-risk")),
    "src/professional-skills/reliability-observability-gate/references/checklist.md": (ALL_ROLES, ("checklist-result", "residual-risk")),
    "src/foundation/capabilities/authentication-authorization/references/evidence-patterns.md": (("task-agent", "analysis-agent", "review-agent"), ("evidence-record", "proof-limit", "residual-risk")),
    "src/foundation/capabilities/authentication-security/references/checklist.md": (ALL_ROLES, ("checklist-result", "residual-risk")),
    "src/foundation/capabilities/permission-boundary-modeling/references/evidence-patterns.md": (ALL_ROLES, ("evidence-record", "proof-limit", "residual-risk")),
    "src/foundation/capabilities/cryptography-key-lifecycle/references/primitives-nonces-and-envelopes.md": (ALL_ROLES, ("selected-approach", "boundary-decision", "proof-limit")),
    "src/foundation/capabilities/cryptography-key-lifecycle/references/rotation-versioning-and-recovery.md": (ALL_ROLES, ("boundary-decision", "validation-plan", "proof-limit")),
    "src/foundation/capabilities/cryptography-key-lifecycle/references/compromise-destruction-and-agility.md": (ALL_ROLES, ("failure-decision", "boundary-decision", "residual-risk")),
    "src/foundation/capabilities/tenant-isolation/references/data-storage-cache-and-search-isolation.md": (ALL_ROLES, ("boundary-decision", "validation-plan", "residual-risk")),
    "src/foundation/capabilities/tenant-isolation/references/async-queue-and-execution-context-isolation.md": (ALL_ROLES, ("boundary-decision", "validation-plan", "proof-limit")),
    "src/foundation/capabilities/tenant-isolation/references/operations-telemetry-and-lifecycle-isolation.md": (ALL_ROLES, ("boundary-decision", "validation-plan", "residual-risk")),
    "src/foundation/capabilities/backup-recovery/references/evidence-patterns.md": (("task-agent", "review-agent"), ("evidence-record", "proof-limit", "residual-risk")),
    "src/foundation/capabilities/concurrency-control/references/checklist.md": (ALL_ROLES, ("checklist-result", "residual-risk")),
    "src/foundation/capabilities/configuration-runtime-policy/references/checklist.md": (("task-agent", "review-agent", "analysis-agent"), ("checklist-result", "residual-risk")),
    "src/foundation/capabilities/data-migration-design/references/evidence-patterns.md": (ALL_ROLES, ("evidence-record", "proof-limit", "residual-risk")),
    "src/foundation/capabilities/degradation-circuit-breaking/references/checklist.md": (ALL_ROLES, ("checklist-result", "residual-risk")),
    "src/foundation/capabilities/distributed-workflow-consistency/references/identity-state-and-unknown-outcomes.md": (ALL_ROLES, ("boundary-decision", "failure-decision", "proof-limit")),
    "src/foundation/capabilities/distributed-workflow-consistency/references/compensation-convergence-and-reconciliation.md": (ALL_ROLES, ("failure-decision", "selected-approach", "residual-risk")),
    "src/foundation/capabilities/distributed-workflow-consistency/references/stuck-manual-repair-and-versioning.md": (ALL_ROLES, ("failure-decision", "validation-plan", "proof-limit")),
    "src/foundation/capabilities/observability/references/checklist.md": (ALL_ROLES, ("checklist-result", "residual-risk")),
    "src/foundation/capabilities/offline-sync-conflict-resolution/references/sync-reconciliation-contracts.md": (ALL_ROLES, ("selected-approach", "proof-limit", "residual-risk")),
    "src/foundation/capabilities/release-rollback/references/evidence-patterns.md": (ALL_ROLES, ("evidence-record", "proof-limit", "residual-risk")),
    "src/foundation/capabilities/transaction-consistency/references/checklist.md": (("analysis-agent", "task-agent"), ("checklist-result", "residual-risk")),
    "src/foundation/capabilities/api-contract-design/references/evidence-patterns.md": (ALL_ROLES, ("evidence-record", "proof-limit", "residual-risk")),
    "src/foundation/capabilities/consumer-impact-analysis/references/evidence-patterns.md": (("task-agent", "analysis-agent", "review-agent"), ("evidence-record", "proof-limit", "residual-risk")),
    "src/foundation/capabilities/contract-testing/references/evidence-patterns.md": (ALL_ROLES, ("evidence-record", "proof-limit", "residual-risk")),
    "src/foundation/capabilities/model-boundary-mapping/references/evidence-patterns.md": (TASK_FIRST_ROLES, ("evidence-record", "proof-limit", "residual-risk")),
    "src/foundation/capabilities/module-boundary-design/references/boundary-kind-and-authority.md": (("analysis-agent", "review-agent"), ("boundary-decision", "decision-record", "residual-risk")),
    "src/foundation/capabilities/module-boundary-design/references/split-merge-and-move-decisions.md": (("analysis-agent", "review-agent"), ("boundary-decision", "selected-approach", "residual-risk")),
    "src/foundation/capabilities/sdk-library-contract-design/references/evidence-patterns.md": (TASK_FIRST_ROLES, ("evidence-record", "proof-limit", "residual-risk")),
    "src/foundation/capabilities/state-management-design/references/checklist.md": (("task-agent",), ("checklist-result", "residual-risk")),
    "src/foundation/capabilities/technology-stack-selection/references/benchmarks-and-patterns.md": (ALL_ROLES, ("option-comparison", "selected-approach")),
    "src/foundation/capabilities/version-compatibility/references/evidence-patterns.md": (ALL_ROLES, ("evidence-record", "proof-limit", "residual-risk")),
    "src/foundation/capabilities/code-clarity-maintainability/references/checklist.md": (ALL_ROLES, ("checklist-result", "residual-risk")),
    "src/foundation/capabilities/documentation-generation/references/evidence-patterns.md": (("task-agent", "review-agent"), ("evidence-record", "proof-limit", "residual-risk")),
    "src/foundation/capabilities/refactoring/references/behavior-preservation-evidence.md": (("review-agent", "analysis-agent"), ("evidence-record", "proof-limit", "residual-risk")),
    "src/foundation/capabilities/regression-testing/references/evidence-patterns.md": (ALL_ROLES, ("evidence-record", "proof-limit", "residual-risk")),
    "src/foundation/capabilities/repeat-failure-analysis/references/repeat-failure-checklist.md": (ALL_ROLES, ("checklist-result", "residual-risk")),
    "src/foundation/capabilities/test-data-management/references/checklist.md": (ALL_ROLES, ("checklist-result", "residual-risk")),
    "src/foundation/capabilities/accessibility-inclusive-design/references/inclusive-interaction-contracts.md": (ALL_ROLES, ("selected-approach", "proof-limit")),
    "src/foundation/capabilities/build-tool-professional-usage/references/evidence-patterns.md": (TASK_FIRST_ROLES, ("evidence-record", "proof-limit", "residual-risk")),
    "src/foundation/capabilities/client-lifecycle-state-restoration/references/restoration-boundaries.md": (ALL_ROLES, ("selected-approach", "proof-limit")),
    "src/foundation/capabilities/csharp-dotnet-professional-usage/references/async-resource-and-iterator-contracts.md": (TASK_FIRST_ROLES, ("decision-record", "residual-risk")),
    "src/foundation/capabilities/csharp-dotnet-professional-usage/references/runtime-deployment-and-interop-contracts.md": (TASK_FIRST_ROLES, ("selected-approach", "proof-limit", "residual-risk")),
    "src/foundation/capabilities/infrastructure-as-code-safety/references/state-plan-and-drift-contracts.md": (ALL_ROLES, ("decision-record", "proof-limit", "residual-risk")),
    "src/foundation/capabilities/interaction-state-modeling/references/evidence-patterns.md": (ALL_ROLES, ("evidence-record", "proof-limit", "residual-risk")),
    "src/foundation/capabilities/kotlin-professional-usage/references/coroutine-flow-state-contracts.md": (TASK_FIRST_ROLES, ("selected-approach", "proof-limit", "residual-risk")),
    "src/foundation/capabilities/kotlin-professional-usage/references/type-interop-and-dsl-contracts.md": (TASK_FIRST_ROLES, ("decision-record", "residual-risk")),
    "src/foundation/capabilities/powershell-professional-usage/references/pipeline-error-and-native-contracts.md": (TASK_FIRST_ROLES, ("decision-record", "residual-risk")),
    "src/foundation/capabilities/swift-professional-usage/references/value-memory-and-type-contracts.md": (TASK_FIRST_ROLES, ("decision-record", "residual-risk")),
    "src/foundation/capabilities/swift-professional-usage/references/concurrency-interop-and-ui-contracts.md": (TASK_FIRST_ROLES, ("selected-approach", "proof-limit", "residual-risk")),
    "src/foundation/capabilities/web-platform-professional-usage/references/document-event-rendering-contracts.md": (ALL_ROLES, ("selected-approach", "proof-limit")),
    "src/foundation/capabilities/web-platform-professional-usage/references/navigation-network-background-contracts.md": (ALL_ROLES, ("validation-plan", "residual-risk")),
    "src/domain-extensions/bigdata-product-extension/references/consumer-and-schema-contracts.md": (ALL_ROLES, ("boundary-decision", "decision-record", "residual-risk")),
    "src/domain-extensions/bigdata-product-extension/references/pipeline-replay-and-event-identity.md": (ALL_ROLES, ("boundary-decision", "decision-record", "failure-decision", "residual-risk")),
    "src/domain-extensions/bigdata-product-extension/references/quality-lineage-and-point-in-time-correctness.md": (ALL_ROLES, ("decision-record", "failure-decision", "validation-plan", "residual-risk")),
    "src/domain-extensions/bigdata-product-extension/references/storage-performance-and-recovery.md": (ALL_ROLES, ("selected-approach", "failure-decision", "validation-plan", "residual-risk")),
    "src/domain-extensions/bigdata-product-extension/references/observability-and-privacy.md": (ALL_ROLES, ("boundary-decision", "validation-plan", "residual-risk")),
    "src/domain-extensions/cross-platform-client-extension/references/bridge-plugin-and-ffi-contracts.md": (ALL_ROLES, ("selected-approach", "failure-decision", "validation-plan")),
    "src/domain-extensions/cross-platform-client-extension/references/framework-target-evidence-contracts.md": (ALL_ROLES, ("evidence-record", "proof-limit", "residual-risk")),
    "src/domain-extensions/cross-platform-client-extension/references/parity-and-regression-contracts.md": (ALL_ROLES, ("decision-record", "proof-limit", "validation-plan")),
    "src/domain-extensions/cross-platform-client-extension/references/shared-and-target-ownership-contracts.md": (ALL_ROLES, ("boundary-decision", "decision-record", "proof-limit")),
    "src/domain-extensions/iot-embedded-extension/references/checklist.md": (ALL_ROLES, ("checklist-result", "residual-risk")),
    "src/domain-extensions/ai-product-extension/references/checklist.md": (ALL_ROLES, ("checklist-result", "residual-risk")),
    "src/foundation/capabilities/client-application-testing/references/client-test-matrix.md": (ALL_ROLES, ("validation-plan", "residual-risk")),
    "src/foundation/capabilities/design-pattern-selection/references/pattern-evidence-record.md": (ALL_ROLES, ("evidence-record", "proof-limit", "residual-risk")),
    "src/foundation/capabilities/domain-object-identification/references/benchmarks-and-patterns.md": (ALL_ROLES, ("option-comparison", "selected-approach")),
    "src/foundation/capabilities/domain-object-identification/references/checklist.md": (ALL_ROLES, ("checklist-result", "residual-risk")),
    "src/foundation/capabilities/domain-object-identification/references/evidence-patterns.md": (ALL_ROLES, ("evidence-record", "proof-limit", "residual-risk")),
    "src/foundation/capabilities/failure-contract-design/references/benchmarks-and-patterns.md": (TASK_FIRST_ROLES, ("option-comparison", "selected-approach")),
    "src/foundation/capabilities/failure-contract-design/references/checklist.md": (TASK_FIRST_ROLES, ("checklist-result", "residual-risk")),
    "src/foundation/capabilities/failure-contract-design/references/evidence-patterns.md": (TASK_FIRST_ROLES, ("evidence-record", "proof-limit", "residual-risk")),
    "src/foundation/capabilities/filesystem-process-safety/references/atomic-filesystem-commit-and-containment.md": (ALL_ROLES, ("boundary-decision", "proof-limit", "residual-risk")),
    "src/foundation/capabilities/filesystem-process-safety/references/child-process-invocation-and-completion.md": (ALL_ROLES, ("boundary-decision", "proof-limit", "residual-risk")),
    "src/foundation/capabilities/implementation-structure-design/references/evidence-patterns.md": (TASK_FIRST_ROLES, ("evidence-record", "validation-plan", "proof-limit", "residual-risk")),
    "src/foundation/capabilities/implementation-structure-design/references/object-module-decomposition.md": (TASK_FIRST_ROLES, ("decision-record", "validation-plan", "proof-limit", "residual-risk")),
    "src/foundation/capabilities/implementation-structure-design/references/reuse-and-placement.md": (TASK_FIRST_ROLES, ("selected-approach", "validation-plan", "proof-limit", "residual-risk")),
    "src/foundation/capabilities/minimal-correct-implementation/references/simplicity-ladder.md": (ALL_ROLES, ("option-comparison", "selected-approach", "residual-risk")),
    "src/foundation/capabilities/package-dependency-management/references/checklist.md": (ALL_ROLES, ("checklist-result", "residual-risk")),
    "src/foundation/capabilities/package-dependency-management/references/ecosystem-command-map.md": (ALL_ROLES, ("validation-plan", "proof-limit", "evidence-gap")),
    "src/foundation/capabilities/package-dependency-management/references/evidence-patterns.md": (ALL_ROLES, ("evidence-record", "proof-limit", "residual-risk")),
    "src/foundation/capabilities/privacy-data-lifecycle/references/data-lifecycle-controls.md": (ALL_ROLES, ("decision-record", "residual-risk")),
    "src/foundation/capabilities/privacy-data-lifecycle/references/de-identification-and-provider-controls.md": (ALL_ROLES, ("selected-approach", "proof-limit")),
    "src/foundation/capabilities/refactoring/references/behavior-preservation-evidence.md": (("review-agent", "analysis-agent"), ("evidence-record", "proof-limit", "residual-risk")),
    "src/foundation/capabilities/refactoring/references/checklist.md": (("review-agent", "analysis-agent"), ("checklist-result", "residual-risk")),
    "src/foundation/capabilities/refactoring/references/split-merge-cleanup-patterns.md": (("review-agent", "analysis-agent"), ("option-comparison", "selected-approach")),
    "src/foundation/capabilities/targeted-validation-selection/references/repository-command-entry-evidence.md": (ALL_ROLES, ("evidence-record", "proof-limit", "residual-risk")),
    "src/foundation/capabilities/test-strategy/references/benchmarks-and-patterns.md": (ALL_ROLES, ("option-comparison", "selected-approach")),
    "src/foundation/capabilities/test-strategy/references/checklist.md": (ALL_ROLES, ("checklist-result", "residual-risk")),
    "src/foundation/capabilities/test-strategy/references/evidence-patterns.md": (ALL_ROLES, ("evidence-record", "proof-limit", "residual-risk")),
    "src/foundation/capabilities/threat-modeling/references/benchmarks-and-patterns.md": (ALL_ROLES, ("option-comparison", "selected-approach")),
    "src/foundation/capabilities/threat-modeling/references/evidence-patterns.md": (ALL_ROLES, ("evidence-record", "proof-limit", "residual-risk")),
    "src/foundation/capabilities/web-security/references/benchmarks-and-patterns.md": (ALL_ROLES, ("option-comparison", "selected-approach")),
    "src/foundation/capabilities/web-security/references/evidence-patterns.md": (ALL_ROLES, ("evidence-record", "proof-limit", "residual-risk")),
    "src/professional-skills/ai-code-review-refactor/references/ai-review-pattern-catalog.md": (("review-agent",), ("option-comparison", "selected-approach")),
    "src/professional-skills/ai-code-review-refactor/references/checklist.md": (("review-agent",), ("checklist-result", "residual-risk")),
    "src/professional-skills/backend-change-builder/references/checklist.md": (("task-agent",), ("checklist-result", "residual-risk")),
    "src/professional-skills/backend-change-builder/references/proactive-triggers.md": (("task-agent",), ("boundary-decision", "residual-risk")),
    "src/professional-skills/backend-change-builder/references/professional-modes.md": (("task-agent",), ("mode-result", "proof-limit")),
    "src/professional-skills/quality-test-gate/references/checklist.md": (ALL_ROLES, ("checklist-result", "validation-plan")),
    "src/professional-skills/quality-test-gate/references/test-output-and-gates.md": (ALL_ROLES, ("gate-decision", "residual-risk")),
    "src/professional-skills/quality-test-gate/references/test-structure-boundaries.md": (ALL_ROLES, ("validation-plan", "proof-limit")),
    "src/professional-skills/repository-tooling-change-builder/references/generator-and-plugin-contracts.md": (("task-agent",), ("boundary-decision", "selected-approach", "proof-limit")),
    "src/professional-skills/repository-tooling-change-builder/references/harness-validity-contracts.md": (("task-agent",), ("decision-record", "validation-plan", "proof-limit")),
    "src/professional-skills/repository-tooling-change-builder/references/repository-automation-contracts.md": (("task-agent",), ("decision-record", "failure-decision", "proof-limit")),
    "src/professional-skills/security-privacy-gate/references/security-output-and-gates.md": (ALL_ROLES, ("gate-decision", "residual-risk")),
    "src/professional-skills/data-api-contract-changer/references/checklist.md": (("analysis-agent", "task-agent"), ("checklist-result", "residual-risk")),
    "src/foundation/capabilities/model-boundary-mapping/references/benchmarks-and-patterns.md": (TASK_FIRST_ROLES, ("option-comparison", "selected-approach")),
    "src/foundation/capabilities/sdk-library-contract-design/references/benchmarks-and-patterns.md": (TASK_FIRST_ROLES, ("option-comparison", "selected-approach")),
    "src/foundation/capabilities/api-contract-design/references/checklist.md": (ALL_ROLES, ("checklist-result", "residual-risk")),
    "src/domain-extensions/payment-trading-extension/references/financial-role-and-state-authority.md": (ALL_ROLES, ("boundary-decision", "residual-risk")),
    "src/domain-extensions/payment-trading-extension/references/raw-card-custody-evidence.md": (ALL_ROLES, ("evidence-record", "proof-limit", "residual-risk")),
    "src/domain-extensions/payment-trading-extension/references/non-custodial-sensitive-data-boundary.md": (ALL_ROLES, ("boundary-decision", "proof-limit", "residual-risk")),
    "src/domain-extensions/payment-trading-extension/references/duplicate-financial-effect-control.md": (ALL_ROLES, ("selected-approach", "residual-risk")),
    "src/domain-extensions/payment-trading-extension/references/owned-financial-state-accounting-and-balances.md": (ALL_ROLES, ("decision-record", "residual-risk")),
    "src/domain-extensions/payment-trading-extension/references/trading-order-execution-and-identity.md": (ALL_ROLES, ("decision-record", "failure-decision", "residual-risk")),
    "src/domain-extensions/payment-trading-extension/references/market-data-and-trading-risk-controls.md": (ALL_ROLES, ("selected-approach", "failure-decision", "residual-risk")),
    "src/domain-extensions/payment-trading-extension/references/venue-product-monetary-and-calendar-contracts.md": (ALL_ROLES, ("decision-record", "residual-risk")),
    "src/domain-extensions/payment-trading-extension/references/provider-venue-event-authentication.md": (ALL_ROLES, ("boundary-decision", "residual-risk")),
    "src/domain-extensions/payment-trading-extension/references/financial-reconciliation-and-monitoring.md": (ALL_ROLES, ("decision-record", "validation-plan", "residual-risk")),
    "src/domain-extensions/web3-product-extension/references/custody-and-chain-transactions.md": (ALL_ROLES, ("boundary-decision", "selected-approach", "failure-decision", "residual-risk")),
    "src/domain-extensions/web3-product-extension/references/monitoring-and-independent-assurance.md": (ALL_ROLES, ("decision-record", "validation-plan", "proof-limit", "residual-risk")),
    "src/domain-extensions/web3-product-extension/references/upgrades-and-deployed-behavior.md": (ALL_ROLES, ("release-decision", "residual-risk")),
    "src/domain-extensions/web3-product-extension/references/verification-evidence.md": (ALL_ROLES, ("evidence-record", "validation-plan", "proof-limit", "residual-risk")),
    "src/domain-extensions/web3-product-extension/references/governance-authority.md": (ALL_ROLES, ("boundary-decision", "residual-risk")),
    "src/domain-extensions/web3-product-extension/references/allowances-nonstandard-assets-and-delegated-calls.md": (ALL_ROLES, ("boundary-decision", "failure-decision", "residual-risk")),
    "src/domain-extensions/web3-product-extension/references/account-and-cross-domain-execution.md": (ALL_ROLES, ("boundary-decision", "failure-decision", "residual-risk")),
    "src/domain-extensions/cloud-platform-extension/references/resource-control-and-data-plane-boundaries.md": (ALL_ROLES, ("boundary-decision", "decision-record", "proof-limit")),
    "src/foundation/capabilities/idempotency-retry-design/references/checklist.md": (ALL_ROLES, ("checklist-result", "residual-risk")),
    "src/foundation/capabilities/api-contract-design/references/api-style-and-semantics.md": (ALL_ROLES, ("selected-approach", "residual-risk")),
    "src/professional-skills/platform-infrastructure-change-builder/references/iac-source-contracts.md": (("task-agent",), ("proof-limit", "selected-approach", "validation-plan")),
    "src/professional-skills/platform-infrastructure-change-builder/references/kubernetes-source-contracts.md": (("task-agent",), ("proof-limit", "selected-approach", "validation-plan")),
    "src/foundation/capabilities/dependency-vulnerability-scanning/references/benchmarks-and-patterns.md": (ALL_ROLES, ("option-comparison", "selected-approach")),
    "src/foundation/capabilities/dependency-vulnerability-scanning/references/checklist.md": (ALL_ROLES, ("checklist-result", "residual-risk")),
    "src/foundation/capabilities/dependency-vulnerability-scanning/references/evidence-patterns.md": (ALL_ROLES, ("evidence-record", "proof-limit", "residual-risk")),
    "src/foundation/capabilities/infrastructure-as-code-safety/references/state-plan-and-drift-contracts.md": (ALL_ROLES, ("decision-record", "proof-limit", "residual-risk")),
    "src/foundation/capabilities/infrastructure-as-code-safety/references/identity-destruction-and-recovery-contracts.md": (ALL_ROLES, ("decision-record", "proof-limit", "residual-risk")),
    "src/foundation/capabilities/powershell-professional-usage/references/pipeline-error-and-native-contracts.md": (TASK_FIRST_ROLES, ("decision-record", "residual-risk")),
    "src/foundation/capabilities/powershell-professional-usage/references/remoting-provider-and-administration-contracts.md": (TASK_FIRST_ROLES, ("selected-approach", "proof-limit", "residual-risk")),
    "src/domain-extensions/low-level-systems-extension/references/ownership-and-concurrency-contracts.md": (ALL_ROLES, ("boundary-decision", "failure-decision", "proof-limit", "residual-risk")),
    "src/domain-extensions/low-level-systems-extension/references/abi-platform-and-syscall-contracts.md": (ALL_ROLES, ("boundary-decision", "failure-decision", "residual-risk")),
    "src/domain-extensions/low-level-systems-extension/references/resource-lifecycle-and-error-contracts.md": (ALL_ROLES, ("decision-record", "failure-decision", "residual-risk")),
    "src/domain-extensions/low-level-systems-extension/references/performance-and-verification-evidence.md": (ALL_ROLES, ("evidence-record", "validation-plan", "proof-limit", "residual-risk")),
    "src/domain-extensions/low-level-systems-extension/references/signals-ffi-atomics-shared-memory-and-fork.md": (ALL_ROLES, ("boundary-decision", "selected-approach", "failure-decision", "proof-limit", "residual-risk")),
    "src/foundation/capabilities/code-review/references/checklist.md": (("review-agent", "analysis-agent", "task-agent"), ("checklist-result", "residual-risk")),
    "src/foundation/capabilities/code-review/references/evidence-patterns.md": (("review-agent", "analysis-agent", "task-agent"), ("evidence-record", "proof-limit", "residual-risk")),
    "src/foundation/capabilities/code-review/references/finding-taxonomy.md": (("review-agent", "analysis-agent", "task-agent"), ("gate-decision", "residual-risk")),
    "src/foundation/capabilities/regression-testing/references/benchmarks-and-patterns.md": (ALL_ROLES, ("option-comparison", "selected-approach")),
    "src/foundation/capabilities/regression-testing/references/checklist.md": (ALL_ROLES, ("checklist-result", "residual-risk")),
    "src/foundation/capabilities/regression-testing/references/evidence-patterns.md": (ALL_ROLES, ("evidence-record", "proof-limit", "residual-risk")),
}

V6_MOVE_SPECS = (
    (
        "data-api-contract-changer",
        "Treat API, event, schema, error, and data formats as consumer contracts with explicit compatibility windows.",
        "src/professional-skills/data-api-contract-changer/references/checklist.md",
        "99032123aeee134d8e1dc032f31ef8ed04565f4f778c15e00e3c0d48df91820c",
        "Define compatibility tests and contract tests.",
    ),
    (
        "model-boundary-mapping",
        "Keep DTOs separate from domain, persistence, generated-provider, and view models to prevent authority leakage.",
        "src/foundation/capabilities/model-boundary-mapping/references/benchmarks-and-patterns.md",
        "1ea889da0513df79b88d1e8155fbebec66f2bd72a6eba532437646855e6f1c1f",
        "transport, domain, persistence, event, and view models represent different facts",
    ),
    (
        "sdk-library-contract-design",
        "Own distributed contract encoding.",
        "src/foundation/capabilities/sdk-library-contract-design/references/benchmarks-and-patterns.md",
        "ceced3b0f423d1d07fd70704d4355faccdde1730d74e78400e268fe5959ed106",
        "Public API diffing",
    ),
    (
        "api-contract-design",
        "Start from consumer goal and resource semantics.",
        "src/foundation/capabilities/api-contract-design/references/checklist.md",
        "7ac16aa85d15e8500cf5518d96124fb7cff1964f5fbb3630204d52bd4e62b113",
        "Define operation name, method, path, and resource semantics.",
    ),
    (
        "payment-trading-extension",
        "Use authoritative provider evidence",
        "src/domain-extensions/payment-trading-extension/references/financial-role-and-state-authority.md",
        "f9140a70eb248e99878f9d0b67fbdaea4fb994327ee12016a1da0aabe1e11a57",
        "Bind confirmation, entitlement, fulfillment, position, and balance changes",
    ),
    (
        "cloud-platform-extension",
        "Bind every resource to its account/project/subscription, hierarchy, billing owner, environment, and inherited policy boundary.",
        "src/domain-extensions/cloud-platform-extension/references/resource-control-and-data-plane-boundaries.md",
        "f53f8b020743c683d435f9a32b9a6ad32eca0035601adbc152f9ef89b5334beb",
        "Record the owning AWS account, Azure subscription and management group, or",
    ),
    (
        "idempotency-retry-design",
        "Define business identity before choosing a key mechanism.",
        "src/foundation/capabilities/idempotency-retry-design/references/checklist.md",
        "9ff2a1c12ac04c8b17f4a8c506f5db7cb3ae20b91c4212199427a7a11df358eb",
        "Bind identity to the required principal, tenant, subject, operation, canonical request meaning, and version behavior.",
    ),
)

V7_MOVE_SPECS = (
    (
        "platform-infrastructure-change-builder",
        "Keep source configuration, recorded state, provider actual state, and effective deployed state distinct.",
        "src/professional-skills/platform-infrastructure-change-builder/references/iac-source-contracts.md",
        "1291d38e6de3707601a619dd79d8a7f3228384e8f3cef742f56a84d0279ad023",
        "state/identity/locking, unknowns/targeting",
    ),
    (
        "dependency-vulnerability-scanning",
        "Map the resolved graph delta before judging risk: direct owner, transitive paths, runtime/build/test/CI placement, optional features, platform variants, and affected artifacts.",
        "src/foundation/capabilities/dependency-vulnerability-scanning/references/checklist.md",
        "3a6c7131f1e4065f9acc60032750bc094e7f1049b17989f88aebd11b31926818",
        "Review direct, transitive, runtime, build, test, CI, and container dependency changes.",
    ),
    (
        "infrastructure-as-code-safety",
        "Bind target, remote state backend, workspace or stack, writer, and locking semantics before trusting a proposal.",
        "src/foundation/capabilities/infrastructure-as-code-safety/references/state-plan-and-drift-contracts.md",
        "0547730b7f6fc63c0940543a9e9c945774494c01b4f3d7385f9f240fb500e2c7",
        "| Recorded | Backend, workspace/stack, version, encryption, recovery owner. |",
    ),
    (
        "powershell-professional-usage",
        "Classify terminating/non-terminating errors; set catch/`ErrorAction`, preserve error records, and define automation exit.",
        "src/foundation/capabilities/powershell-professional-usage/references/pipeline-error-and-native-contracts.md",
        "89412971ac469a6fdd57a4fae9fe8118decd128032bc54c681d050f1232e04ac",
        "classify terminating and non-terminating cases",
    ),
    (
        "low-level-systems-extension",
        "**Prove ownership and lifetime**: trace acquisition, transfer, borrowing, publication, and release across functions, threads, languages, callbacks, and failure paths.",
        "src/domain-extensions/low-level-systems-extension/references/ownership-and-concurrency-contracts.md",
        "74263deab6d05975ef81759da425ce4d7ce5bb3f7f735874a9daaec3a9a374c9",
        "Define ownership, lifetime, allocation and deallocation pairing",
    ),
    (
        "code-review",
        "**Resolve the review surface.** Identify the Current Task Boundary, latest diff, all changed files, and reachable caller, consumer, sibling, or configuration impact before judging local lines.",
        "src/foundation/capabilities/code-review/references/evidence-patterns.md",
        "ab11a967aaba9476a65c8614f36b4264a0d020c94d503f547fa3ce1ea5ccc052",
        "inspected diff boundary",
    ),
    (
        "regression-testing",
        "Require causal-trigger reproduction rather than adjacent correct behavior as the recurrence guard.",
        "src/foundation/capabilities/regression-testing/references/benchmarks-and-patterns.md",
        "a4d701771cf3bd838ce9b9de23292a765c08ed7b5d6885724c2a7ff3a033845f",
        "These patterns preserve a known failure mechanism",
    ),
)

PAYMENT_ROOT_PREDECESSOR_SHA256 = (
    "a85c220eece629aed74f6db1b839027e61f608fa1c8868d8ed0fc9134649af98"
)
PAYMENT_ROOT_SUCCESSOR_SHA256 = (
    "07a16c89965fdbdc95e6446841d694935c855055c1f2dacbe1996f2a4c4d4762"
)
PAYMENT_CHECKLIST_PREDECESSOR_SHA256 = (
    "ed4872eaafeb42d56e0426c8dfbe812efdb26424904f2558f4b47f5179321819"
)
PAYMENT_REGISTRY_PREDECESSOR_SHA256 = (
    "c6caf7c3e9244e40ac382d395e28f41c45e249544e9714d99bb8e12bc469a6c1"
)
PAYMENT_REGISTRY_SUCCESSOR_SHA256 = (
    "f735238303b8377508a3043805f4b43aaac5110e8e76c01996e7aa6b5dfd47a1"
)
PAYMENT_REGISTRY_FILE_SUCCESSOR_SHA256 = (
    "2d53ccc4206c94d9850e007d21603f04ba1f06f7721de5da1cd47dcfe6e16129"
)
PAYMENT_ROOT_KERNEL_SHA256 = (
    "7431dbda39c49f5f2a560d3f5e4d8cf2eb453d37a0c841ec9b41d52eb4e013b8"
)
PAYMENT_REFERENCE_SPECS = {
    "financial-role-and-state-authority.md": {
        "load_when": "payment custody model, provider/custody/ledger/settlement roles, source of truth, or authoritative completion state is open",
        "do_not_load_when": "roles, source of truth, custody and authoritative state are already explicit, or no monetary state exists, including price display or ordinary orders without funds, ledger, settlement, or execution state",
        "gap_class": "repo-resolvable-fact",
        "route_affecting_surfaces": (
            "primary-professional-skill",
            "layer3",
            "domain",
            "acceptance",
            "scope",
            "material-risk-floor",
        ),
        "rules": (
            "Classify the payment custody model.",
            "Identify the provider, exchange, custody, ledger, settlement, revocation, and finality roles that determine authority.",
            "Bind confirmation, entitlement, fulfillment, position, and balance changes to authoritative server-side events or state determined by those roles.",
        ),
    },
    "raw-card-custody-evidence.md": {
        "load_when": "approved raw-card custody requires PCI/PAN/CVV retention, storage, display, logging, or evidence closure",
        "do_not_load_when": "no raw-card custody exists; the flow is provider-hosted/non-custodial",
        "gap_class": "route-or-material-unknown",
        "route_affecting_surfaces": ("layer3", "acceptance", "scope", "material-risk-floor"),
        "rules": (
            "Record current applicable PCI scope, accountable owner, proof gaps, and retention, storage, display, and logging evidence for approved raw-card custody.",
            "Use that record as control evidence without asserting certification.",
            "Prove approved raw-card custody retains no CVV or other sensitive authentication data after authorization unless current governing PCI requirements permit a documented issuing exception.",
            "Prove that control evidence protects stored PAN.",
            "Prove that control evidence masks displayed PAN.",
            "Cover logs, traces, errors, and ordinary artifacts in PAN discovery and control evidence.",
        ),
    },
    "non-custodial-sensitive-data-boundary.md": {
        "load_when": "tokenized/provider-hosted payment flow must prove PAN/CVV/payment-secret exclusion",
        "do_not_load_when": "application has no reachable payment secret, or approved raw-card custody rather than a non-custodial boundary is being assessed",
        "gap_class": "repo-resolvable-fact",
        "route_affecting_surfaces": ("layer3", "acceptance", "scope", "material-risk-floor"),
        "rules": (
            "Prove that non-custodial controls keep PAN, CVV, payment secrets, and equivalent sensitive values outside application storage.",
            "Prove that non-custodial controls keep those sensitive values outside ordinary artifacts.",
            "Prove that non-custodial controls keep those sensitive values out of logs, traces, and errors.",
            "Record tokenization or provider-boundary proof and named gaps for non-custodial flows.",
        ),
    },
    "duplicate-financial-effect-control.md": {
        "load_when": "retry, replay, concurrent submission, result reuse, or unknown outcome can repeat a financial effect",
        "do_not_load_when": "no retryable financial effect exists, or current provider/storage uniqueness is already proven and unchanged",
        "gap_class": "repo-resolvable-fact",
        "route_affecting_surfaces": ("layer3", "acceptance", "scope", "material-risk-floor"),
        "rules": (
            "Select duplicate controls for each retryable financial effect from defined business uniqueness, retry, unknown-result, concurrent-submission, result-reuse, provider, venue, workflow, and persistence guarantees.",
        ),
    },
    "owned-financial-state-accounting-and-balances.md": {
        "load_when": "owned payment/ledger transitions, correction history, accounting ownership, or balance authority is open",
        "do_not_load_when": "pure provider orchestration owns no ledger, accounting book, or application balance",
        "gap_class": "repo-resolvable-fact",
        "route_affecting_surfaces": ("layer3", "acceptance", "scope", "material-risk-floor"),
        "rules": (
            "Model owned payment and ledger transitions across authorization, capture, settlement, failure, cancellation, refund, dispute, reversal, expiry, adjustment, and reconciliation. The model names transition authority, stale-event behavior, and compensation limits.",
            "Derive balancing, correction, reversal, and append-versus-update behavior from accounting ownership and storage guarantees. The result preserves financial history without imposing ledger semantics on pure orchestration.",
            "Define applicable available, pending, reserved, held, settled, negative, disputed, margin, and collateral balances. Their transition events and authoritative sources govern delayed or corrected execution.",
        ),
    },
    "trading-order-execution-and-identity.md": {
        "load_when": "order acknowledgement/fill/cancel/replace, execution identity, race, gap, or recovery behavior is open",
        "do_not_load_when": "payment-only work has no order execution, fill, cancel, venue identity, or trading-session recovery",
        "gap_class": "repo-resolvable-fact",
        "route_affecting_surfaces": ("layer3", "acceptance", "scope", "material-risk-floor"),
        "rules": (
            "Model execution across acknowledgement, rejection, partial fill, fill, cancel, and cancel-replace. Race handling preserves executed quantity and prevents terminated quantity from reopening after fill-versus-cancel or replace-versus-late-report.",
            "Correlate client order or request identity with venue order, execution, fill, and correction identity. Reconciliation covers primary-session and drop-copy differences, duplicates, gaps, reordering, session resets, sequence restarts, and snapshot or authoritative-query recovery.",
        ),
    },
    "market-data-and-trading-risk-controls.md": {
        "load_when": "price-sensitive execution, risk limits, overrides, kill switch, leverage, margin, or liquidation behavior is open",
        "do_not_load_when": "no price-sensitive execution, leverage, override, limit, or kill-switch behavior changes",
        "gap_class": "route-or-material-unknown",
        "route_affecting_surfaces": ("layer3", "acceptance", "scope", "material-risk-floor"),
        "rules": (
            "Gate price-sensitive execution on market-data authority, freshness, sequence continuity, venue and instrument status, halt or auction state, and snapshot recovery. Derive fat-finger, price-collar, slippage, and unavailable-evidence behavior from current risk policy.",
            "Derive refund, adjustment, payout, trading override, self-trade prevention, pre-trade limit, and kill-switch authority from current risk policy. The policy governs stale input, fail-safe behavior, activation, recovery, user impact, and tamper evidence.",
            "For leveraged products, model collateral, maintenance margin, margin call, liquidation, insurance or loss allocation, and auto-deleveraging states. Authoritative risk inputs bind triggers and position priority; outcomes cover partial execution, halt, stale price, appeal, and reconciliation.",
        ),
    },
    "venue-product-monetary-and-calendar-contracts.md": {
        "load_when": "venue/product units, tick/lot/notional, fee/funding, precision/rounding, currency, cutoff, calendar, or timestamp contract is open",
        "do_not_load_when": "no venue/product monetary representation or calendar contract changes, and current contracts are explicit",
        "gap_class": "repo-resolvable-fact",
        "route_affecting_surfaces": ("layer3", "acceptance", "scope", "material-risk-floor"),
        "rules": (
            "Apply venue/product contracts for tick size, lot size, quantity and notional bounds, fee and funding semantics, price and quantity scale, precision, and rounding. The contract governs validation, execution, persistence, reporting, and reconciliation boundaries.",
            "Make currency exponent, conversion, tax, settlement calendar, cutoff, time zone, clock source and skew, provider or exchange timestamp, and business-date rules explicit at ingestion, ordering, accounting, reporting, and reconciliation boundaries.",
        ),
    },
    "provider-venue-event-authentication.md": {
        "load_when": "inbound provider/venue events require identity, replay, ordering, version, credential, or audit closure",
        "do_not_load_when": "no inbound external financial event is consumed",
        "gap_class": "repo-resolvable-fact",
        "route_affecting_surfaces": ("layer3", "acceptance", "scope", "material-risk-floor"),
        "rules": (
            "Authenticate and attribute inbound provider or venue events under the current protocol. The contract covers replay identity, ordering or reorder behavior, version compatibility, credential ownership, and audit evidence without prescribing one signature scheme.",
        ),
    },
    "financial-reconciliation-and-monitoring.md": {
        "load_when": "orders, executions, positions, balances, ledgers, settlements, corrections, breaks, replay windows, or operational signals require reconciliation closure",
        "do_not_load_when": "no cross-source reconciliation or financial-operability boundary changes",
        "gap_class": "repo-resolvable-fact",
        "route_affecting_surfaces": ("layer3", "acceptance", "scope", "material-risk-floor"),
        "rules": (
            "Reconcile applicable orders, executions, fills, positions, balances, ledgers, statements, settlements, fees, funding, and corporate actions. Apply relevant lifecycle adjustments and define break classification, correction authority, replay windows, and unresolved-owner escalation.",
            "Monitor selected duplicate effects, report gaps, reordering, stale market data, price or limit rejection, kill-switch activation, and balance or position drift. The monitored set includes settlement breaks, failed reversals, and aged reconciliation exceptions; telemetry has bounded labels and sensitive fields.",
        ),
    },
}
PAYMENT_CHECKLIST_RULE_COUNT = 27
PAYMENT_REFERENCE_PREFIX = "src/domain-extensions/payment-trading-extension/references/"
PAYMENT_TYPE_OUTPUTS = {
    "financial-role-and-state-authority.md": ("targeted", ("boundary-decision", "residual-risk")),
    "raw-card-custody-evidence.md": ("evidence-pattern", ("evidence-record", "proof-limit", "residual-risk")),
    "non-custodial-sensitive-data-boundary.md": ("targeted", ("boundary-decision", "proof-limit", "residual-risk")),
    "duplicate-financial-effect-control.md": ("targeted", ("selected-approach", "residual-risk")),
    "owned-financial-state-accounting-and-balances.md": ("targeted", ("decision-record", "residual-risk")),
    "trading-order-execution-and-identity.md": ("targeted", ("decision-record", "failure-decision", "residual-risk")),
    "market-data-and-trading-risk-controls.md": ("targeted", ("selected-approach", "failure-decision", "residual-risk")),
    "venue-product-monetary-and-calendar-contracts.md": ("targeted", ("decision-record", "residual-risk")),
    "provider-venue-event-authentication.md": ("targeted", ("boundary-decision", "residual-risk")),
    "financial-reconciliation-and-monitoring.md": ("targeted", ("decision-record", "validation-plan", "residual-risk")),
}
PAYMENT_UNCHANGED_REFERENCE_HASHES = {
    "duplicate-financial-effect-control.md": "9a43e04a4268d8f13fdfd5ea084f6c07f5abdb3239ad05fe70cd95263542d3f0",
    "financial-reconciliation-and-monitoring.md": "90496b522815975b6954133963ea387788c9b6ee73f204e24d1316eb18ab1ea6",
    "financial-role-and-state-authority.md": "b889b753b69c90644553d6d005e773db8de745220b38153b9dd14b774017bc68",
    "market-data-and-trading-risk-controls.md": "2989a69a1e7cdd45a17e6c442afa0b28515de2e87c0ac512ee0bf060e1db7d2c",
    "non-custodial-sensitive-data-boundary.md": "1fe519ee8e63e8ef417e987cd41d2f82491bec734cf652402bcca6058568aa3e",
    "owned-financial-state-accounting-and-balances.md": "bc65a28287ce8b5e00129561b8a8b9db8f4faa55ff293e5c34c3eee4eb85c545",
    "provider-venue-event-authentication.md": "2c9f2717a5a27e1f0631529a35757da3c44383ad469487127c5068e06249101a",
    "trading-order-execution-and-identity.md": "f4fcdceb7c01c0834aa37a542f79ab0f3844503587b89f6e57e63acf4919bc8d",
    "venue-product-monetary-and-calendar-contracts.md": "fd3b14587bbb72620e86fbc1232cd1a96df392dfba681a41b882cdd912b77a4b",
}
PAYMENT_RAW_CARD_RULES_SHA256 = (
    "cac8919e5c80e9a89c038df16817e5d9ea02ce0c5bde2f5738ddcca0868a5c12"
)
PAYMENT_RAW_CARD_SUCCESSOR_SHA256 = (
    "cd268c13cb95a162894e4db110df4c76b9bf2c5e0ebdb844b96c4ad193b17d13"
)

WEB3_ROOT_PREDECESSOR_SHA256 = (
    "00cd821a80adc03b08f46e2bc6ef5b0f8d9f5175eef4b1b14bca564e46c5be5a"
)
WEB3_CHECKLIST_PREDECESSOR_SHA256 = (
    "e8cb068ad8db55389dd63099f19a89dab260ea1bc5d5a5b2af5a2d7dd77ced3a"
)
WEB3_ROOT_PATH = "src/domain-extensions/web3-product-extension/SKILL.md"
WEB3_REFERENCE_PREFIX = "src/domain-extensions/web3-product-extension/references/"

WEB3_CUSTODY_PREDECESSOR_RULE = (
    "- **Bind key controls to custody**: non-custodial secrets never reach application servers or logs. Approved custody proves generation, isolation, recovery, rotation, and audit boundaries."
)
WEB3_CUSTODY_SUCCESSOR_RULE = (
    "- **Bind key controls to custody**: when the selected custody model is non-custodial, require evidence that custody secrets never reach application servers or logs. Approved custody proves generation, isolation, recovery, rotation, and audit boundaries."
)
WEB3_ROOT_RULE_SUCCESSOR_OVERRIDES = {
    WEB3_CUSTODY_PREDECESSOR_RULE: WEB3_CUSTODY_SUCCESSOR_RULE,
}
WEB3_RETIRED_SEMANTIC_CANDIDATE_ID = (
    "ae6a1910bca8a62a947f85887097667ee1f608cbeabcfcf52943d17f430bf8ce"
)

WEB3_ROOT_RULES = {
    "custody-and-chain-transactions.md": (
        WEB3_CUSTODY_PREDECESSOR_RULE,
        "- **Confirm irreversible intent before submission**: expose chain, asset, target, authority, amount, fees, and consequence. Scale confirmation and simulation to value and reversibility.",
        "- **Bind off-chain authorization**: signatures commit to action, domain, network, verifier, nonce, expiry, and version when relevant.",
        "- **Protect price-dependent actions**: prove oracle authority, freshness, manipulation cost, and fail-safe behavior.",
        "- **Derive oracle windows from evidence**: use current market behavior instead of a preset duration.",
        "- **Reconcile indexers to canonical state**: off-chain authorization or balances account for confirmation depth, reorg, replay, and finality.",
        "- replay succeeds because authorization omits domain or nonce binding",
        "- custody recovery bypasses normal signing controls",
        "- a fresh oracle remains economically manipulable",
        "- an indexer reports state removed by reorganization",
    ),
    "monitoring-and-independent-assurance.md": (
        "- **Scale independent assurance to exposure**: select review and verification depth from value, novelty, privilege, attack surface, and recoverability.",
    ),
    "upgrades-and-deployed-behavior.md": (
        "- **Use deployed arithmetic semantics**: prove overflow, precision, scaling, rounding, and exceptional arithmetic against the deployed compiler and assets.",
    ),
    "verification-evidence.md": (),
    "governance-authority.md": (
        "- an upgrade or bridge key concentrates loss exposure",
    ),
    "allowances-nonstandard-assets-and-delegated-calls.md": (
        "- **Protect external-call invariants**: prove state or value cannot be reused or observed inconsistently across reentrant calls.",
    ),
    "account-and-cross-domain-execution.md": (),
}

WEB3_CHECKLIST_RULES = {
    "custody-and-chain-transactions.md": (
        "- Keep private keys, seed phrases, signing secrets, and recovery material inside the declared custody boundary and outside diagnostics. Prove non-custodial user secrets do not reach application servers.",
        "- Derive custodial storage, signing, backup, recovery, and access controls from the selected custody model.",
        "- Record chain, network, contract, code, asset, wallet, custody, privileged authority, and their change sources. Treat aliases, forks, proxies, and environments as explicit mappings, and define mismatch behavior with recovery evidence.",
        "- Bind signatures to human-meaningful intent, chain or domain, verifier, actor, asset, amount or effect, replay state, validity, protocol version, and signer-verifiable approval evidence.",
        "- Model reachable transaction states across prepared, submitted, pending, confirmed, failed, reverted, dropped, replaced, finalized, and reorganized outcomes. The lifecycle covers confirmation evidence, reorg rollback or replay, and user-visible recovery.",
        "- Define submission uniqueness, nonce ownership, retry, unknown results, replacement and cancellation races, and result reuse. The contract spans clients, relayers, wallets, and backends without assuming one idempotency mechanism.",
        "- Derive fees, resource estimates, replacement or cancellation economics, timeout, confirmation depth, finality, slippage, deadlines, quote freshness, extractable-value exposure, gas griefing, and work ceilings. Target-chain behavior and user loss govern the result. Oracle-dependent behavior records current authority, freshness-window evidence, manipulation controls, and fail-safe behavior.",
        "- Define reconciliation across canonical chain state, receipts, logs, wallet or custody records, backend state, caches, and indexers. The contract covers lag, missed ranges, forks, replay, deletion, and authoritative rebuild behavior.",
        "- Derive ownership, transfer, delegation, lock, escrow, custody, and stale-index decisions from current chain state and contract semantics. Asset authority remains distinct from UI or indexer visibility.",
    ),
    "monitoring-and-independent-assurance.md": (
        "- Monitor task-selected signing, submission, revert, replacement, finality, indexer, bridge, upgrade, governance, oracle, and custody failures.",
        "- Record safe fields, authority, alert ownership, response action, and explicit telemetry gaps in one record for each selected signal.",
        "- Scale independent assurance with exposure.",
        "- Record the assurance owner, reviewed artifact, evidence freshness, and proof limits in one independent-assurance record.",
        "- Avoid asserting audit completion from independent-assurance evidence.",
    ),
    "upgrades-and-deployed-behavior.md": (
        "- Prove storage-layout compatibility plus authorized and denied initializer or reinitializer behavior for an upgrade.",
        "- Prove migration order and upgrade recovery behavior.",
        "- Record deployed code/configuration identity with distinct proxy-admin and implementation ownership.",
        "- Bind arithmetic, compiler, VM, asset-scale, and rounding semantics to the recorded deployed identity.",
    ),
    "verification-evidence.md": (
        "- Bind each claim to chain/network, contract address, runtime bytecode, proxy/implementation, configuration, block/deployment reference, and freshness.",
        "- Trace source/build lineage through compiler settings, artifact, deployment transaction, and current bytecode, with unverified links recorded as proof limits.",
        "- For upgrades, compare old and new storage layouts from the bound build artifacts. Exercise authorized, denied, repeated, and out-of-order initializer paths plus migration and recovery order in a chain fork or equivalent simulation.",
        "- For transaction and invariant behavior, record the property, scenario, command or test, environment and block, actual result, and owner. Include applicable reorg, replay, nonce, replacement, unknown-outcome, arithmetic, and external-call cases.",
        "- For oracles and bridges, exercise trust-model-selected stale, manipulation, outage, delayed-finality, challenge, replay, duplicate, relayer/validator, and destination-completion cases.",
        "- For custody and recovery, bind generation, storage, signing, authorization, denial, rotation, backup, recovery, and audit evidence without retaining secrets.",
        "- Record production, chain-condition, economic-manipulation, audit, and privileged-actor limits for local tests, forks, simulations, source verification, and captured chain state.",
    ),
    "governance-authority.md": (
        "- For governance, bind delegation, snapshot, quorum, proposal, cancellation, execution, timelock, emergency or bypass paths, pause, and recovery authority to current contracts and blast radius.",
    ),
    "allowances-nonstandard-assets-and-delegated-calls.md": (
        "- Define the scope of each allowance, permit, approval, or delegated spend.",
        "- Define its nonce or replay state.",
        "- Define validity and revocation behavior.",
        "- Define its spender-change behavior.",
        "- Define its residual authority behavior.",
        "- Account for callbacks, hooks, fees, rebasing, return differences, and other nonstandard asset semantics.",
        "- Cover reentrancy across callbacks in delegated-call evidence.",
        "- Reject reuse of state or value assumptions after external control returns.",
    ),
    "account-and-cross-domain-execution.md": (
        "- For account abstraction or intent execution, define account, entry-point, bundler, paymaster, solver, and sponsor authority. The boundary covers simulation, signature, nonce, policy, fees, validity, sponsorship, delegated effects, censorship, absent actors, malicious quotes, and substituted execution.",
        "- For bridge, L2-settlement, or cross-domain messages, define source and destination finality, sequencer and challenge-window behavior, proof and message identity, and validator or relayer trust. The contract covers replay binding, duplicate control, reorg recovery, reconciliation, and distinct destination-completion evidence.",
    ),
}

WEB3_REFERENCE_SPECS = {
    "custody-and-chain-transactions.md": {
        "type": "targeted",
        "required_output": ("boundary-decision", "selected-approach", "failure-decision", "residual-risk"),
        "load_when": "custody, signing, chain transaction, finality, oracle, indexer, or asset-authority behavior needs a decision",
        "do_not_load_when": "hash or signature terminology appears without chain or custody behavior",
        "gap_class": "route-or-material-unknown",
        "route_affecting_surfaces": ("primary-professional-skill", "layer3", "domain", "acceptance", "scope", "material-risk-floor"),
    },
    "monitoring-and-independent-assurance.md": {
        "type": "targeted",
        "required_output": ("decision-record", "validation-plan", "proof-limit", "residual-risk"),
        "load_when": "selected Web3 failure monitoring, response, or independent-assurance scope is open",
        "do_not_load_when": "no Web3 monitoring, response, or assurance claim exists",
        "gap_class": "repo-resolvable-fact",
        "route_affecting_surfaces": ("acceptance", "scope", "material-risk-floor"),
    },
    "upgrades-and-deployed-behavior.md": {
        "type": "targeted",
        "required_output": ("release-decision", "residual-risk"),
        "load_when": "contract upgrade, storage migration, deployed identity, or arithmetic behavior is open",
        "do_not_load_when": "deployed code, configuration, upgrade, storage, and arithmetic behavior are unchanged",
        "gap_class": "route-or-material-unknown",
        "route_affecting_surfaces": ("primary-professional-skill", "layer3", "domain", "acceptance", "scope", "material-risk-floor"),
    },
    "verification-evidence.md": {
        "type": "evidence-pattern",
        "required_output": ("evidence-record", "validation-plan", "proof-limit", "residual-risk"),
        "load_when": "a Web3 claim needs source, build, deployment, fork-simulation, chain-state, or proof-limit closure",
        "do_not_load_when": "no Web3 claim or evidence decision exists",
        "gap_class": "repo-resolvable-fact",
        "route_affecting_surfaces": ("acceptance", "scope", "material-risk-floor"),
    },
    "governance-authority.md": {
        "type": "targeted",
        "required_output": ("boundary-decision", "residual-risk"),
        "load_when": "on-chain governance, privileged upgrade, or bridge authority is open",
        "do_not_load_when": "governance, privileged upgrade, and bridge authority are unchanged",
        "gap_class": "route-or-material-unknown",
        "route_affecting_surfaces": ("primary-professional-skill", "layer3", "domain", "acceptance", "scope", "material-risk-floor"),
    },
    "allowances-nonstandard-assets-and-delegated-calls.md": {
        "type": "targeted",
        "required_output": ("boundary-decision", "failure-decision", "residual-risk"),
        "load_when": "allowance, permit, approval, delegated spend, nonstandard asset, callback, or reentrancy behavior is open",
        "do_not_load_when": "none of those allowance, delegated-call, nonstandard-asset, callback, or reentrancy behaviors changes",
        "gap_class": "route-or-material-unknown",
        "route_affecting_surfaces": ("layer3", "domain", "acceptance", "scope", "material-risk-floor"),
    },
    "account-and-cross-domain-execution.md": {
        "type": "targeted",
        "required_output": ("boundary-decision", "failure-decision", "residual-risk"),
        "load_when": "account abstraction, intent, bridge, L2 settlement, or cross-domain authority is open",
        "do_not_load_when": "none of account abstraction, intent, bridge, L2 settlement, or cross-domain authority changes",
        "gap_class": "route-or-material-unknown",
        "route_affecting_surfaces": ("primary-professional-skill", "layer3", "domain", "acceptance", "scope", "material-risk-floor"),
    },
}
WEB3_REFERENCE_HEADINGS = {
    "custody-and-chain-transactions.md": "# Custody and Chain Transactions",
    "monitoring-and-independent-assurance.md": "# Monitoring and Independent Assurance",
    "upgrades-and-deployed-behavior.md": "# Upgrades and Deployed Behavior",
    "verification-evidence.md": "# Verification Evidence Pattern",
    "governance-authority.md": "# Governance Authority",
    "allowances-nonstandard-assets-and-delegated-calls.md": "# Allowances, Nonstandard Assets, and Delegated Calls",
    "account-and-cross-domain-execution.md": "# Account and Cross-Domain Execution",
}
WEB3_CHECKLIST_RULE_COUNT = 50

BIGDATA_ROOT_PREDECESSOR_SHA256 = (
    "771eaabcb4dd6e8b6ed524edcfffa627b56335701f5015388e3aa657cf0e8e23"
)
BIGDATA_CHECKLIST_PREDECESSOR_SHA256 = (
    "dbc8522a0e455a539880a1f94e7735b65a737ca3433f8acdcc216cbab2fe10d0"
)
BIGDATA_ROOT_PATH = "src/domain-extensions/bigdata-product-extension/SKILL.md"
BIGDATA_REFERENCE_PREFIX = "src/domain-extensions/bigdata-product-extension/references/"
BIGDATA_CONSUMER_OLD_RULE = (
    "**Prove consumer compatibility**: verify every active consumer can read the deployed schema transition."
)
BIGDATA_CONSUMER_NEW_RULE = (
    "**Prove consumer compatibility**: verify that active consumers in the current source-backed inventory can read the deployed schema transition, with inventory gaps recorded as a blocking proof limit."
)
BIGDATA_REFERENCE_SPECS = {
    "consumer-and-schema-contracts.md": {
        "heading": "# Consumer and Schema Contracts",
        "load_when": "distributed consumer, schema, grain, metric meaning, correction, or compatibility is open",
        "do_not_load_when": "the task changes one database table without a distributed pipeline or replay boundary",
        "gap_class": "route-or-material-unknown",
        "route_affecting_surfaces": (
            "primary-professional-skill",
            "layer3",
            "domain",
            "acceptance",
            "scope",
            "material-risk-floor",
        ),
        "required_output": ("boundary-decision", "decision-record", "residual-risk"),
        "rules": (
            BIGDATA_CONSUMER_NEW_RULE,
            "Identify authoritative source systems, sinks, owners, freshness contracts, classified fields, and downstream consumers for affected assets.",
            "Make metric meaning explicit: grain, dimensions, filters, time-zone and calendar rules, aggregation, correction, and consumer-visible null or default behavior.",
            "Separate structural compatibility from semantic consumer compatibility. Treat changes to grain, meaning, units, defaults, ordering, or correction as contract changes, and cover active readers plus replay within the compatibility window.",
        ),
    },
    "pipeline-replay-and-event-identity.md": {
        "heading": "# Pipeline, Replay, and Event Identity",
        "load_when": "batch, stream, CDC, event-time, checkpoint, replay, backfill, or writer coexistence is open",
        "do_not_load_when": "no pipeline, replay, backfill, checkpoint, or writer-coexistence decision exists",
        "gap_class": "route-or-material-unknown",
        "route_affecting_surfaces": (
            "primary-professional-skill",
            "layer3",
            "domain",
            "acceptance",
            "scope",
            "material-risk-floor",
        ),
        "required_output": (
            "boundary-decision",
            "decision-record",
            "failure-decision",
            "residual-risk",
        ),
        "rules": (
            "Define batch, stream, snapshot, incremental CDC, full-refresh, and hybrid boundaries, including the snapshot-to-log cutover position, transaction ordering, handoff, checkpoint, recovery, and authoritative output.",
            "When event time or delayed or corrected events affect correctness, choose event-time authority, clock semantics, watermark, allowed lateness, finalization, and correction behavior. Replay and consumer requirements bound retraction and retention.",
            "Define event identity, partition ordering, deduplication, checkpoint commit, retry, and replay semantics. For CDC, preserve transaction boundaries, tombstones, and deletion propagation. Scope exactly-once claims to named engine or storage boundaries and close external side-effect crash windows.",
            "Assign writer ownership across live processing, backfill, correction, and replay. Define precedence, interruption, resume, overlap detection, and reconciliation so resumed work cannot overwrite a later authoritative correction.",
        ),
    },
    "quality-lineage-and-point-in-time-correctness.md": {
        "heading": "# Quality, Lineage, and Point-in-Time Correctness",
        "load_when": "quality, failed-data, lineage, point-in-time, leakage, or experiment semantics is open",
        "do_not_load_when": "no quality, lineage, point-in-time, leakage, or experiment decision exists",
        "gap_class": "repo-resolvable-fact",
        "route_affecting_surfaces": ("acceptance", "scope", "material-risk-floor"),
        "required_output": (
            "decision-record",
            "failure-decision",
            "validation-plan",
            "residual-risk",
        ),
        "rules": (
            "Preserve point-in-time correctness for mutable dimensions and features without temporal leakage, using backfill and live-coexistence validation against authoritative totals and representative historical snapshots.",
            "Define quality invariants for completeness, uniqueness, validity, referential integrity, distributions, row counts, and semantic drift. Consumer impact and replay capability determine failed-data disposition.",
            "Record lineage from source and schema through transformation, storage, dashboard, model, and API consumers, owner, deployment version, and recovery evidence.",
        ),
    },
    "storage-performance-and-recovery.md": {
        "heading": "# Storage, Performance, and Recovery",
        "load_when": "partition, storage, metadata, recovery, skew, state, memory, compute, or cost is open",
        "do_not_load_when": "no storage, recovery, resource, performance, or cost decision exists",
        "gap_class": "repo-resolvable-fact",
        "route_affecting_surfaces": ("acceptance", "scope", "material-risk-floor"),
        "required_output": (
            "selected-approach",
            "failure-decision",
            "validation-plan",
            "residual-risk",
        ),
        "rules": (
            "For partitioned, file-based, table-format, or stateful processing, derive keys, layout, compaction, metadata and manifest lifecycles, and state evolution. Observed cardinality, access, skew, small-file growth, and state-store growth constrain the choice.",
            "Prove metadata, manifests, snapshots, or checkpoints are recoverable before claiming the data files are restorable.",
            "Inspect representative joins, repartitioning, scans, state, spill, memory, storage, and compute cost as evidence for pruning, clustering or indexing, retention, compaction, and query controls.",
        ),
    },
    "observability-and-privacy.md": {
        "heading": "# Observability and Privacy",
        "load_when": "pipeline signals or classified samples, logs, failed data, exports, retention, or deletion is open",
        "do_not_load_when": "no pipeline-observability or classified-data handling decision exists",
        "gap_class": "route-or-material-unknown",
        "route_affecting_surfaces": (
            "primary-professional-skill",
            "layer3",
            "domain",
            "acceptance",
            "scope",
            "material-risk-floor",
        ),
        "required_output": ("boundary-decision", "validation-plan", "residual-risk"),
        "rules": (
            "Monitor freshness, lag, volume, bad records, task failure, state or partition growth, replay or backfill progress, correction debt, quality drift, and cost. Each signal has bounded labels, an alert owner, and a recovery action.",
            "Apply data classification to samples, logs, dead-letter or quarantine records, temporary storage, exports, and human-review or evaluation stores. Applicable policy and debugging needs determine access, retention, deletion, masking, tokenization, isolation, or exclusion.",
        ),
    },
}
BIGDATA_CHECKLIST_RULE_COUNT = 16

LOW_LEVEL_ROOT_PREDECESSOR_SHA256 = (
    "814bfc94dd8f1619a93d7f7e0bda2573a97d27c12b635436c80223dd44eb8855"
)
LOW_LEVEL_CHECKLIST_PREDECESSOR_SHA256 = (
    "bc09969d78fa85fe4c22c97984263aa95414b8fa2379f9524af13a58153aa3f9"
)
LOW_LEVEL_ROOT_PATH = "src/domain-extensions/low-level-systems-extension/SKILL.md"
LOW_LEVEL_REFERENCE_PREFIX = "src/domain-extensions/low-level-systems-extension/references/"
LOW_LEVEL_REFERENCE_SPECS = {
    "ownership-and-concurrency-contracts.md": {
        "heading": "# Ownership and Concurrency Contracts",
        "preface": "Use this Reference only for the named low-level ownership-and-concurrency-contracts decision.",
        "type": "targeted",
        "load_when": "native ownership, lifetime, unsafe preconditions, lock ordering, scheduling, or concurrency proof is open",
        "do_not_load_when": "no native ownership, unsafe boundary, lock ordering, scheduling, or concurrency decision exists",
        "gap_class": "route-or-material-unknown",
        "route_affecting_surfaces": (
            "primary-professional-skill",
            "layer3",
            "domain",
            "acceptance",
            "scope",
            "material-risk-floor",
        ),
        "required_output": (
            "boundary-decision",
            "failure-decision",
            "proof-limit",
            "residual-risk",
        ),
        "rules": (
            "- Define ownership, lifetime, allocation and deallocation pairing, aliasing, bounds, initialization, and unsafe-code preconditions across functions, threads, processes, languages, callbacks, and kernel boundaries.",
            "- Map threads, locks, lock nesting, scheduler and priority behavior, ownership transfer, shutdown, deadlock, starvation, and priority inversion on reachable success and failure paths.",
            "- A deadlock-freedom argument covers reachable reentrancy, callbacks, cancellation, cleanup, and teardown through an acyclic lock order. Runtime stress is corroborating evidence; untested schedules remain residual risk.",
        ),
    },
    "abi-platform-and-syscall-contracts.md": {
        "heading": "# ABI, Platform, and Syscall Contracts",
        "preface": "Use this Reference only for the named low-level abi-platform-and-syscall-contracts decision.",
        "type": "targeted",
        "load_when": "ABI representation, deployed consumers, target platform, syscall, privilege, sandbox, or partial I/O is open",
        "do_not_load_when": "C++ or Rust is mentioned without a native ABI OS or resource boundary",
        "gap_class": "route-or-material-unknown",
        "route_affecting_surfaces": (
            "primary-professional-skill",
            "layer3",
            "domain",
            "acceptance",
            "scope",
            "material-risk-floor",
        ),
        "required_output": ("boundary-decision", "failure-decision", "residual-risk"),
        "rules": (
            "- Make ABI representation explicit: calling convention, symbol and version contract, struct and union layout, packing, alignment, padding, bit fields, endianness, word size, and serialization compatibility for deployed consumers.",
            "- Cover supported OS, architecture, compiler, runtime, filesystem, network-stack, privilege, and permission differences that affect behavior or compatibility.",
            "- Handle partial I/O, interruption, would-block results, timeout, cancellation, error mapping, kernel and user length validation, privilege changes, and sandbox behavior under its syscall contract.",
        ),
    },
    "resource-lifecycle-and-error-contracts.md": {
        "heading": "# Resource Lifecycle and Error Contracts",
        "preface": "Use this Reference only for the named low-level resource-lifecycle-and-error-contracts decision.",
        "type": "targeted",
        "load_when": "native resource lifecycle, partial initialization, error translation, retry, diagnostics, or recovery is open",
        "do_not_load_when": "no native resource, error, diagnostic, retry, or recovery decision exists",
        "gap_class": "repo-resolvable-fact",
        "route_affecting_surfaces": ("acceptance", "scope", "material-risk-floor"),
        "required_output": ("decision-record", "failure-decision", "residual-risk"),
        "rules": (
            "- Track acquisition, transfer, exhaustion, and release of descriptors, sockets, handles, memory, threads, timers, mappings, temporary files, and kernel objects across partial initialization and shutdown.",
            "- Preserve causal diagnostics and protocol state across error translation and retry while excluding secrets and invalid or partially initialized data.",
        ),
    },
    "performance-and-verification-evidence.md": {
        "heading": "# Performance And Verification Evidence Pattern",
        "preface": "Use this evidence-pattern Reference only for the named low-level performance-and-verification evidence decision.",
        "type": "evidence-pattern",
        "load_when": "low-level performance, measurement, validation, absence, or post-edit evidence needs closure",
        "do_not_load_when": "no low-level performance, validation, evidence, or absence claim is open",
        "gap_class": "repo-resolvable-fact",
        "route_affecting_surfaces": ("acceptance", "scope", "material-risk-floor"),
        "required_output": (
            "evidence-record",
            "validation-plan",
            "proof-limit",
            "residual-risk",
        ),
        "rules": (
            "- Tie optimization to a representative workload, baseline, variance, resource budget, and regression decision; preserve correctness, ABI, and tail behavior while changing structure.",
            "- Select sanitizer, fuzz, race, stress, boundary, fault-injection, platform-matrix, and leak evidence from reachable undefined behavior, concurrency, parser, ABI, and resource risks.",
            "- Absence claims bind diagnostics to a supported compiler/target/build matrix and stated state space. Unproved inputs, schedules, platforms, and foreign-code behavior remain residual risk.",
            "- Observe actionable crashes, panics, assertions, latency, throughput, memory, descriptor or handle pressure, retries, and recovery outcomes without exposing unsafe memory or secrets.",
        ),
    },
    "signals-ffi-atomics-shared-memory-and-fork.md": {
        "heading": "# Signals, FFI, Atomics, Shared Memory, and Fork",
        "preface": "Use this Reference only for the named low-level signals-ffi-atomics-shared-memory-and-fork decision.",
        "type": "targeted",
        "load_when": "signal, interrupt, FFI, unwind, atomic, shared-memory, DMA, fork, cancellation, or abnormal-error behavior is open",
        "do_not_load_when": "none of those signal, FFI, atomic, shared-memory, fork, cancellation, or abnormal-error behaviors changes",
        "gap_class": "route-or-material-unknown",
        "route_affecting_surfaces": (
            "primary-professional-skill",
            "layer3",
            "domain",
            "acceptance",
            "scope",
            "material-risk-floor",
        ),
        "required_output": (
            "boundary-decision",
            "selected-approach",
            "failure-decision",
            "proof-limit",
            "residual-risk",
        ),
        "rules": (
            "- For signal or interrupt contexts, identify platform-permitted operations, reentrancy, nesting or masking, deferred-work handoff, publication ordering, interrupted-state cleanup, and termination behavior. The contract reflects the target runtime and platform.",
            "- At FFI and callback boundaries, contain panic, exception, and unwind behavior. The cross-runtime contract defines allocator pairing, ownership transfer, thread affinity, callback registration and revocation, context lifetime, and error translation.",
            "- For atomics or shared memory, justify the selected memory order with required happens-before and publication relationships.",
            "- For shared memory or DMA, define alignment, coherency, CPU and device ordering, producer and consumer ownership, visibility, and buffer lifetime.",
            "- For fork, cancellation, or abnormal errors, define permitted continuation and cleanup or rollback ownership from inherited runtime, lock, thread, allocator, handle, and resource state. Evidence covers leaks, deadlock, double release, and use after lifetime end.",
        ),
    },
}
LOW_LEVEL_CHECKLIST_RULE_COUNT = 17

V7_COMPACTION_RECORDS = (
    {
        "owner": "platform-infrastructure-change-builder",
        "path": "src/professional-skills/platform-infrastructure-change-builder/SKILL.md",
        "old_content_sha256": "1ec8055d19eb721b50882644a12a723739d214224f5be300ba2d6010bfc111db",
        "new_content_sha256": "a679dc02672433337f8a7788454ed5b704744a3debcbcda97adf745cd00740ed",
        "classification": "always-kernel-compaction",
        "disposition": "compacted-in-place",
        "required_by": ("task-agent",),
        "required_output": ("changed-source", "proposal-evidence", "proof-limit", "release-boundary"),
        "new_anchor": "Separate state layers; change the smallest owner; bind secret-free non-mutating proposal evidence to target and versions.",
        "preserved_facets": ("Treat proposal evidence as non-authorizing unless separate production-mutation authority is confirmed.", "smallest owner", "non-mutating", "delivery-release-gate"),
        "co_trigger_effect": "unchanged",
        "route_effect": "unchanged",
        "validation": "fixed-content-hash-and-preserved-kernel",
        "proof_limit": "static source projection; live infrastructure is unobserved",
    },
    {
        "owner": "dependency-vulnerability-scanning",
        "path": "src/foundation/capabilities/dependency-vulnerability-scanning/SKILL.md",
        "old_content_sha256": "886f9be0313d642304a71776194de055084f74784626cc992142ce1350f1a26d",
        "new_content_sha256": "936703222d41977c6ba50f5832b729acc778a36f610f38cde7070206abe346c1",
        "classification": "always-kernel-compaction",
        "disposition": "compacted-in-place",
        "required_by": ALL_ROLES,
        "required_output": ("dependency-risk-decision", "proof-limit", "residual-risk"),
        "new_anchor": "Resolve graph/origin/license/remediation/exception/artifact scope; labels do not decide risk.",
        "preserved_facets": ("graph risk", "package-dependency-management", "supply-chain risk", "material risk"),
        "co_trigger_effect": "unchanged",
        "route_effect": "unchanged",
        "validation": "fixed-content-hash-and-preserved-kernel",
        "proof_limit": "root kernel only; conditional details remain JIT References",
    },
    {
        "owner": "infrastructure-as-code-safety",
        "path": "src/foundation/capabilities/infrastructure-as-code-safety/SKILL.md",
        "old_content_sha256": "fa720acbe2805592be2b0ac43022bd3b17fd028164a6aacf0c7c48961f1f8b31",
        "new_content_sha256": "ece9b4accd40549bf15895779777262449a3846fdc3923d5ac1d3a5178b3e5c1",
        "classification": "always-kernel-compaction",
        "disposition": "compacted-in-place",
        "required_by": ALL_ROLES,
        "required_output": ("decision-record", "proof-limit", "residual-risk"),
        "new_anchor": "Bind proposals to source/recorded/effective state, identity/effects/recovery, versions, and unknowns.",
        "preserved_facets": ("state/identity/destruction/recovery", "production mutation", "source rollback"),
        "co_trigger_effect": "unchanged",
        "route_effect": "unchanged",
        "validation": "fixed-content-hash-and-preserved-kernel",
        "proof_limit": "root kernel only; tool-specific decisions remain JIT",
    },
    {
        "owner": "powershell-professional-usage",
        "path": "src/foundation/capabilities/powershell-professional-usage/SKILL.md",
        "old_content_sha256": "bc8de586dfa6c9f055b6d4270c3039514ad1967de4af4d4e89d7a40ed42a3ad7",
        "new_content_sha256": "3d852f13fe931fff6cdabe7f6e0a157ac116d60bf5fbad855ae759d43fd8f329",
        "classification": "always-kernel-compaction",
        "disposition": "compacted-in-place",
        "required_by": TASK_FIRST_ROLES,
        "required_output": ("decision-record", "proof-limit", "residual-risk"),
        "new_anchor": "Bind runtime, remoting, provider, convergence, cleanup, repeat-run, and recovery semantics to both authorities.",
        "preserved_facets": ("actual edition/host", "text conversion", "command strings", "repeat-run"),
        "co_trigger_effect": "unchanged",
        "route_effect": "unchanged",
        "validation": "fixed-content-hash-and-preserved-kernel",
        "proof_limit": "root kernel only; PowerShell boundary details remain JIT",
    },
    {
        "owner": "ai-code-review-refactor",
        "path": "src/professional-skills/ai-code-review-refactor/SKILL.md",
        "old_content_sha256": "3e493585ff9f824532b6dd72f3ba6f26fa487fdd6aaece11d191678d97f6c603",
        "new_content_sha256": "2df1ba4fb910c602d5915900da27617ecb30f5661e92f25ca40af8d05ddc74ee",
        "classification": "always-kernel-compaction",
        "disposition": "compacted-in-place",
        "required_by": ("review-agent",),
        "required_output": ("review-result", "proof-limit", "residual-risk"),
        "new_anchor": "Judge every changed path in the actual latest diff within the fixed boundary.",
        "preserved_facets": ("independently reviewing", "non-mutating", "cannot reroute", "actual latest diff"),
        "co_trigger_effect": "unchanged",
        "route_effect": "unchanged",
        "validation": "fixed-content-hash-and-preserved-kernel",
        "proof_limit": "independent review remains downstream",
    },
    {
        "owner": "low-level-systems-extension",
        "path": "src/domain-extensions/low-level-systems-extension/SKILL.md",
        "old_content_sha256": "a6d264e4b57c434bf0dbf508d069ec8c95e7a06ce6193df2c9a717d2a7649c48",
        "new_content_sha256": "65ebb80c0eb62c2fa18a3f1bbfd7440e93096b179a70d1943a4acd27ad72c022",
        "classification": "always-kernel-compaction",
        "disposition": "compacted-in-place",
        "required_by": ALL_ROLES,
        "required_output": ("checklist-result", "residual-risk"),
        "new_anchor": "Preserve native ownership/lifetime, unsafe preconditions, ABI consumers, concurrency ordering, syscall/privilege, resource cleanup, arithmetic, and measured-performance invariants.",
        "preserved_facets": ("native or operating-system", "ABI consumers", "unproved schedules", "kernel/driver"),
        "co_trigger_effect": "unchanged",
        "route_effect": "unchanged",
        "validation": "fixed-content-hash-and-preserved-kernel",
        "proof_limit": "platform and schedule absence claims remain bounded",
    },
    {
        "owner": "code-review",
        "path": "src/foundation/capabilities/code-review/SKILL.md",
        "old_content_sha256": "f426938fa185119cc2840dd0093958659950359303bd1ee1741cc3ac704ff28b",
        "new_content_sha256": "8cc752ce9f23822e9b7eaab20e10eff995fb738965eaed9892b7384942913073",
        "classification": "always-kernel-compaction",
        "disposition": "compacted-in-place",
        "required_by": ("review-agent", "analysis-agent", "task-agent"),
        "required_output": ("review-result", "proof-limit", "residual-risk"),
        "new_anchor": "Trace consequential input, authority, mutation, effect, failure, cleanup, and output paths.",
        "preserved_facets": ("bounded latest diff", "Exclude mutation", "failure mechanism", "scope-blocker"),
        "co_trigger_effect": "unchanged",
        "route_effect": "unchanged",
        "validation": "fixed-content-hash-and-preserved-kernel",
        "proof_limit": "finding calibration remains in named JIT Reference",
    },
    {
        "owner": "regression-testing",
        "path": "src/foundation/capabilities/regression-testing/SKILL.md",
        "old_content_sha256": "2613b6c6aa94850a51069b62486a09b256be2aaeac4f461a7b0938cd9d5d0341",
        "new_content_sha256": "4c267275fad6956335102a12ac2066986459a0f8bd7b0c37da8c054d58507cbb",
        "classification": "always-kernel-compaction",
        "disposition": "compacted-in-place",
        "required_by": ALL_ROLES,
        "required_output": ("recurrence-map", "proof-limit", "residual-risk"),
        "new_anchor": "Preserve the causal trigger, fixture, observable failure, and real boundary.",
        "preserved_facets": ("accepted prior failure", "same-pattern", "Broad retry", "unsafe"),
        "co_trigger_effect": "unchanged",
        "route_effect": "unchanged",
        "validation": "fixed-content-hash-and-preserved-kernel",
        "proof_limit": "conditional recurrence detail remains JIT",
    },
    {
        "owner": "platform-infrastructure-change-builder",
        "path": "src/professional-skills/platform-infrastructure-change-builder/references/iac-source-contracts.md",
        "old_content_sha256": "aa64b963c62f87ff52416d4f912fc3941c057f83d08d88fc13aed0e50080900b",
        "new_content_sha256": "66e25bbe199f8e7ca2062fe4aa525d574f5eacb40a829e20c91e05b56add90dd",
        "classification": "conditional-reference-compaction",
        "disposition": "compacted-in-place",
        "required_by": ("task-agent",),
        "required_output": ("proof-limit", "selected-approach", "validation-plan"),
        "new_anchor": "Terraform, OpenTofu, Pulumi, and CloudFormation are non-equivalent.",
        "preserved_facets": V7_ACTIVE_REFERENCE_FACETS["src/professional-skills/platform-infrastructure-change-builder/references/iac-source-contracts.md"],
        "co_trigger_effect": "unchanged",
        "route_effect": "unchanged",
        "validation": "fixed-content-hash-and-preserved-facets",
        "proof_limit": "rolling sources do not prove live provider behavior",
    },
    {
        "owner": "code-review",
        "path": "src/foundation/capabilities/code-review/references/finding-taxonomy.md",
        "old_content_sha256": "f0e61f7a95172e9f0891c94dd07887fe05769f6214cf8c4e111f8a7837c0a93c",
        "new_content_sha256": "065914b8997d71de1b9ad096c19524125bf16354e659587e24d3e7ec882c974d",
        "classification": "conditional-reference-compaction",
        "disposition": "compacted-in-place",
        "required_by": ("review-agent", "analysis-agent", "task-agent"),
        "required_output": ("gate-decision", "residual-risk"),
        "new_anchor": "Do not manufacture severity from uncertainty.",
        "preserved_facets": V7_ACTIVE_REFERENCE_FACETS["src/foundation/capabilities/code-review/references/finding-taxonomy.md"],
        "co_trigger_effect": "unchanged",
        "route_effect": "unchanged",
        "validation": "fixed-content-hash-and-preserved-facets",
        "proof_limit": "taxonomy does not replace current policy or specialist authority",
    },
    {
        "owner": "api-contract-design",
        "path": "src/foundation/capabilities/api-contract-design/references/api-style-and-semantics.md",
        "old_content_sha256": "ca3f3e5921570932753c5d618561aa5995c8465b848e23f494a28bc8fbfd8678",
        "new_content_sha256": "fe369d8cda288b4ff1c3af6662a293bde838ce6a2d4e9e1897b853cbbd151673",
        "classification": "conditional-reference-compaction",
        "disposition": "compacted-in-place",
        "required_by": ALL_ROLES,
        "required_output": ("selected-approach", "residual-risk"),
        "new_anchor": "POST is not idempotent by default.",
        "preserved_facets": ("REST/JSON", "gRPC", "GraphQL", "Events and webhooks", "GET/HEAD", "PATCH", "Status Code Discipline", "Versioning Approach"),
        "co_trigger_effect": "unchanged",
        "route_effect": "unchanged",
        "validation": "fixed-content-hash-and-preserved-facets",
        "proof_limit": "style guidance does not establish a concrete API consumer contract",
    },
    {
        "owner": "security-privacy-gate",
        "path": "src/professional-skills/security-privacy-gate/references/security-output-and-gates.md",
        "old_content_sha256": "3907c01403cd301077cb058ab9b4186e4f00380a463f307da8c4514d46934e21",
        "new_content_sha256": "067ac9a3ae149ca3fc2572b1473ebbf5678e5eb3fc634267081a54c70968850a",
        "classification": "conditional-reference-compaction",
        "disposition": "compacted-in-place",
        "required_by": ALL_ROLES,
        "required_output": ("gate-decision", "residual-risk"),
        "new_anchor": "Trace attacker-controlled data and authority from entry point to asset, sink, and disclosure path.",
        "preserved_facets": SECURITY_RESTORED_RULES,
        "co_trigger_effect": "unchanged",
        "route_effect": "unchanged",
        "validation": "fixed-content-hash-and-preserved-facets",
        "proof_limit": "security gate remains conditional and source-static",
    },
)

C1I_RELOCATION_FINGERPRINT_NEW_ANCHORS = {
    "1ae0b3ba47c63c573eb804a40bd8bfdbe7faff88d97ab6aa97b408bf948cfdad": (
        "Broaden only for a concrete shared boundary or escape risk."
    ),
    "d4d5a5ae1512e87a04f1fc3f106d887daa187698b3a2091df7930be155f0d7bf": (
        "Add a level only for a distinct material mechanism, boundary, consumer, or oracle."
    ),
    "e3f309e234b073063dd57be201596e23e8ad111fc81556ba5a3c3f75aaa847a7": (
        "keep stale, partial, flaky, retried, and skipped evidence explicit for `quality-test-gate`."
    ),
    "1baca81dba632f8004f57d2276192ddbe74d7024f319a97603093775fb16119a": """## Anti-Patterns

Reject catalog-, coverage-, broad-suite-, mock-, or manual-only proof without a task-specific mechanism and oracle.""",
    "695bd3592647a61218d5f041b3c3ceb933753406b54929694601712ecb511ef7": (
        "Map each failure to the lowest capable boundary; retain device coverage for OS transitions."
    ),
    "090161109e5fafe86319cd760118fc6f3b390c91f8ef9e2f828d460d63a4922f": (
        "Prove update recovery through image validation, atomic activation, last-known-good boot, power-loss behavior, mixed-fleet compatibility, rollback, and offline recovery."
    ),
}


def _reference_binding(owner: str, destination: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
    if destination.endswith("/SKILL.md"):
        return FROZEN_REFERENCE_BINDINGS[destination]
    root = (ROOT / ROOT_PATHS[owner]).read_text(encoding="utf-8")
    relative = destination.removeprefix(str(Path(ROOT_PATHS[owner]).parent) + "/")
    needle = f"({relative})"
    matches = [line for line in root.splitlines() if line.startswith("|") and needle in line]
    if len(matches) != 1:
        raise AssertionError(f"expected one root binding for {destination}, got {len(matches)}")
    cells = [cell.strip() for cell in matches[0].split("|")]
    required_by = tuple(item.strip() for item in cells[5].split(",") if item.strip())
    required_output = tuple(item.strip() for item in cells[6].split(",") if item.strip())
    return required_by, required_output


def _ledger_entry(
    owner: str,
    old_anchor: str,
    destination: str,
    fingerprint: str,
    new_anchor: str | None = None,
    *,
    source_path: str | None = None,
    disposition: str = "relocated-existing-reference",
    decision_problem: str | None = None,
) -> dict[str, object]:
    required_by, required_output = FROZEN_REFERENCE_BINDINGS[destination]
    retained_anchor = new_anchor or NEW_ANCHOR_OVERRIDES.get(old_anchor, old_anchor)
    return {
        "owner": owner,
        "source_path": source_path or str(Path(destination).parents[1] / "SKILL.md"),
        "old_anchor": old_anchor,
        "source_rule_fingerprint": fingerprint,
        "classification": "conditional-decision-rule",
        "decision_problem": decision_problem or Path(destination).stem,
        "destination": destination,
        "required_by": required_by,
        "required_output": required_output,
        "new_anchor": retained_anchor,
        "disposition": disposition,
        "preserved_facets": (retained_anchor,),
        "co_trigger_effect": "unchanged",
        "route_effect": "unchanged",
        "validation": "root-absent-and-unique-destination-present",
        "proof_limit": "static source ownership; runtime load remains registry- and receipt-gated",
    }


RELOCATION_LEDGER = tuple(
    _ledger_entry(
        owner,
        old_anchor,
        destination,
        fingerprint,
        C1I_RELOCATION_FINGERPRINT_NEW_ANCHORS.get(fingerprint),
    )
    for (owner, old_anchor, destination), fingerprint in zip(
        MOVES + SECURITY_FRONTIER_MOVES,
        FROZEN_SOURCE_FINGERPRINTS,
        strict=True,
    )
) + tuple(_ledger_entry(*spec) for spec in V6_MOVE_SPECS) + tuple(
    _ledger_entry(*spec) for spec in V7_MOVE_SPECS
) + tuple(
    _ledger_entry(owner, old_anchor, destination, fingerprint)
    for (
        owner,
        old_anchor,
        fingerprint,
        destination,
        _required_by,
        _required_output,
    ) in G2_BASE_B0_MOVE_SPECS
) + tuple(
    _ledger_entry(
        owner,
        old_anchor,
        destination,
        fingerprint,
        G2_BASE_B1_FINGERPRINT_NEW_ANCHORS.get(
            fingerprint, G2_BASE_B1_NEW_ANCHORS.get(owner)
        ),
        source_path=(ROOT_PATHS[owner] if owner == "installed-client-change-builder" else None),
        disposition=(
            "returned-to-always-kernel-after-named-jit-split"
            if owner == "installed-client-change-builder"
            else "relocated-existing-reference"
        ),
    )
    for (
        owner,
        old_anchor,
        fingerprint,
        destination,
        _required_by,
        _required_output,
    ) in G2_BASE_B1_MOVE_SPECS
) + tuple(
    _ledger_entry(
        owner,
        old_anchor,
        destination,
        fingerprint,
        G2_BASE_B2_FINGERPRINT_NEW_ANCHORS.get(
            fingerprint, G2_BASE_B2_NEW_ANCHORS.get(old_anchor)
        ),
    )
    for (
        owner,
        old_anchor,
        fingerprint,
        destination,
        _required_by,
        _required_output,
    ) in G2_BASE_B2_MOVE_SPECS
) + tuple(
    _ledger_entry(
        owner,
        old_anchor,
        destination,
        fingerprint,
        G2_BASE_B3_FINGERPRINT_NEW_ANCHORS.get(fingerprint),
    )
    for (
        owner,
        old_anchor,
        fingerprint,
        destination,
        _required_by,
        _required_output,
    ) in G2_BASE_B3_MOVE_SPECS
) + tuple(
    _ledger_entry(
        owner,
        old_anchor,
        destination,
        fingerprint,
        G2_BASE_B4_FINGERPRINT_NEW_ANCHORS.get(fingerprint),
    )
    for (
        owner,
        old_anchor,
        fingerprint,
        destination,
        _required_by,
        _required_output,
    ) in G2_BASE_B4_MOVE_SPECS
) + tuple(
    _ledger_entry(
        owner,
        old_anchor,
        destination,
        fingerprint,
        C1I_RELOCATION_FINGERPRINT_NEW_ANCHORS.get(fingerprint),
    )
    for (
        owner,
        old_anchor,
        fingerprint,
        destination,
        _required_by,
        _required_output,
    ) in G2_BASE_B5_MOVE_SPECS
) + tuple(
    _ledger_entry(
        owner,
        old_anchor,
        destination,
        fingerprint,
        G2_BASE_B6_NEW_ANCHORS.get(fingerprint),
    )
    for (
        owner,
        old_anchor,
        fingerprint,
        destination,
        _required_by,
        _required_output,
    ) in G2_BASE_B6_MOVE_SPECS
) + tuple(
    _ledger_entry(owner, old_anchor, destination, fingerprint)
    for (
        owner,
        old_anchor,
        fingerprint,
        destination,
        _required_by,
        _required_output,
    ) in G2_BASE_B7_MOVE_SPECS
)+ tuple(
    {
        **_ledger_entry(owner, old_anchor, destination, fingerprint),
        "new_anchor": G2_BASE_B8_NEW_ANCHORS.get(fingerprint, old_anchor),
    }
    for (
        owner,
        old_anchor,
        fingerprint,
        destination,
        _required_by,
        _required_output,
    ) in G2_BASE_B8_MOVE_SPECS
) + tuple(
    _ledger_entry(
        "payment-trading-extension",
        rule,
        PAYMENT_REFERENCE_PREFIX + filename,
        _fingerprint(rule),
        source_path=PAYMENT_REFERENCE_PREFIX + "checklist.md",
        disposition="split-relocated-new-reference",
    )
    for filename, spec in PAYMENT_REFERENCE_SPECS.items()
    for rule in spec["rules"]
) + tuple(
    _ledger_entry(
        "web3-product-extension",
        rule,
        WEB3_REFERENCE_PREFIX + filename,
        _fingerprint(rule),
        new_anchor=WEB3_ROOT_RULE_SUCCESSOR_OVERRIDES.get(rule),
        source_path=WEB3_ROOT_PATH,
        disposition="split-relocated-new-reference",
    )
    for filename, rules in WEB3_ROOT_RULES.items()
    for rule in rules
) + tuple(
    _ledger_entry(
        "web3-product-extension",
        rule,
        WEB3_REFERENCE_PREFIX + filename,
        _fingerprint(rule),
        source_path=WEB3_REFERENCE_PREFIX + "checklist.md",
        disposition="split-relocated-new-reference",
    )
    for filename, rules in WEB3_CHECKLIST_RULES.items()
    for rule in rules
) + tuple(
    _ledger_entry(
        "bigdata-product-extension",
        rule,
        BIGDATA_REFERENCE_PREFIX + filename,
        _fingerprint(rule),
        source_path=BIGDATA_REFERENCE_PREFIX + "checklist.md",
        disposition="split-relocated-new-reference",
    )
    for filename, spec in BIGDATA_REFERENCE_SPECS.items()
    for index, rule in enumerate(spec["rules"])
    if not (filename == "consumer-and-schema-contracts.md" and index == 0)
) + tuple(
    _ledger_entry(
        "low-level-systems-extension",
        rule.removeprefix("- "),
        LOW_LEVEL_REFERENCE_PREFIX + filename,
        _fingerprint(rule.removeprefix("- ")),
        source_path=LOW_LEVEL_REFERENCE_PREFIX + "checklist.md",
        disposition="split-relocated-new-reference",
    )
    for filename, spec in LOW_LEVEL_REFERENCE_SPECS.items()
    for index, rule in enumerate(spec["rules"])
    if not (filename == "ownership-and-concurrency-contracts.md" and index == 0)
) + tuple(
    _ledger_entry(
        owner,
        old_anchor,
        destination,
        fingerprint,
        new_anchor,
        source_path="src/professional-skills/installed-client-change-builder/references/framework-contracts.md",
        disposition="split-relocated-new-reference",
    )
    for owner, old_anchor, fingerprint, destination, new_anchor in C1_FRAMEWORK_MOVE_SPECS
) + tuple(
    _ledger_entry(
        owner,
        old_anchor,
        destination,
        fingerprint,
        FG_C1K_LANGUAGE_NEW_ANCHORS.get(fingerprint, new_anchor),
        source_path=ROOT_PATHS[owner],
        disposition="split-relocated-new-reference",
    )
    for owner, old_anchor, fingerprint, destination, new_anchor in C1_LANGUAGE_MOVE_SPECS
)


class ContextContentRelocationTests(unittest.TestCase):
    def test_g2_base_partition_matches_the_frozen_g1_frontier(self) -> None:
        batch_owners = {
            owner for owners in G2_BASE_BATCHES.values() for owner in owners
        }
        frontend_deltas = {
            "B1": len(FRONTEND_JIT_OWNER_SPECS["frontend-change-builder"]["references"])
            - len(FRONTEND_JIT_OWNER_SPECS["frontend-change-builder"]["removed"]),
            "B6": sum(
                len(spec["references"]) - len(spec["removed"])
                for owner, spec in FRONTEND_JIT_OWNER_SPECS.items()
                if owner != "frontend-change-builder"
            ),
        }
        self.assertEqual({"B1": 5, "B6": 13}, frontend_deltas)
        review_deltas = {
            "B1": sum(
                path not in {"references/checklist.md", "references/solution-optimality.md"}
                for path in REVIEW_JIT_OWNER_SPECS["architecture-impact-reviewer"]["references"]
            )
            - len(REVIEW_JIT_OWNER_SPECS["architecture-impact-reviewer"]["removed"]),
            "B4": sum(
                path != "references/benchmarks-and-enforcement.md"
                for path in REVIEW_JIT_OWNER_SPECS["module-boundary-design"]["references"]
            )
            - len(REVIEW_JIT_OWNER_SPECS["module-boundary-design"]["removed"]),
        }
        self.assertEqual({"B1": 3, "B4": 1}, review_deltas)
        self.assertEqual(233, sum(G2_BASE_EXPECTED_REFERENCE_COUNTS.values()))
        self.assertEqual(
            "43beb22720f6848259dfd28883e6cf52742de81660d78b53a65b87f0ffe9d08c",
            G2_BASE_MANIFEST_DIGEST,
        )
        self.assertEqual(82, len(batch_owners))
        self.assertEqual(
            86,
            len(batch_owners | G2_PHASE8_OWNERS),
        )
        selected_references: set[str] = set()
        for batch, owners in G2_BASE_BATCHES.items():
            with self.subTest(batch=batch):
                batch_references = set().union(
                    *(_g2_task_review_active_references(owner) for owner in owners)
                )
                self.assertEqual(
                    G2_BASE_EXPECTED_REFERENCE_COUNTS[batch]
                    + frontend_deltas.get(batch, 0)
                    + review_deltas.get(batch, 0),
                    len(batch_references),
                )
                self.assertTrue(selected_references.isdisjoint(batch_references))
                selected_references.update(batch_references)
        self.assertEqual(
            sum(G2_BASE_EXPECTED_REFERENCE_COUNTS.values())
            + sum(frontend_deltas.values())
            + sum(review_deltas.values()),
            len(selected_references),
        )

    def test_g2_base_batches_close_serially_from_b0(self) -> None:
        self.assertEqual(
            frozenset({"B0", "B1", "B2", "B3", "B4", "B5", "B6", "B7", "B8"}), G2_BASE_COMPLETED_BATCHES
        )

    def test_g2_foundation_roots_preserve_compiled_projection_kernel(self) -> None:
        for owners in G2_BASE_BATCHES.values():
            for owner in owners:
                root = _g2_owner_root(owner)
                if "/foundation/" not in root.as_posix():
                    continue
                text = root.read_text(encoding="utf-8")
                sections = re.findall(
                    r"## Anti-Patterns\n\n(?P<body>.*?)(?=\n## )",
                    text,
                    flags=re.DOTALL,
                )
                with self.subTest(owner=owner):
                    self.assertEqual(1, len(sections))
                    self.assertTrue(sections[0].strip())

    def test_g2_professional_roots_preserve_compiled_projection_kernel(self) -> None:
        required = (
            "Role",
            "When To Use",
            "Do Not Use",
            "Required Inputs",
            "Professional Decision Rules",
            "Stop / Escalation Conditions",
            "Output Contract",
        )
        for owners in G2_BASE_BATCHES.values():
            for owner in owners:
                root = _g2_owner_root(owner)
                if "/professional-skills/" not in root.as_posix():
                    continue
                text = root.read_text(encoding="utf-8")
                for heading in required:
                    sections = re.findall(
                        rf"## {re.escape(heading)}\n\n(?P<body>.*?)(?=\n## )",
                        text,
                        flags=re.DOTALL,
                    )
                    with self.subTest(owner=owner, heading=heading):
                        self.assertEqual(1, len(sections))
                        self.assertTrue(sections[0].strip())

    def test_g2_b0_relocation_ledger_is_frozen_and_lossless(self) -> None:
        b0_entries = tuple(
            entry
            for entry in RELOCATION_LEDGER
            if entry["owner"] in G2_BASE_BATCHES["B0"]
        )
        self.assertEqual(
            set(G2_BASE_BATCHES["B0"]),
            {entry["owner"] for entry in b0_entries},
        )
        self.assertEqual(11, len(b0_entries))
        expected_bindings = {
            (owner, destination): (required_by, required_output)
            for (
                owner,
                _old_anchor,
                _fingerprint,
                destination,
                required_by,
                required_output,
            ) in G2_BASE_B0_MOVE_SPECS
        }
        for entry in b0_entries:
            with self.subTest(
                owner=entry["owner"], destination=entry["destination"]
            ):
                self.assertEqual(LEDGER_FIELDS, set(entry))
                self.assertEqual(
                    entry["source_rule_fingerprint"],
                    _fingerprint(str(entry["old_anchor"])),
                )
                self.assertEqual(
                    "conditional-decision-rule", entry["classification"]
                )
                self.assertEqual(
                    Path(str(entry["destination"])).stem,
                    entry["decision_problem"],
                )
                self.assertTrue(entry["required_by"])
                self.assertTrue(entry["required_output"])
                self.assertEqual(
                    expected_bindings[(entry["owner"], entry["destination"])],
                    (entry["required_by"], entry["required_output"]),
                )
                self.assertEqual("unchanged", entry["co_trigger_effect"])
                self.assertEqual("unchanged", entry["route_effect"])
                root_text = (ROOT / str(entry["source_path"])).read_text(
                    encoding="utf-8"
                )
                destination_text = (ROOT / str(entry["destination"])).read_text(
                    encoding="utf-8"
                )
                self.assertNotIn(str(entry["old_anchor"]), root_text)
                self.assertEqual(
                    1, destination_text.count(str(entry["new_anchor"]))
                )
                for facet in entry["preserved_facets"]:
                    self.assertIn(str(facet), destination_text)

    def test_g2_b0_roots_preserve_their_always_loaded_kernels(self) -> None:
        self.assertEqual(
            set(G2_BASE_BATCHES["B0"]),
            {record[0] for record in G2_BASE_B0_COMPACTIONS},
        )
        for owner, path, old_sha256, new_sha256, facets in (
            G2_BASE_B0_COMPACTIONS
        ):
            text = (ROOT / path).read_text(encoding="utf-8")
            with self.subTest(owner=owner):
                self.assertRegex(old_sha256, r"^[0-9a-f]{64}$")
                self.assertEqual(
                    new_sha256,
                    hashlib.sha256(text.encode("utf-8")).hexdigest(),
                )
                for facet in facets:
                    self.assertIn(facet, text)
                self.assertIn("## Targeted References", text)
                self.assertIn("## Output Contract", text)
                if "/foundation/capabilities/" in path:
                    rules = re.search(
                        r"## High-Value Rules\n\n(?P<body>.*?)(?=\n## )",
                        text,
                        flags=re.DOTALL,
                    )
                    self.assertIsNotNone(rules)
                    rule_count = sum(
                        line.startswith("- ")
                        for line in rules.group("body").splitlines()
                    )
                    self.assertGreaterEqual(rule_count, 3)
                    self.assertLessEqual(rule_count, 8)

    def test_g2_b1_relocation_ledger_is_frozen_and_lossless(self) -> None:
        b1_entries = tuple(
            entry
            for entry in RELOCATION_LEDGER
            if entry["owner"] in G2_BASE_BATCHES["B1"]
            and entry["source_rule_fingerprint"]
            in {spec[2] for spec in G2_BASE_B1_MOVE_SPECS}
        )
        self.assertEqual(len(G2_BASE_B1_MOVE_SPECS), len(b1_entries))
        self.assertEqual(
            set(G2_BASE_BATCHES["B1"]),
            {entry["owner"] for entry in b1_entries},
        )
        architecture_children = [
            spec[1]
            for spec in G2_BASE_B1_MOVE_SPECS
            if spec[0] == "architecture-impact-reviewer"
        ]
        self.assertEqual(5, len(architecture_children))
        self.assertEqual(
            "b16e27550c495e5ac5dc7e6a6af36255c8de6b670baac993570050218280732c",
            _fingerprint(" ".join(architecture_children)),
        )
        placement_text = (
            ROOT
            / "src/professional-skills/architecture-impact-reviewer/references/placement-and-ownership.md"
        ).read_text(encoding="utf-8")
        self.assertEqual(
            1,
            placement_text.count(
                "When placement remains open, compare the smallest local design "
                "with broader alternatives against material change-locality, "
                "coupling, compatibility, operability, and deletion constraints."
            ),
        )
        split_text = (
            ROOT
            / "src/foundation/capabilities/module-boundary-design/references/split-merge-and-move-decisions.md"
        ).read_text(encoding="utf-8")
        self.assertEqual(
            1,
            split_text.count(
                "Language and build mechanisms prove only the scopes, imports, "
                "targets, deps, and visibility they actually enforce. They do not "
                "prove semantic responsibility, state authority, generated or "
                "dynamic edges, runtime calls, external consumers, or incident "
                "ownership."
            ),
        )
        self.assertTrue(
            split_text.startswith(
                "# Split, Merge, and Move Decisions\n\n"
                "Language and build mechanisms prove only the scopes, imports, "
                "targets, deps, and visibility they actually enforce. They do not "
                "prove semantic responsibility, state authority, generated or "
                "dynamic edges, runtime calls, external consumers, or incident "
                "ownership.\n\n## Decomposition Evidence\n"
            )
        )
        self.assertNotIn("\n## Proof Limits\n", split_text)
        for entry in b1_entries:
            with self.subTest(owner=entry["owner"]):
                self.assertEqual(LEDGER_FIELDS, set(entry))
                self.assertEqual(
                    entry["source_rule_fingerprint"],
                    _fingerprint(str(entry["old_anchor"])),
                )
                root_text = (ROOT / str(entry["source_path"])).read_text(
                    encoding="utf-8"
                )
                destination_text = (ROOT / str(entry["destination"])).read_text(
                    encoding="utf-8"
                )
                self.assertNotIn(str(entry["old_anchor"]), root_text)
                self.assertEqual(
                    1, destination_text.count(str(entry["new_anchor"]))
                )

    def test_g2_b1_roots_preserve_their_always_loaded_kernels(self) -> None:
        self.assertEqual(15, len(G2_BASE_B1_COMPACTIONS))
        for owner, path, old_sha256, new_sha256, facets in (
            G2_BASE_B1_COMPACTIONS
        ):
            text = (ROOT / path).read_text(encoding="utf-8")
            with self.subTest(owner=owner):
                self.assertRegex(old_sha256, r"^[0-9a-f]{64}$")
                self.assertEqual(
                    new_sha256,
                    hashlib.sha256(text.encode("utf-8")).hexdigest(),
                )
                for facet in facets:
                    self.assertIn(facet, text)
                self.assertIn("## Targeted References", text)
                self.assertIn("## Output Contract", text)

    def test_g2_b2_foundation_roots_keep_three_to_eight_kernel_rules(self) -> None:
        for owner in G2_BASE_BATCHES["B2"]:
            text = _g2_owner_root(owner).read_text(encoding="utf-8")
            rules = re.search(
                r"## High-Value Rules\n\n(?P<body>.*?)(?=\n## )",
                text,
                flags=re.DOTALL,
            )
            with self.subTest(owner=owner):
                self.assertIsNotNone(rules)
                rule_count = sum(
                    line.startswith("- ")
                    for line in rules.group("body").splitlines()
                )
                self.assertGreaterEqual(rule_count, 3)
                self.assertLessEqual(rule_count, 8)

    def test_g2_b2_relocation_ledger_is_frozen_and_lossless(self) -> None:
        fingerprints = {spec[2] for spec in G2_BASE_B2_MOVE_SPECS}
        entries = tuple(
            entry
            for entry in RELOCATION_LEDGER
            if entry["source_rule_fingerprint"] in fingerprints
        )
        self.assertEqual(13, len(entries))
        self.assertEqual(
            {
                "authentication-authorization",
                "authentication-security",
                "cryptography-key-lifecycle",
                "permission-boundary-modeling",
                "tenant-isolation",
            },
            {entry["owner"] for entry in entries},
        )
        for entry in entries:
            with self.subTest(owner=entry["owner"], anchor=entry["old_anchor"]):
                self.assertEqual(LEDGER_FIELDS, set(entry))
                self.assertEqual(
                    entry["source_rule_fingerprint"],
                    _fingerprint(str(entry["old_anchor"])),
                )
                root_text = (ROOT / str(entry["source_path"])).read_text(
                    encoding="utf-8"
                )
                destination_text = (ROOT / str(entry["destination"])).read_text(
                    encoding="utf-8"
                )
                self.assertNotIn(str(entry["old_anchor"]), root_text)
                self.assertEqual(
                    1, destination_text.count(str(entry["new_anchor"]))
                )

    def test_g2_b3_foundation_roots_keep_three_to_eight_kernel_rules(self) -> None:
        for owner in G2_BASE_BATCHES["B3"]:
            text = _g2_owner_root(owner).read_text(encoding="utf-8")
            rules = re.search(
                r"## High-Value Rules\n\n(?P<body>.*?)(?=\n## )",
                text,
                flags=re.DOTALL,
            )
            with self.subTest(owner=owner):
                self.assertIsNotNone(rules)
                rule_count = sum(
                    line.startswith("- ")
                    for line in rules.group("body").splitlines()
                )
                self.assertGreaterEqual(rule_count, 3)
                self.assertLessEqual(rule_count, 8)

    def test_g2_b3_relocation_ledger_is_frozen_and_lossless(self) -> None:
        fingerprints = {spec[2] for spec in G2_BASE_B3_MOVE_SPECS}
        entries = tuple(
            entry
            for entry in RELOCATION_LEDGER
            if entry["source_rule_fingerprint"] in fingerprints
        )
        self.assertEqual(16, len(entries))
        self.assertEqual(
            set(G2_BASE_BATCHES["B3"]) - {"idempotency-retry-design"},
            {entry["owner"] for entry in entries},
        )
        for entry in entries:
            with self.subTest(owner=entry["owner"], anchor=entry["old_anchor"]):
                self.assertEqual(LEDGER_FIELDS, set(entry))
                self.assertEqual(
                    entry["source_rule_fingerprint"],
                    _fingerprint(str(entry["old_anchor"])),
                )
                root_text = (ROOT / str(entry["source_path"])).read_text(
                    encoding="utf-8"
                )
                destination_text = (ROOT / str(entry["destination"])).read_text(
                    encoding="utf-8"
                )
                self.assertNotIn(str(entry["old_anchor"]), root_text)
                self.assertEqual(
                    1, destination_text.count(str(entry["new_anchor"]))
                )

    def test_g2_b4_foundation_roots_keep_three_to_eight_kernel_rules(self) -> None:
        for owner in G2_BASE_BATCHES["B4"]:
            text = _g2_owner_root(owner).read_text(encoding="utf-8")
            rules = re.search(
                r"## High-Value Rules\n\n(?P<body>.*?)(?=\n## )",
                text,
                flags=re.DOTALL,
            )
            with self.subTest(owner=owner):
                self.assertIsNotNone(rules)
                rule_count = sum(
                    line.startswith("- ")
                    for line in rules.group("body").splitlines()
                )
                self.assertGreaterEqual(rule_count, 3)
                self.assertLessEqual(rule_count, 8)

    def test_g2_b4_relocation_ledger_is_frozen_and_lossless(self) -> None:
        fingerprints = {spec[2] for spec in G2_BASE_B4_MOVE_SPECS}
        entries = tuple(
            entry
            for entry in RELOCATION_LEDGER
            if entry["source_rule_fingerprint"] in fingerprints
        )
        self.assertEqual(13, len(entries))
        self.assertEqual(
            set(G2_BASE_BATCHES["B4"]),
            {entry["owner"] for entry in entries},
        )
        for entry in entries:
            with self.subTest(owner=entry["owner"], anchor=entry["old_anchor"]):
                self.assertEqual(LEDGER_FIELDS, set(entry))
                self.assertEqual(
                    entry["source_rule_fingerprint"],
                    _fingerprint(str(entry["old_anchor"])),
                )
                root_text = (ROOT / str(entry["source_path"])).read_text(
                    encoding="utf-8"
                )
                destination_text = (ROOT / str(entry["destination"])).read_text(
                    encoding="utf-8"
                )
                self.assertNotIn(str(entry["old_anchor"]), root_text)
                self.assertEqual(1, destination_text.count(str(entry["new_anchor"])))

    def test_g2_b5_foundation_roots_keep_three_to_eight_kernel_rules(self) -> None:
        for owner in G2_BASE_BATCHES["B5"]:
            text = _g2_owner_root(owner).read_text(encoding="utf-8")
            rules = re.search(
                r"## High-Value Rules\n\n(?P<body>.*?)(?=\n## )",
                text,
                flags=re.DOTALL,
            )
            with self.subTest(owner=owner):
                self.assertIsNotNone(rules)
                rule_count = sum(
                    line.startswith("- ")
                    for line in rules.group("body").splitlines()
                )
                self.assertGreaterEqual(rule_count, 3)
                self.assertLessEqual(rule_count, 8)

    def test_g2_b5_relocation_ledger_is_frozen_and_lossless(self) -> None:
        fingerprints = {spec[2] for spec in G2_BASE_B5_MOVE_SPECS}
        entries = tuple(
            entry
            for entry in RELOCATION_LEDGER
            if entry["source_rule_fingerprint"] in fingerprints
        )
        self.assertEqual(10, len(entries))
        self.assertEqual(set(G2_BASE_BATCHES["B5"]), {entry["owner"] for entry in entries})
        for entry in entries:
            with self.subTest(owner=entry["owner"], anchor=entry["old_anchor"]):
                self.assertEqual(LEDGER_FIELDS, set(entry))
                self.assertEqual(entry["source_rule_fingerprint"], _fingerprint(str(entry["old_anchor"])))
                root_text = (ROOT / str(entry["source_path"])).read_text(encoding="utf-8")
                destination_text = (ROOT / str(entry["destination"])).read_text(encoding="utf-8")
                self.assertNotIn(str(entry["old_anchor"]), root_text)
                self.assertEqual(1, destination_text.count(str(entry["new_anchor"])))

    def test_g2_b6_foundation_roots_keep_three_to_eight_kernel_rules(self) -> None:
        for owner in G2_BASE_BATCHES["B6"]:
            text = _g2_owner_root(owner).read_text(encoding="utf-8")
            rules = re.search(r"## High-Value Rules\n\n(?P<body>.*?)(?=\n## )", text, flags=re.DOTALL)
            with self.subTest(owner=owner):
                self.assertIsNotNone(rules)
                rule_count = sum(line.startswith("- ") for line in rules.group("body").splitlines())
                self.assertGreaterEqual(rule_count, 3)
                self.assertLessEqual(rule_count, 8)

    def test_g2_b6_relocation_ledger_is_frozen_and_lossless(self) -> None:
        fingerprints = {spec[2] for spec in G2_BASE_B6_MOVE_SPECS}
        entries = tuple(entry for entry in RELOCATION_LEDGER if entry["source_rule_fingerprint"] in fingerprints)
        self.assertEqual(14, len(entries))
        self.assertEqual(set(G2_BASE_BATCHES["B6"]), {entry["owner"] for entry in entries})
        for entry in entries:
            with self.subTest(owner=entry["owner"], anchor=entry["old_anchor"]):
                self.assertEqual(LEDGER_FIELDS, set(entry))
                self.assertEqual(entry["source_rule_fingerprint"], _fingerprint(str(entry["old_anchor"])))
                root_text = (ROOT / str(entry["source_path"])).read_text(encoding="utf-8")
                destination_text = (ROOT / str(entry["destination"])).read_text(encoding="utf-8")
                self.assertNotIn(str(entry["old_anchor"]), root_text)
                self.assertEqual(1, destination_text.count(str(entry["new_anchor"])))

    def test_g2_b7_domain_active_references_preserve_role_pairing(self) -> None:
        expected_counts = {
            "android-platform-extension": 7,
            "cross-platform-client-extension": 4,
            "ios-ipados-platform-extension": 6,
            "linux-desktop-platform-extension": 7,
            "macos-platform-extension": 6,
            "windows-platform-extension": 7,
        }
        selected: set[str] = set()
        for owner, expected_count in expected_counts.items():
            references = _g2_task_review_active_references(owner)
            with self.subTest(owner=owner):
                self.assertEqual(expected_count, len(references))
                if owner != "cross-platform-client-extension":
                    self.assertTrue(
                        all(
                            reference.endswith("-implementation-and-review-evidence.md")
                            for reference in references
                        )
                    )
                    root_text = _g2_owner_root(owner).read_text(encoding="utf-8")
                    self.assertIn("Analysis loads only active decision-family References.", root_text)
                    self.assertIn("Task and Review load paired evidence companions", root_text)
            selected.update(references)
        self.assertEqual(37, len(selected))

    def test_g2_b7_relocation_ledger_is_frozen_and_lossless(self) -> None:
        fingerprint = G2_BASE_B7_MOVE_SPECS[0][2]
        entries = tuple(
            entry for entry in RELOCATION_LEDGER
            if entry["source_rule_fingerprint"] == fingerprint
        )
        self.assertEqual(1, len(entries))
        entry = entries[0]
        self.assertEqual(LEDGER_FIELDS, set(entry))
        self.assertEqual(fingerprint, _fingerprint(str(entry["old_anchor"])))
        root_text = (ROOT / str(entry["source_path"])).read_text(encoding="utf-8")
        destination_text = (ROOT / str(entry["destination"])).read_text(encoding="utf-8")
        self.assertNotIn(str(entry["old_anchor"]), root_text)
        self.assertEqual(1, destination_text.count(str(entry["new_anchor"])))

    def test_g2_b8_domain_active_references_match_frozen_membership(self) -> None:
        expected_counts = {
            "ai-product-extension": 1,
            "cloud-platform-extension": 5,
            "iot-embedded-extension": 1,
        }
        selected: set[str] = set()
        for owner, expected_count in expected_counts.items():
            references = _g2_task_review_active_references(owner)
            with self.subTest(owner=owner):
                self.assertEqual(expected_count, len(references))
            selected.update(references)
        self.assertEqual(7, len(selected))

    def test_g2_b8_relocation_ledger_is_frozen_and_lossless(self) -> None:
        fingerprints = {spec[2] for spec in G2_BASE_B8_MOVE_SPECS}
        entries = tuple(
            entry
            for entry in RELOCATION_LEDGER
            if entry["source_rule_fingerprint"] in fingerprints
        )
        self.assertEqual(3, len(entries))
        for entry in entries:
            with self.subTest(anchor=entry["old_anchor"]):
                self.assertEqual(LEDGER_FIELDS, set(entry))
                self.assertEqual(
                    entry["source_rule_fingerprint"],
                    _fingerprint(str(entry["old_anchor"])),
                )
                root_text = (ROOT / str(entry["source_path"])).read_text(encoding="utf-8")
                destination_text = (ROOT / str(entry["destination"])).read_text(encoding="utf-8")
                self.assertNotIn(str(entry["old_anchor"]), root_text)
                self.assertEqual(1, destination_text.count(str(entry["new_anchor"])))

    def test_visible_ledger_has_exact_closed_owner_frontier(self) -> None:
        self.assertEqual(85, len(ROOT_PATHS))
        self.assertEqual(
            set(ROOT_PATHS),
            {entry["owner"] for entry in RELOCATION_LEDGER} | {"engineering-change-analysis"},
        )
        for entry in RELOCATION_LEDGER:
            owner = str(entry["owner"])
            destination = str(entry["destination"])
            with self.subTest(owner=owner, destination=destination):
                self.assertEqual(LEDGER_FIELDS, set(entry))
                self.assertEqual(_fingerprint(str(entry["old_anchor"])), entry["source_rule_fingerprint"])
                self.assertEqual("conditional-decision-rule", entry["classification"])
                self.assertEqual(Path(destination).stem, entry["decision_problem"])
                self.assertTrue(entry["required_by"])
                self.assertTrue(entry["required_output"])
                self.assertEqual(
                    FROZEN_REFERENCE_BINDINGS[destination],
                    _reference_binding(owner, destination),
                )
                self.assertEqual("unchanged", entry["co_trigger_effect"])
                self.assertEqual("unchanged", entry["route_effect"])
                self.assertIn(owner, ROOT_PATHS)
                self.assertTrue((ROOT / destination).is_file())
                self.assertNotIn("/index.md", destination)

    def test_active_reference_compaction_preserves_required_facets(self) -> None:
        for path, facets in V7_ACTIVE_REFERENCE_FACETS.items():
            text = (ROOT / path).read_text(encoding="utf-8")
            for facet in facets:
                with self.subTest(path=path, facet=facet):
                    self.assertIn(facet, text)

    def test_v7_compaction_ledger_binds_content_and_preserved_kernels(self) -> None:
        self.assertEqual(12, len(V7_COMPACTION_RECORDS))
        for entry in V7_COMPACTION_RECORDS:
            path = str(entry["path"])
            text = (ROOT / path).read_text(encoding="utf-8")
            with self.subTest(owner=entry["owner"], path=path):
                self.assertEqual(COMPACTION_FIELDS, set(entry))
                self.assertRegex(str(entry["old_content_sha256"]), r"^[0-9a-f]{64}$")
                successor = G2_BASE_SUCCESSOR_CONTENT_HASHES.get(path)
                if successor is None:
                    self.assertEqual(
                        entry["new_content_sha256"],
                        hashlib.sha256(text.encode("utf-8")).hexdigest(),
                    )
                else:
                    self.assertEqual(entry["new_content_sha256"], successor[0])
                    self.assertEqual(
                        successor[1],
                        hashlib.sha256(text.encode("utf-8")).hexdigest(),
                    )
                self.assertIn(entry["classification"], {"always-kernel-compaction", "conditional-reference-compaction"})
                self.assertEqual("compacted-in-place", entry["disposition"])
                self.assertTrue(entry["required_by"])
                self.assertTrue(entry["required_output"])
                if successor is None:
                    current_owner_text = text
                else:
                    destinations = {
                        str(item["destination"])
                        for item in RELOCATION_LEDGER
                        if item["owner"] == entry["owner"]
                        and str(item["destination"]) != path
                    }
                    current_owner_text = text + "\n" + "\n".join(
                        (ROOT / destination).read_text(encoding="utf-8")
                        for destination in sorted(destinations)
                    )
                self.assertEqual(
                    1,
                    current_owner_text.count(str(entry["new_anchor"])),
                )
                for facet in entry["preserved_facets"]:
                    self.assertIn(str(facet), current_owner_text)
                self.assertEqual("unchanged", entry["co_trigger_effect"])
                self.assertEqual("unchanged", entry["route_effect"])
                self.assertNotIn("/index.md", path)

    def test_relocated_groups_leave_root_and_have_one_existing_owner(self) -> None:
        for entry in RELOCATION_LEDGER:
            owner = str(entry["owner"])
            old_anchor = str(entry["old_anchor"])
            destination = str(entry["destination"])
            with self.subTest(owner=owner, old_anchor=old_anchor):
                root_text = (ROOT / ROOT_PATHS[owner]).read_text(encoding="utf-8")
                destination_text = (ROOT / destination).read_text(encoding="utf-8")
                self.assertNotIn(old_anchor, root_text)
                self.assertEqual(1, destination_text.count(str(entry["new_anchor"])))

    def test_payment_split_is_exactly_once_and_uses_the_current_predecessor(self) -> None:
        self.assertEqual(
            "a85c220eece629aed74f6db1b839027e61f608fa1c8868d8ed0fc9134649af98",
            PAYMENT_ROOT_PREDECESSOR_SHA256,
        )
        self.assertEqual(
            "ed4872eaafeb42d56e0426c8dfbe812efdb26424904f2558f4b47f5179321819",
            PAYMENT_CHECKLIST_PREDECESSOR_SHA256,
        )
        self.assertEqual(10, len(PAYMENT_REFERENCE_SPECS))
        self.assertEqual(
            PAYMENT_CHECKLIST_RULE_COUNT,
            sum(len(spec["rules"]) for spec in PAYMENT_REFERENCE_SPECS.values()),
        )
        self.assertFalse(
            (ROOT / PAYMENT_REFERENCE_PREFIX / "checklist.md").exists(),
            "the split predecessor checklist must be removed",
        )
        all_reference_text = ""
        for filename, spec in PAYMENT_REFERENCE_SPECS.items():
            path = ROOT / PAYMENT_REFERENCE_PREFIX / filename
            with self.subTest(filename=filename):
                self.assertTrue(path.is_file())
                text = path.read_text(encoding="utf-8")
                all_reference_text += "\n" + text
                for rule in spec["rules"]:
                    self.assertEqual(1, text.count(rule))

                if filename == "raw-card-custody-evidence.md":
                    self.assertEqual(
                        PAYMENT_RAW_CARD_SUCCESSOR_SHA256,
                        hashlib.sha256(text.encode("utf-8")).hexdigest(),
                    )
                    rules = text.split("## Decision Rules\n\n", 1)[1]
                    self.assertEqual(
                        PAYMENT_RAW_CARD_RULES_SHA256,
                        hashlib.sha256(rules.encode("utf-8")).hexdigest(),
                    )
                else:
                    self.assertEqual(
                        PAYMENT_UNCHANGED_REFERENCE_HASHES[filename],
                        hashlib.sha256(text.encode("utf-8")).hexdigest(),
                    )
        for spec in PAYMENT_REFERENCE_SPECS.values():
            for rule in spec["rules"]:
                with self.subTest(rule=rule):
                    self.assertEqual(1, all_reference_text.count(rule))

        payment_entries = tuple(
            entry
            for entry in RELOCATION_LEDGER
            if entry["owner"] == "payment-trading-extension"
            and entry["source_path"] == PAYMENT_REFERENCE_PREFIX + "checklist.md"
        )
        self.assertEqual(PAYMENT_CHECKLIST_RULE_COUNT, len(payment_entries))
        self.assertTrue(
            all(
                entry["disposition"] == "split-relocated-new-reference"
                for entry in payment_entries
            )
        )

    def test_payment_root_registry_and_admissibility_projection_are_exact(self) -> None:
        root_path = ROOT / "src/domain-extensions/payment-trading-extension/SKILL.md"
        root_text = root_path.read_text(encoding="utf-8")
        self.assertEqual(
            PAYMENT_ROOT_SUCCESSOR_SHA256,
            hashlib.sha256(root_text.encode("utf-8")).hexdigest(),
        )
        root_kernel = root_text.split("## Targeted References\n", 1)[0]
        self.assertEqual(
            PAYMENT_ROOT_KERNEL_SHA256,
            hashlib.sha256(root_kernel.encode("utf-8")).hexdigest(),
        )
        self.assertEqual(1251, VALIDATION.count_o200k_base_tokens(root_text))
        self.assertNotIn("load the checklist for detailed closure", root_kernel)
        self.assertEqual(
            1,
            root_kernel.count(
                "Preserve the accepted financial invariant across authoritative state, duplicate effects, custody, owned transitions, ledger/accounting boundaries, inbound events, exact arithmetic, reconciliation, and accountable regulation."
            ),
        )
        self.assertEqual(
            1,
            root_kernel.count("Load the named Reference for detailed closure."),
        )
        for checklist_item in (
            "Establish the financial invariant and authoritative state.",
            "Load each named Reference whose decision problem is active.",
            "Record selected controls, reconciliation evidence, proof limits, and residual risk.",
        ):
            self.assertEqual(1, root_kernel.count(checklist_item))

        registry_path = ROOT / "src/registry/domain-skills.yaml"
        self.assertEqual(
            PAYMENT_REGISTRY_FILE_SUCCESSOR_SHA256,
            hashlib.sha256(registry_path.read_bytes()).hexdigest(),
        )
        registry = VALIDATION.load_yaml_file(registry_path)
        payment = next(
            row
            for row in registry["domain_skills"]
            if row["name"] == "payment-trading-extension"
        )
        references = payment["reference_index"]
        self.assertEqual(
            {f"references/{filename}" for filename in PAYMENT_REFERENCE_SPECS},
            {row["path"] for row in references},
        )
        declarations = payment["context_admissibility"]
        self.assertEqual(
            "changeforge.reference-context-admissibility/v3",
            declarations["contract"],
        )
        self.assertEqual(
            {f"references/{filename}" for filename in PAYMENT_REFERENCE_SPECS},
            set(declarations["references"]),
        )
        for filename, spec in PAYMENT_REFERENCE_SPECS.items():
            relative = f"references/{filename}"
            row = next(item for item in references if item["path"] == relative)
            declaration = declarations["references"][relative]
            expected_type, expected_output = PAYMENT_TYPE_OUTPUTS[filename]
            with self.subTest(filename=filename):
                self.assertEqual(expected_type, row["type"])
                self.assertEqual(spec["load_when"], row["load_when"])
                self.assertEqual(spec["do_not_load_when"], row["do_not_load_when"])
                self.assertEqual(list(ALL_ROLES), row["required_by"])
                self.assertEqual(list(expected_output), row["required_output"])
                self.assertEqual(spec["gap_class"], declaration["gap_class"])
                self.assertEqual(
                    list(spec["route_affecting_surfaces"]),
                    declaration["route_affecting_surfaces"],
                )
                self.assertEqual(Path(filename).stem, declaration["decision_problem"])
                self.assertEqual([], declaration["conflicts_with"])
                self.assertEqual([], declaration["sequenced_after"])
                self.assertEqual([], declaration["must_co_trigger_with"])
                self.assertEqual(
                    (ALL_ROLES, expected_output),
                    _reference_binding("payment-trading-extension", PAYMENT_REFERENCE_PREFIX + filename),
                )

        canonical_row = json.dumps(
            payment,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        self.assertEqual(
            PAYMENT_REGISTRY_SUCCESSOR_SHA256,
            hashlib.sha256(canonical_row.encode("utf-8")).hexdigest(),
        )

        authority = VALIDATION.reference_context_admissibility_authority(
            VALIDATION.load_yaml_file(ROOT / "src/registry/professional-skills.yaml"),
            VALIDATION.load_yaml_file(ROOT / "src/registry/foundation-skills.yaml"),
            registry,
            context="payment split focused authority",
        )
        for filename in PAYMENT_REFERENCE_SPECS:
            decision = VALIDATION.reference_context_admissibility_decisions(
                authority,
                references=[("payment-trading-extension", f"references/{filename}")],
                path="direct",
            )
            with self.subTest(decision=filename):
                self.assertFalse(decision["reachable"])
                self.assertEqual("analyzed", decision["minimum_path"])

    def test_web3_split_is_exactly_once_and_uses_the_accepted_predecessor(self) -> None:
        self.assertEqual(
            "00cd821a80adc03b08f46e2bc6ef5b0f8d9f5175eef4b1b14bca564e46c5be5a",
            WEB3_ROOT_PREDECESSOR_SHA256,
        )
        self.assertEqual(
            "e8cb068ad8db55389dd63099f19a89dab260ea1bc5d5a5b2af5a2d7dd77ced3a",
            WEB3_CHECKLIST_PREDECESSOR_SHA256,
        )
        self.assertEqual(7, len(WEB3_REFERENCE_SPECS))
        self.assertEqual(set(WEB3_REFERENCE_SPECS), set(WEB3_ROOT_RULES))
        self.assertEqual(set(WEB3_REFERENCE_SPECS), set(WEB3_CHECKLIST_RULES))
        self.assertEqual(
            WEB3_CHECKLIST_RULE_COUNT,
            sum(
                len(WEB3_ROOT_RULES[filename])
                + len(WEB3_CHECKLIST_RULES[filename])
                for filename in WEB3_REFERENCE_SPECS
            ),
        )
        self.assertFalse(
            (ROOT / WEB3_REFERENCE_PREFIX / "checklist.md").exists(),
            "the accepted Web3 split removes the broad checklist",
        )

        all_reference_text = ""
        for filename, spec in WEB3_REFERENCE_SPECS.items():
            path = ROOT / WEB3_REFERENCE_PREFIX / filename
            with self.subTest(filename=filename):
                self.assertTrue(path.is_file())
                text = path.read_text(encoding="utf-8")
                all_reference_text += "\n" + text
                self.assertTrue(text.startswith(WEB3_REFERENCE_HEADINGS[filename] + "\n\n"))
                expected_preface = (
                    "Use this evidence-pattern Reference only for the named Web3 verification-evidence decision."
                    if spec["type"] == "evidence-pattern"
                    else "Use this Reference only for the named decision."
                )
                self.assertEqual(1, text.count(expected_preface))
                for rule in WEB3_ROOT_RULES[filename] + WEB3_CHECKLIST_RULES[filename]:
                    current_rule = WEB3_ROOT_RULE_SUCCESSOR_OVERRIDES.get(rule, rule)
                    self.assertEqual(1, text.count(current_rule))

        for filename in WEB3_REFERENCE_SPECS:
            for rule in WEB3_ROOT_RULES[filename] + WEB3_CHECKLIST_RULES[filename]:
                current_rule = WEB3_ROOT_RULE_SUCCESSOR_OVERRIDES.get(rule, rule)
                with self.subTest(unique_rule=rule):
                    self.assertEqual(1, all_reference_text.count(current_rule))

        root_entries = tuple(
            entry
            for entry in RELOCATION_LEDGER
            if entry["owner"] == "web3-product-extension"
            and entry["source_path"] == WEB3_ROOT_PATH
        )
        checklist_entries = tuple(
            entry
            for entry in RELOCATION_LEDGER
            if entry["owner"] == "web3-product-extension"
            and entry["source_path"] == WEB3_REFERENCE_PREFIX + "checklist.md"
        )
        self.assertEqual(14, len(root_entries))
        self.assertEqual(36, len(checklist_entries))
        self.assertTrue(
            all(
                entry["disposition"] == "split-relocated-new-reference"
                for entry in root_entries + checklist_entries
            )
        )
        custody_entry = next(
            entry
            for entry in root_entries
            if entry["old_anchor"] == WEB3_CUSTODY_PREDECESSOR_RULE
        )
        self.assertEqual(
            "92ad7423a6e076517f2c5f88d43268242ed17c5e0199944cea6dbf507896ae5e",
            custody_entry["source_rule_fingerprint"],
        )
        self.assertEqual(WEB3_CUSTODY_SUCCESSOR_RULE, custody_entry["new_anchor"])
        self.assertEqual(
            "6e5e61fc1de4dfa672129fb2449b43be6d3c8759d01c767595eb9d778339dcbe",
            _fingerprint(WEB3_CUSTODY_SUCCESSOR_RULE),
        )

    def test_web3_root_registry_type_authority_and_admissibility_are_exact(self) -> None:
        root_text = (ROOT / WEB3_ROOT_PATH).read_text(encoding="utf-8")
        for rules in WEB3_ROOT_RULES.values():
            for rule in rules:
                with self.subTest(root_rule=rule):
                    self.assertNotIn(rule, root_text)
        for exact_kernel in (
            "This focused Layer 3 Domain Skill gives `analysis-agent`, `task-agent`, and `review-agent` the Web3 kernel and named References.",
            "Preserve the accepted on-chain invariant.",
            "Load each named Reference whose decision problem is active.",
            "Hash or signature terms can falsely trigger Web3 without chain or custody evidence.",
            "Trace asset authority, signer/custody, contract calls, chain identity, finality, and recovery.",
            "Select controls from exposure, target-chain semantics, liquidity, and operational evidence.",
            "Prove invariant, reorg, replay, oracle, upgrade, and recovery behavior.",
        ):
            self.assertEqual(1, root_text.count(exact_kernel))
        self.assertIn(
            "| [custody and chain transactions](references/custody-and-chain-transactions.md) | targeted | custody, signing, chain transaction, finality, oracle, indexer, or asset-authority behavior needs a decision | hash or signature terminology appears without chain or custody behavior | analysis-agent, task-agent, review-agent | boundary-decision, selected-approach, failure-decision, residual-risk |",
            root_text,
        )
        root_tokens = VALIDATION.count_o200k_base_tokens(root_text)
        self.assertEqual(834, root_tokens)
        self.assertLess(root_tokens, 900)

        reference_tokens = {}
        for filename in WEB3_REFERENCE_SPECS:
            path = ROOT / WEB3_REFERENCE_PREFIX / filename
            reference_tokens[filename] = VALIDATION.count_o200k_base_tokens(
                path.read_text(encoding="utf-8")
            )
        self.assertEqual(644, reference_tokens["custody-and-chain-transactions.md"])
        self.assertEqual(
            1478,
            root_tokens + reference_tokens["custody-and-chain-transactions.md"],
        )
        self.assertTrue(
            all(
                len((ROOT / WEB3_REFERENCE_PREFIX / filename).read_text(encoding="utf-8").splitlines())
                < 60
                for filename in WEB3_REFERENCE_SPECS
            )
        )
        for path in (
            ROOT / WEB3_ROOT_PATH,
            *(
                ROOT / WEB3_REFERENCE_PREFIX / filename
                for filename in WEB3_REFERENCE_SPECS
            ),
        ):
            with self.subTest(readability=path.name):
                self.assertEqual(
                    [],
                    [
                        finding
                        for finding in VALIDATION.ai_readability_findings(
                            path.read_text(encoding="utf-8"), str(path)
                        )
                        if finding.get("severity") == "error"
                    ],
                )
        custody_text = (
            ROOT / WEB3_REFERENCE_PREFIX / "custody-and-chain-transactions.md"
        ).read_text(encoding="utf-8")
        sections = re.split(r"^#{2,3} ", custody_text, flags=re.MULTILINE)[1:]
        decision_counts = [
            len(re.findall(r"^- ", section, flags=re.MULTILINE))
            for section in sections
        ]
        self.assertEqual([15, 4], decision_counts)

        registry = VALIDATION.load_yaml_file(ROOT / "src/registry/domain-skills.yaml")
        web3 = next(
            row
            for row in registry["domain_skills"]
            if row["name"] == "web3-product-extension"
        )
        references = web3["reference_index"]
        expected_paths = {
            f"references/{filename}" for filename in WEB3_REFERENCE_SPECS
        }
        self.assertEqual(expected_paths, {row["path"] for row in references})
        declarations = web3["context_admissibility"]
        self.assertEqual(
            "changeforge.reference-context-admissibility/v3",
            declarations["contract"],
        )
        self.assertEqual(expected_paths, set(declarations["references"]))

        canonical_surface_files = {
            "custody-and-chain-transactions.md",
            "upgrades-and-deployed-behavior.md",
            "governance-authority.md",
            "account-and-cross-domain-execution.md",
        }
        for filename, spec in WEB3_REFERENCE_SPECS.items():
            relative = f"references/{filename}"
            row = next(item for item in references if item["path"] == relative)
            declaration = declarations["references"][relative]
            with self.subTest(filename=filename):
                self.assertEqual(spec["type"], row["type"])
                self.assertEqual(spec["load_when"], row["load_when"])
                self.assertEqual(spec["do_not_load_when"], row["do_not_load_when"])
                self.assertNotEqual(row["load_when"], row["do_not_load_when"])
                self.assertEqual(list(ALL_ROLES), row["required_by"])
                self.assertEqual(list(spec["required_output"]), row["required_output"])
                self.assertEqual(spec["gap_class"], declaration["gap_class"])
                self.assertEqual(
                    list(spec["route_affecting_surfaces"]),
                    declaration["route_affecting_surfaces"],
                )
                self.assertNotIn(
                    "primary-professional", declaration["route_affecting_surfaces"]
                )
                self.assertEqual(
                    1 if filename in canonical_surface_files else 0,
                    declaration["route_affecting_surfaces"].count(
                        "primary-professional-skill"
                    ),
                )
                self.assertEqual(Path(filename).stem, declaration["decision_problem"])
                self.assertEqual([], declaration["conflicts_with"])
                self.assertEqual([], declaration["sequenced_after"])
                self.assertEqual([], declaration["must_co_trigger_with"])
                self.assertEqual(
                    (ALL_ROLES, spec["required_output"]),
                    _reference_binding(
                        "web3-product-extension", WEB3_REFERENCE_PREFIX + filename
                    ),
                )

        authority = VALIDATION.reference_context_admissibility_authority(
            VALIDATION.load_yaml_file(ROOT / "src/registry/professional-skills.yaml"),
            VALIDATION.load_yaml_file(ROOT / "src/registry/foundation-skills.yaml"),
            registry,
            context="Web3 split focused authority",
        )
        for filename in WEB3_REFERENCE_SPECS:
            decision = VALIDATION.reference_context_admissibility_decisions(
                authority,
                references=[("web3-product-extension", f"references/{filename}")],
                path="direct",
            )
            with self.subTest(path_decision=filename):
                self.assertFalse(decision["reachable"])
                self.assertEqual("analyzed", decision["minimum_path"])

    def test_bigdata_split_is_exactly_once_and_uses_the_accepted_predecessor(self) -> None:
        self.assertEqual(
            "771eaabcb4dd6e8b6ed524edcfffa627b56335701f5015388e3aa657cf0e8e23",
            BIGDATA_ROOT_PREDECESSOR_SHA256,
        )
        self.assertEqual(
            "dbc8522a0e455a539880a1f94e7735b65a737ca3433f8acdcc216cbab2fe10d0",
            BIGDATA_CHECKLIST_PREDECESSOR_SHA256,
        )
        self.assertEqual(5, len(BIGDATA_REFERENCE_SPECS))
        self.assertEqual(
            BIGDATA_CHECKLIST_RULE_COUNT,
            sum(len(spec["rules"]) for spec in BIGDATA_REFERENCE_SPECS.values()),
        )
        self.assertEqual(
            [4, 4, 3, 3, 2],
            [len(spec["rules"]) for spec in BIGDATA_REFERENCE_SPECS.values()],
        )
        self.assertFalse(
            (ROOT / BIGDATA_REFERENCE_PREFIX / "checklist.md").exists(),
            "the accepted BigData split removes the broad checklist",
        )

        all_reference_text = ""
        for filename, spec in BIGDATA_REFERENCE_SPECS.items():
            path = ROOT / BIGDATA_REFERENCE_PREFIX / filename
            with self.subTest(filename=filename):
                self.assertTrue(path.is_file())
                text = path.read_text(encoding="utf-8")
                all_reference_text += "\n" + text
                self.assertTrue(text.startswith(spec["heading"] + "\n\n"))
                self.assertEqual(
                    1,
                    text.count(
                        f"Use this Reference only for the named BigData {Path(filename).stem} decision."
                    ),
                )
                self.assertEqual(1, text.count("## Decision Rules"))
                for rule in spec["rules"]:
                    self.assertEqual(1, text.count(rule))

        consumer_text = (
            ROOT / BIGDATA_REFERENCE_PREFIX / "consumer-and-schema-contracts.md"
        ).read_text(encoding="utf-8")
        self.assertNotIn(BIGDATA_CONSUMER_OLD_RULE, consumer_text)
        self.assertEqual(1, consumer_text.count(BIGDATA_CONSUMER_NEW_RULE))

        for spec in BIGDATA_REFERENCE_SPECS.values():
            for rule in spec["rules"]:
                with self.subTest(unique_rule=rule):
                    self.assertEqual(1, all_reference_text.count(rule))

        bigdata_entries = tuple(
            entry for entry in RELOCATION_LEDGER
            if entry["owner"] == "bigdata-product-extension"
        )
        self.assertEqual(BIGDATA_CHECKLIST_RULE_COUNT, len(bigdata_entries))
        root_entries = tuple(
            entry for entry in bigdata_entries
            if entry["source_path"] == BIGDATA_ROOT_PATH
        )
        checklist_entries = tuple(
            entry for entry in bigdata_entries
            if entry["source_path"] == BIGDATA_REFERENCE_PREFIX + "checklist.md"
        )
        self.assertEqual(1, len(root_entries))
        self.assertEqual(15, len(checklist_entries))
        self.assertEqual(
            "a693cfd967d13c0f165b88b744cf6599673d937e48b37fb972afe7233957b485",
            root_entries[0]["source_rule_fingerprint"],
        )
        self.assertEqual(
            "relocated-existing-reference", root_entries[0]["disposition"]
        )
        self.assertTrue(
            all(
                entry["disposition"] == "split-relocated-new-reference"
                for entry in checklist_entries
            )
        )

    def test_bigdata_root_registry_admissibility_and_content_limits_are_exact(self) -> None:
        root_text = (ROOT / BIGDATA_ROOT_PATH).read_text(encoding="utf-8")
        for spec in BIGDATA_REFERENCE_SPECS.values():
            for rule in spec["rules"]:
                with self.subTest(root_rule=rule):
                    self.assertNotIn(rule, root_text)
        for exact_kernel in (
            "Apply this focused Layer 3 Domain Skill to distributed pipeline decisions.",
            "Provide `analysis-agent`, `task-agent`, and `review-agent` with",
            "Close triggered compatibility, replay, promotion, failed-data, quality, classification, resource, lineage, and experiment risks through named References and current pipeline evidence.",
            "Identify affected producers, transformations, consumers, invariants, and replay window.",
            "Load each named Reference whose decision problem is active.",
            "Record mechanisms, negative paths, cost limits, proof limits, and residual risk.",
        ):
            self.assertEqual(1, root_text.count(exact_kernel))
        self.assertIn("distributed pipeline", root_text)
        self.assertIn("replay", root_text)

        root_tokens = VALIDATION.count_o200k_base_tokens(root_text)
        self.assertEqual(820, root_tokens)
        self.assertLess(root_tokens, 900)
        reference_tokens = {
            filename: VALIDATION.count_o200k_base_tokens(
                (ROOT / BIGDATA_REFERENCE_PREFIX / filename).read_text(encoding="utf-8")
            )
            for filename in BIGDATA_REFERENCE_SPECS
        }
        self.assertEqual(
            [153, 207, 134, 147, 124],
            list(reference_tokens.values()),
        )
        self.assertEqual(207, max(reference_tokens.values()))
        self.assertEqual(1027, root_tokens + max(reference_tokens.values()))
        for filename in BIGDATA_REFERENCE_SPECS:
            path = ROOT / BIGDATA_REFERENCE_PREFIX / filename
            text = path.read_text(encoding="utf-8")
            with self.subTest(readability=filename):
                self.assertLess(len(text.splitlines()), 60)
                self.assertLessEqual(
                    sum(line.startswith("- ") for line in text.splitlines()), 4
                )
                self.assertEqual(
                    [],
                    [
                        finding
                        for finding in VALIDATION.ai_readability_findings(text, str(path))
                        if finding.get("severity") == "error"
                    ],
                )

        registry = VALIDATION.load_yaml_file(ROOT / "src/registry/domain-skills.yaml")
        bigdata = next(
            row for row in registry["domain_skills"]
            if row["name"] == "bigdata-product-extension"
        )
        expected_paths = {
            f"references/{filename}" for filename in BIGDATA_REFERENCE_SPECS
        }
        self.assertEqual(expected_paths, {row["path"] for row in bigdata["reference_index"]})
        declarations = bigdata["context_admissibility"]
        self.assertEqual(
            "changeforge.reference-context-admissibility/v3",
            declarations["contract"],
        )
        self.assertEqual(expected_paths, set(declarations["references"]))
        for filename, spec in BIGDATA_REFERENCE_SPECS.items():
            relative = f"references/{filename}"
            row = next(
                item for item in bigdata["reference_index"] if item["path"] == relative
            )
            declaration = declarations["references"][relative]
            with self.subTest(registry=filename):
                self.assertEqual("targeted", row["type"])
                self.assertEqual(spec["load_when"], row["load_when"])
                self.assertEqual(spec["do_not_load_when"], row["do_not_load_when"])
                self.assertEqual(list(ALL_ROLES), row["required_by"])
                self.assertEqual(list(spec["required_output"]), row["required_output"])
                self.assertEqual(spec["gap_class"], declaration["gap_class"])
                self.assertEqual(
                    list(spec["route_affecting_surfaces"]),
                    declaration["route_affecting_surfaces"],
                )
                self.assertEqual(Path(filename).stem, declaration["decision_problem"])
                self.assertEqual([], declaration["conflicts_with"])
                self.assertEqual([], declaration["sequenced_after"])
                self.assertEqual([], declaration["must_co_trigger_with"])
                self.assertEqual(
                    (ALL_ROLES, spec["required_output"]),
                    _reference_binding(
                        "bigdata-product-extension", BIGDATA_REFERENCE_PREFIX + filename
                    ),
                )

        authority = VALIDATION.reference_context_admissibility_authority(
            VALIDATION.load_yaml_file(ROOT / "src/registry/professional-skills.yaml"),
            VALIDATION.load_yaml_file(ROOT / "src/registry/foundation-skills.yaml"),
            registry,
            context="BigData split focused authority",
        )
        for filename in BIGDATA_REFERENCE_SPECS:
            decision = VALIDATION.reference_context_admissibility_decisions(
                authority,
                references=[("bigdata-product-extension", f"references/{filename}")],
                path="direct",
            )
            with self.subTest(path_decision=filename):
                self.assertFalse(decision["reachable"])
                self.assertEqual("analyzed", decision["minimum_path"])

    def test_low_level_split_is_exactly_once_and_uses_the_accepted_predecessor(self) -> None:
        self.assertEqual(
            "814bfc94dd8f1619a93d7f7e0bda2573a97d27c12b635436c80223dd44eb8855",
            LOW_LEVEL_ROOT_PREDECESSOR_SHA256,
        )
        self.assertEqual(
            "bc09969d78fa85fe4c22c97984263aa95414b8fa2379f9524af13a58153aa3f9",
            LOW_LEVEL_CHECKLIST_PREDECESSOR_SHA256,
        )
        self.assertEqual(5, len(LOW_LEVEL_REFERENCE_SPECS))
        self.assertEqual(
            LOW_LEVEL_CHECKLIST_RULE_COUNT,
            sum(len(spec["rules"]) for spec in LOW_LEVEL_REFERENCE_SPECS.values()),
        )
        self.assertEqual(
            [3, 3, 2, 4, 5],
            [len(spec["rules"]) for spec in LOW_LEVEL_REFERENCE_SPECS.values()],
        )
        self.assertFalse(
            (ROOT / LOW_LEVEL_REFERENCE_PREFIX / "checklist.md").exists(),
            "the accepted Low-level split removes the broad checklist",
        )

        all_reference_text = ""
        for filename, spec in LOW_LEVEL_REFERENCE_SPECS.items():
            path = ROOT / LOW_LEVEL_REFERENCE_PREFIX / filename
            with self.subTest(filename=filename):
                self.assertTrue(path.is_file())
                text = path.read_text(encoding="utf-8")
                all_reference_text += "\n" + text
                self.assertTrue(text.startswith(spec["heading"] + "\n\n"))
                self.assertEqual(1, text.count(spec["preface"]))
                self.assertEqual(1, text.count("## Decision Rules"))
                for rule in spec["rules"]:
                    self.assertEqual(1, text.count(rule))

        for spec in LOW_LEVEL_REFERENCE_SPECS.values():
            for rule in spec["rules"]:
                with self.subTest(unique_rule=rule):
                    self.assertEqual(1, all_reference_text.count(rule))

        low_level_entries = tuple(
            entry for entry in RELOCATION_LEDGER
            if entry["owner"] == "low-level-systems-extension"
            and entry["classification"] == "conditional-decision-rule"
        )
        self.assertEqual(LOW_LEVEL_CHECKLIST_RULE_COUNT, len(low_level_entries))
        root_entries = tuple(
            entry for entry in low_level_entries
            if entry["source_path"] == LOW_LEVEL_ROOT_PATH
        )
        checklist_entries = tuple(
            entry for entry in low_level_entries
            if entry["source_path"] == LOW_LEVEL_REFERENCE_PREFIX + "checklist.md"
        )
        self.assertEqual(1, len(root_entries))
        self.assertEqual(16, len(checklist_entries))
        self.assertEqual(
            "74263deab6d05975ef81759da425ce4d7ce5bb3f7f735874a9daaec3a9a374c9",
            root_entries[0]["source_rule_fingerprint"],
        )
        self.assertEqual("relocated-existing-reference", root_entries[0]["disposition"])
        self.assertEqual(
            "**Prove ownership and lifetime**: trace acquisition, transfer, borrowing, publication, and release across functions, threads, languages, callbacks, and failure paths.",
            root_entries[0]["old_anchor"],
        )
        self.assertTrue(
            all(
                entry["disposition"] == "split-relocated-new-reference"
                for entry in checklist_entries
            )
        )

    def test_low_level_root_registry_admissibility_and_content_limits_are_exact(self) -> None:
        root_text = (ROOT / LOW_LEVEL_ROOT_PATH).read_text(encoding="utf-8")
        for exact_kernel in (
            "Apply this focused Layer 3 Domain Skill at verified native or operating-system boundaries.",
            "Provide `analysis-agent`, `task-agent`, and `review-agent` with memory, concurrency,",
            "ABI/FFI, syscall, resource, and profiling constraints.",
            "Preserve native ownership/lifetime, unsafe preconditions, ABI consumers, concurrency ordering, syscall/privilege, resource cleanup, arithmetic, and measured-performance invariants.",
            "Bound absence claims by the supported compiler/target/build matrix, analyzed state space, and unproved schedules, platforms, inputs, and foreign behavior.",
            "ABI-compatible syntax can still change allocator ownership, callback lifetime, lock order, arithmetic behavior, or permitted recovery syscalls.",
            "Trace the affected native boundary and consumers.",
            "Load named References for active decision problems.",
            "Verify the selected mechanism within stated limits.",
            "Stop on unverified ownership, ABI consumers, concurrency topology, target, privilege, or recovery.",
            "Escalate exploitable memory, kernel/driver, deadline, or incompatible-consumer risk.",
            "systems invariant, selected mechanism, safety/compatibility and measurement evidence, validation result, proof limits, unverified state space, and residual risk",
        ):
            self.assertEqual(1, root_text.count(exact_kernel))
        self.assertEqual(870, VALIDATION.count_o200k_base_tokens(root_text))
        self.assertEqual(59, len(root_text.splitlines()))
        self.assertLess(VALIDATION.count_o200k_base_tokens(root_text), 900)

        expected_tokens = [144, 138, 88, 166, 232]
        expected_lines = [9, 9, 8, 10, 11]
        expected_counts = [3, 3, 2, 4, 5]
        actual_tokens = []
        for (filename, spec), line_count, decision_count in zip(
            LOW_LEVEL_REFERENCE_SPECS.items(),
            expected_lines,
            expected_counts,
            strict=True,
        ):
            path = ROOT / LOW_LEVEL_REFERENCE_PREFIX / filename
            text = path.read_text(encoding="utf-8")
            actual_tokens.append(VALIDATION.count_o200k_base_tokens(text))
            decision_body = text.split("## Decision Rules\n\n", 1)[1]
            with self.subTest(content=filename):
                self.assertEqual(line_count, len(text.splitlines()))
                self.assertEqual(
                    decision_count,
                    sum(bool(line.strip()) for line in decision_body.splitlines()),
                )
                self.assertLess(line_count, 60)
                self.assertEqual(
                    [],
                    [
                        finding
                        for finding in VALIDATION.ai_readability_findings(text, str(path))
                        if finding.get("severity") == "error"
                    ],
                )
        self.assertEqual(expected_tokens, actual_tokens)
        self.assertEqual(1102, 870 + max(actual_tokens))
        self.assertEqual(1638, 870 + sum(actual_tokens))

        registry = VALIDATION.load_yaml_file(ROOT / "src/registry/domain-skills.yaml")
        low_level = next(
            row for row in registry["domain_skills"]
            if row["name"] == "low-level-systems-extension"
        )
        expected_paths = {
            f"references/{filename}" for filename in LOW_LEVEL_REFERENCE_SPECS
        }
        self.assertEqual(
            expected_paths, {row["path"] for row in low_level["reference_index"]}
        )
        declarations = low_level["context_admissibility"]
        self.assertEqual(
            "changeforge.reference-context-admissibility/v3",
            declarations["contract"],
        )
        self.assertEqual(expected_paths, set(declarations["references"]))
        for filename, spec in LOW_LEVEL_REFERENCE_SPECS.items():
            relative = f"references/{filename}"
            row = next(
                item for item in low_level["reference_index"] if item["path"] == relative
            )
            declaration = declarations["references"][relative]
            with self.subTest(registry=filename):
                self.assertEqual(spec["type"], row["type"])
                self.assertEqual(spec["load_when"], row["load_when"])
                self.assertEqual(spec["do_not_load_when"], row["do_not_load_when"])
                self.assertEqual(list(ALL_ROLES), row["required_by"])
                self.assertEqual(list(spec["required_output"]), row["required_output"])
                self.assertEqual(spec["gap_class"], declaration["gap_class"])
                self.assertEqual(
                    list(spec["route_affecting_surfaces"]),
                    declaration["route_affecting_surfaces"],
                )
                self.assertEqual(Path(filename).stem, declaration["decision_problem"])
                self.assertEqual([], declaration["conflicts_with"])
                self.assertEqual([], declaration["sequenced_after"])
                self.assertEqual([], declaration["must_co_trigger_with"])
                self.assertEqual(
                    (ALL_ROLES, spec["required_output"]),
                    _reference_binding(
                        "low-level-systems-extension",
                        LOW_LEVEL_REFERENCE_PREFIX + filename,
                    ),
                )

        anti_trigger_union = " ".join(
            row["do_not_load_when"] for row in low_level["reference_index"]
        ).casefold()
        for marker in ("native", "abi", "os", "resource boundary"):
            self.assertIn(marker, anti_trigger_union)
        authority = VALIDATION.reference_context_admissibility_authority(
            VALIDATION.load_yaml_file(ROOT / "src/registry/professional-skills.yaml"),
            VALIDATION.load_yaml_file(ROOT / "src/registry/foundation-skills.yaml"),
            registry,
            context="Low-level split focused authority",
        )
        for filename in LOW_LEVEL_REFERENCE_SPECS:
            decision = VALIDATION.reference_context_admissibility_decisions(
                authority,
                references=[("low-level-systems-extension", f"references/{filename}")],
                path="direct",
            )
            with self.subTest(path_decision=filename):
                self.assertFalse(decision["reachable"])
                self.assertEqual("analyzed", decision["minimum_path"])

    def test_security_compaction_restores_every_required_semantic(self) -> None:
        path = ROOT / "src/professional-skills/security-privacy-gate/references/security-output-and-gates.md"
        text = path.read_text(encoding="utf-8")
        for rule in SECURITY_RESTORED_RULES:
            with self.subTest(rule=rule):
                self.assertEqual(1, text.count(rule))

    def test_c1_installed_client_framework_and_language_jit_is_lossless(self) -> None:
        installed_root = ROOT / "src/professional-skills/installed-client-change-builder"
        self.assertFalse((installed_root / "references/framework-contracts.md").exists())
        frameworks = {
            "flutter-framework-contracts.md": (
                "Keep shared widget or state ownership separate from platform-channel ownership.",
                "Test restoration, links, plugins, and packaging on each affected release target in the accepted target set.",
                "Pin the repository SDK, plugins, and native projects before deciding behavior.",
            ),
            "react-native-framework-contracts.md": (
                "Distinguish JavaScript state from native application state and process recreation.",
                "Keep platform-specific behavior in the narrowest existing platform seam.",
            ),
            "electron-framework-contracts.md": (
                "Keep lifecycle and privileged operating-system work in the main-process owner.",
                "Validate renderer-to-main boundaries, deep-link entry, and the packaged artifact.",
            ),
            "tauri-framework-contracts.md": (
                "Keep commands, plugins, capabilities, and webview callers inside their declared authority.",
                "Validate deep-link registration and the platform-specific bundle output.",
            ),
            "qt-framework-contracts.md": (
                "Preserve top-level window ownership and platform-specific window-manager behavior.",
                "Validate runtime libraries, plugins, QML modules, and platform package contents.",
            ),
            "dotnet-maui-framework-contracts.md": (
                "Map cross-platform window events to the affected native lifecycle.",
                "Validate platform lifecycle hooks, restored state, permissions, and each package target.",
            ),
            "kotlin-multiplatform-framework-contracts.md": (
                "Put shared behavior only in source sets whose declared targets support it.",
                "Validate each target compilation and final binary or host-application integration.",
            ),
        }
        combined = ""
        for filename, rules in frameworks.items():
            path = installed_root / "references" / filename
            with self.subTest(filename=filename):
                self.assertTrue(path.is_file())
                text = path.read_text(encoding="utf-8")
                combined += "\n" + text
                self.assertIn("## Decision Rules", text)
                self.assertIn("## Sources And Version Limit", text)
                for rule in rules:
                    self.assertEqual(1, text.count(rule))
        self.assertEqual(15, sum(combined.count(rule) for rules in frameworks.values() for rule in rules))

        roots_and_rules = {
            "csharp-dotnet-professional-usage": (
                "Select `async-resource-and-iterator-contracts` for active async, cancellation, resource, iterator/LINQ, null/type, or DI decisions.",
                "Select `runtime-deployment-and-interop-contracts` for active trim/AOT, loading, native/COM, UI, RID, publish, or deployment decisions.",
                "Bind decisions to current compiler, runtime, target, host, caller, and owner evidence.",
                "Stop on unknown controlling version or boundary.",
            ),
            "kotlin-professional-usage": (
                "When coroutine, cancellation, Flow, shared/state stream, or Compose-state decisions are active, load `coroutine-flow-state-contracts`.",
                "When nullability, Java interop, sealed/reified/value/data/variance, delegate, or DSL decisions are active, load `type-interop-and-dsl-contracts`.",
                "Bind the decision to current compiler/backend, libraries, caller, lifecycle owner, and target evidence.",
                "Stop on an unknown controlling version or boundary.",
            ),
            "swift-professional-usage": (
                "Select `value-memory-and-type-contracts` for active identity, ownership, ARC, copy, Optional, generic/existential, or error decisions.",
                "Select `concurrency-interop-and-ui-contracts` for active actor/Sendable, task/cancellation, continuation, Objective-C, SwiftUI, or package decisions.",
                "Bind decisions to current compiler/mode, target, modules, SDK, package, caller, and owner evidence.",
                "Stop on unknown controlling version or boundary.",
            ),
        }
        for owner, rules in roots_and_rules.items():
            text = (ROOT / "src/foundation/capabilities" / owner / "SKILL.md").read_text(encoding="utf-8")
            with self.subTest(owner=owner):
                self.assertEqual(4, sum(text.count(rule) for rule in rules))
                rule_section = re.search(r"## High-Value Rules\n\n(?P<body>.*?)(?=\n## )", text, flags=re.DOTALL)
                self.assertIsNotNone(rule_section)
                expected_rule_count = 4 if owner == "kotlin-professional-usage" else 3
                self.assertEqual(expected_rule_count, sum(line.startswith("- ") for line in rule_section.group("body").splitlines()))
                for rule in rules:
                    self.assertEqual(1, text.count(rule))
                    self.assertEqual(0, text.replace(rule, "", 1).count(rule))

        self.assertIn(
            "Use repository or runtime evidence to establish coroutine, Compose, lifecycle, compiler, and platform versions because Kotlin and Android documentation is rolling.",
            (ROOT / "src/foundation/capabilities/kotlin-professional-usage/references/coroutine-flow-state-contracts.md").read_text(encoding="utf-8"),
        )
        swift_concurrency = (ROOT / "src/foundation/capabilities/swift-professional-usage/references/concurrency-interop-and-ui-contracts.md").read_text(encoding="utf-8")
        for anchor in (
            "Escaped child, hidden sibling failure, unchecked cancellation.",
            "- Exercise actor reentrancy and affected unsafe/imported non-`Sendable` crossings.",
        ):
            self.assertEqual(1, swift_concurrency.count(anchor))
            self.assertEqual(0, swift_concurrency.replace(anchor, "", 1).count(anchor))

        c1_entries = tuple(
            entry
            for entry in RELOCATION_LEDGER
            if entry["owner"]
            in {
                "installed-client-change-builder",
                "csharp-dotnet-professional-usage",
                "kotlin-professional-usage",
                "swift-professional-usage",
            }
            and entry["disposition"]
            in {
                "returned-to-always-kernel-after-named-jit-split",
                "split-relocated-new-reference",
            }
        )
        self.assertEqual(40, len(c1_entries))

    def test_c1d_data_middleware_kernel_and_companion_ownership_is_lossless(self) -> None:
        for path, expected_sha256 in C1D_CONTENT_HASHES.items():
            text = (ROOT / path).read_text(encoding="utf-8")
            with self.subTest(path=path):
                self.assertEqual(
                    expected_sha256,
                    hashlib.sha256(text.encode("utf-8")).hexdigest(),
                )

        for path, expected_sha256 in C1D_UNCHANGED_REFERENCE_HASHES.items():
            text = (ROOT / path).read_text(encoding="utf-8")
            with self.subTest(unchanged_reference=path):
                self.assertEqual(
                    expected_sha256,
                    hashlib.sha256(text.encode("utf-8")).hexdigest(),
                )

        expected_kernels = {
            "data-migration-design": (
                "Bind source and target authority plus mixed-version readers and writers to one cutover state.",
                "Coordinate live writes and backfill through owned ordering, resumability, semantic validation, and recovery.",
                "Load the named benchmark, checklist, or evidence Reference according to the open output.",
            ),
            "release-rollback": (
                "Bind one release identity and current compatibility decision before exposure or recovery.",
                "Give each changed surface an owned rollback, disable, compensation, restore, reconciliation, or forward-repair path.",
                "Load the named benchmark, checklist, or evidence Reference according to the open output.",
            ),
            "permission-boundary-modeling": (
                "Resolve decision inputs from trusted identity, resource, relationship, policy, or lifecycle state.",
                "Enforce the decision before protected disclosure or effect on each in-scope path.",
                "Load the named benchmark, checklist, or evidence Reference according to the open output.",
            ),
        }
        for owner, rules in expected_kernels.items():
            text = (
                ROOT / "src/foundation/capabilities" / owner / "SKILL.md"
            ).read_text(encoding="utf-8")
            section = re.search(
                r"## High-Value Rules\n\n(?P<body>.*?)(?=\n## )",
                text,
                flags=re.DOTALL,
            )
            with self.subTest(owner=owner):
                self.assertIsNotNone(section)
                assert section is not None
                self.assertEqual(
                    3,
                    sum(
                        line.startswith("- ")
                        for line in section.group("body").splitlines()
                    ),
                )
                for rule in rules:
                    self.assertEqual(1, text.count(rule))

    def test_fg_c1k_installed_client_frontier_is_lossless_and_bounded(self) -> None:
        source_specs = {
            "src/professional-skills/installed-client-change-builder/SKILL.md": ("40b877e360ef3e6dfb793d13a3a5def396b53c77b177366946a8c7391bf7659c", 894),
            "src/professional-skills/installed-client-change-builder/references/native-platform-source-contracts.md": ("7e1fb286caf5638028fbd06f840fe4ce4bcf5a4a5c4e7773df50c43a35ec56d4", 642),
            "src/foundation/capabilities/privacy-data-lifecycle/SKILL.md": ("fa205d22b1adfe249c9fbf3345d58630ec6bb98bb062f13b64f9e56f6f00b9a8", 488),
            "src/foundation/capabilities/privacy-data-lifecycle/references/data-lifecycle-controls.md": ("a9ebaa8be0b55facb1816eed6fce932f992a975c508c6db59c025501f301aef2", 623),
            "src/foundation/capabilities/csharp-dotnet-professional-usage/SKILL.md": ("e2e6cd19efce00ea4f417d96648a814ced208c0f2b12f10239adb040f4aa66da", 493),
            "src/foundation/capabilities/csharp-dotnet-professional-usage/references/async-resource-and-iterator-contracts.md": ("11f62c79d6c383127a3afee5ee940cbba2943606dd2f25af117d3d0cc17cefd7", 670),
            "src/foundation/capabilities/csharp-dotnet-professional-usage/references/runtime-deployment-and-interop-contracts.md": ("9b301a2ffa740333fd99a8775e36af9278d7181abab9cebf52b6a92153ff12bb", 669),
            "src/foundation/capabilities/swift-professional-usage/SKILL.md": ("9634eab0f722a56206d531b274d5ab7a2c340a4ecb3bdda240cd7f9e43a99620", 476),
            "src/foundation/capabilities/swift-professional-usage/references/concurrency-interop-and-ui-contracts.md": ("6f62745217d0de2936a76f58372e05acf4f8ae0524e7ae24d23acf4a717524b9", 671),
            "src/foundation/capabilities/swift-professional-usage/references/value-memory-and-type-contracts.md": ("740caeae10cc30b6c80655ecf5155b713e52762281b4fa9c0b73ea39d3662528", 671),
        }
        for path, (expected_hash, expected_tokens) in source_specs.items():
            text = (ROOT / path).read_text(encoding="utf-8")
            with self.subTest(source=path):
                self.assertEqual(expected_hash, hashlib.sha256(text.encode("utf-8")).hexdigest())
                self.assertEqual(expected_tokens, VALIDATION.count_o200k_base_tokens(text))

        protected_references = {
            "src/professional-skills/installed-client-change-builder/references/dotnet-maui-framework-contracts.md": ("a2443e016ae5e270f6e3f625cc9de4c580b4d5419031c092f9212284539a5baa", 125),
            "src/professional-skills/installed-client-change-builder/references/electron-framework-contracts.md": ("7bae06a3fb6f23031c79f86595d45f5d34b01606d4ad73cbf3a0897bf7f6b8d9", 160),
            "src/professional-skills/installed-client-change-builder/references/flutter-framework-contracts.md": ("0be7ae0cb79cff1634139be1586fb31b275a4a95ff5cc4f6114ad5be1f9cc504", 137),
            "src/professional-skills/installed-client-change-builder/references/kotlin-multiplatform-framework-contracts.md": ("68b9008c125e5ee0181b9cdd81c677ef29a3803ff0ef3b645e36752eb0069cdd", 178),
            "src/professional-skills/installed-client-change-builder/references/qt-framework-contracts.md": ("a00a0182e8f05ba85ba4f923928ffab9350e19e1ce471255d4fccc7b6e85b4ed", 129),
            "src/professional-skills/installed-client-change-builder/references/react-native-framework-contracts.md": ("daa5958b7065ce843c175e4470b487d26dda17f4e2e430edd23f1f1632863cd2", 127),
            "src/professional-skills/installed-client-change-builder/references/tauri-framework-contracts.md": ("365093157fc5bf006d0ee9a29bf4991d8f4e35867f54288e4780246335b131f1", 141),
            "src/foundation/capabilities/privacy-data-lifecycle/references/de-identification-and-provider-controls.md": ("044097a144d73147e53317d8f68bc7c7ba8697ed8c0521552aeaab87f204874f", 603),
        }
        for path, (expected_hash, expected_tokens) in protected_references.items():
            text = (ROOT / path).read_text(encoding="utf-8")
            with self.subTest(protected_reference=path):
                self.assertEqual(expected_hash, hashlib.sha256(text.encode("utf-8")).hexdigest())
                self.assertEqual(expected_tokens, VALIDATION.count_o200k_base_tokens(text))
                self.assertNotEqual(expected_hash, hashlib.sha256((text + " ").encode("utf-8")).hexdigest())

        root_projections = {
            "src/professional-skills/installed-client-change-builder/SKILL.md": ("installed-client-change-builder", "24ac55f2e860ff7b0ec41f18d95b543a024f79157741552f60c064778da6a7ac", 216),
            "src/foundation/capabilities/privacy-data-lifecycle/SKILL.md": (None, "838f2e94146c5d2eab8f5d8d932c4b2aaa74bd64ede1844bc28c2ff5f5bf5356", 230),
            "src/foundation/capabilities/csharp-dotnet-professional-usage/SKILL.md": (None, "57b3d446e87d2aa2293476c1b34e2fe8b38b5332b7428b407fa1995c251ac20c", 247),
            "src/foundation/capabilities/swift-professional-usage/SKILL.md": (None, "5a873c77a0b41cbabd5836a26973987f4b44ddc84b24f18620d09648e1361623", 250),
        }
        for path, (selector, expected_hash, expected_tokens) in root_projections.items():
            _metadata, raw_frontmatter, body = VALIDATION.parse_frontmatter(ROOT / path)
            h1_titles, sections = BUILD._markdown_heading_sections(body)
            headings = (
                BUILD.PROFESSIONAL_BUILT_KERNEL_HEADINGS
                if selector is not None
                else BUILD.FOUNDATION_BUILT_KERNEL_HEADINGS
            )
            output = ["---", raw_frontmatter, "---", "", f"# {h1_titles[0]}"]
            for heading in headings:
                values = sections.get(heading, [])
                if not values and heading == "Inputs":
                    continue
                self.assertEqual(1, len(values))
                self.assertTrue(values[0])
                output.extend(["", f"## {heading}", "", values[0]])
            output.extend(BUILD._compact_jit_reference_delivery_lines(selector))
            output.append("")
            projected = "\n".join(output)
            with self.subTest(root_projection=path):
                self.assertEqual(expected_hash, hashlib.sha256(projected.encode("utf-8")).hexdigest())
                self.assertEqual(expected_tokens, VALIDATION.count_o200k_base_tokens(projected))

        unique_facets = {
            "src/professional-skills/installed-client-change-builder/SKILL.md": (
                "Preserve the accepted route/targets through active named References and carriers.",
                "Main owns release and routing.",
            ),
            "src/foundation/capabilities/privacy-data-lifecycle/SKILL.md": (
                "Map accepted flow through meaning, purpose, and minimization.",
                "Route legal/compliance conclusions to accountable governance.",
            ),
            "src/foundation/capabilities/csharp-dotnet-professional-usage/SKILL.md": (
                "Select `async-resource-and-iterator-contracts` for active async, cancellation, resource, iterator/LINQ, null/type, or DI decisions.",
                "Select `runtime-deployment-and-interop-contracts` for active trim/AOT, loading, native/COM, UI, RID, publish, or deployment decisions.",
            ),
            "src/foundation/capabilities/swift-professional-usage/SKILL.md": (
                "Select `value-memory-and-type-contracts` for active identity, ownership, ARC, copy, Optional, generic/existential, or error decisions.",
                "Select `concurrency-interop-and-ui-contracts` for active actor/Sendable, task/cancellation, continuation, Objective-C, SwiftUI, or package decisions.",
            ),
        }
        for path, facets in unique_facets.items():
            text = (ROOT / path).read_text(encoding="utf-8")
            for facet in facets:
                with self.subTest(root_facet=path, facet=facet):
                    self.assertEqual(1, text.count(facet))
                    self.assertEqual(0, text.replace(facet, "", 1).count(facet))

        reference_paths = tuple(sorted(
            path for path in (*source_specs, *protected_references)
            if path.endswith(".md") and not path.endswith("/SKILL.md")
        ))
        self.assertEqual(14, len(reference_paths))
        reference_tokens = {
            path: VALIDATION.count_o200k_base_tokens((ROOT / path).read_text(encoding="utf-8"))
            for path in reference_paths
        }
        self.assertLessEqual(max(reference_tokens.values()), 671)
        self.assertEqual(671, max(reference_tokens.values()))

        self.assertEqual(943, sum(item[2] for item in root_projections.values()))
        projected_sum = 3_466 - (1_079 - 943) - (1_010 - 671)
        self.assertEqual(2_991, projected_sum)
        self.assertEqual(2_990, projected_sum - 1)
        self.assertEqual(2_997, projected_sum + 6)
        self.assertLessEqual(projected_sum + 6, 3_000)
        self.assertGreater(projected_sum + 10, 3_000)

        protected_hashes = {
            "src/registry/professional-skills.yaml": "32a3b49da13930f3baccf54dbd8de12064b1f07d273b2948dfaeb12586eaf49a",
            "src/registry/foundation-skills.yaml": "385843496634f9e9ef4426790cacff211858cab4f73c6c15f521fc2732b5b8fd",
            "src/registry/domain-skills.yaml": "2d53ccc4206c94d9850e007d21603f04ba1f06f7721de5da1cd47dcfe6e16129",
            "scripts/build.py": "2543ed2c2cb7498babeae20d1f7bd244f968522f116c90b8b08c4106a25efcf1",
            "scripts/validation_utils.py": "a76092b2d24cdfaec66eb44e1f8d4e48a9f76d9dda8a875a3b5602771649f995",
        }
        for path, expected_hash in protected_hashes.items():
            text = (ROOT / path).read_text(encoding="utf-8")
            with self.subTest(protected=path):
                self.assertEqual(expected_hash, hashlib.sha256(text.encode("utf-8")).hexdigest())

    def test_post_b_installed_client_state_jit_is_lossless_and_bounded(self) -> None:
        for path, expected_sha256 in POST_B_TASK_CONTENT_HASHES.items():
            text = (ROOT / path).read_text(encoding="utf-8")
            with self.subTest(content_hash=path):
                self.assertEqual(
                    expected_sha256,
                    hashlib.sha256(text.encode("utf-8")).hexdigest(),
                )

        for path, expected_sha256 in POST_B_TASK_PROTECTED_HASHES.items():
            text = (ROOT / path).read_text(encoding="utf-8")
            with self.subTest(protected_hash=path):
                self.assertEqual(
                    expected_sha256,
                    hashlib.sha256(text.encode("utf-8")).hexdigest(),
                )
                self.assertNotEqual(
                    expected_sha256,
                    hashlib.sha256((text + " ").encode("utf-8")).hexdigest(),
                )

        fingerprints = []
        for source_path, old_rule, destinations in POST_B_TASK_RULE_RELOCATIONS:
            fingerprint = _fingerprint(old_rule)
            fingerprints.append(fingerprint)
            with self.subTest(rule=fingerprint, source=source_path):
                self.assertNotIn(
                    old_rule,
                    (ROOT / source_path).read_text(encoding="utf-8"),
                )
                self.assertRegex(fingerprint, r"^[0-9a-f]{64}$")
            for destination, anchors in destinations:
                destination_text = (ROOT / destination).read_text(
                    encoding="utf-8"
                )
                for anchor in anchors:
                    with self.subTest(rule=fingerprint, destination=destination):
                        self.assertEqual(1, destination_text.count(anchor))
                        self.assertNotEqual(
                            1,
                            destination_text.replace(anchor, "", 1).count(anchor),
                        )
        self.assertEqual(len(fingerprints), len(set(fingerprints)))

        for path, expected_tokens in POST_B_TASK_BUILT_TOKENS.items():
            text = (ROOT / path).read_text(encoding="utf-8")
            if path.endswith("/SKILL.md"):
                selector = (
                    "installed-client-change-builder"
                    if path.startswith("src/professional-skills/")
                    else None
                )
                _metadata, raw_frontmatter, body = VALIDATION.parse_frontmatter(
                    ROOT / path
                )
                h1_titles, sections = BUILD._markdown_heading_sections(body)
                headings = (
                    BUILD.PROFESSIONAL_BUILT_KERNEL_HEADINGS
                    if selector is not None
                    else BUILD.FOUNDATION_BUILT_KERNEL_HEADINGS
                )
                output = [
                    "---",
                    raw_frontmatter,
                    "---",
                    "",
                    f"# {h1_titles[0]}",
                ]
                for heading in headings:
                    values = sections.get(heading, [])
                    if not values and heading == "Inputs":
                        continue
                    self.assertEqual(1, len(values))
                    self.assertTrue(values[0])
                    output.extend(["", f"## {heading}", "", values[0]])
                output.extend(BUILD._compact_jit_reference_delivery_lines(selector))
                output.append("")
                projected = "\n".join(output)
            else:
                projected = text
            with self.subTest(token_budget=path):
                self.assertEqual(
                    expected_tokens,
                    VALIDATION.count_o200k_base_tokens(projected),
                )

        professional = VALIDATION.load_yaml_file(
            ROOT / "src/registry/professional-skills.yaml"
        )
        foundation = VALIDATION.load_yaml_file(
            ROOT / "src/registry/foundation-skills.yaml"
        )
        domain = VALIDATION.load_yaml_file(
            ROOT / "src/registry/domain-skills.yaml"
        )
        self.assertEqual(
            "32a3b49da13930f3baccf54dbd8de12064b1f07d273b2948dfaeb12586eaf49a",
            hashlib.sha256(
                (ROOT / "src/registry/professional-skills.yaml").read_bytes()
            ).hexdigest(),
        )
        self.assertEqual(
            "385843496634f9e9ef4426790cacff211858cab4f73c6c15f521fc2732b5b8fd",
            hashlib.sha256(
                (ROOT / "src/registry/foundation-skills.yaml").read_bytes()
            ).hexdigest(),
        )
        self.assertEqual(
            "2d53ccc4206c94d9850e007d21603f04ba1f06f7721de5da1cd47dcfe6e16129",
            hashlib.sha256(
                (ROOT / "src/registry/domain-skills.yaml").read_bytes()
            ).hexdigest(),
        )

        selector_authority = VALIDATION.layer3_selector_authority(
            foundation,
            professional,
            domain,
            context="post-B installed-client state witness",
        )
        projection = VALIDATION.layer3_selector_runtime_projection(
            selector_authority,
            professional_skill="installed-client-change-builder",
            profile="task-agent",
            selection_owner="main-control-agent",
            exact_layer3=None,
        )
        receipt = VALIDATION.layer3_selector_runtime_selection_receipt(
            projection,
            evidence_signals=[
                "client visibility background process termination relaunch "
                "crash upgrade logout account-switch restoration",
                "installed or browser client read write queue reconcile delete "
                "or resume across connectivity loss and restoration",
                "choose local server global derived optimistic and persisted "
                "state boundaries",
            ],
        )
        expected_layer3 = [
            "client-lifecycle-state-restoration",
            "offline-sync-conflict-resolution",
            "state-management-design",
        ]
        self.assertEqual(expected_layer3, receipt["selected_layer3"])
        self.assertEqual(
            "9c6b2f9def3f5314f1ff5c33197eb02855d86238fc59f2e7676b4e19d1ac6643",
            receipt["receipt_sha256"],
        )
        self.assertNotEqual(
            receipt["receipt_sha256"],
            {**receipt, "receipt_sha256": "0" * 64}["receipt_sha256"],
        )

        context_authority = VALIDATION.reference_context_admissibility_authority(
            professional,
            foundation,
            domain,
            context="post-B installed-client state staged witness",
        )
        staged = VALIDATION.reference_context_staged_plan(
            context_authority,
            references=POST_B_TASK_SELECTED_REFERENCES,
            path="direct",
            profile="task-agent",
            selection_owner="main-control-agent",
            available_carrier_fields=[],
            receipt_replayed=True,
            brief_current=False,
            review_fresh=True,
        )
        expected_selected_union = [
            list(item) for item in POST_B_TASK_SELECTED_REFERENCES
        ]
        expected_loaded_union = [
            [
                "client-lifecycle-state-restoration",
                "references/restoration-boundaries.md",
            ],
            [
                "installed-client-change-builder",
                "references/dotnet-maui-framework-contracts.md",
            ],
            [
                "installed-client-change-builder",
                "references/electron-framework-contracts.md",
            ],
            [
                "installed-client-change-builder",
                "references/flutter-framework-contracts.md",
            ],
            [
                "installed-client-change-builder",
                "references/kotlin-multiplatform-framework-contracts.md",
            ],
            [
                "installed-client-change-builder",
                "references/native-platform-source-contracts.md",
            ],
            [
                "installed-client-change-builder",
                "references/qt-framework-contracts.md",
            ],
            [
                "installed-client-change-builder",
                "references/react-native-framework-contracts.md",
            ],
            [
                "installed-client-change-builder",
                "references/tauri-framework-contracts.md",
            ],
            [
                "offline-sync-conflict-resolution",
                "references/sync-reconciliation-contracts.md",
            ],
            [
                "state-management-design",
                "references/benchmarks-and-patterns.md",
            ],
            ["state-management-design", "references/checklist.md"],
            ["state-management-design", "references/evidence-patterns.md"],
        ]
        self.assertTrue(staged["reachable"])
        self.assertEqual(expected_selected_union, staged["selected_union"])
        self.assertEqual(expected_loaded_union, staged["loaded_union"])
        self.assertEqual(13, len(staged["selected_union"]))
        self.assertEqual(13, len(staged["loaded_union"]))
        self.assertEqual(
            {tuple(item) for item in expected_selected_union},
            {tuple(item) for item in expected_loaded_union},
        )
        self.assertNotEqual(
            expected_selected_union,
            expected_selected_union[:-1],
        )
        self.assertNotEqual(expected_loaded_union, expected_loaded_union[:-1])
        domain_names = {
            row["name"] for row in domain["domain_skills"]
        }
        self.assertEqual(
            set(),
            {owner for owner, _path in POST_B_TASK_SELECTED_REFERENCES}
            & domain_names,
        )
        active_reference = [
            "offline-sync-conflict-resolution",
            "references/sync-reconciliation-contracts.md",
        ]
        active_stage = next(
            stage
            for stage in staged["stages"]
            if stage["loaded_references"] == [active_reference]
        )
        self.assertEqual(13, len(staged["stages"]))
        self.assertEqual(9, active_stage["stage"])
        self.assertEqual([active_reference], active_stage["loaded_references"])
        self.assertEqual([], active_stage["carried_predecessors"])
        self.assertEqual([], staged["carried_predecessors"])
        expected_output = ["selected-approach", "proof-limit", "residual-risk"]
        expected_receipt = {
            "reference": active_reference,
            "required_outputs": expected_output,
        }
        self.assertEqual(
            [expected_receipt],
            active_stage["required_output_receipts"],
        )
        self.assertEqual(13, len(staged["required_output_receipts"]))
        self.assertEqual(
            expected_receipt,
            staged["required_output_receipts"][9],
        )
        self.assertNotEqual(expected_output, expected_output[:-1])

        components = [
            697,
            657,
            POST_B_TASK_BUILT_TOKENS[
                "src/professional-skills/installed-client-change-builder/SKILL.md"
            ],
            POST_B_TASK_BUILT_TOKENS[
                "src/foundation/capabilities/client-lifecycle-state-restoration/SKILL.md"
            ],
            POST_B_TASK_BUILT_TOKENS[
                "src/foundation/capabilities/offline-sync-conflict-resolution/SKILL.md"
            ],
            POST_B_TASK_BUILT_TOKENS[
                "src/foundation/capabilities/state-management-design/SKILL.md"
            ],
            POST_B_TASK_BUILT_TOKENS[
                "src/foundation/capabilities/offline-sync-conflict-resolution/references/sync-reconciliation-contracts.md"
            ],
        ]
        self.assertEqual(2_613, sum(components))
        separator_tokens = VALIDATION.count_o200k_base_tokens("\n\n")
        self.assertEqual(1, separator_tokens)
        component_upper = sum(components) + separator_tokens * (len(components) - 1)
        self.assertEqual(2_619, component_upper)
        self.assertLessEqual(component_upper, 3_000)
        self.assertEqual(3_001, component_upper + 382)

    def test_post_b_ai_review_cross_platform_jit_is_lossless_and_bounded(
        self,
    ) -> None:
        for path, expected_sha256 in POST_B_REVIEW_CONTENT_HASHES.items():
            text = (ROOT / path).read_text(encoding="utf-8")
            with self.subTest(content_hash=path):
                self.assertEqual(
                    expected_sha256,
                    hashlib.sha256(text.encode("utf-8")).hexdigest(),
                )

        for path, expected_sha256 in POST_B_REVIEW_PROTECTED_HASHES.items():
            text = (ROOT / path).read_text(encoding="utf-8")
            with self.subTest(protected_hash=path):
                self.assertEqual(
                    expected_sha256,
                    hashlib.sha256(text.encode("utf-8")).hexdigest(),
                )
                self.assertNotEqual(
                    expected_sha256,
                    hashlib.sha256((text + " ").encode("utf-8")).hexdigest(),
                )

        fingerprints = []
        for path, old_rule, current_anchor in POST_B_REVIEW_RULE_RELOCATIONS:
            text = (ROOT / path).read_text(encoding="utf-8")
            fingerprint = _fingerprint(old_rule)
            fingerprints.append(fingerprint)
            with self.subTest(rule=fingerprint, path=path):
                self.assertRegex(fingerprint, r"^[0-9a-f]{64}$")
                self.assertNotIn(old_rule, text)
                self.assertEqual(1, text.count(current_anchor))
                self.assertNotEqual(
                    1,
                    text.replace(current_anchor, "", 1).count(current_anchor),
                )
        self.assertEqual(len(fingerprints), len(set(fingerprints)))
        self.assertIn(
            "a3b3050e006433aa8a1582b20d81283cb4b5cd10c83b3aab72f4211fde48a33f",
            fingerprints,
        )

        def compact_projection(
            path: str,
            headings: tuple[str, ...],
            selector: str | None,
        ) -> str:
            _metadata, raw_frontmatter, body = VALIDATION.parse_frontmatter(
                ROOT / path
            )
            h1_titles, sections = BUILD._markdown_heading_sections(body)
            self.assertEqual(1, len(h1_titles))
            output = [
                "---",
                raw_frontmatter,
                "---",
                "",
                f"# {h1_titles[0]}",
            ]
            for heading in headings:
                values = sections.get(heading, [])
                if not values and heading == "Inputs":
                    continue
                self.assertEqual(1, len(values))
                self.assertTrue(values[0])
                output.extend(["", f"## {heading}", "", values[0]])
            output.extend(BUILD._compact_jit_reference_delivery_lines(selector))
            output.append("")
            return "\n".join(output)

        cross_path = (
            "src/domain-extensions/cross-platform-client-extension/SKILL.md"
        )
        cross_projection = compact_projection(
            cross_path,
            BUILD.PROFESSIONAL_BUILT_KERNEL_HEADINGS,
            None,
        )
        self.assertEqual(
            POST_B_REVIEW_BUILT_TOKENS[cross_path],
            VALIDATION.count_o200k_base_tokens(cross_projection),
        )
        self.assertEqual(
            "e7ae448387f1d7f79e38bdb876d09c80f1b798be00fd2fe4bb6f98c7e9f89b8f",
            hashlib.sha256(cross_projection.encode("utf-8")).hexdigest(),
        )
        review_reference_path = (
            "src/professional-skills/ai-code-review-refactor/"
            "references/review-output-and-gates.md"
        )
        self.assertEqual(
            POST_B_REVIEW_BUILT_TOKENS[review_reference_path],
            VALIDATION.count_o200k_base_tokens(
                (ROOT / review_reference_path).read_text(encoding="utf-8")
            ),
        )
        fixed_root_specs = (
            (
                "src/professional-skills/ai-code-review-refactor/SKILL.md",
                BUILD.PROFESSIONAL_BUILT_KERNEL_HEADINGS,
                "ai-code-review-refactor",
                275,
            ),
            (
                "src/foundation/capabilities/design-pattern-selection/SKILL.md",
                BUILD.FOUNDATION_BUILT_KERNEL_HEADINGS,
                None,
                222,
            ),
            (
                "src/foundation/capabilities/implementation-structure-design/SKILL.md",
                BUILD.FOUNDATION_BUILT_KERNEL_HEADINGS,
                None,
                302,
            ),
        )
        for path, headings, selector, expected_tokens in fixed_root_specs:
            with self.subTest(fixed_root=path):
                self.assertEqual(
                    expected_tokens,
                    VALIDATION.count_o200k_base_tokens(
                        compact_projection(path, headings, selector)
                    ),
                )

        professional = VALIDATION.load_yaml_file(
            ROOT / "src/registry/professional-skills.yaml"
        )
        foundation = VALIDATION.load_yaml_file(
            ROOT / "src/registry/foundation-skills.yaml"
        )
        domain = VALIDATION.load_yaml_file(ROOT / "src/registry/domain-skills.yaml")
        registry_hashes = {
            "src/registry/professional-skills.yaml": "32a3b49da13930f3baccf54dbd8de12064b1f07d273b2948dfaeb12586eaf49a",
            "src/registry/foundation-skills.yaml": "385843496634f9e9ef4426790cacff211858cab4f73c6c15f521fc2732b5b8fd",
            "src/registry/domain-skills.yaml": "2d53ccc4206c94d9850e007d21603f04ba1f06f7721de5da1cd47dcfe6e16129",
        }
        for path, expected_sha256 in registry_hashes.items():
            with self.subTest(registry=path):
                self.assertEqual(
                    expected_sha256,
                    hashlib.sha256((ROOT / path).read_bytes()).hexdigest(),
                )

        selector_authority = VALIDATION.layer3_selector_authority(
            foundation,
            professional,
            domain,
            context="post-B AI review cross-platform witness",
        )
        projection = VALIDATION.layer3_selector_runtime_projection(
            selector_authority,
            professional_skill="ai-code-review-refactor",
            profile="review-agent",
            selection_owner="engineering-brief",
            exact_layer3=None,
        )
        receipt = VALIDATION.layer3_selector_runtime_selection_receipt(
            projection,
            evidence_signals=[
                "shared installed client",
                "concrete platform targets",
                "changed-surface",
                "design-pattern-change",
                "analysis-only-action",
            ],
        )
        expected_layer3 = [
            "cross-platform-client-extension",
            "design-pattern-selection",
            "implementation-structure-design",
        ]
        self.assertEqual(expected_layer3, receipt["selected_layer3"])
        self.assertEqual(
            "c5b8d737ac8a43584998f469790adb29da4bd37db17bd6c9e619d9f5c61a542b",
            receipt["receipt_sha256"],
        )
        self.assertNotEqual(
            receipt["receipt_sha256"],
            {**receipt, "receipt_sha256": "0" * 64}["receipt_sha256"],
        )

        context_authority = VALIDATION.reference_context_admissibility_authority(
            professional,
            foundation,
            domain,
            context="post-B AI review cross-platform staged witness",
        )
        staged = VALIDATION.reference_context_staged_plan(
            context_authority,
            references=POST_B_REVIEW_SELECTED_REFERENCES,
            path="analyzed",
            profile="review-agent",
            selection_owner="engineering-brief",
            available_carrier_fields=context_authority["carrier_fields"][
                "review-agent"
            ]["engineering-brief"],
            receipt_replayed=True,
            brief_current=True,
            review_fresh=True,
        )
        expected_selected_union = [
            list(item) for item in POST_B_REVIEW_SELECTED_REFERENCES
        ]
        expected_loaded_union = [
            ["ai-code-review-refactor", "references/ai-review-pattern-catalog.md"],
            ["ai-code-review-refactor", "references/review-output-and-gates.md"],
            ["ai-code-review-refactor", "references/solution-optimality.md"],
            [
                "cross-platform-client-extension",
                "references/bridge-plugin-and-ffi-contracts.md",
            ],
            [
                "cross-platform-client-extension",
                "references/framework-target-evidence-contracts.md",
            ],
            [
                "cross-platform-client-extension",
                "references/parity-and-regression-contracts.md",
            ],
            [
                "cross-platform-client-extension",
                "references/shared-and-target-ownership-contracts.md",
            ],
            ["design-pattern-selection", "references/pattern-evidence-record.md"],
            ["implementation-structure-design", "references/evidence-patterns.md"],
            [
                "implementation-structure-design",
                "references/object-module-decomposition.md",
            ],
            [
                "implementation-structure-design",
                "references/reuse-and-placement.md",
            ],
        ]
        self.assertTrue(staged["reachable"])
        self.assertEqual(expected_selected_union, staged["selected_union"])
        self.assertEqual(expected_loaded_union, staged["loaded_union"])
        self.assertEqual(11, len(staged["selected_union"]))
        self.assertEqual(11, len(staged["loaded_union"]))
        self.assertEqual(
            {tuple(item) for item in expected_selected_union},
            {tuple(item) for item in expected_loaded_union},
        )
        self.assertNotEqual(expected_selected_union, expected_selected_union[:-1])
        self.assertNotEqual(expected_loaded_union, expected_loaded_union[:-1])
        domain_names = {row["name"] for row in domain["domain_skills"]}
        self.assertEqual(
            {"cross-platform-client-extension"},
            {owner for owner, _path in POST_B_REVIEW_SELECTED_REFERENCES}
            & domain_names,
        )
        active_reference = [
            "ai-code-review-refactor",
            "references/review-output-and-gates.md",
        ]
        active_stage = next(
            stage
            for stage in staged["stages"]
            if stage["loaded_references"] == [active_reference]
        )
        self.assertEqual(11, len(staged["stages"]))
        self.assertEqual(1, active_stage["stage"])
        self.assertEqual([], active_stage["carried_predecessors"])
        self.assertEqual([], staged["carried_predecessors"])
        expected_output = ["gate-decision", "residual-risk"]
        expected_receipt = {
            "reference": active_reference,
            "required_outputs": expected_output,
        }
        self.assertEqual(
            [expected_receipt],
            active_stage["required_output_receipts"],
        )
        self.assertEqual(11, len(staged["required_output_receipts"]))
        self.assertEqual(
            expected_receipt,
            staged["required_output_receipts"][1],
        )
        self.assertNotEqual(expected_output, expected_output[:-1])

        components = [
            561,
            275,
            222,
            302,
            785,
            POST_B_REVIEW_BUILT_TOKENS[cross_path],
            POST_B_REVIEW_BUILT_TOKENS[review_reference_path],
        ]
        self.assertEqual(2_943, sum(components))
        separator_tokens = VALIDATION.count_o200k_base_tokens("\n\n")
        self.assertEqual(1, separator_tokens)
        component_upper = sum(components) + separator_tokens * (len(components) - 1)
        self.assertEqual(2_949, component_upper)
        self.assertLessEqual(component_upper, 3_700)
        self.assertEqual(3_701, component_upper + 752)

    def test_c1f_repository_and_reliability_content_is_lossless_and_bounded(self) -> None:
        for path, expected_sha256 in C1F_FINAL_SOURCE_HASHES.items():
            text = (ROOT / path).read_text(encoding="utf-8")
            with self.subTest(source_hash=path):
                self.assertEqual(expected_sha256, hashlib.sha256(text.encode("utf-8")).hexdigest())
                for anchor in C1F_RULE_OWNER_ANCHORS[path]:
                    self.assertEqual(1, text.count(anchor))

        for path, (selector, expected_tokens, expected_sha256) in C1F_BUILT_PROJECTION_SPECS.items():
            _metadata, raw_frontmatter, body = VALIDATION.parse_frontmatter(ROOT / path)
            h1_titles, sections = BUILD._markdown_heading_sections(body)
            headings = BUILD.PROFESSIONAL_BUILT_KERNEL_HEADINGS if selector is not None else BUILD.FOUNDATION_BUILT_KERNEL_HEADINGS
            output = ["---", raw_frontmatter, "---", "", f"# {h1_titles[0]}"]
            for heading in headings:
                values = sections.get(heading, [])
                if not values and heading == "Inputs":
                    continue
                self.assertEqual(1, len(values))
                output.extend(["", f"## {heading}", "", values[0]])
            output.extend(BUILD._compact_jit_reference_delivery_lines(selector))
            output.append("")
            projection = "\n".join(output)
            with self.subTest(built_projection=path):
                self.assertEqual(expected_tokens, VALIDATION.count_o200k_base_tokens(projection))
                self.assertEqual(expected_sha256, hashlib.sha256(projection.encode("utf-8")).hexdigest())

        for path, expected_sha256 in {
            "src/registry/professional-skills.yaml": "32a3b49da13930f3baccf54dbd8de12064b1f07d273b2948dfaeb12586eaf49a",
            "src/registry/foundation-skills.yaml": "385843496634f9e9ef4426790cacff211858cab4f73c6c15f521fc2732b5b8fd",
            "src/registry/domain-skills.yaml": "2d53ccc4206c94d9850e007d21603f04ba1f06f7721de5da1cd47dcfe6e16129",
        }.items():
            self.assertEqual(expected_sha256, hashlib.sha256((ROOT / path).read_bytes()).hexdigest())

        task_fixed = 697 + 261 + 222 + 269 + 223 + 657
        self.assertEqual(2_329, task_fixed)
        self.assertEqual(2_760, task_fixed + 431)
        self.assertEqual(2_766, task_fixed + 431 + 6)
        self.assertLessEqual(task_fixed + 431 + 6, 3_000)
        review_fixed = 561 + 341 + 209 + 180 + 224 + 785
        self.assertEqual(2_300, review_fixed)
        self.assertEqual(2_930, review_fixed + 630)
        self.assertEqual(2_936, review_fixed + 630 + 6)
        self.assertLessEqual(review_fixed + 630 + 6, 3_700)

    def test_fg_r1c_reliability_reference_frontier_is_complete_and_bounded(self) -> None:
        reference_specs = {
            "src/professional-skills/reliability-observability-gate/references/checklist.md": (433, "9c53232be1010c24c3845ecae6f44e9a0f0657382cc9288bfb9ab20747b42a88"),
            "src/professional-skills/reliability-observability-gate/references/evidence-patterns.md": (392, "d08296d182ea7f25047d99a24a6ce6d3a64e10a5558adef3fc605a24988a86d2"),
            "src/professional-skills/reliability-observability-gate/references/reliability-output-and-gates.md": (630, "d961e283581fd22648f6d1a7e37cf516621315d117ef61670424a78bba1ae6b3"),
            "src/professional-skills/reliability-observability-gate/references/solution-optimality.md": (288, "9927e42ee974c29fdb0f2ad0e4516d5cfa5df2cf10c813ce4b83d75432b7ad96"),
            "src/foundation/capabilities/degradation-circuit-breaking/references/benchmarks-and-patterns.md": (610, "2ce97e80ec657c3f6eedf127fe9842885dc8eaedc1fcfd1a238556a40750e1c6"),
            "src/foundation/capabilities/degradation-circuit-breaking/references/checklist.md": (385, "6b1ac1327e6edb36126c2dc7d338bc44c1d24de957dbd416099eb4e88036b3ad"),
            "src/foundation/capabilities/degradation-circuit-breaking/references/evidence-patterns.md": (468, "be5e9b06d53aa99dd3c0ff07ea228d2d3ac997b69711ab5be60bb8d9754abab6"),
            "src/foundation/capabilities/observability/references/benchmarks-and-patterns.md": (590, "f5b75daaca0e1e6ebeafe49bdb12ad221ba865e7d8203e7b64f8ed29c7567b66"),
            "src/foundation/capabilities/observability/references/checklist.md": (252, "12c336a527b9a91e83007ccf2cf11fec3394fecdffbb1d9633c40a6f7cf4f230"),
            "src/foundation/capabilities/observability/references/evidence-patterns.md": (470, "c5ead790acd816494f684e5ec2454006415d1abc6c405048a461671e9bdc26ca"),
            "src/foundation/capabilities/backup-recovery/references/benchmarks-and-patterns.md": (414, "5013f1ac42d41ab389b3a81c56db9bf3d231bac81c895b3d7ba2d5405098c8f6"),
            "src/foundation/capabilities/backup-recovery/references/checklist.md": (219, "80db2eb859fd3bea13c0b37f9e1b4f69d8f001f2f46d30c5f156626843e90e6c"),
            "src/foundation/capabilities/backup-recovery/references/evidence-patterns.md": (615, "e4093df7ef353013bc32df6b30a8b07e52c567304ab4fea36f920eede8e48062"),
        }
        self.assertEqual(13, len(reference_specs))
        for path, (expected_tokens, expected_sha256) in reference_specs.items():
            text = (ROOT / path).read_text(encoding="utf-8")
            with self.subTest(reference=path):
                self.assertEqual(expected_sha256, hashlib.sha256(text.encode("utf-8")).hexdigest())
                self.assertEqual(expected_tokens, VALIDATION.count_o200k_base_tokens(text))

        for path, expected_sha256 in {
            "src/registry/professional-skills.yaml": "32a3b49da13930f3baccf54dbd8de12064b1f07d273b2948dfaeb12586eaf49a",
            "src/registry/foundation-skills.yaml": "385843496634f9e9ef4426790cacff211858cab4f73c6c15f521fc2732b5b8fd",
            "tests/scripts/test_reference_registry_jit.py": "c4730adbdb7a5bdbae7ab24d979f563a2fab17d5fb634d83326a00d0dd00ad85",
            "tests/scripts/test_eval_rendered_context_budget.py": "9bc52e95f1ad5e6a3d5a8ad164eb789172c6b2b2b374749e42ddc12df9237a5a",
        }.items():
            with self.subTest(protected_hash=path):
                self.assertEqual(expected_sha256, hashlib.sha256((ROOT / path).read_bytes()).hexdigest())

        root_tokens = 341 + 209 + 180 + 224
        self.assertEqual(954, root_tokens)
        self.assertEqual(630, max(spec[0] for spec in reference_specs.values()))
        self.assertEqual(2_961, 3_503 - (1_183 - root_tokens) - (943 - 630))
        self.assertEqual(2_960, 3_502 - (1_183 - root_tokens) - (943 - 630))
        self.assertEqual(2_967, 3_509 - (1_183 - root_tokens) - (943 - 630))
        self.assertLessEqual(2_967, 3_000)
        self.assertEqual(3_001, 2_967 + 34)

    def test_c1g_delivery_compatibility_and_configuration_content_is_lossless_and_bounded(self) -> None:
        for path, expected_sha256 in C1G_FINAL_SOURCE_HASHES.items():
            text = (ROOT / path).read_text(encoding="utf-8")
            with self.subTest(source_hash=path):
                self.assertEqual(
                    expected_sha256,
                    hashlib.sha256(text.encode("utf-8")).hexdigest(),
                )
                for anchor in C1G_RULE_OWNER_ANCHORS[path]:
                    self.assertEqual(1, text.count(anchor))

        for path, expected_sha256 in C1G_PROTECTED_HASHES.items():
            with self.subTest(protected_hash=path):
                self.assertEqual(
                    expected_sha256,
                    hashlib.sha256((ROOT / path).read_bytes()).hexdigest(),
                )

        for path, (selector, expected_tokens, expected_sha256) in C1G_BUILT_PROJECTION_SPECS.items():
            _metadata, raw_frontmatter, body = VALIDATION.parse_frontmatter(ROOT / path)
            h1_titles, sections = BUILD._markdown_heading_sections(body)
            headings = (
                BUILD.PROFESSIONAL_BUILT_KERNEL_HEADINGS
                if selector is not None
                else BUILD.FOUNDATION_BUILT_KERNEL_HEADINGS
            )
            output = ["---", raw_frontmatter, "---", "", f"# {h1_titles[0]}"]
            for heading in headings:
                values = sections.get(heading, [])
                if not values and heading == "Inputs":
                    continue
                self.assertEqual(1, len(values))
                output.extend(["", f"## {heading}", "", values[0]])
            output.extend(BUILD._compact_jit_reference_delivery_lines(selector))
            output.append("")
            projection = "\n".join(output)
            with self.subTest(built_projection=path):
                self.assertEqual(
                    expected_tokens,
                    VALIDATION.count_o200k_base_tokens(projection),
                )
                if expected_sha256 is not None:
                    self.assertEqual(
                        expected_sha256,
                        hashlib.sha256(projection.encode("utf-8")).hexdigest(),
                    )

        reference_tokens = []
        for owner, relative_path in C1G_SELECTED_REFERENCES:
            root = (
                ROOT / "src/professional-skills" / owner
                if owner == "delivery-release-gate"
                else ROOT / "src/foundation/capabilities" / owner
            )
            reference_tokens.append(
                VALIDATION.count_o200k_base_tokens(
                    (root / relative_path).read_text(encoding="utf-8")
                )
            )
        self.assertEqual(474, max(reference_tokens))

        professional = VALIDATION.load_yaml_file(
            ROOT / "src/registry/professional-skills.yaml"
        )
        foundation = VALIDATION.load_yaml_file(
            ROOT / "src/registry/foundation-skills.yaml"
        )
        domain = VALIDATION.load_yaml_file(ROOT / "src/registry/domain-skills.yaml")
        authority = VALIDATION.reference_context_admissibility_authority(
            professional,
            foundation,
            domain,
            context="C1G delivery compatibility and configuration witness",
        )
        staged = VALIDATION.reference_context_staged_plan(
            authority,
            references=C1G_SELECTED_REFERENCES,
            path="direct",
            profile="task-agent",
            selection_owner="main-control-agent",
            available_carrier_fields=[],
            receipt_replayed=True,
            brief_current=False,
            review_fresh=True,
        )
        expected_selected_union = [list(reference) for reference in C1G_SELECTED_REFERENCES]
        expected_loaded_union = [list(reference) for reference in sorted(C1G_SELECTED_REFERENCES)]
        self.assertTrue(staged["reachable"])
        self.assertEqual(expected_selected_union, staged["selected_union"])
        self.assertEqual(expected_loaded_union, staged["loaded_union"])
        self.assertEqual(12, len(staged["stages"]))
        self.assertEqual([], staged["carried_predecessors"])
        self.assertEqual(
            {tuple(reference) for reference in expected_selected_union},
            {tuple(reference) for reference in expected_loaded_union},
        )
        active_reference = [
            "version-compatibility",
            "references/compatibility-benchmarks.md",
        ]
        active_stage = next(
            stage
            for stage in staged["stages"]
            if stage["loaded_references"] == [active_reference]
        )
        self.assertEqual(10, active_stage["stage"])
        self.assertEqual([], active_stage["carried_predecessors"])
        self.assertEqual(
            [{
                "reference": active_reference,
                "required_outputs": ["option-comparison", "selected-approach"],
            }],
            active_stage["required_output_receipts"],
        )

        relevant_ledger = [
            entry
            for entry in RELOCATION_LEDGER
            if entry["owner"]
            in {
                "delivery-release-gate",
                "version-compatibility",
                "configuration-runtime-policy",
            }
        ]
        self.assertEqual(
            {
                "delivery-release-gate",
                "version-compatibility",
                "configuration-runtime-policy",
            },
            {entry["owner"] for entry in relevant_ledger},
        )
        self.assertTrue(
            all(
                entry["route_effect"] == "unchanged"
                and entry["co_trigger_effect"] == "unchanged"
                for entry in relevant_ledger
            )
        )

        task_components = [697, 310, 229, 250, 183, 474, 657]
        self.assertEqual(2_800, sum(task_components))
        self.assertEqual(2_806, sum(task_components) + 6)
        self.assertLessEqual(sum(task_components) + 6, 3_000)
        review_components = [561, 310, 229, 250, 183, 474, 785]
        self.assertEqual(2_792, sum(review_components))
        self.assertEqual(2_798, sum(review_components) + 6)
        self.assertLessEqual(sum(review_components) + 6, 3_700)

    def test_c1j_data_middleware_content_is_lossless_and_route_stable(self) -> None:
        mismatches = []
        for path, pre_sha256, post_sha256, tokens, anchors in C1J_SOURCE_SPECS:
            actual_sha256 = hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
            if actual_sha256 != post_sha256:
                with self.subTest(source_preimage=path):
                    self.assertEqual(pre_sha256, actual_sha256)
                mismatches.append(path)
            with self.subTest(source_hash=path):
                self.assertEqual(post_sha256, actual_sha256)
            if actual_sha256 == post_sha256:
                text = (ROOT / path).read_text(encoding="utf-8")
                with self.subTest(source_tokens=path):
                    self.assertEqual(tokens, VALIDATION.count_o200k_base_tokens(text))
                for anchor in anchors:
                    with self.subTest(source_anchor=path, anchor=anchor[:48]):
                        self.assertEqual(1, text.count(anchor))
        if mismatches:
            return

        for path, expected_sha256 in C1J_PROTECTED_HASHES.items():
            with self.subTest(protected_hash=path):
                self.assertEqual(
                    expected_sha256,
                    hashlib.sha256((ROOT / path).read_bytes()).hexdigest(),
                )

        for path, (expected_tokens, expected_sha256) in C1J_BUILT_PROJECTION_SPECS.items():
            _metadata, raw_frontmatter, body = VALIDATION.parse_frontmatter(ROOT / path)
            h1_titles, sections = BUILD._markdown_heading_sections(body)
            output = ["---", raw_frontmatter, "---", "", f"# {h1_titles[0]}"]
            for heading in BUILD.FOUNDATION_BUILT_KERNEL_HEADINGS:
                values = sections.get(heading, [])
                if not values and heading == "Inputs":
                    continue
                self.assertEqual(1, len(values))
                output.extend(["", f"## {heading}", "", values[0]])
            output.extend(BUILD._compact_jit_reference_delivery_lines(None))
            output.append("")
            projection = "\n".join(output)
            with self.subTest(built_projection=path):
                self.assertEqual(expected_tokens, VALIDATION.count_o200k_base_tokens(projection))
                self.assertEqual(expected_sha256, hashlib.sha256(projection.encode("utf-8")).hexdigest())

        reference_tokens = []
        for (owner, relative_path), expected_tokens in C1J_REFERENCE_TOKENS.items():
            owner_root = (
                ROOT / "src/professional-skills" / owner
                if owner == "data-middleware-change-builder"
                else ROOT / "src/foundation/capabilities" / owner
            )
            actual_tokens = VALIDATION.count_o200k_base_tokens(
                (owner_root / relative_path).read_text(encoding="utf-8")
            )
            with self.subTest(reference=owner + "/" + relative_path):
                self.assertEqual(expected_tokens, actual_tokens)
            reference_tokens.append(actual_tokens)
        self.assertEqual(608, max(reference_tokens))

        professional = VALIDATION.load_yaml_file(ROOT / "src/registry/professional-skills.yaml")
        foundation = VALIDATION.load_yaml_file(ROOT / "src/registry/foundation-skills.yaml")
        domain = VALIDATION.load_yaml_file(ROOT / "src/registry/domain-skills.yaml")
        selector_authority = VALIDATION.layer3_selector_authority(
            foundation, professional, domain, context="C1J data-middleware content witness"
        )
        projection = VALIDATION.layer3_selector_runtime_projection(
            selector_authority,
            professional_skill="data-middleware-change-builder",
            profile="task-agent",
            selection_owner="main-control-agent",
            exact_layer3=None,
        )
        evidence_signals = ["cache-stampede", "distributed-effect-change"]
        receipt = VALIDATION.layer3_selector_runtime_selection_receipt(
            projection, evidence_signals=evidence_signals
        )
        self.assertEqual(
            ["concurrency-control", "transaction-consistency", "distributed-workflow-consistency"],
            receipt["selected_layer3"],
        )
        self.assertEqual(
            "781c2b9d96451b0dee91dfce30b51f91e692fee664219aa8a0c127e6a70f204e",
            receipt["receipt_sha256"],
        )
        without_cache_stampede = VALIDATION.layer3_selector_runtime_selection_receipt(
            projection, evidence_signals=evidence_signals[1:]
        )
        self.assertNotEqual(receipt["selected_layer3"], without_cache_stampede["selected_layer3"])
        self.assertNotEqual(receipt["receipt_sha256"], without_cache_stampede["receipt_sha256"])

        authority = VALIDATION.reference_context_admissibility_authority(
            professional, foundation, domain, context="C1J data-middleware staged witness"
        )
        staged = VALIDATION.reference_context_staged_plan(
            authority,
            references=C1J_SELECTED_REFERENCES,
            path="direct",
            profile="task-agent",
            selection_owner="main-control-agent",
            available_carrier_fields=[],
            receipt_replayed=True,
            brief_current=False,
            review_fresh=True,
        )
        expected_selected_union = [list(reference) for reference in C1J_SELECTED_REFERENCES]
        expected_loaded_union = [list(reference) for reference in sorted(C1J_SELECTED_REFERENCES)]
        self.assertTrue(staged["reachable"])
        self.assertEqual(expected_selected_union, staged["selected_union"])
        self.assertEqual(expected_loaded_union, staged["loaded_union"])
        self.assertEqual(12, len(staged["stages"]))
        self.assertEqual(
            [[reference] for reference in expected_loaded_union],
            [stage["loaded_references"] for stage in staged["stages"]],
        )
        self.assertTrue(all(stage["carried_predecessors"] == [] for stage in staged["stages"]))
        self.assertEqual([], staged["carried_predecessors"])
        self.assertEqual(
            {tuple(reference) for reference in expected_selected_union},
            {tuple(reference) for reference in expected_loaded_union},
        )
        domain_names = {row["name"] for row in domain["domain_skills"]}
        self.assertEqual(set(), {owner for owner, _path in C1J_SELECTED_REFERENCES} & domain_names)
        benchmark_reference = ["transaction-consistency", "references/benchmarks-and-patterns.md"]
        benchmark_stage = next(
            stage for stage in staged["stages"] if stage["loaded_references"] == [benchmark_reference]
        )
        self.assertEqual(9, benchmark_stage["stage"])
        self.assertEqual(
            [{"reference": benchmark_reference, "required_outputs": ["option-comparison", "selected-approach"]}],
            benchmark_stage["required_output_receipts"],
        )
        evidence_reference = ["transaction-consistency", "references/evidence-patterns.md"]
        evidence_stage = next(
            stage for stage in staged["stages"] if stage["loaded_references"] == [evidence_reference]
        )
        self.assertEqual(11, evidence_stage["stage"])
        self.assertEqual(
            [{"reference": evidence_reference, "required_outputs": ["evidence-record", "proof-limit", "residual-risk"]}],
            evidence_stage["required_output_receipts"],
        )
        self.assertEqual(12, len(staged["required_output_receipts"]))

        relevant_ledger = [
            entry for entry in RELOCATION_LEDGER
            if entry["owner"] in {"concurrency-control", "transaction-consistency", "distributed-workflow-consistency"}
        ]
        self.assertEqual(
            {"concurrency-control", "transaction-consistency", "distributed-workflow-consistency"},
            {entry["owner"] for entry in relevant_ledger},
        )
        self.assertTrue(all(
            entry["route_effect"] == "unchanged" and entry["co_trigger_effect"] == "unchanged"
            for entry in relevant_ledger
        ))

        task_components = [697, 269, 214, 283, 246, 608, 657]
        self.assertEqual(2_974, sum(task_components))
        self.assertEqual(2_980, sum(task_components) + 6)
        self.assertLessEqual(sum(task_components) + 6, 3_000)

    def test_c1i_quality_content_is_lossless_and_route_stable(self) -> None:
        mismatches = []
        for path, expected_sha256 in C1I_FINAL_SOURCE_HASHES.items():
            text = (ROOT / path).read_text(encoding="utf-8")
            actual_sha256 = hashlib.sha256(text.encode("utf-8")).hexdigest()
            if actual_sha256 != expected_sha256:
                with self.subTest(source_preimage=path):
                    self.assertEqual(C1I_PRE_SOURCE_HASHES[path], actual_sha256)
                mismatches.append(path)
            with self.subTest(source_hash=path):
                self.assertEqual(expected_sha256, actual_sha256)
        if mismatches:
            return

        for path, expected_tokens in C1I_SOURCE_TOKENS.items():
            text = (ROOT / path).read_text(encoding="utf-8")
            with self.subTest(source_tokens=path):
                self.assertEqual(
                    expected_tokens,
                    VALIDATION.count_o200k_base_tokens(text),
                )
                for anchor in C1I_RULE_OWNER_ANCHORS[path]:
                    self.assertEqual(1, text.count(anchor))

        for path, expected_sha256 in C1I_PROTECTED_HASHES.items():
            with self.subTest(protected_hash=path):
                self.assertEqual(
                    expected_sha256,
                    hashlib.sha256((ROOT / path).read_bytes()).hexdigest(),
                )

        for path, (selector, expected_tokens, expected_sha256) in (
            C1I_BUILT_PROJECTION_SPECS.items()
        ):
            _metadata, raw_frontmatter, body = VALIDATION.parse_frontmatter(
                ROOT / path
            )
            h1_titles, sections = BUILD._markdown_heading_sections(body)
            headings = (
                BUILD.PROFESSIONAL_BUILT_KERNEL_HEADINGS
                if selector is not None
                else BUILD.FOUNDATION_BUILT_KERNEL_HEADINGS
            )
            output = ["---", raw_frontmatter, "---", "", f"# {h1_titles[0]}"]
            for heading in headings:
                values = sections.get(heading, [])
                self.assertEqual(1, len(values))
                output.extend(["", f"## {heading}", "", values[0]])
            output.extend(BUILD._compact_jit_reference_delivery_lines(selector))
            output.append("")
            projection = "\n".join(output)
            with self.subTest(built_projection=path):
                self.assertEqual(
                    expected_tokens,
                    VALIDATION.count_o200k_base_tokens(projection),
                )
                self.assertEqual(
                    expected_sha256,
                    hashlib.sha256(projection.encode("utf-8")).hexdigest(),
                )

        reference_tokens = []
        for owner, relative_path in C1I_SELECTED_REFERENCES:
            root = (
                ROOT / "src/professional-skills" / owner
                if owner == "quality-test-gate"
                else ROOT / "src/foundation/capabilities" / owner
            )
            reference_tokens.append(
                VALIDATION.count_o200k_base_tokens(
                    (root / relative_path).read_text(encoding="utf-8")
                )
            )
        self.assertEqual(565, max(reference_tokens))

        professional = VALIDATION.load_yaml_file(
            ROOT / "src/registry/professional-skills.yaml"
        )
        foundation = VALIDATION.load_yaml_file(
            ROOT / "src/registry/foundation-skills.yaml"
        )
        domain = VALIDATION.load_yaml_file(ROOT / "src/registry/domain-skills.yaml")
        selector_authority = VALIDATION.layer3_selector_authority(
            foundation,
            professional,
            domain,
            context="C1I quality content witness",
        )
        projection = VALIDATION.layer3_selector_runtime_projection(
            selector_authority,
            professional_skill="quality-test-gate",
            profile="task-agent",
            selection_owner="main-control-agent",
            exact_layer3=None,
        )
        evidence_signals = [
            "explicit-test-data-decision",
            "an accepted proof strategy needs exact repository-defined commands",
            "analysis-action",
        ]
        receipt = VALIDATION.layer3_selector_runtime_selection_receipt(
            projection,
            evidence_signals=evidence_signals,
        )
        self.assertEqual(
            [
                "test-data-management",
                "targeted-validation-selection",
                "test-strategy",
            ],
            receipt["selected_layer3"],
        )
        self.assertEqual(
            "0c9aa8b856780e9aecfa385003bc7f2b87167ed326e3863b570c79af4a7848a9",
            receipt["receipt_sha256"],
        )
        without_test_data = VALIDATION.layer3_selector_runtime_selection_receipt(
            projection,
            evidence_signals=evidence_signals[1:],
        )
        self.assertNotEqual(
            receipt["selected_layer3"],
            without_test_data["selected_layer3"],
        )
        self.assertNotEqual(
            receipt["receipt_sha256"],
            without_test_data["receipt_sha256"],
        )

        authority = VALIDATION.reference_context_admissibility_authority(
            professional,
            foundation,
            domain,
            context="C1I quality content staged witness",
        )
        staged = VALIDATION.reference_context_staged_plan(
            authority,
            references=C1I_SELECTED_REFERENCES,
            path="direct",
            profile="task-agent",
            selection_owner="main-control-agent",
            available_carrier_fields=[],
            receipt_replayed=True,
            brief_current=False,
            review_fresh=True,
        )
        expected_selected_union = [
            list(reference) for reference in C1I_SELECTED_REFERENCES
        ]
        expected_loaded_union = [
            list(reference) for reference in sorted(C1I_SELECTED_REFERENCES)
        ]
        self.assertTrue(staged["reachable"])
        self.assertEqual(expected_selected_union, staged["selected_union"])
        self.assertEqual(expected_loaded_union, staged["loaded_union"])
        self.assertEqual(10, len(staged["stages"]))
        self.assertEqual(
            [[reference] for reference in expected_loaded_union],
            [stage["loaded_references"] for stage in staged["stages"]],
        )
        self.assertTrue(
            all(stage["carried_predecessors"] == [] for stage in staged["stages"])
        )
        self.assertEqual([], staged["carried_predecessors"])
        self.assertEqual(
            {tuple(reference) for reference in expected_selected_union},
            {tuple(reference) for reference in expected_loaded_union},
        )
        self.assertNotEqual(
            expected_selected_union,
            expected_selected_union[:-1],
        )
        self.assertNotEqual(expected_loaded_union, expected_loaded_union[:-1])
        domain_names = {row["name"] for row in domain["domain_skills"]}
        self.assertEqual(
            set(),
            {owner for owner, _path in C1I_SELECTED_REFERENCES} & domain_names,
        )
        active_reference = [
            "test-strategy",
            "references/evidence-patterns.md",
        ]
        active_stage = next(
            stage
            for stage in staged["stages"]
            if stage["loaded_references"] == [active_reference]
        )
        self.assertEqual(9, active_stage["stage"])
        self.assertEqual([], active_stage["carried_predecessors"])
        self.assertEqual(
            [{
                "reference": active_reference,
                "required_outputs": [
                    "evidence-record",
                    "proof-limit",
                    "residual-risk",
                ],
            }],
            active_stage["required_output_receipts"],
        )
        self.assertEqual(10, len(staged["required_output_receipts"]))

    def test_frontend_direct_jit_split_is_source_owned_and_bounded(self) -> None:
        registries = {
            "professional": VALIDATION.load_yaml_file(
                ROOT / "src/registry/professional-skills.yaml"
            )["professional_skills"],
            "foundation": VALIDATION.load_yaml_file(
                ROOT / "src/registry/foundation-skills.yaml"
            )["foundation_skills"],
        }
        for owner, owner_spec in FRONTEND_JIT_OWNER_SPECS.items():
            root_path = ROOT / owner_spec["root"]
            root_text = root_path.read_text(encoding="utf-8")
            projected_root = (
                root_text.split("\n## Targeted References", 1)[0]
                + "\n\n## JIT Reference Delivery\n\n"
                + "Current-Professional JIT. Exact skips it; never select/reroute/preload\n"
                + "index/catalog.\n"
            )
            with self.subTest(owner=owner, boundary="root-cap"):
                self.assertLessEqual(
                    VALIDATION.count_o200k_base_tokens(projected_root),
                    owner_spec["cap"],
                )

            entry = next(
                item
                for item in registries[owner_spec["registry"]]
                if item["name"] == owner
            )
            contracts = {item["path"]: item for item in entry["reference_index"]}
            admissibility = entry["context_admissibility"]
            self.assertEqual(
                "changeforge.reference-context-admissibility/v3",
                admissibility["contract"],
            )

            for removed in owner_spec["removed"]:
                with self.subTest(owner=owner, removed=removed):
                    self.assertNotIn(removed, contracts)
                    self.assertFalse((root_path.parent / removed).exists())

            for relative_path, spec in owner_spec["references"].items():
                ref_type, roles, outputs, gap_class, surfaces = spec
                physical = root_path.parent / relative_path
                with self.subTest(owner=owner, reference=relative_path):
                    self.assertTrue(physical.is_file())
                    self.assertLessEqual(
                        VALIDATION.count_o200k_base_tokens(
                            physical.read_text(encoding="utf-8")
                        ),
                        400,
                    )
                    self.assertEqual(
                        {
                            "path": relative_path,
                            "type": ref_type,
                            "load_when": contracts[relative_path]["load_when"],
                            "do_not_load_when": contracts[relative_path]["do_not_load_when"],
                            "required_by": list(roles),
                            "required_output": list(outputs),
                        },
                        contracts[relative_path],
                    )
                    declaration = admissibility["references"][relative_path]
                    self.assertEqual(gap_class, declaration["gap_class"])
                    self.assertEqual(list(surfaces), declaration["route_affecting_surfaces"])
                    self.assertEqual([], declaration["conflicts_with"])
                    self.assertEqual(relative_path.removeprefix("references/").removesuffix(".md"), declaration["decision_problem"])
                    self.assertEqual([], declaration["sequenced_after"])
                    self.assertEqual([], declaration["must_co_trigger_with"])
                    self.assertNotIn("carried_by", declaration)

        frontend_specs = FRONTEND_JIT_OWNER_SPECS["frontend-change-builder"]["references"]
        self.assertEqual(6, len(frontend_specs))
        self.assertEqual(
            18,
            sum(
                len(spec["references"])
                for owner, spec in FRONTEND_JIT_OWNER_SPECS.items()
                if owner != "frontend-change-builder"
            ),
        )

    def test_review_architecture_jit_split_is_source_owned_and_bounded(self) -> None:
        registries = {
            "professional": VALIDATION.load_yaml_file(
                ROOT / "src/registry/professional-skills.yaml"
            )["professional_skills"],
            "foundation": VALIDATION.load_yaml_file(
                ROOT / "src/registry/foundation-skills.yaml"
            )["foundation_skills"],
        }
        for relative_path, expected_sha256 in REVIEW_JIT_IMMUTABLE_HASHES.items():
            with self.subTest(path=relative_path, boundary="immutable"):
                self.assertEqual(
                    expected_sha256,
                    hashlib.sha256((ROOT / relative_path).read_bytes()).hexdigest(),
                )

        review_inventory: set[tuple[str, str]] = set()
        for owner, owner_spec in REVIEW_JIT_OWNER_SPECS.items():
            root_path = ROOT / owner_spec["root"]
            root_text = root_path.read_text(encoding="utf-8")
            if owner_spec["cap"] is not None:
                _metadata, raw_frontmatter, body = VALIDATION.parse_frontmatter(
                    root_path
                )
                h1_titles, sections = BUILD._markdown_heading_sections(body)
                self.assertEqual(1, len(h1_titles))
                headings = (
                    BUILD.PROFESSIONAL_BUILT_KERNEL_HEADINGS
                    if owner_spec["registry"] == "professional"
                    else BUILD.FOUNDATION_BUILT_KERNEL_HEADINGS
                )
                selector = owner if owner_spec["registry"] == "professional" else None
                output = [
                    "---",
                    raw_frontmatter,
                    "---",
                    "",
                    f"# {h1_titles[0]}",
                ]
                for heading in headings:
                    values = sections.get(heading, [])
                    self.assertEqual(1, len(values))
                    self.assertTrue(values[0])
                    output.extend(["", f"## {heading}", "", values[0]])
                output.extend(BUILD._compact_jit_reference_delivery_lines(selector))
                output.append("")
                projected_root = "\n".join(output)
                _projected_h1, projected_sections = (
                    BUILD._markdown_heading_sections(projected_root)
                )
                self.assertEqual(
                    [*headings, "JIT Reference Delivery"],
                    list(projected_sections),
                )
                with self.subTest(owner=owner, boundary="root-cap"):
                    self.assertLessEqual(
                        VALIDATION.count_o200k_base_tokens(projected_root),
                        owner_spec["cap"],
                    )
                if owner == "architecture-impact-reviewer":
                    self.assertIn("## High-Value Gotchas", root_text)
                    self.assertIn("## Execution Checklist", root_text)
                    self.assertNotIn("## High-Value Gotchas", projected_root)
                    self.assertNotIn("## Execution Checklist", projected_root)
                    self.assertEqual(
                        317,
                        VALIDATION.count_o200k_base_tokens(projected_root),
                    )
                    self.assertEqual(
                        "6141a381dec084f4b21dbd8caa858eaab6d30d158aedb95df67e66b49c235d78",
                        hashlib.sha256(projected_root.encode("utf-8")).hexdigest(),
                    )

            entry = next(
                item
                for item in registries[owner_spec["registry"]]
                if item["name"] == owner
            )
            contracts = {item["path"]: item for item in entry["reference_index"]}
            admissibility = entry["context_admissibility"]
            self.assertEqual(
                "changeforge.reference-context-admissibility/v3",
                admissibility["contract"],
            )

            for removed in owner_spec["removed"]:
                with self.subTest(owner=owner, removed=removed):
                    self.assertNotIn(removed, contracts)
                    self.assertFalse((root_path.parent / removed).exists())

            expected_paths = set(owner_spec["references"])
            self.assertEqual(expected_paths, set(contracts) - {"references/index.md"})
            for relative_path, spec in owner_spec["references"].items():
                ref_type, roles, outputs, gap_class, surfaces, cap = spec
                physical = root_path.parent / relative_path
                review_inventory.add((owner, relative_path))
                with self.subTest(owner=owner, reference=relative_path):
                    self.assertTrue(physical.is_file())
                    if cap is not None:
                        self.assertLessEqual(
                            VALIDATION.count_o200k_base_tokens(
                                physical.read_text(encoding="utf-8")
                            ),
                            cap,
                        )
                    self.assertEqual(
                        {
                            "path": relative_path,
                            "type": ref_type,
                            "load_when": contracts[relative_path]["load_when"],
                            "do_not_load_when": contracts[relative_path]["do_not_load_when"],
                            "required_by": list(roles),
                            "required_output": list(outputs),
                        },
                        contracts[relative_path],
                    )
                    declaration = admissibility["references"][relative_path]
                    self.assertEqual(gap_class, declaration["gap_class"])
                    self.assertEqual(
                        list(surfaces), declaration["route_affecting_surfaces"]
                    )
                    self.assertEqual([], declaration["conflicts_with"])
                    self.assertEqual([], declaration["sequenced_after"])
                    self.assertEqual([], declaration["must_co_trigger_with"])
                    self.assertNotIn("carried_by", declaration)

        self.assertEqual(13, len(review_inventory))
        for old_fragment, destination in REVIEW_JIT_FRAGMENT_DESTINATIONS.items():
            destination_text = (ROOT / destination).read_text(encoding="utf-8")
            owner_root = next(
                ROOT / spec["root"]
                for owner, spec in REVIEW_JIT_OWNER_SPECS.items()
                if destination.startswith(str((ROOT / spec["root"]).parent.relative_to(ROOT)))
            )
            owner_text = owner_root.read_text(encoding="utf-8")
            reference_text = "\n".join(
                (owner_root.parent / relative_path).read_text(encoding="utf-8")
                for relative_path in REVIEW_JIT_OWNER_SPECS[owner_root.parent.name]["references"]
            )
            with self.subTest(fragment=old_fragment[:48]):
                self.assertNotIn(old_fragment, owner_text)
                self.assertEqual(1, destination_text.count(old_fragment))
                self.assertEqual(1, reference_text.count(old_fragment))

    def test_fg_r1b_security_frontier_is_lossless_and_bounded(self) -> None:
        source_specs = {
            "src/professional-skills/security-privacy-gate/SKILL.md": (
                "43e7f925fbf76beedfc59c3f859757b081c92a0769bc80b0edce00a162f864cd",
                "f11d7bdde385a27584a4b22e07cd389adc4c59d8933597433238c4ecc5ba7ae5",
                940,
            ),
            "src/domain-extensions/ai-product-extension/SKILL.md": (
                "e8d6fc19bdded0944dacf89c37ca32e36bc21dc947bbf74c4dff82c10b3bc3db",
                "26315ec6803a7eda4dd4a38375d6c9edc1be069eb29aad52b233d199ee847860",
                430,
            ),
            "src/domain-extensions/ai-product-extension/references/checklist.md": (
                "bec98ce924a11e5c68b830086f2f384b76ca6e661cdfcfd3771062903c4ed94a",
                "0adcb38e5532c235fdd20fecb1a6e906c5a4a163ef95d9a1fd740b9dbe3637f9",
                738,
            ),
            "src/foundation/capabilities/secret-configuration-security/SKILL.md": (
                "3249bf4c59907e1e600e2d0553f6fa38391ba12efa89813e75d828efbc918837",
                "40e92045d2137d2de50fa4293d094aa0c7afc4c40fdccb5733e1fc1a203d6616",
                493,
            ),
            "src/foundation/capabilities/cryptography-key-lifecycle/SKILL.md": (
                "181f483f20ab5d68cf0883d5b42c00dd474b377418c3e85d9e4724072f455ee1",
                "218b09a82cecd316d0fd4152bb7df4b3ea16805f4676dad74f292a3ecb66b5d9",
                547,
            ),
            "src/foundation/capabilities/cryptography-key-lifecycle/references/primitives-nonces-and-envelopes.md": (
                "6b7236d832a14b2e901b53719d8d57e98dbd0c415a69309b3b4b80f18f8ed2e0",
                "107b7d4dd676cb7e82a6c6d2eeeb6576fc38e26f829969dfb3b090017e4399e6",
                759,
            ),
            "src/foundation/capabilities/cryptography-key-lifecycle/references/compromise-destruction-and-agility.md": (
                "0cff76fb2486eb7a7f7f8d0ba5385749ccb278669956fa09ece6284ca103cab1",
                "46b35c3c9d9eb968a26685e57300b9c39e0277dd911cf775e95a20afc94e89fc",
                753,
            ),
        }
        for path, (old_sha256, expected_sha256, expected_tokens) in source_specs.items():
            text = (ROOT / path).read_text(encoding="utf-8")
            current_sha256 = hashlib.sha256(text.encode("utf-8")).hexdigest()
            with self.subTest(source=path):
                self.assertNotEqual(old_sha256, current_sha256)
                self.assertEqual(expected_sha256, current_sha256)
                self.assertEqual(
                    expected_tokens,
                    VALIDATION.count_o200k_base_tokens(text),
                )

        projection_specs = {
            "src/professional-skills/security-privacy-gate/SKILL.md": (
                "security-privacy-gate",
                280,
                "ec28b25d629d3cc1d16eb3bb1060d8746b543fa9f85ee81a023fbd8ea28fdcee",
            ),
            "src/domain-extensions/ai-product-extension/SKILL.md": (
                None,
                198,
                "3437d17718fd1b22dafc2f171c99faad630d78e51dfd86bd8514fced8e8211f4",
            ),
            "src/foundation/capabilities/secret-configuration-security/SKILL.md": (
                None,
                202,
                "c0bddf002b385fddd4834ad4670cdc91cb539b22bfc3b1ed2870dff423439d2b",
            ),
            "src/foundation/capabilities/cryptography-key-lifecycle/SKILL.md": (
                None,
                193,
                "8b1bb04146140fc51ba3198a1bb7f8cce46a5747ddfe71699df17d172f7254d8",
            ),
        }
        for path, (selector, expected_tokens, expected_sha256) in projection_specs.items():
            _metadata, raw_frontmatter, body = VALIDATION.parse_frontmatter(ROOT / path)
            h1_titles, sections = BUILD._markdown_heading_sections(body)
            headings = (
                BUILD.PROFESSIONAL_BUILT_KERNEL_HEADINGS
                if "professional-skills" in path or "domain-extensions" in path
                else BUILD.FOUNDATION_BUILT_KERNEL_HEADINGS
            )
            output = ["---", raw_frontmatter, "---", "", f"# {h1_titles[0]}"]
            for heading in headings:
                values = sections.get(heading, [])
                self.assertEqual(1, len(values))
                self.assertTrue(values[0])
                output.extend(["", f"## {heading}", "", values[0]])
            output.extend(BUILD._compact_jit_reference_delivery_lines(selector))
            output.append("")
            projection = "\n".join(output)
            with self.subTest(projection=path):
                self.assertEqual(
                    expected_tokens,
                    VALIDATION.count_o200k_base_tokens(projection),
                )
                self.assertEqual(
                    expected_sha256,
                    hashlib.sha256(projection.encode("utf-8")).hexdigest(),
                )

        security_root = (
            ROOT / "src/professional-skills/security-privacy-gate/SKILL.md"
        ).read_text(encoding="utf-8")
        self.assertEqual(1, security_root.count("## High-Value Gotchas"))
        self.assertEqual(1, security_root.count("## Execution Checklist"))
        self.assertEqual(
            1,
            security_root.count(
                "Select the named Reference owning the reachable-path control decision."
            ),
        )
        self.assertEqual(
            1,
            security_root.count(
                "Stop when exploit-relevant evidence does not establish policy, "
                "reachability, and control applicability."
            ),
        )
        self.assertEqual(
            1,
            security_root.count(
                "Reject abuse without a privilege path or less-trusted writer."
            ),
        )

        ai_root = (
            ROOT / "src/domain-extensions/ai-product-extension/SKILL.md"
        ).read_text(encoding="utf-8")
        self.assertEqual(
            1,
            ai_root.count(
                "Focused Layer 3 Domain Skill: `analysis-agent` maps authority, "
                "`task-agent` applies controls, `review-agent` judges evidence."
            ),
        )

        ai_checklist = (
            ROOT / "src/domain-extensions/ai-product-extension/references/checklist.md"
        ).read_text(encoding="utf-8")
        self.assertNotIn("## Product Decision Rules", ai_checklist)
        for facet in (
            "Keep low-impact output proportional without universal citations",
            "Govern retrieval data and indexes by source permission",
            "Separate trusted policy, user input, retrieved content",
            "Bind tool calls to identity, principal, argument schema",
            "Compare baseline and treatment across representative success",
            "Minimize authorized context data to the task need.",
            "Treat model output as untrusted",
            "Map provider-bound and retained AI data",
            "## Failure Gotchas",
            "## Execution Closure",
        ):
            with self.subTest(ai_facet=facet):
                self.assertEqual(1, ai_checklist.count(facet))

        crypto_root = (
            ROOT / "src/foundation/capabilities/cryptography-key-lifecycle/SKILL.md"
        ).read_text(encoding="utf-8")
        self.assertEqual(
            1,
            crypto_root.count(
                "Select named References for coupled construction, transition, or "
                "compromise decisions."
            ),
        )
        primitives = (
            ROOT
            / "src/foundation/capabilities/cryptography-key-lifecycle/references/primitives-nonces-and-envelopes.md"
        ).read_text(encoding="utf-8")
        compromise = (
            ROOT
            / "src/foundation/capabilities/cryptography-key-lifecycle/references/compromise-destruction-and-agility.md"
        ).read_text(encoding="utf-8")
        for facet in (
            "Derive nonce uniqueness, permitted reuse, and misuse-resistance bounds",
            "Cross-read supported writers/readers; reject malformed or unsupported envelopes.",
            "https://csrc.nist.gov/pubs/sp/800/38/d/final",
            "https://www.rfc-editor.org/rfc/rfc9771.html",
        ):
            with self.subTest(primitive_facet=facet):
                self.assertEqual(1, primitives.count(facet))
        for facet in (
            "Treat revocation as neither copy erasure nor reversal of prior disclosure.",
            "| Compromise scope |",
            "| Destruction proof |",
            "| Transition |",
            "https://csrc.nist.gov/pubs/cswp/39/upd1/considerations-for-achieving-crypto-agility/final",
            "https://docs.aws.amazon.com/kms/latest/developerguide/deleting-keys.html",
        ):
            with self.subTest(compromise_facet=facet):
                self.assertEqual(1, compromise.count(facet))

        reference_specs = {
            "src/domain-extensions/ai-product-extension/references/checklist.md": (
                "ai-product-extension",
                ("checklist-result", "residual-risk"),
                738,
                "0adcb38e5532c235fdd20fecb1a6e906c5a4a163ef95d9a1fd740b9dbe3637f9",
            ),
            "src/foundation/capabilities/cryptography-key-lifecycle/references/compromise-destruction-and-agility.md": (
                "cryptography-key-lifecycle",
                ("failure-decision", "boundary-decision", "residual-risk"),
                753,
                "46b35c3c9d9eb968a26685e57300b9c39e0277dd911cf775e95a20afc94e89fc",
            ),
            "src/foundation/capabilities/cryptography-key-lifecycle/references/primitives-nonces-and-envelopes.md": (
                "cryptography-key-lifecycle",
                ("selected-approach", "boundary-decision", "proof-limit"),
                759,
                "107b7d4dd676cb7e82a6c6d2eeeb6576fc38e26f829969dfb3b090017e4399e6",
            ),
            "src/foundation/capabilities/cryptography-key-lifecycle/references/rotation-versioning-and-recovery.md": (
                "cryptography-key-lifecycle",
                ("boundary-decision", "validation-plan", "proof-limit"),
                665,
                "f964ec75061aeeb281c33846a18c1adb2eb11e2ebd91de42c280e9761ff571fc",
            ),
            "src/foundation/capabilities/secret-configuration-security/references/benchmarks-and-patterns.md": (
                "secret-configuration-security",
                ("option-comparison", "selected-approach"),
                458,
                "edfa0183f4b7180db71918938787f61fa3cba8a5a427c4d5267bfc68a623dae4",
            ),
            "src/foundation/capabilities/secret-configuration-security/references/checklist.md": (
                "secret-configuration-security",
                ("checklist-result", "residual-risk"),
                243,
                "28cbaaa87e146bd84c24f79099eb4834a202d801230fa854acd8499f5aec089e",
            ),
            "src/foundation/capabilities/secret-configuration-security/references/evidence-patterns.md": (
                "secret-configuration-security",
                ("evidence-record", "proof-limit", "residual-risk"),
                444,
                "637b32426f4236deb0dee1c23588584e6ff137882900b61a315aecd660be490a",
            ),
            "src/professional-skills/security-privacy-gate/references/checklist.md": (
                "security-privacy-gate",
                ("checklist-result", "residual-risk"),
                136,
                "059a2463147824418c686f1cd1565ca3cfb85f3fb99eb2dd37f5ff2aa8144514",
            ),
            "src/professional-skills/security-privacy-gate/references/evidence-patterns.md": (
                "security-privacy-gate",
                ("evidence-record", "proof-limit", "residual-risk"),
                427,
                "3e368eb8ddcef3e77a22de4d38ff0d2fac022702e9f9cca471811815b5a2fbc8",
            ),
            "src/professional-skills/security-privacy-gate/references/security-output-and-gates.md": (
                "security-privacy-gate",
                ("gate-decision", "residual-risk"),
                625,
                "05129afaa245591be03b05cd5c2edc5dcfd5b494002d2dd70a9891b2d253f81e",
            ),
        }
        for path, (owner, outputs, expected_tokens, expected_sha256) in reference_specs.items():
            text = (ROOT / path).read_text(encoding="utf-8")
            with self.subTest(reference=path):
                self.assertEqual(
                    expected_sha256,
                    hashlib.sha256(text.encode("utf-8")).hexdigest(),
                )
                self.assertEqual(
                    expected_tokens,
                    VALIDATION.count_o200k_base_tokens(text),
                )
                self.assertEqual(
                    (ALL_ROLES, outputs),
                    _reference_binding(owner, path),
                )

        root_tokens = 280 + 198 + 202 + 193
        self.assertEqual(873, root_tokens)
        fixed_tokens = 697 + root_tokens + 657
        self.assertEqual(2_227, fixed_tokens)
        self.assertEqual(759, max(spec[2] for spec in reference_specs.values()))
        self.assertEqual(2_986, fixed_tokens + 759)
        self.assertEqual(2_985, 3_546 - (343 + 258 + 245 + 402 - root_tokens) - (945 - 759))
        self.assertEqual(2_992, 3_553 - (343 + 258 + 245 + 402 - root_tokens) - (945 - 759))
        self.assertLessEqual(2_992, 3_000)
        self.assertEqual(3_001, 2_992 + 9)

    def test_fg_c1m_security_cloud_tenant_frontier_is_lossless_and_bounded(self) -> None:
        source_specs = {
            "src/foundation/capabilities/tenant-isolation/SKILL.md": ("aeedaabbeed5d780e1bea5c407f94ab38e977766d08db695f7f81b9252cfb6d0", "43c5dd6ba2f0c81430eff5440d997b2a9c7eb32e1f86608ebc0e6d1659adc543", 638),
            "src/foundation/capabilities/tenant-isolation/references/data-storage-cache-and-search-isolation.md": ("c05545f49a609963e45307c1a36272e96836fdccfbb50e03f55c871ede4c19fd", "bbec8d6710bb857c010a3374ad5019e214af2fb58f7687c4db1838cb3cacc4ab", 612),
            "src/foundation/capabilities/tenant-isolation/references/async-queue-and-execution-context-isolation.md": ("96a51be7ef333ed680b4699b15dd5329ebad6df64671d2955e9d0bd07f5440b2", "a3696f28fa9b5292a6c11fa6c46be6997a2f81ffe768c54688fab8bbfc42553e", 634),
            "src/foundation/capabilities/tenant-isolation/references/operations-telemetry-and-lifecycle-isolation.md": ("89a08528bdbbe594871920fb11a4ff7fa293f39fcf6e94cc365e2b0bedd2ca47", "26b2857862108b53a558ba5487af58edf970baabcd1a6d3ce58834375997bf27", 634),
            "src/professional-skills/security-privacy-gate/references/security-output-and-gates.md": ("c2b99fcf869a60e4eaa3b31572bab1c7c6ea0c3301dc4c2fbcd90560c4e845a1", "05129afaa245591be03b05cd5c2edc5dcfd5b494002d2dd70a9891b2d253f81e", 625),
        }
        mismatches = []
        for path, (pre_sha256, post_sha256, expected_tokens) in source_specs.items():
            text = (ROOT / path).read_text(encoding="utf-8")
            actual_sha256 = hashlib.sha256(text.encode("utf-8")).hexdigest()
            if actual_sha256 != post_sha256:
                with self.subTest(source_preimage=path):
                    self.assertEqual(pre_sha256, actual_sha256)
                mismatches.append(path)
            with self.subTest(source_hash=path):
                self.assertEqual(post_sha256, actual_sha256)
            if actual_sha256 == post_sha256:
                self.assertEqual(expected_tokens, VALIDATION.count_o200k_base_tokens(text))
        if mismatches:
            return

        for path, expected_sha256 in {
            "src/professional-skills/security-privacy-gate/SKILL.md": "f11d7bdde385a27584a4b22e07cd389adc4c59d8933597433238c4ecc5ba7ae5",
            "src/domain-extensions/cloud-platform-extension/SKILL.md": "6c300ff1c468f83c7b75c54997c67539710e6f8e236fc655d4ecda5e806a4224",
            "src/foundation/capabilities/permission-boundary-modeling/SKILL.md": "7c522d072a783f995f195be77cc33496ca69d4720bc8335d40f595d784a9b9ff",
            "src/registry/professional-skills.yaml": "32a3b49da13930f3baccf54dbd8de12064b1f07d273b2948dfaeb12586eaf49a",
            "src/registry/foundation-skills.yaml": "385843496634f9e9ef4426790cacff211858cab4f73c6c15f521fc2732b5b8fd",
            "src/registry/domain-skills.yaml": "2d53ccc4206c94d9850e007d21603f04ba1f06f7721de5da1cd47dcfe6e16129",
        }.items():
            self.assertEqual(expected_sha256, hashlib.sha256((ROOT / path).read_bytes()).hexdigest())

        reference_specs = {
            ("security-privacy-gate", "references/checklist.md"): (136, "059a2463147824418c686f1cd1565ca3cfb85f3fb99eb2dd37f5ff2aa8144514", ("checklist-result", "residual-risk")),
            ("security-privacy-gate", "references/evidence-patterns.md"): (427, "3e368eb8ddcef3e77a22de4d38ff0d2fac022702e9f9cca471811815b5a2fbc8", ("evidence-record", "proof-limit", "residual-risk")),
            ("security-privacy-gate", "references/security-output-and-gates.md"): (625, "05129afaa245591be03b05cd5c2edc5dcfd5b494002d2dd70a9891b2d253f81e", ("gate-decision", "residual-risk")),
            ("cloud-platform-extension", "references/resource-control-and-data-plane-boundaries.md"): (421, "eb9aa5a9b1f760b83825428562293f0afdfa9a4bcdb4af76c2d5081aef3e3fdc", ("boundary-decision", "decision-record", "proof-limit")),
            ("cloud-platform-extension", "references/iam-workload-identity-and-network-contracts.md"): (440, "52661d530555b8c0ab6298f9d1288c3877beec6e3878a8a015e891ed76998dc1", ("boundary-decision", "failure-decision", "validation-plan")),
            ("cloud-platform-extension", "references/region-failure-domain-consistency-and-quota-contracts.md"): (485, "37d6621e04971dad77d5a5820022ace201388b0389bf690d2939356f0dd44eb4", ("decision-record", "proof-limit", "validation-plan")),
            ("cloud-platform-extension", "references/encryption-kms-and-cost-contracts.md"): (476, "7d5bfd16cca9c4b5a7911c58b14cf15e50e7f200ecedbb87f13a29c7079bfbc6", ("boundary-decision", "failure-decision", "residual-risk")),
            ("cloud-platform-extension", "references/provider-api-and-managed-service-authority.md"): (430, "4fc9962a94a2fcbdbf89128f7c26f8ea82b00e8532da9d604eccbcc0037381be", ("decision-record", "proof-limit", "validation-plan")),
            ("permission-boundary-modeling", "references/benchmarks-and-patterns.md"): (527, "9b0cd77ef56ec36c379a5eef6a3f7beadbe17fe99a563ad0a57dbad9f6462533", ("option-comparison", "selected-approach")),
            ("permission-boundary-modeling", "references/checklist.md"): (294, "2a74584d536871e5c510ac7dc64791878bf6a503fa1da7d6eab9ad2ac635cebc", ("checklist-result", "residual-risk")),
            ("permission-boundary-modeling", "references/evidence-patterns.md"): (635, "f876b57f88901fa11afcbbf60a549a0af4ca884a4b05df338534b85b49346d38", ("evidence-record", "proof-limit", "residual-risk")),
            ("tenant-isolation", "references/data-storage-cache-and-search-isolation.md"): (612, "bbec8d6710bb857c010a3374ad5019e214af2fb58f7687c4db1838cb3cacc4ab", ("boundary-decision", "validation-plan", "residual-risk")),
            ("tenant-isolation", "references/async-queue-and-execution-context-isolation.md"): (634, "a3696f28fa9b5292a6c11fa6c46be6997a2f81ffe768c54688fab8bbfc42553e", ("boundary-decision", "validation-plan", "proof-limit")),
            ("tenant-isolation", "references/operations-telemetry-and-lifecycle-isolation.md"): (634, "26b2857862108b53a558ba5487af58edf970baabcd1a6d3ce58834375997bf27", ("boundary-decision", "validation-plan", "residual-risk")),
        }
        selected_references = (
            ("security-privacy-gate", "references/checklist.md"),
            ("security-privacy-gate", "references/evidence-patterns.md"),
            ("security-privacy-gate", "references/security-output-and-gates.md"),
            ("cloud-platform-extension", "references/resource-control-and-data-plane-boundaries.md"),
            ("cloud-platform-extension", "references/iam-workload-identity-and-network-contracts.md"),
            ("cloud-platform-extension", "references/region-failure-domain-consistency-and-quota-contracts.md"),
            ("cloud-platform-extension", "references/encryption-kms-and-cost-contracts.md"),
            ("cloud-platform-extension", "references/provider-api-and-managed-service-authority.md"),
            ("permission-boundary-modeling", "references/benchmarks-and-patterns.md"),
            ("permission-boundary-modeling", "references/checklist.md"),
            ("permission-boundary-modeling", "references/evidence-patterns.md"),
            ("tenant-isolation", "references/data-storage-cache-and-search-isolation.md"),
            ("tenant-isolation", "references/async-queue-and-execution-context-isolation.md"),
            ("tenant-isolation", "references/operations-telemetry-and-lifecycle-isolation.md"),
        )
        for (owner, relative_path), (tokens, sha256, outputs) in reference_specs.items():
            if owner == "security-privacy-gate":
                source_root = ROOT / "src/professional-skills" / owner
            elif owner == "cloud-platform-extension":
                source_root = ROOT / "src/domain-extensions" / owner
            else:
                source_root = ROOT / "src/foundation/capabilities" / owner
            text = (source_root / relative_path).read_text(encoding="utf-8")
            with self.subTest(reference=owner + "/" + relative_path):
                self.assertEqual(sha256, hashlib.sha256(text.encode("utf-8")).hexdigest())
                self.assertEqual(tokens, VALIDATION.count_o200k_base_tokens(text))
                self.assertEqual((ALL_ROLES, outputs), _reference_binding(owner, str(source_root.relative_to(ROOT) / relative_path)))

        def compact_projection(path: str, headings: tuple[str, ...], selector: str | None) -> str:
            _metadata, raw_frontmatter, body = VALIDATION.parse_frontmatter(ROOT / path)
            h1_titles, sections = BUILD._markdown_heading_sections(body)
            self.assertEqual(1, len(h1_titles))
            output = ["---", raw_frontmatter, "---", "", f"# {h1_titles[0]}"]
            for heading in headings:
                values = sections.get(heading, [])
                if not values and heading == "Inputs":
                    continue
                self.assertEqual(1, len(values))
                self.assertTrue(values[0])
                output.extend(["", f"## {heading}", "", values[0]])
            output.extend(BUILD._compact_jit_reference_delivery_lines(selector))
            if selector is not None:
                output.extend(["", "## Layer 3 Delivery", "", "Foundation and Domain items are top-level Skills; no Layer 3 references are compiled."])
            output.append("")
            return "\n".join(output)

        root_specs = {
            "src/professional-skills/security-privacy-gate/SKILL.md": (BUILD.PROFESSIONAL_BUILT_KERNEL_HEADINGS, "security-privacy-gate", 303, "1f5f5d81f6dd59c74a1a43ed9e7710478b16a0657eaa5312fe623ee598fb300e"),
            "src/domain-extensions/cloud-platform-extension/SKILL.md": (BUILD.PROFESSIONAL_BUILT_KERNEL_HEADINGS, None, 250, "fcbe9dc653c2d7f98fe01738547701d6ba79fff570c24b176e130d3c17941ad2"),
            "src/foundation/capabilities/permission-boundary-modeling/SKILL.md": (BUILD.FOUNDATION_BUILT_KERNEL_HEADINGS, None, 233, "b2e0f2942ce44f05e6e9df79b84ec2143d50cf2fdf774080a7426421dacbcd5d"),
            "src/foundation/capabilities/tenant-isolation/SKILL.md": (BUILD.FOUNDATION_BUILT_KERNEL_HEADINGS, None, 217, "8ca8f4143c96cda353931bdead1f2fbdaaa3837b27497e9111bc2caf669bee81"),
        }
        for path, (headings, selector, tokens, sha256) in root_specs.items():
            projection = compact_projection(path, headings, selector)
            with self.subTest(root_projection=path):
                self.assertEqual(tokens, VALIDATION.count_o200k_base_tokens(projection))
                self.assertEqual(sha256, hashlib.sha256(projection.encode("utf-8")).hexdigest())

        professional = VALIDATION.load_yaml_file(ROOT / "src/registry/professional-skills.yaml")
        foundation = VALIDATION.load_yaml_file(ROOT / "src/registry/foundation-skills.yaml")
        domain = VALIDATION.load_yaml_file(ROOT / "src/registry/domain-skills.yaml")
        selector_authority = VALIDATION.layer3_selector_authority(
            foundation, professional, domain, context="C1M security cloud tenant witness"
        )
        selector_projection = VALIDATION.layer3_selector_runtime_projection(
            selector_authority,
            professional_skill="security-privacy-gate",
            profile="task-agent",
            selection_owner="main-control-agent",
            exact_layer3=None,
        )
        receipt = VALIDATION.layer3_selector_runtime_selection_receipt(
            selector_projection,
            evidence_signals=["cloud control plane", "account authority", "changed-surface", "tenant-isolation"],
        )
        self.assertEqual(
            ["cloud-platform-extension", "permission-boundary-modeling", "tenant-isolation"],
            receipt["selected_layer3"],
        )
        self.assertEqual(
            "ff438335ba459e33cfccf8dd2a9a3903ad3094ebef55562d5467d3e855e6d3b8",
            receipt["receipt_sha256"],
        )
        self.assertEqual(
            {"cloud-platform-extension"},
            set(receipt["selected_layer3"]) & {row["name"] for row in domain["domain_skills"]},
        )

        authority = VALIDATION.reference_context_admissibility_authority(
            professional, foundation, domain, context="C1M security cloud tenant staged witness"
        )
        staged = VALIDATION.reference_context_staged_plan(
            authority,
            references=selected_references,
            path="direct",
            profile="task-agent",
            selection_owner="main-control-agent",
            available_carrier_fields=[],
            receipt_replayed=True,
            brief_current=False,
            review_fresh=True,
        )
        expected_selected = [list(reference) for reference in selected_references]
        expected_loaded = [list(reference) for reference in sorted(selected_references)]
        self.assertTrue(staged["reachable"])
        self.assertEqual(expected_selected, staged["selected_union"])
        self.assertEqual(expected_loaded, staged["loaded_union"])
        self.assertEqual(14, len(staged["stages"]))
        self.assertEqual([[reference] for reference in expected_loaded], [stage["loaded_references"] for stage in staged["stages"]])
        self.assertTrue(all(stage["carried_predecessors"] == [] for stage in staged["stages"]))
        self.assertEqual([], staged["carried_predecessors"])
        self.assertEqual(14, len(staged["required_output_receipts"]))
        active_reference = ["permission-boundary-modeling", "references/evidence-patterns.md"]
        active_stage = next(stage for stage in staged["stages"] if stage["loaded_references"] == [active_reference])
        self.assertEqual(7, active_stage["stage"])
        self.assertEqual(
            [{"reference": active_reference, "required_outputs": ["evidence-record", "proof-limit", "residual-risk"]}],
            active_stage["required_output_receipts"],
        )

        for path, anchor in (
            ("src/foundation/capabilities/tenant-isolation/SKILL.md", "Map active tenant surfaces to trusted context"),
            ("src/foundation/capabilities/tenant-isolation/SKILL.md", "Preserve tenant provenance across asynchronous work"),
            ("src/foundation/capabilities/tenant-isolation/SKILL.md", "Preserve per-tenant attribution for privileged operations and lifecycle effects."),
            ("src/foundation/capabilities/tenant-isolation/SKILL.md", "Prove same-tenant success and wrong-tenant"),
            ("src/foundation/capabilities/tenant-isolation/references/data-storage-cache-and-search-isolation.md", "Tenant filtering occurs after read, list, count, or facet computation."),
            ("src/foundation/capabilities/tenant-isolation/references/async-queue-and-execution-context-isolation.md", "Async context loss uses no tenant or the prior tenant."),
            ("src/foundation/capabilities/tenant-isolation/references/operations-telemetry-and-lifecycle-isolation.md", "Telemetry exposes cross-tenant data."),
            ("src/professional-skills/security-privacy-gate/references/security-output-and-gates.md", "A block names missing evidence, unblock condition, and repair owner."),
        ):
            with self.subTest(owner_anchor=path, anchor=anchor):
                self.assertEqual(1, (ROOT / path).read_text(encoding="utf-8").count(anchor))

        component_tokens = [697, 303, 250, 233, 217, 635, 657]
        component_sha256 = [
            "28dde3cc5659529fa79b251dcf71b305372df5533d2050495a174f8782291f7e",
            "1f5f5d81f6dd59c74a1a43ed9e7710478b16a0657eaa5312fe623ee598fb300e",
            "fcbe9dc653c2d7f98fe01738547701d6ba79fff570c24b176e130d3c17941ad2",
            "b2e0f2942ce44f05e6e9df79b84ec2143d50cf2fdf774080a7426421dacbcd5d",
            "8ca8f4143c96cda353931bdead1f2fbdaaa3837b27497e9111bc2caf669bee81",
            "f876b57f88901fa11afcbbf60a549a0af4ca884a4b05df338534b85b49346d38",
            "b1dc031dec6d279d689ca18f620a82b8bc28548d12bba49a5233a969837cb1ac",
        ]
        self.assertEqual(7, len(component_sha256))
        self.assertEqual(2_992, sum(component_tokens))
        self.assertEqual(2_991, sum(component_tokens) - 1)
        self.assertEqual(2_998, sum(component_tokens) + 6)
        self.assertLessEqual(2_998, 3_000)
        self.assertEqual(3_001, 2_998 + 3)

    def test_fg_c1l_data_api_frontier_is_lossless_and_bounded(self) -> None:
        source_specs = {
            "src/professional-skills/data-api-contract-changer/SKILL.md": ("c0a371b449b95793909b7ae1349c0084833385038909926356bc7c96dd5f73ed", 823),
            "src/foundation/capabilities/model-boundary-mapping/SKILL.md": ("5d56f83d16fc7314948396b797fb934f91260dba7542931f6737b1c1ee068980", 483),
            "src/foundation/capabilities/model-boundary-mapping/references/benchmarks-and-patterns.md": ("f4260c6f4d875e061c1a5a2dcba6399ca3a2ddd9341c2c1fc4ee2d129f06f48c", 531),
            "src/foundation/capabilities/sdk-library-contract-design/SKILL.md": ("0f27341bf49450b9124274ef10ab4af6bf69bd5aa3ab4c97d807ae72e885314b", 459),
            "src/foundation/capabilities/sdk-library-contract-design/references/benchmarks-and-patterns.md": ("70e2a6d903a1d125c5f893206b670fb1578ba43031b11a7f67e84f9683f259a2", 536),
            "src/foundation/capabilities/api-contract-design/SKILL.md": ("b24fd02429226253065fa7582ad70567c4bc8d1b646d659929f31501ef3d0153", 462),
        }
        for path, (expected_hash, expected_tokens) in source_specs.items():
            text = (ROOT / path).read_text(encoding="utf-8")
            with self.subTest(source=path):
                self.assertEqual(expected_hash, hashlib.sha256(text.encode("utf-8")).hexdigest())
                self.assertEqual(expected_tokens, VALIDATION.count_o200k_base_tokens(text))

        protected_references = {
            "src/professional-skills/data-api-contract-changer/references/checklist.md": ("53ec6da7acdfcf17bee0fcc6c334fe276514240386784e5bc2598680adf3687a", 161),
            "src/professional-skills/data-api-contract-changer/references/evidence-patterns.md": ("334f34792d7c76d06712f8a412df3d59c787410ff335d67b3bbaa527a8eff5de", 337),
            "src/professional-skills/data-api-contract-changer/references/solution-optimality.md": ("8f572a469795d34b94e25a0e02df22f6fc540229348e18a4b91fead3c350dc27", 278),
            "src/foundation/capabilities/model-boundary-mapping/references/checklist.md": ("92ad52116a501ab1e23bf74fab66f0633680beed3d059b087323b107fb64beea", 309),
            "src/foundation/capabilities/model-boundary-mapping/references/evidence-patterns.md": ("81012ea2893871b3a41f61b161cb231f7679cf28e95e954db3564c21ab61dc51", 716),
            "src/foundation/capabilities/sdk-library-contract-design/references/checklist.md": ("e98f6bb1f860315cfc35513569d4ebb304be3bb56b620c385fe81b8a50daae28", 180),
            "src/foundation/capabilities/sdk-library-contract-design/references/evidence-patterns.md": ("2b7534bf30740cc117c58a5c0ebfc7d27cee852c803ed74ab5825eac6f762308", 627),
            "src/foundation/capabilities/api-contract-design/references/api-style-and-semantics.md": ("fe369d8cda288b4ff1c3af6662a293bde838ce6a2d4e9e1897b853cbbd151673", 623),
            "src/foundation/capabilities/api-contract-design/references/checklist.md": ("8992ab3d14c21214641445d93aedbcccf19702d88879c39674d3a140f8039fc6", 112),
            "src/foundation/capabilities/api-contract-design/references/evidence-patterns.md": ("4e47c583d591963ad98dbb1d4eb9a20f3c0c1e45b7b6e74a6136cd2c3030a1d5", 335),
        }
        for path, (expected_hash, expected_tokens) in protected_references.items():
            text = (ROOT / path).read_text(encoding="utf-8")
            with self.subTest(protected_reference=path):
                self.assertEqual(expected_hash, hashlib.sha256(text.encode("utf-8")).hexdigest())
                self.assertEqual(expected_tokens, VALIDATION.count_o200k_base_tokens(text))
                self.assertNotEqual(expected_hash, hashlib.sha256((text + " ").encode("utf-8")).hexdigest())

        root_projections = {
            "src/professional-skills/data-api-contract-changer/SKILL.md": ("data-api-contract-changer", 300, "f0779c57fb4c72eb1294eb7a4119070a16cab83b008dc25fa89420e7565d4211"),
            "src/foundation/capabilities/model-boundary-mapping/SKILL.md": (None, 209, "61061c8452d14599f435da37cf8c81d45a8d72ae437b30bc3a297f216f179263"),
            "src/foundation/capabilities/sdk-library-contract-design/SKILL.md": (None, 198, "1c4dfac80199dd1aa80147237375786cefa9886621c10a7607d60bd0cbdc9d2a"),
            "src/foundation/capabilities/api-contract-design/SKILL.md": (None, 209, "4bf5229519d767637f267538dad8e89249aa3620473267d7da1b2fcee143dcbb"),
        }
        for path, (selector, expected_tokens, expected_hash) in root_projections.items():
            _metadata, raw_frontmatter, body = VALIDATION.parse_frontmatter(ROOT / path)
            h1_titles, sections = BUILD._markdown_heading_sections(body)
            headings = BUILD.PROFESSIONAL_BUILT_KERNEL_HEADINGS if selector is not None else BUILD.FOUNDATION_BUILT_KERNEL_HEADINGS
            output = ["---", raw_frontmatter, "---", "", f"# {h1_titles[0]}"]
            for heading in headings:
                values = sections.get(heading, [])
                if not values and heading == "Inputs":
                    continue
                self.assertEqual(1, len(values))
                self.assertTrue(values[0])
                output.extend(["", f"## {heading}", "", values[0]])
            output.extend(BUILD._compact_jit_reference_delivery_lines(selector))
            output.append("")
            projection = "\n".join(output)
            with self.subTest(root_projection=path):
                self.assertEqual(expected_tokens, VALIDATION.count_o200k_base_tokens(projection))
                self.assertEqual(expected_hash, hashlib.sha256(projection.encode("utf-8")).hexdigest())

        for path, expected_hash in {
            "src/registry/professional-skills.yaml": "32a3b49da13930f3baccf54dbd8de12064b1f07d273b2948dfaeb12586eaf49a",
            "src/registry/foundation-skills.yaml": "385843496634f9e9ef4426790cacff211858cab4f73c6c15f521fc2732b5b8fd",
            "src/registry/domain-skills.yaml": "2d53ccc4206c94d9850e007d21603f04ba1f06f7721de5da1cd47dcfe6e16129",
        }.items():
            self.assertEqual(expected_hash, hashlib.sha256((ROOT / path).read_bytes()).hexdigest())

        for path, owner, roles, outputs in (
            ("src/professional-skills/data-api-contract-changer/references/checklist.md", "data-api-contract-changer", ("analysis-agent", "task-agent"), ("checklist-result", "residual-risk")),
            ("src/professional-skills/data-api-contract-changer/references/evidence-patterns.md", "data-api-contract-changer", ("analysis-agent", "task-agent"), ("evidence-record", "proof-limit", "residual-risk")),
            ("src/professional-skills/data-api-contract-changer/references/solution-optimality.md", "data-api-contract-changer", ("analysis-agent", "task-agent"), ("selected-approach", "residual-risk")),
            ("src/foundation/capabilities/model-boundary-mapping/references/benchmarks-and-patterns.md", "model-boundary-mapping", TASK_FIRST_ROLES, ("option-comparison", "selected-approach")),
            ("src/foundation/capabilities/model-boundary-mapping/references/checklist.md", "model-boundary-mapping", TASK_FIRST_ROLES, ("checklist-result", "residual-risk")),
            ("src/foundation/capabilities/model-boundary-mapping/references/evidence-patterns.md", "model-boundary-mapping", TASK_FIRST_ROLES, ("evidence-record", "proof-limit", "residual-risk")),
            ("src/foundation/capabilities/sdk-library-contract-design/references/benchmarks-and-patterns.md", "sdk-library-contract-design", TASK_FIRST_ROLES, ("option-comparison", "selected-approach")),
            ("src/foundation/capabilities/sdk-library-contract-design/references/checklist.md", "sdk-library-contract-design", TASK_FIRST_ROLES, ("checklist-result", "residual-risk")),
            ("src/foundation/capabilities/sdk-library-contract-design/references/evidence-patterns.md", "sdk-library-contract-design", TASK_FIRST_ROLES, ("evidence-record", "proof-limit", "residual-risk")),
            ("src/foundation/capabilities/api-contract-design/references/api-style-and-semantics.md", "api-contract-design", ALL_ROLES, ("selected-approach", "residual-risk")),
            ("src/foundation/capabilities/api-contract-design/references/checklist.md", "api-contract-design", ALL_ROLES, ("checklist-result", "residual-risk")),
            ("src/foundation/capabilities/api-contract-design/references/evidence-patterns.md", "api-contract-design", ALL_ROLES, ("evidence-record", "proof-limit", "residual-risk")),
        ):
            with self.subTest(reference_binding=path):
                self.assertEqual((roles, outputs), _reference_binding(owner, path))

        for path, facet in (
            ("src/professional-skills/data-api-contract-changer/SKILL.md", "Limit loading to the active decision's named Reference, with index/catalog paths excluded."),
            ("src/foundation/capabilities/model-boundary-mapping/references/benchmarks-and-patterns.md", "transport, domain, persistence, event, and view models represent different facts"),
            ("src/foundation/capabilities/sdk-library-contract-design/references/benchmarks-and-patterns.md", "Public API diffing"),
            ("src/foundation/capabilities/api-contract-design/SKILL.md", "If the API decision remains active, load only its named Reference."),
        ):
            with self.subTest(preserved_facet=path):
                self.assertEqual(1, (ROOT / path).read_text(encoding="utf-8").count(facet))

        root_tokens = 300 + 209 + 198 + 209
        self.assertEqual(916, root_tokens)
        fixed_tokens = 697 + root_tokens + 657
        self.assertEqual(2_270, fixed_tokens)
        self.assertEqual(716, max(tokens for _hash, tokens in protected_references.values()))
        self.assertEqual(2_806, fixed_tokens + 536)
        self.assertEqual(2_805, 3_426 - (294 + 278 + 269 + 277 - root_tokens) - (955 - 536))
        self.assertEqual(2_812, 3_433 - (294 + 278 + 269 + 277 - root_tokens) - (955 - 536))
        self.assertEqual(2_986, fixed_tokens + 716)
        self.assertEqual(2_985, fixed_tokens + 716 - 1)
        self.assertEqual(2_992, fixed_tokens + 716 + 6)
        self.assertLessEqual(2_992, 3_000)
        self.assertEqual(3_001, 2_992 + 9)

    def test_fg_c1n_quality_client_frontier_is_lossless_and_bounded(self) -> None:
        source_specs = {
            "src/professional-skills/quality-test-gate/SKILL.md": ("72e52da01ee72043250b9626fbdd7d55e43059a62a507cab8b9ec61e4bd06b0e", "1e694bd93dddec4dd1f6a57ee5400257bd6fe8b82da76485b5898ebf627018cb", 740),
            "src/foundation/capabilities/client-application-testing/SKILL.md": ("a7eef78bc5e104f23b2537f19b7e723c1c70c4f7c0e46e2079c2c92fdc04f066", "3d6a6ca06af0b395e869df3366dd22dbaa85aa7485116a7a15431e1487c1f70d", 387),
            "src/foundation/capabilities/client-application-testing/references/client-test-matrix.md": ("2da3c88cb13a28ee824602dd97a207b172cba620307c453d75ccb75bccd62ddf", "02edd179aae452bb8d1c4663bc73fa8f7bff2b980def64c4c51ad086c18a7777", 592),
        }
        mismatches = []
        for path, (pre_sha256, post_sha256, expected_tokens) in source_specs.items():
            text = (ROOT / path).read_text(encoding="utf-8")
            actual_sha256 = hashlib.sha256(text.encode("utf-8")).hexdigest()
            if actual_sha256 != post_sha256:
                with self.subTest(source_preimage=path):
                    self.assertEqual(pre_sha256, actual_sha256)
                mismatches.append(path)
            with self.subTest(source_hash=path):
                self.assertEqual(post_sha256, actual_sha256)
            if actual_sha256 == post_sha256:
                self.assertEqual(expected_tokens, VALIDATION.count_o200k_base_tokens(text))
        if mismatches:
            return

        source_anchors = {
            "src/professional-skills/quality-test-gate/SKILL.md": (
                "Map acceptance and failure paths to proving signals.",
                "**Analysis mode (`analysis-agent`):** Select the proof strategy.",
                "**Task mode (`task-agent`):** Implement the smallest proving test.",
                "**Review mode (`review-agent`):** Judge coverage and freshness.",
                "Map each acceptance and material failure to one signal.",
                "Select the lowest level exercising the real boundary.",
                "Record stale, flaky, skipped, or partial evidence as limited.",
                "## High-Value Gotchas",
                "## Execution Checklist",
                "Record unproved scope with its owner and release consequence.",
                "Stop before production mutation or authority overrun.",
                "Escalate unowned flaky, skipped, or partial evidence.",
                "Flag uncovered changed files or acceptance.",
                "**Analysis mode (`analysis-agent`):** validation strategy; acceptance-to-signal mapping; uncovered acceptance.",
                "**Task mode (`task-agent`):** proving test change; covered behavior; remaining regression risk.",
                "**Review mode (`review-agent`):** coverage verdict; uncovered changed behavior; stale or missing proof.",
            ),
            "src/foundation/capabilities/client-application-testing/SKILL.md": (
                "Own client interruption, artifact, environment, oracle, and cleanup decisions; exclude general strategy, release, platform, and accessibility-conformance decisions.",
                "Derive the smallest client matrix for the named failure.",
                "For the named client failure, bind its oracle to clean state and a release-equivalent artifact.",
                "Select `client-test-matrix.md` only when client dimensions compete.",
                "Stop without the matrix, artifact, OS control, or cleanup authority.",
                "client-test decision with risk matrix interruption and activation cases permission and connectivity transitions artifact and data states environment coverage oracles cleanup unavailable scope and proof limits",
                "[client test matrix](references/client-test-matrix.md)",
            ),
            "src/foundation/capabilities/client-application-testing/references/client-test-matrix.md": (
                "Lifecycle: background/return, recreation, process death, relaunch, crash, low memory",
                "Map each failure to the lowest capable boundary; retain device coverage for OS transitions.",
                "Use release-equivalent artifacts for packaging, architecture, optimization, entitlement, or upgrade.",
                "Reset app data/accounts/server fixtures/notifications/network/permissions/clocks/device settings.",
                "Current pages establish no repository SDK/toolchain, devices, support, runner, or release artifact.",
                "Record risk, matrix, artifact, oracle, cleanup, exclusions, command/manual evidence, and unproved claims.",
                "Reject recreation-as-process-death, one-target-as-supported-matrix, and screenshot/tree-only oracles.",
            ),
        }
        for path, anchors in source_anchors.items():
            text = (ROOT / path).read_text(encoding="utf-8")
            for anchor in anchors:
                with self.subTest(source_anchor=path, anchor=anchor):
                    self.assertEqual(1, text.count(anchor))

        def compact_projection(path: str, headings: tuple[str, ...], selector: str | None) -> str:
            _metadata, raw_frontmatter, body = VALIDATION.parse_frontmatter(ROOT / path)
            h1_titles, sections = BUILD._markdown_heading_sections(body)
            output = ["---", raw_frontmatter, "---", "", f"# {h1_titles[0]}"]
            for heading in headings:
                values = sections.get(heading, [])
                if not values and heading == "Inputs":
                    continue
                self.assertEqual(1, len(values))
                self.assertTrue(values[0])
                output.extend(["", f"## {heading}", "", values[0]])
            output.extend(BUILD._compact_jit_reference_delivery_lines(selector))
            output.append("")
            return "\n".join(output)

        root_specs = {
            "src/professional-skills/quality-test-gate/SKILL.md": (BUILD.PROFESSIONAL_BUILT_KERNEL_HEADINGS, "quality-test-gate", 309, "a1b284bddfd1cdf9fed94e175d603e2db962ab597ba443ab58d3e1a8c3d543b6"),
            "src/foundation/capabilities/test-data-management/SKILL.md": (BUILD.FOUNDATION_BUILT_KERNEL_HEADINGS, None, 257, "535ce74d430ee2cf20f237d416d8f0ec8b8f2c498cc7b262d2ab16624af16e65"),
            "src/foundation/capabilities/client-application-testing/SKILL.md": (BUILD.FOUNDATION_BUILT_KERNEL_HEADINGS, None, 215, "6a82967cb4e768321dca47421353b4a3ced565841444e760fe1c6078da9558ae"),
            "src/foundation/capabilities/test-strategy/SKILL.md": (BUILD.FOUNDATION_BUILT_KERNEL_HEADINGS, None, 232, "eb3ff8d61501d0a450aa9f72d60f5f96248791b06fb3b0cae7a57792d6780750"),
        }
        projections = {}
        for path, (headings, selector, expected_tokens, expected_sha256) in root_specs.items():
            projection = compact_projection(path, headings, selector)
            projections[path] = projection
            self.assertEqual(expected_tokens, VALIDATION.count_o200k_base_tokens(projection))
            self.assertEqual(expected_sha256, hashlib.sha256(projection.encode("utf-8")).hexdigest())
        quality_dev = projections["src/professional-skills/quality-test-gate/SKILL.md"].rstrip("\n") + "\n\n## Layer 3 Delivery\n\nFoundation and Domain items are top-level Skills; no Layer 3 references are compiled.\n"
        self.assertEqual(332, VALIDATION.count_o200k_base_tokens(quality_dev))
        self.assertEqual("8bea21744146360fc9d8a946c724f174b71723a28ce5960c1ff872b0e621f6dd", hashlib.sha256(quality_dev.encode("utf-8")).hexdigest())
        self.assertNotIn("## High-Value Gotchas", projections["src/professional-skills/quality-test-gate/SKILL.md"])
        self.assertNotIn("## Execution Checklist", projections["src/professional-skills/quality-test-gate/SKILL.md"])

        for path, expected_sha256 in {
            "src/registry/professional-skills.yaml": "32a3b49da13930f3baccf54dbd8de12064b1f07d273b2948dfaeb12586eaf49a",
            "src/registry/foundation-skills.yaml": "385843496634f9e9ef4426790cacff211858cab4f73c6c15f521fc2732b5b8fd",
            "src/registry/domain-skills.yaml": "2d53ccc4206c94d9850e007d21603f04ba1f06f7721de5da1cd47dcfe6e16129",
            "scripts/build.py": "2543ed2c2cb7498babeae20d1f7bd244f968522f116c90b8b08c4106a25efcf1",
            "scripts/validation_utils.py": "a76092b2d24cdfaec66eb44e1f8d4e48a9f76d9dda8a875a3b5602771649f995",
            "evals/agent-light-trajectories/cases.yaml": "25cc065fde1298111bbc5d3236976f3601b0db30453c805516689f2998c0191b",
            "tests/scripts/test_reference_registry_jit.py": "c4730adbdb7a5bdbae7ab24d979f563a2fab17d5fb634d83326a00d0dd00ad85",
        }.items():
            self.assertEqual(expected_sha256, hashlib.sha256((ROOT / path).read_bytes()).hexdigest())

        reference_specs = {
            ("client-application-testing", "references/client-test-matrix.md"): (592, "02edd179aae452bb8d1c4663bc73fa8f7bff2b980def64c4c51ad086c18a7777", ("validation-plan", "residual-risk")),
            ("quality-test-gate", "references/checklist.md"): (326, "c208301c6abaa0f47cb90826ae23420b9bef3c57facdeec932b9bc036eb7b19e", ("checklist-result", "validation-plan")),
            ("quality-test-gate", "references/test-output-and-gates.md"): (565, "c1bf533e04443976a6bbe8ee77121a9117e88ffb868c39402311e9aa016c3409", ("gate-decision", "residual-risk")),
            ("quality-test-gate", "references/test-structure-boundaries.md"): (500, "86038eeaa916ead150b505246f0308619f21a85e191cf1b772dcb2859a567d95", ("validation-plan", "proof-limit")),
            ("test-data-management", "references/benchmarks-and-patterns.md"): (539, "146f17f6b108c73f2452bb363678dbe9a15f3fb87d5f961bc41edf64ee6b89b9", ("option-comparison", "selected-approach")),
            ("test-data-management", "references/checklist.md"): (161, "e23b833747c26a46ae1935a6ec48a6ff78efc5d7e28eb7315c4f7e73e1b76771", ("checklist-result", "residual-risk")),
            ("test-data-management", "references/evidence-patterns.md"): (476, "b482b7c27c1528195b61077bad9c401cf08c62b3435e9072152b608b1a83b623", ("evidence-record", "proof-limit", "residual-risk")),
            ("test-strategy", "references/benchmarks-and-patterns.md"): (529, "b47521c4c96bc46257707e7d56bce7140fddd44fc5f35762063dfed13eb6b7c2", ("option-comparison", "selected-approach")),
            ("test-strategy", "references/checklist.md"): (515, "04883de9a1f8b1c3509a67a32c3720dcc88fafe10b525f74d0a03c96e07cf6f9", ("checklist-result", "residual-risk")),
            ("test-strategy", "references/evidence-patterns.md"): (537, "4dd4cf01fe1ee9e2f4a8d2d5a487799a7cbc72edd4867cb105b40f4d6d0f703a", ("evidence-record", "proof-limit", "residual-risk")),
        }
        selected_references = tuple(reference_specs)
        for (owner, relative_path), (tokens, sha256, outputs) in reference_specs.items():
            root = ROOT / ("src/professional-skills" if owner == "quality-test-gate" else "src/foundation/capabilities") / owner
            path = root / relative_path
            text = path.read_text(encoding="utf-8")
            self.assertEqual(sha256, hashlib.sha256(text.encode("utf-8")).hexdigest())
            self.assertEqual(tokens, VALIDATION.count_o200k_base_tokens(text))
            self.assertEqual((ALL_ROLES, outputs), _reference_binding(owner, str(path.relative_to(ROOT))))

        professional = VALIDATION.load_yaml_file(ROOT / "src/registry/professional-skills.yaml")
        foundation = VALIDATION.load_yaml_file(ROOT / "src/registry/foundation-skills.yaml")
        domain = VALIDATION.load_yaml_file(ROOT / "src/registry/domain-skills.yaml")
        selector_authority = VALIDATION.layer3_selector_authority(foundation, professional, domain, context="C1N quality client witness")
        selector_projection = VALIDATION.layer3_selector_runtime_projection(selector_authority, professional_skill="quality-test-gate", profile="task-agent", selection_owner="main-control-agent", exact_layer3=None)
        receipt = VALIDATION.layer3_selector_runtime_selection_receipt(selector_projection, evidence_signals=["explicit-test-data-decision", "changed installed-client behavior needs lifecycle OS integration installation device configuration or accessibility proof", "analysis-action"])
        self.assertEqual(["test-data-management", "client-application-testing", "test-strategy"], receipt["selected_layer3"])
        self.assertEqual("561a404c9f71b49fc1c15e727f8fe21e426622ed9224df71d0d21056513da9b4", receipt["receipt_sha256"])
        self.assertEqual(set(), set(receipt["selected_layer3"]) & {row["name"] for row in domain["domain_skills"]})

        authority = VALIDATION.reference_context_admissibility_authority(professional, foundation, domain, context="C1N quality client staged witness")
        staged = VALIDATION.reference_context_staged_plan(authority, references=selected_references, path="direct", profile="task-agent", selection_owner="main-control-agent", available_carrier_fields=[], receipt_replayed=True, brief_current=False, review_fresh=True)
        expected = [list(reference) for reference in selected_references]
        self.assertTrue(staged["reachable"])
        self.assertEqual(expected, staged["selected_union"])
        self.assertEqual(expected, staged["loaded_union"])
        self.assertEqual([[reference] for reference in expected], [stage["loaded_references"] for stage in staged["stages"]])
        self.assertEqual(10, len(staged["required_output_receipts"]))
        self.assertTrue(all(stage["carried_predecessors"] == [] for stage in staged["stages"]))
        self.assertEqual([], staged["carried_predecessors"])
        self.assertEqual(0, staged["stages"][0]["stage"])
        self.assertEqual([{"reference": expected[0], "required_outputs": ["validation-plan", "residual-risk"]}], staged["stages"][0]["required_output_receipts"])

        relocated_block = """## Anti-Patterns

- Reject recreation-as-process-death, one-target-as-supported-matrix, and screenshot/tree-only oracles."""
        self.assertEqual("44e42f4052aaec59a875b929e2244a6f2906fabbd083753e0f9b58f0c59022bc", _fingerprint(relocated_block))
        self.assertEqual(1, (ROOT / "src/foundation/capabilities/client-application-testing/references/client-test-matrix.md").read_text(encoding="utf-8").count(relocated_block))

        component_tokens = [697, 332, 257, 215, 232, 592, 657]
        component_sha256 = ["28dde3cc5659529fa79b251dcf71b305372df5533d2050495a174f8782291f7e", "8bea21744146360fc9d8a946c724f174b71723a28ce5960c1ff872b0e621f6dd", "535ce74d430ee2cf20f237d416d8f0ec8b8f2c498cc7b262d2ab16624af16e65", "6a82967cb4e768321dca47421353b4a3ced565841444e760fe1c6078da9558ae", "eb3ff8d61501d0a450aa9f72d60f5f96248791b06fb3b0cae7a57792d6780750", "02edd179aae452bb8d1c4663bc73fa8f7bff2b980def64c4c51ad086c18a7777", "b1dc031dec6d279d689ca18f620a82b8bc28548d12bba49a5233a969837cb1ac"]
        self.assertEqual(7, len(component_sha256))
        self.assertEqual(2_982, sum(component_tokens))
        self.assertEqual(2_981, sum(component_tokens) - 1)
        self.assertEqual(2_988, sum(component_tokens) + 6)
        self.assertLessEqual(2_988, 3_000)
        self.assertEqual(3_001, 2_988 + 13)

    def test_fg_c1o_platform_infrastructure_frontier_is_lossless_and_bounded(self) -> None:
        source_specs = {
            "src/professional-skills/platform-infrastructure-change-builder/SKILL.md": ("48271a02cccb87ce375b3707c463d3ab6e2169d22e73b30c49e65d0a1f02f2de", "4d43548f48103571f863dc798d5023ae7ad18bd9a674cc74ec14557ee7a74d0a", 652),
            "src/professional-skills/platform-infrastructure-change-builder/references/iac-source-contracts.md": ("85c27e27eb48cdfcfc84a58d758bf6b52d23ebde6bc23ba8feba286ca4acf226", "ac76ff616b46e89bc3fbe32c02bb270161ae132d97162b38ba36866ae2148b29", 701),
            "src/foundation/capabilities/powershell-professional-usage/references/pipeline-error-and-native-contracts.md": ("5db3112e97f40af7b37867397407e58a6803a9fbe8920433499e598b5cfd4296", "ab30d62d5e947340effe9918dd49546f2e69c47806b049c4f125673260833c8e", 653),
            "src/foundation/capabilities/powershell-professional-usage/references/remoting-provider-and-administration-contracts.md": ("24bdac4de57d63660ac03c94426434b2bb84f019e97ec172f7c32895e1864b68", "97ce7438c774d56a64d46fd241c3d6876b97929b8294f43897818185ba812cd4", 722),
        }
        mismatches = []
        for path, (pre_sha256, post_sha256, expected_tokens) in source_specs.items():
            source = (ROOT / path).read_text(encoding="utf-8")
            actual_sha256 = hashlib.sha256(source.encode("utf-8")).hexdigest()
            if actual_sha256 != post_sha256:
                with self.subTest(source_preimage=path):
                    self.assertEqual(pre_sha256, actual_sha256)
                mismatches.append(path)
            with self.subTest(source_hash=path):
                self.assertEqual(post_sha256, actual_sha256)
            if actual_sha256 == post_sha256:
                self.assertEqual(expected_tokens, VALIDATION.count_o200k_base_tokens(source))
        if mismatches:
            return

        source_anchors = {
            "src/professional-skills/platform-infrastructure-change-builder/SKILL.md": (
                "`task-agent` infrastructure source changes within authority, excluding production mutation and review.",
                "Begin by inspecting target/state/recovery.",
                "Bind target, owner, state/backend/lock/writer, and versions.",
                "Select the smallest recoverable change from current identity/drift evidence.",
                "Compare proposal unknowns and destructive/privilege/network/secret/cost/dependency effects.",
                "## High-Value Gotchas",
                "## Execution Checklist",
                "Route production apply, deployment, release, and rollback authority to `delivery-release-gate`.",
                "Stop while authority, state/writer/recovery, or effects remain unresolved.",
                "owner/source, target/version, proposal/effects/recovery, proof limits, release boundary",
            ),
            "src/professional-skills/platform-infrastructure-change-builder/references/iac-source-contracts.md": (
                "Treat proposal evidence as non-authorizing unless separate production-mutation authority is confirmed.",
                "Terraform, OpenTofu, Pulumi, and CloudFormation are non-equivalent.",
                "Separate state layers; change the smallest owner; bind secret-free non-mutating proposal evidence to target and versions.",
                "Proposal evidence is neither execution authority nor convergence proof.",
            ),
            "src/foundation/capabilities/powershell-professional-usage/references/pipeline-error-and-native-contracts.md": (
                "Bind emitted .NET type, cardinality/enumeration, parameter binding, null/empty behavior, and formatting boundary.",
                "Assign stream consumers; classify terminating and non-terminating cases; bind `-ErrorAction`, preference scope, catch/finally, `ErrorRecord`, retryability, and final exit.",
                "Bind argument vector to edition/OS; prove quoting/empty/wildcards/redaction, immediate `$LASTEXITCODE`, accepted codes, timeout, cancellation, and one failure translation.",
                "Round-trip non-ASCII text and bytes through the exact edition, cmdlet, redirection, and native boundary.",
                "Success flags, text conversion, command strings, syntax portability, and blind reruns do not prove contracts.",
            ),
            "src/foundation/capabilities/powershell-professional-usage/references/remoting-provider-and-administration-contracts.md": (
                "Bind remote endpoint/transport/evaluation/session/timeout/cancellation/retry/partial-result/cleanup and wrong-host/hidden-target failure.",
                "Bind identity/authorization, credential scope/lifetime, second hop, transport, audit/redaction, and leak/privilege-broadening rejection.",
                "Real provider changes require an explicitly authorized, isolated, recoverable test provider",
                "a valid second-run result makes no unintended mutation and retains passing post-state verification.",
                "prove rollback, compensation, or reconciliation rather than invoking it again.",
            ),
        }
        for path, anchors in source_anchors.items():
            source = (ROOT / path).read_text(encoding="utf-8")
            for anchor in anchors:
                with self.subTest(source_anchor=path, anchor=anchor):
                    self.assertEqual(1, source.count(anchor))
        self.assertNotIn(
            "never production mutation or review.",
            (ROOT / "src/professional-skills/platform-infrastructure-change-builder/SKILL.md").read_text(encoding="utf-8"),
        )

        relocated_groups = (
            ("src/professional-skills/platform-infrastructure-change-builder/references/iac-source-contracts.md", "Bind source, state, identity, and non-mutating proposal evidence to the selected\ntool. Terraform, OpenTofu, Pulumi, and CloudFormation are non-equivalent. Never\nauthorize production mutation.", "9a22c7a1a79c57e699a099470071482c3e7686620ee1e18687adbf327f86c9a6", "Load for a named source, state, identity, or proposal decision."),
            ("src/foundation/capabilities/powershell-professional-usage/references/pipeline-error-and-native-contracts.md", "- **Pipeline object:** record emitted .NET types, scalar/collection cardinality, automatic enumeration, `ByValue`/`ByPropertyName` binding, null/empty behavior, and where formatting begins.", "84b557464dcd136f4f4ed227158fd77146f8a1a86e5fa6333f042bbad32f989b", "| Object | Bind emitted .NET type, cardinality/enumeration, parameter binding, null/empty behavior, and formatting boundary. |"),
            ("src/foundation/capabilities/powershell-professional-usage/references/pipeline-error-and-native-contracts.md", "- **Native result:** capture stdout/stderr or bytes intentionally, inspect `$LASTEXITCODE` immediately, define accepted codes, and translate timeout/cancellation/failure once.", "58d0c0105f0655e36f016dc35ffeaae5256e7e15a754e98d5a1f3a4cd22875bf", "| Native | Bind argument vector to edition/OS; prove quoting/empty/wildcards/redaction, immediate `$LASTEXITCODE`, accepted codes, timeout, cancellation, and one failure translation. |"),
            ("src/foundation/capabilities/powershell-professional-usage/references/pipeline-error-and-native-contracts.md", "- **Encoding:** state source, destination, BOM, newline, console/process encoding, append behavior, and the exact cmdlet or native boundary selecting it.", "11db4b520ec951d21aeca6d569a83d987de0976f433b0930922f12d70f524077", "| Encoding/function | Bind text/byte source, destination, BOM/newline, console/process encoding and append behavior; test advanced-function binding/cardinality before use. |"),
            ("src/foundation/capabilities/powershell-professional-usage/references/remoting-provider-and-administration-contracts.md", "| Remote execution | Transport and endpoint, local/remote expression evaluation, session lifetime, fan-out/throttle, timeout, cancellation, retry, and partial-result policy | Work runs on the wrong machine, sessions leak, or one target's failure is hidden |", "fa0f32f0b09bb6d890afd9108d37998795e042657e6161ee2f2f08ea40e89e61", "Bind remote endpoint/transport/evaluation/session/timeout/cancellation/retry/partial-result/cleanup and wrong-host/hidden-target failure."),
            ("src/foundation/capabilities/powershell-professional-usage/references/remoting-provider-and-administration-contracts.md", "| Remote object | Serialized type/property contract, methods lost, depth/size, culture/time, secure transport, and reconstruction owner | A deserialized object is treated as a live local object or loses required fidelity |", "8ee96ce721d8e1c59fd291617f780c8a3fa16aaeb129ec98e7486d7fe2989246", "Bind serialized type/properties/method loss/depth/size/culture/time/reconstruction and live-object rejection."),
            ("src/foundation/capabilities/powershell-professional-usage/references/remoting-provider-and-administration-contracts.md", "| Administrative state | Repeat-safety classification, desired-state predicate, current-state read, minimal mutation, `ShouldProcess`, concurrency/lock, restart boundary, verification, rollback or compensation, and applicable second-run contract | A claimed repeat-safe operation duplicates, oscillates, broadens privilege, or reports success without post-state; an intentionally non-idempotent effect lacks bounded recovery |", "884defa3892b4f658033d1d464018a4ecd99aaf8341c8edf353f3534b1b04767", "Bind Repeat-safety classification, desired-state predicate, current read, minimal mutation, `ShouldProcess`, lock/restart, verification/recovery, and second-run contract."),
        )
        for path, old_anchor, fingerprint, new_anchor in relocated_groups:
            self.assertEqual(fingerprint, _fingerprint(old_anchor))
            source = (ROOT / path).read_text(encoding="utf-8")
            self.assertNotIn(old_anchor, source)
            self.assertEqual(1, source.count(new_anchor))

        def compact_projection(path: str, headings: tuple[str, ...], selector: str | None) -> str:
            _metadata, raw_frontmatter, body = VALIDATION.parse_frontmatter(ROOT / path)
            h1_titles, sections = BUILD._markdown_heading_sections(body)
            self.assertEqual(1, len(h1_titles))
            output = ["---", raw_frontmatter, "---", "", f"# {h1_titles[0]}"]
            for heading in headings:
                values = sections.get(heading, [])
                if not values and heading == "Inputs":
                    continue
                self.assertEqual(1, len(values))
                self.assertTrue(values[0])
                output.extend(["", f"## {heading}", "", values[0]])
            output.extend(BUILD._compact_jit_reference_delivery_lines(selector))
            if selector is not None:
                output.extend(["", "## Layer 3 Delivery", "", "Foundation and Domain items are top-level Skills; no Layer 3 references are compiled."])
            output.append("")
            return "\n".join(output)

        root_specs = {
            "src/professional-skills/platform-infrastructure-change-builder/SKILL.md": (BUILD.PROFESSIONAL_BUILT_KERNEL_HEADINGS, "platform-infrastructure-change-builder", 229, "edf20265275b1afa37ecd528904f486436cfa88cd04b6ecacb773a0ed8105958"),
            "src/domain-extensions/cloud-platform-extension/SKILL.md": (BUILD.PROFESSIONAL_BUILT_KERNEL_HEADINGS, None, 250, "fcbe9dc653c2d7f98fe01738547701d6ba79fff570c24b176e130d3c17941ad2"),
            "src/foundation/capabilities/configuration-runtime-policy/SKILL.md": (BUILD.FOUNDATION_BUILT_KERNEL_HEADINGS, None, 183, "f91cb26ad5c184d9505fec203a388ee461fda50f6a9c1684abc83bda5bfb8237"),
            "src/foundation/capabilities/powershell-professional-usage/SKILL.md": (BUILD.FOUNDATION_BUILT_KERNEL_HEADINGS, None, 197, "8f5d6f6f82a18be75f0eca521865139c604e2e41cc73858b535285f026b5f094"),
        }
        root_projections = {}
        for path, (headings, selector, tokens, sha256) in root_specs.items():
            projection = compact_projection(path, headings, selector)
            root_projections[path] = projection
            self.assertEqual(tokens, VALIDATION.count_o200k_base_tokens(projection))
            self.assertEqual(sha256, hashlib.sha256(projection.encode("utf-8")).hexdigest())
        self.assertNotIn("## High-Value Gotchas", root_projections["src/professional-skills/platform-infrastructure-change-builder/SKILL.md"])
        self.assertNotIn("## Execution Checklist", root_projections["src/professional-skills/platform-infrastructure-change-builder/SKILL.md"])

        protected = {
            "src/domain-extensions/cloud-platform-extension/SKILL.md": "6c300ff1c468f83c7b75c54997c67539710e6f8e236fc655d4ecda5e806a4224",
            "src/foundation/capabilities/configuration-runtime-policy/SKILL.md": "a0c6c4b122e76426256bc5deac35b741b32a406255992ac4c958ff10cfb2f9c6",
            "src/foundation/capabilities/powershell-professional-usage/SKILL.md": "cd32328dda6ccaa431388c220cac38b08988ad220eb2a8a29b8b2a69224ff27c",
            "src/professional-skills/platform-infrastructure-change-builder/references/kubernetes-source-contracts.md": "4408105827924db9af29351153865837a26a6e2c6e1075212668d00dee1830f6",
            "src/registry/professional-skills.yaml": "32a3b49da13930f3baccf54dbd8de12064b1f07d273b2948dfaeb12586eaf49a",
            "src/registry/foundation-skills.yaml": "385843496634f9e9ef4426790cacff211858cab4f73c6c15f521fc2732b5b8fd",
            "src/registry/domain-skills.yaml": "2d53ccc4206c94d9850e007d21603f04ba1f06f7721de5da1cd47dcfe6e16129",
            "scripts/build.py": "2543ed2c2cb7498babeae20d1f7bd244f968522f116c90b8b08c4106a25efcf1",
            "scripts/validation_utils.py": "a76092b2d24cdfaec66eb44e1f8d4e48a9f76d9dda8a875a3b5602771649f995",
            "evals/agent-light-trajectories/cases.yaml": "25cc065fde1298111bbc5d3236976f3601b0db30453c805516689f2998c0191b",
            "tests/scripts/test_reference_registry_jit.py": "c4730adbdb7a5bdbae7ab24d979f563a2fab17d5fb634d83326a00d0dd00ad85",
            "tests/scripts/test_eval_rendered_context_budget.py": "9bc52e95f1ad5e6a3d5a8ad164eb789172c6b2b2b374749e42ddc12df9237a5a",
            "scripts/audit-skill-content.py": "19075d5a17baf72de6da658f113e3b029720a927fd8723885b6806d97a74cfab",
            "tests/scripts/test_validate_root_content.py": "432ed062a7f2f71cc0c23ac90c0fc3d06aaa85901c3376965ff6291dd2a306fc",
        }
        for path, expected_sha256 in protected.items():
            self.assertEqual(expected_sha256, hashlib.sha256((ROOT / path).read_bytes()).hexdigest())

        reference_specs = {
            ("cloud-platform-extension", "references/encryption-kms-and-cost-contracts.md"): (476, "7d5bfd16cca9c4b5a7911c58b14cf15e50e7f200ecedbb87f13a29c7079bfbc6", ALL_ROLES, ("boundary-decision", "failure-decision", "residual-risk")),
            ("cloud-platform-extension", "references/iam-workload-identity-and-network-contracts.md"): (440, "52661d530555b8c0ab6298f9d1288c3877beec6e3878a8a015e891ed76998dc1", ALL_ROLES, ("boundary-decision", "failure-decision", "validation-plan")),
            ("cloud-platform-extension", "references/provider-api-and-managed-service-authority.md"): (430, "4fc9962a94a2fcbdbf89128f7c26f8ea82b00e8532da9d604eccbcc0037381be", ALL_ROLES, ("decision-record", "proof-limit", "validation-plan")),
            ("cloud-platform-extension", "references/region-failure-domain-consistency-and-quota-contracts.md"): (485, "37d6621e04971dad77d5a5820022ace201388b0389bf690d2939356f0dd44eb4", ALL_ROLES, ("decision-record", "proof-limit", "validation-plan")),
            ("cloud-platform-extension", "references/resource-control-and-data-plane-boundaries.md"): (421, "eb9aa5a9b1f760b83825428562293f0afdfa9a4bcdb4af76c2d5081aef3e3fdc", ALL_ROLES, ("boundary-decision", "decision-record", "proof-limit")),
            ("configuration-runtime-policy", "references/benchmarks-and-patterns.md"): (455, "9ef96a4caa8a66abad659cd04a1dbe7fced550efcf94907f1bd143eb2f94a53b", TASK_FIRST_ROLES, ("option-comparison", "selected-approach")),
            ("configuration-runtime-policy", "references/checklist.md"): (378, "55406df248bce907803dffd55d3473109d149526cea056a4d5f7c9113954275d", TASK_FIRST_ROLES, ("checklist-result", "residual-risk")),
            ("configuration-runtime-policy", "references/evidence-patterns.md"): (436, "11db23aaedf78b0f5629b894c25bf3725b38559e6a216219bd63f3018aadfca4", TASK_FIRST_ROLES, ("evidence-record", "proof-limit", "residual-risk")),
            ("platform-infrastructure-change-builder", "references/iac-source-contracts.md"): (701, "ac76ff616b46e89bc3fbe32c02bb270161ae132d97162b38ba36866ae2148b29", ("task-agent",), ("proof-limit", "selected-approach", "validation-plan")),
            ("platform-infrastructure-change-builder", "references/kubernetes-source-contracts.md"): (600, "4408105827924db9af29351153865837a26a6e2c6e1075212668d00dee1830f6", ("task-agent",), ("proof-limit", "selected-approach", "validation-plan")),
            ("powershell-professional-usage", "references/pipeline-error-and-native-contracts.md"): (653, "ab30d62d5e947340effe9918dd49546f2e69c47806b049c4f125673260833c8e", TASK_FIRST_ROLES, ("decision-record", "residual-risk")),
            ("powershell-professional-usage", "references/remoting-provider-and-administration-contracts.md"): (722, "97ce7438c774d56a64d46fd241c3d6876b97929b8294f43897818185ba812cd4", TASK_FIRST_ROLES, ("selected-approach", "proof-limit", "residual-risk")),
        }
        selected_references = tuple(reference_specs)
        for (owner, relative_path), (tokens, sha256, roles, outputs) in reference_specs.items():
            if owner == "platform-infrastructure-change-builder":
                source_root = ROOT / "src/professional-skills" / owner
            elif owner == "cloud-platform-extension":
                source_root = ROOT / "src/domain-extensions" / owner
            else:
                source_root = ROOT / "src/foundation/capabilities" / owner
            path = source_root / relative_path
            source = path.read_text(encoding="utf-8")
            self.assertEqual(sha256, hashlib.sha256(source.encode("utf-8")).hexdigest())
            self.assertEqual(tokens, VALIDATION.count_o200k_base_tokens(source))
            self.assertEqual((roles, outputs), _reference_binding(owner, str(path.relative_to(ROOT))))

        professional = VALIDATION.load_yaml_file(ROOT / "src/registry/professional-skills.yaml")
        foundation = VALIDATION.load_yaml_file(ROOT / "src/registry/foundation-skills.yaml")
        domain = VALIDATION.load_yaml_file(ROOT / "src/registry/domain-skills.yaml")
        selector_authority = VALIDATION.layer3_selector_authority(foundation, professional, domain, context="C1O platform witness")
        selector_projection = VALIDATION.layer3_selector_runtime_projection(selector_authority, professional_skill="platform-infrastructure-change-builder", profile="task-agent", selection_owner="main-control-agent", exact_layer3=None)
        receipt = VALIDATION.layer3_selector_runtime_selection_receipt(selector_projection, evidence_signals=["cloud control plane", "account authority", "changed-surface", "configuration runtime policy typed config default validation fail fast hot reload feature flag owner expiry cleanup kill switch stale flag mode kind switch tenant user experiment rollout rollback config observability", "powershell pipeline binding errors native exit arguments encoding remoting credentials providers modules or administrative idempotency"])
        self.assertEqual(["cloud-platform-extension", "configuration-runtime-policy", "powershell-professional-usage"], receipt["selected_layer3"])
        self.assertEqual("274ab034c0a7efd4d2986963b7774d8ac909c445b89f5c19e0e306a97fdfcdd4", receipt["receipt_sha256"])
        self.assertEqual({"cloud-platform-extension"}, set(receipt["selected_layer3"]) & {row["name"] for row in domain["domain_skills"]})

        authority = VALIDATION.reference_context_admissibility_authority(professional, foundation, domain, context="C1O platform staged witness")
        staged = VALIDATION.reference_context_staged_plan(authority, references=selected_references, path="direct", profile="task-agent", selection_owner="main-control-agent", available_carrier_fields=[], receipt_replayed=True, brief_current=False, review_fresh=True)
        expected = [list(reference) for reference in selected_references]
        self.assertTrue(staged["reachable"])
        self.assertEqual(expected, staged["selected_union"])
        self.assertEqual(expected, staged["loaded_union"])
        self.assertEqual([[reference] for reference in expected], [stage["loaded_references"] for stage in staged["stages"]])
        self.assertEqual(12, len(staged["required_output_receipts"]))
        self.assertTrue(all(stage["carried_predecessors"] == [] for stage in staged["stages"]))
        self.assertEqual([], staged["carried_predecessors"])
        self.assertEqual(11, staged["stages"][11]["stage"])
        self.assertEqual([expected[11]], staged["stages"][11]["loaded_references"])
        self.assertEqual([{"reference": expected[11], "required_outputs": ["selected-approach", "proof-limit", "residual-risk"]}], staged["stages"][11]["required_output_receipts"])

        component_tokens = [697, 229, 250, 183, 197, 722, 657]
        component_sha256 = ["28dde3cc5659529fa79b251dcf71b305372df5533d2050495a174f8782291f7e", "edf20265275b1afa37ecd528904f486436cfa88cd04b6ecacb773a0ed8105958", "fcbe9dc653c2d7f98fe01738547701d6ba79fff570c24b176e130d3c17941ad2", "f91cb26ad5c184d9505fec203a388ee461fda50f6a9c1684abc83bda5bfb8237", "8f5d6f6f82a18be75f0eca521865139c604e2e41cc73858b535285f026b5f094", "97ce7438c774d56a64d46fd241c3d6876b97929b8294f43897818185ba812cd4", "b1dc031dec6d279d689ca18f620a82b8bc28548d12bba49a5233a969837cb1ac"]
        self.assertEqual(7, len(component_sha256))
        self.assertEqual(2_935, sum(component_tokens))
        self.assertEqual(2_934, sum(component_tokens) - 1)
        self.assertEqual(2_941, sum(component_tokens) + 6)
        self.assertLessEqual(2_941, 3_000)
        self.assertEqual(722, max(tokens for tokens, _sha256, _roles, _outputs in reference_specs.values()))
        self.assertEqual(3_001, 3_000 + 1)

    def test_fg_c1p_platform_iac_safety_frontier_is_lossless_and_bounded(self) -> None:
        source_specs = {
            "src/foundation/capabilities/configuration-runtime-policy/SKILL.md": ("c882680f287f1a0d5a7af0ae0efcc7e105086e26c2310a344aaeda03e5e23a26", "a0c6c4b122e76426256bc5deac35b741b32a406255992ac4c958ff10cfb2f9c6", 467, ("Bind typed source, values, owner, default, precedence, apply boundary, and effective state.", "For protected invariants, use consequence-derived defaults, pre-effect validation, bounded variants, and atomic last-good recovery.", "Load only the named output Reference.", "Return a Configuration Policy")),
            "src/foundation/capabilities/infrastructure-as-code-safety/SKILL.md": ("2daccdd6840d15306c8c4cdb2c690fa303d0f3f4acecadce28656f9b72a187f9", "30c8a48b94f411059bb8e17e1670d1b5ca79db1c27b06394d5818f14de10c21c", 379, ("Bind state authority and layer boundaries.", "Bind proposals to source/recorded/effective state, identity/effects/recovery, versions, and unknowns.", "Reject unproved tool equivalence, execution, or convergence.", "Stop on unresolved authority, effects, recovery, or production mutation.")),
            "src/foundation/capabilities/infrastructure-as-code-safety/references/identity-destruction-and-recovery-contracts.md": ("c66c590d72b17a0b099ef44e814a9cc1d88e0dded8c8eb63d5a63049d3d5eb85", "8cf0a2d5b85a83cd517a937059b28b243c2718e7da90dad405fd33a474e44b1f", 812, ("| Identity | Source/logical address, remote identity, owner, target, state record. |", "- **Terraform:** verify pre-import/move identity, lifecycle, and state recovery.", "Require omitted-dependency and reconciliation boundaries", "Treat deletion protection as one-operation blocking", "Sources do not prove identity, authorization, deletion safety")),
            "src/foundation/capabilities/infrastructure-as-code-safety/references/state-plan-and-drift-contracts.md": ("b5459cd0632cc8a84074ab52140b57ed924dd382e93eb09890ec5f84d2db64bc", "d1d0bbf5306aaa75e25a9ed6a08d0d7c5b0066b75dd091cb276b63da58892bc6", 809, ("| Recorded | Backend, workspace/stack, version, encryption, recovery owner. |", "Keep Terraform/OpenTofu plans, Pulumi plans, CloudFormation sets, Kubernetes dry-run, Helm renders, and Kustomize builds distinct.", "Refresh evidence after a bound source/state/target/version/provider/dependency or relevant-time change.", "Proposals are not execution/convergence proof; source rollback may leave effects.")),
        }
        mismatches = []
        for path, (pre_sha256, post_sha256, tokens, anchors) in source_specs.items():
            source = (ROOT / path).read_text(encoding="utf-8")
            actual_sha256 = hashlib.sha256(source.encode("utf-8")).hexdigest()
            if actual_sha256 != post_sha256:
                self.assertEqual(pre_sha256, actual_sha256)
                mismatches.append(path)
                continue
            self.assertEqual(tokens, VALIDATION.count_o200k_base_tokens(source))
            for anchor in anchors:
                self.assertEqual(1, source.count(anchor))
        if mismatches:
            self.fail(f"C1P source posts not reached: {mismatches}")

        identity_text = (ROOT / "src/foundation/capabilities/infrastructure-as-code-safety/references/identity-destruction-and-recovery-contracts.md").read_text(encoding="utf-8")
        state_text = (ROOT / "src/foundation/capabilities/infrastructure-as-code-safety/references/state-plan-and-drift-contracts.md").read_text(encoding="utf-8")
        self.assertEqual(18, identity_text.count("https://"))
        self.assertEqual(20, state_text.count("https://"))

        def compact_projection(path: str, headings: tuple[str, ...]) -> str:
            _metadata, raw_frontmatter, body = VALIDATION.parse_frontmatter(ROOT / path)
            h1_titles, sections = BUILD._markdown_heading_sections(body)
            self.assertEqual(1, len(h1_titles))
            output = ["---", raw_frontmatter, "---", "", f"# {h1_titles[0]}"]
            for heading in headings:
                values = sections.get(heading, [])
                if not values and heading == "Inputs":
                    continue
                self.assertEqual(1, len(values))
                output.extend(["", f"## {heading}", "", values[0]])
            output.extend(BUILD._compact_jit_reference_delivery_lines(None))
            output.append("")
            return "\n".join(output)

        root_projections = {
            "src/foundation/capabilities/configuration-runtime-policy/SKILL.md": (183, "f91cb26ad5c184d9505fec203a388ee461fda50f6a9c1684abc83bda5bfb8237"),
            "src/foundation/capabilities/infrastructure-as-code-safety/SKILL.md": (165, "a0a06ad825967e548dc5eb817ce003a24519aa99a4c2262cc0bcbc0830a97b76"),
        }
        for path, (tokens, sha256) in root_projections.items():
            projection = compact_projection(path, BUILD.FOUNDATION_BUILT_KERNEL_HEADINGS)
            self.assertEqual(tokens, VALIDATION.count_o200k_base_tokens(projection))
            self.assertEqual(sha256, hashlib.sha256(projection.encode("utf-8")).hexdigest())
            self.assertNotIn("## Targeted References", projection)

        reference_specs = {
            ("cloud-platform-extension", "references/encryption-kms-and-cost-contracts.md"): (476, "7d5bfd16cca9c4b5a7911c58b14cf15e50e7f200ecedbb87f13a29c7079bfbc6", ALL_ROLES, ("boundary-decision", "failure-decision", "residual-risk")),
            ("cloud-platform-extension", "references/iam-workload-identity-and-network-contracts.md"): (440, "52661d530555b8c0ab6298f9d1288c3877beec6e3878a8a015e891ed76998dc1", ALL_ROLES, ("boundary-decision", "failure-decision", "validation-plan")),
            ("cloud-platform-extension", "references/provider-api-and-managed-service-authority.md"): (430, "4fc9962a94a2fcbdbf89128f7c26f8ea82b00e8532da9d604eccbcc0037381be", ALL_ROLES, ("decision-record", "proof-limit", "validation-plan")),
            ("cloud-platform-extension", "references/region-failure-domain-consistency-and-quota-contracts.md"): (485, "37d6621e04971dad77d5a5820022ace201388b0389bf690d2939356f0dd44eb4", ALL_ROLES, ("decision-record", "proof-limit", "validation-plan")),
            ("cloud-platform-extension", "references/resource-control-and-data-plane-boundaries.md"): (421, "eb9aa5a9b1f760b83825428562293f0afdfa9a4bcdb4af76c2d5081aef3e3fdc", ALL_ROLES, ("boundary-decision", "decision-record", "proof-limit")),
            ("configuration-runtime-policy", "references/benchmarks-and-patterns.md"): (455, "9ef96a4caa8a66abad659cd04a1dbe7fced550efcf94907f1bd143eb2f94a53b", TASK_FIRST_ROLES, ("option-comparison", "selected-approach")),
            ("configuration-runtime-policy", "references/checklist.md"): (378, "55406df248bce907803dffd55d3473109d149526cea056a4d5f7c9113954275d", TASK_FIRST_ROLES, ("checklist-result", "residual-risk")),
            ("configuration-runtime-policy", "references/evidence-patterns.md"): (436, "11db23aaedf78b0f5629b894c25bf3725b38559e6a216219bd63f3018aadfca4", TASK_FIRST_ROLES, ("evidence-record", "proof-limit", "residual-risk")),
            ("infrastructure-as-code-safety", "references/identity-destruction-and-recovery-contracts.md"): (812, "8cf0a2d5b85a83cd517a937059b28b243c2718e7da90dad405fd33a474e44b1f", ALL_ROLES, ("decision-record", "proof-limit", "residual-risk")),
            ("infrastructure-as-code-safety", "references/state-plan-and-drift-contracts.md"): (809, "d1d0bbf5306aaa75e25a9ed6a08d0d7c5b0066b75dd091cb276b63da58892bc6", ALL_ROLES, ("decision-record", "proof-limit", "residual-risk")),
            ("platform-infrastructure-change-builder", "references/iac-source-contracts.md"): (701, "ac76ff616b46e89bc3fbe32c02bb270161ae132d97162b38ba36866ae2148b29", ("task-agent",), ("proof-limit", "selected-approach", "validation-plan")),
            ("platform-infrastructure-change-builder", "references/kubernetes-source-contracts.md"): (600, "4408105827924db9af29351153865837a26a6e2c6e1075212668d00dee1830f6", ("task-agent",), ("proof-limit", "selected-approach", "validation-plan")),
        }
        selected_references = tuple(reference_specs)
        for (owner, relative_path), (tokens, sha256, roles, outputs) in reference_specs.items():
            if owner == "platform-infrastructure-change-builder":
                source_root = ROOT / "src/professional-skills" / owner
            elif owner == "cloud-platform-extension":
                source_root = ROOT / "src/domain-extensions" / owner
            else:
                source_root = ROOT / "src/foundation/capabilities" / owner
            path = source_root / relative_path
            source = path.read_text(encoding="utf-8")
            self.assertEqual(sha256, hashlib.sha256(source.encode("utf-8")).hexdigest())
            self.assertEqual(tokens, VALIDATION.count_o200k_base_tokens(source))
            self.assertEqual((roles, outputs), _reference_binding(owner, str(path.relative_to(ROOT))))

        professional = VALIDATION.load_yaml_file(ROOT / "src/registry/professional-skills.yaml")
        foundation = VALIDATION.load_yaml_file(ROOT / "src/registry/foundation-skills.yaml")
        domain = VALIDATION.load_yaml_file(ROOT / "src/registry/domain-skills.yaml")
        selector_authority = VALIDATION.layer3_selector_authority(foundation, professional, domain, context="C1P platform IaC witness")
        selector_projection = VALIDATION.layer3_selector_runtime_projection(selector_authority, professional_skill="platform-infrastructure-change-builder", profile="task-agent", selection_owner="main-control-agent", exact_layer3=None)
        receipt = VALIDATION.layer3_selector_runtime_selection_receipt(selector_projection, evidence_signals=["cloud control plane", "account authority", "changed-surface", "configuration runtime policy typed config default validation fail fast hot reload feature flag owner expiry cleanup kill switch stale flag mode kind switch tenant user experiment rollout rollback config observability", "desired-state infrastructure source with state identity drift destruction or recovery"])
        self.assertEqual(["cloud-platform-extension", "configuration-runtime-policy", "infrastructure-as-code-safety"], receipt["selected_layer3"])
        self.assertEqual("434c91b6b2caf2b3b78ff6ffbfd86491a1d834746060092e516142467fcb6953", receipt["receipt_sha256"])
        self.assertEqual({"cloud-platform-extension"}, set(receipt["selected_layer3"]) & {row["name"] for row in domain["domain_skills"]})

        authority = VALIDATION.reference_context_admissibility_authority(professional, foundation, domain, context="C1P platform IaC staged witness")
        staged = VALIDATION.reference_context_staged_plan(authority, references=selected_references, path="direct", profile="task-agent", selection_owner="main-control-agent", available_carrier_fields=[], receipt_replayed=True, brief_current=False, review_fresh=True)
        expected = [list(reference) for reference in selected_references]
        self.assertTrue(staged["reachable"])
        self.assertEqual(expected, staged["selected_union"])
        self.assertEqual(expected, staged["loaded_union"])
        self.assertEqual([[reference] for reference in expected], [stage["loaded_references"] for stage in staged["stages"]])
        self.assertEqual(12, len(staged["required_output_receipts"]))
        self.assertTrue(all(stage["carried_predecessors"] == [] for stage in staged["stages"]))
        self.assertEqual([], staged["carried_predecessors"])
        active_stage = staged["stages"][8]
        self.assertEqual(8, active_stage["stage"])
        self.assertEqual([expected[8]], active_stage["loaded_references"])
        self.assertEqual([{"reference": expected[8], "required_outputs": ["decision-record", "proof-limit", "residual-risk"]}], active_stage["required_output_receipts"])

        component_tokens = [697, 229, 250, 183, 165, 812, 657]
        component_sha256 = ["28dde3cc5659529fa79b251dcf71b305372df5533d2050495a174f8782291f7e", "edf20265275b1afa37ecd528904f486436cfa88cd04b6ecacb773a0ed8105958", "fcbe9dc653c2d7f98fe01738547701d6ba79fff570c24b176e130d3c17941ad2", "f91cb26ad5c184d9505fec203a388ee461fda50f6a9c1684abc83bda5bfb8237", "a0a06ad825967e548dc5eb817ce003a24519aa99a4c2262cc0bcbc0830a97b76", "8cf0a2d5b85a83cd517a937059b28b243c2718e7da90dad405fd33a474e44b1f", "b1dc031dec6d279d689ca18f620a82b8bc28548d12bba49a5233a969837cb1ac"]
        self.assertEqual(7, len(component_sha256))
        self.assertEqual(2_993, sum(component_tokens))
        self.assertEqual(2_992, sum(component_tokens) - 1)
        self.assertEqual(2_999, sum(component_tokens) + 6)
        self.assertLessEqual(sum(component_tokens) + 6, 3_000)
        self.assertEqual(812, max(tokens for tokens, _sha256, _roles, _outputs in reference_specs.values()))
        negative = list(component_tokens)
        negative[5] = 814
        self.assertEqual(3_001, sum(negative) + 6)

        protected = {
            "src/professional-skills/platform-infrastructure-change-builder/SKILL.md": "4d43548f48103571f863dc798d5023ae7ad18bd9a674cc74ec14557ee7a74d0a",
            "src/domain-extensions/cloud-platform-extension/SKILL.md": "6c300ff1c468f83c7b75c54997c67539710e6f8e236fc655d4ecda5e806a4224",
            "src/registry/professional-skills.yaml": "32a3b49da13930f3baccf54dbd8de12064b1f07d273b2948dfaeb12586eaf49a",
            "src/registry/foundation-skills.yaml": "385843496634f9e9ef4426790cacff211858cab4f73c6c15f521fc2732b5b8fd",
            "src/registry/domain-skills.yaml": "2d53ccc4206c94d9850e007d21603f04ba1f06f7721de5da1cd47dcfe6e16129",
            "scripts/build.py": "2543ed2c2cb7498babeae20d1f7bd244f968522f116c90b8b08c4106a25efcf1",
            "scripts/validation_utils.py": "a76092b2d24cdfaec66eb44e1f8d4e48a9f76d9dda8a875a3b5602771649f995",
            "evals/agent-light-trajectories/cases.yaml": "25cc065fde1298111bbc5d3236976f3601b0db30453c805516689f2998c0191b",
            "tests/scripts/test_reference_registry_jit.py": "c4730adbdb7a5bdbae7ab24d979f563a2fab17d5fb634d83326a00d0dd00ad85",
            "tests/scripts/test_eval_rendered_context_budget.py": "9bc52e95f1ad5e6a3d5a8ad164eb789172c6b2b2b374749e42ddc12df9237a5a",
            "scripts/audit-skill-content.py": "19075d5a17baf72de6da658f113e3b029720a927fd8723885b6806d97a74cfab",
            "tests/scripts/test_validate_root_content.py": "432ed062a7f2f71cc0c23ac90c0fc3d06aaa85901c3376965ff6291dd2a306fc",
        }
        for path, expected_sha256 in protected.items():
            self.assertEqual(expected_sha256, hashlib.sha256((ROOT / path).read_bytes()).hexdigest())

    def test_fg_c1q_data_middleware_authoring_and_budget_frontier_is_lossless(self) -> None:
        source_specs = {
            "src/professional-skills/data-middleware-change-builder/SKILL.md": (
                "378cc3360994e28d7d6b8687fdc2c22f0425d1639524da72742f6e47bd8ccc63",
                "51af820aededb532f57198975c6290b76e6c65b20e9c0ae2817171a9980c5db1",
                795,
                (
                    "Map ownership, failure, recovery, and proof.",
                    "Apply the accepted state change.",
                    "Keep state, consistency, transaction, delivery, migration, and recovery with their owner.",
                    "Require resumable progress and invariant validation before cleanup.",
                    "Load one Reference for its open output.",
                    "A derived store can look healthy while diverging from its source of truth.",
                    "Retry can duplicate an effect when durable identity or acknowledgement ordering is unclear.",
                    "Successful movement or local commit does not prove invariant preservation, recovery, or downstream compatibility.",
                    "**Analysis mode:** Map source and derived ownership, readers and writers, invariants, consistency, migration, recovery, and current evidence limits before selecting the boundary.",
                    "**Task mode:** Apply the accepted state transition with bounded execution, replay or idempotency, reconciliation, rollback or forward repair, redaction, and post-edit validation.",
                    "Stop on unowned state/recovery or unsafe tool execution.",
                    "state-ownership decision and consistency, migration, and recovery model",
                    "stateful boundary changes, replay and reconciliation evidence, and unresolved recovery risk",
                ),
            ),
            "src/foundation/capabilities/data-migration-design/references/evidence-patterns.md": (
                "561e47eebd152e45137711cb91bd6cbac2b2068c44eb83297e57b0b5e7d459e8",
                "b868feeb34a6b3e3399403c1b96608a6baa46f8768945768c02ff1a517f3ea65",
                611,
                (
                    "Use this map to close migration evidence and proof limits.",
                    "| Source known | Schema, ledger/checksums, generated clients, inspected stores. | Inspected state; excludes manual drift or unseen downstream stores. |",
                    "| Versions coexist | Deployment matrix and reader/writer inventory. | Named versions/order; excludes unknown consumers, mobile lag, or external reports. |",
                    "| DDL lock bounded | Lock class, online mode, abort threshold, representative dry run or `not_verified`. | Selected strategy; excludes production contention or peak impact. |",
                    "| Backfill resumes | Batch, checkpoint, idempotent predicate, resume test, progress signal. | Covered rows; excludes sparse partitions, tenant distributions, or full runtime. |",
                    "| Invariant holds | Full, partition, or tenant query with expected/actual counts. | Declared affected data; excludes future writes, late CDC, or hidden transforms. |",
                    "| Recovery credible | Phase tier, command/test/report, owner, point of no return. | Reviewed path; excludes restore RTO, provider SLA, or manual reliability without rehearsal. |",
                    "| Cleanup safe | Caller search, generated diff, zero-use telemetry, backup/restore evidence, signoff. | Inspected readers/writers gone; excludes uninstrumented jobs, ad hoc queries, or archives. |",
                    "| Cutover bounded | Source authority, CDC lag, reconciliation diff, replay/abort, post-cutover validation. | Measured cutover; long-tail order, uninspected regions, and repair jobs remain unproved. |",
                    "| Watch detects harm | Lag, locks, errors, throughput, duration, completeness, owner, thresholds. | Expected failures visible; seasonal production behavior remains unproved. |",
                    "relevant edits reopen proof.",
                    "Production database, CDC, backup, restore, cloud, or deploy action requires permission, available dry run, recovery, stop, and redaction.",
                    "Retry non-idempotent conversion blindly or let backfill and live writers race without an authority rule.",
                ),
            ),
        }
        mismatches = []
        for path, (pre_sha256, post_sha256, tokens, anchors) in source_specs.items():
            source = (ROOT / path).read_text(encoding="utf-8")
            actual_sha256 = hashlib.sha256(source.encode("utf-8")).hexdigest()
            if actual_sha256 != post_sha256:
                self.assertEqual(pre_sha256, actual_sha256)
                mismatches.append(path)
                continue
            self.assertEqual(tokens, VALIDATION.count_o200k_base_tokens(source))
            for anchor in anchors:
                self.assertEqual(1, source.count(anchor))
                self.assertEqual(0, source.replace(anchor, "", 1).count(anchor))
        if mismatches:
            self.fail(f"C1Q source posts not reached: {mismatches}")

        root_path = ROOT / "src/professional-skills/data-middleware-change-builder/SKILL.md"
        _metadata, raw_frontmatter, body = VALIDATION.parse_frontmatter(root_path)
        h1_titles, sections = BUILD._markdown_heading_sections(body)
        self.assertEqual(["data-middleware-change-builder"], h1_titles)
        compact = ["---", raw_frontmatter, "---", "", "# data-middleware-change-builder"]
        for heading in BUILD.PROFESSIONAL_BUILT_KERNEL_HEADINGS:
            values = sections.get(heading, [])
            self.assertEqual(1, len(values))
            compact.extend(["", f"## {heading}", "", values[0]])
        compact.extend(BUILD._compact_jit_reference_delivery_lines("data-middleware-change-builder"))
        compact.append("")
        compact_projection = "\n".join(compact)
        self.assertEqual(246, VALIDATION.count_o200k_base_tokens(compact_projection))
        self.assertEqual("2b71a32f0a209286a10ca1e770882e487479dcfdde5737587dee4954fe55bd94", hashlib.sha256(compact_projection.encode("utf-8")).hexdigest())
        for omitted in ("## When To Use", "## Do Not Use", "## Required Inputs", "## High-Value Gotchas", "## Execution Checklist", "## Targeted References"):
            self.assertNotIn(omitted, compact_projection)
        for retained in ("## Role", "## Professional Decision Rules", "## Stop / Escalation Conditions", "## Output Contract", "## JIT Reference Delivery"):
            self.assertEqual(1, compact_projection.count(retained))
        dev_projection = compact_projection.rstrip() + "\n\n## Layer 3 Delivery\n\nFoundation and Domain items are top-level Skills; no Layer 3 references are compiled.\n"
        self.assertEqual(269, VALIDATION.count_o200k_base_tokens(dev_projection))
        self.assertEqual("22a41125147da43b01da304168205b8840d7ec6649a16c7727bd7719943696f3", hashlib.sha256(dev_projection.encode("utf-8")).hexdigest())

        reference_specs = {
            ("data-middleware-change-builder", "references/checklist.md"): (359, "7913ab5061bcc773b799077d47a02e5f0fee9e66dbe386c4c1bdb5c5d0b9473f", ("analysis-agent", "task-agent"), ("checklist-result", "residual-risk")),
            ("data-middleware-change-builder", "references/evidence-patterns.md"): (374, "c9f9f5090e759139a549b8f2d21bb47c18740d55dbea095686ea6530966b0569", ("analysis-agent", "task-agent"), ("evidence-record", "proof-limit", "residual-risk")),
            ("data-middleware-change-builder", "references/recovery-patterns.md"): (291, "ccd256b2616f32f673419a7452c1b1b47ac23f85485ccfd4a52f5559d614c9aa", ("analysis-agent", "task-agent"), ("option-comparison", "selected-approach")),
            ("data-migration-design", "references/benchmarks-and-patterns.md"): (346, "2b46b6b6480cc0afb931df255730a143988a76d944ab9244a26ff02e0d633005", ALL_ROLES, ("option-comparison", "selected-approach")),
            ("data-migration-design", "references/checklist.md"): (104, "17161f751bca0a79e5cb56d07ce3af3ba889feba2437f8429e5934c5b158ed8d", ALL_ROLES, ("checklist-result", "residual-risk")),
            ("data-migration-design", "references/evidence-patterns.md"): (611, "b868feeb34a6b3e3399403c1b96608a6baa46f8768945768c02ff1a517f3ea65", ALL_ROLES, ("evidence-record", "proof-limit", "residual-risk")),
            ("distributed-workflow-consistency", "references/compensation-convergence-and-reconciliation.md"): (607, "4b8f50abb517dad40a6092b351e245b0db9ae9f0511189c8c7a625a4c1dcd104", ALL_ROLES, ("failure-decision", "selected-approach", "residual-risk")),
            ("distributed-workflow-consistency", "references/identity-state-and-unknown-outcomes.md"): (592, "7a0e547eee5e8b179d2d173058dc46bea0be9191858b6b810e475bbc3d7322d6", ALL_ROLES, ("boundary-decision", "failure-decision", "proof-limit")),
            ("distributed-workflow-consistency", "references/stuck-manual-repair-and-versioning.md"): (606, "e07c57d14b47fef508030c9469abf96d163fcafb9478a3e7c93e47b1511f101a", ALL_ROLES, ("failure-decision", "validation-plan", "proof-limit")),
            ("transaction-consistency", "references/benchmarks-and-patterns.md"): (608, "99a9f2e244e3083030ebd9b64a89be758208f1380787c0824236c4a83244518a", ("analysis-agent", "task-agent"), ("option-comparison", "selected-approach")),
            ("transaction-consistency", "references/checklist.md"): (451, "e588a5f3bd0ee1709ae90944bcdee804c9c243ee61f3c5b96ce1b28154802e9a", ("analysis-agent", "task-agent"), ("checklist-result", "residual-risk")),
            ("transaction-consistency", "references/evidence-patterns.md"): (548, "150e1fe62bd88659fe7ebc2a6bdbdbf6153894340460264c518be871736bc6c5", ("analysis-agent", "task-agent"), ("evidence-record", "proof-limit", "residual-risk")),
        }
        selected_references = tuple(reference_specs)
        for (owner, relative_path), (tokens, sha256, roles, outputs) in reference_specs.items():
            source_root = ROOT / ("src/professional-skills" if owner == "data-middleware-change-builder" else "src/foundation/capabilities") / owner
            path = source_root / relative_path
            source = path.read_text(encoding="utf-8")
            self.assertEqual(sha256, hashlib.sha256(source.encode("utf-8")).hexdigest())
            self.assertEqual(tokens, VALIDATION.count_o200k_base_tokens(source))
            self.assertEqual((roles, outputs), _reference_binding(owner, str(path.relative_to(ROOT))))
        self.assertEqual(611, max(tokens for tokens, _sha256, _roles, _outputs in reference_specs.values()))

        protected = {
            "src/foundation/capabilities/data-migration-design/SKILL.md": "8b3651ba9b7a7a97203fe2dee1806a74a34f74e2250c573e9cd786b0932cc8fa",
            "src/foundation/capabilities/transaction-consistency/SKILL.md": "076dff13a9468d13713ec106f5a96586f44635855f9600998209d197a8fb5308",
            "src/foundation/capabilities/distributed-workflow-consistency/SKILL.md": "df3a7d24a62d3aabc74405abeb7ce98376da7a049c3ec8b36c43c25694a98b2e",
            "src/registry/professional-skills.yaml": "32a3b49da13930f3baccf54dbd8de12064b1f07d273b2948dfaeb12586eaf49a",
            "src/registry/foundation-skills.yaml": "385843496634f9e9ef4426790cacff211858cab4f73c6c15f521fc2732b5b8fd",
            "src/registry/domain-skills.yaml": "2d53ccc4206c94d9850e007d21603f04ba1f06f7721de5da1cd47dcfe6e16129",
            "scripts/build.py": "2543ed2c2cb7498babeae20d1f7bd244f968522f116c90b8b08c4106a25efcf1",
            "scripts/validation_utils.py": "a76092b2d24cdfaec66eb44e1f8d4e48a9f76d9dda8a875a3b5602771649f995",
            "evals/agent-light-trajectories/cases.yaml": "25cc065fde1298111bbc5d3236976f3601b0db30453c805516689f2998c0191b",
            "tests/scripts/test_reference_registry_jit.py": "c4730adbdb7a5bdbae7ab24d979f563a2fab17d5fb634d83326a00d0dd00ad85",
            "tests/scripts/test_eval_rendered_context_budget.py": "9bc52e95f1ad5e6a3d5a8ad164eb789172c6b2b2b374749e42ddc12df9237a5a",
            "scripts/audit-skill-content.py": "19075d5a17baf72de6da658f113e3b029720a927fd8723885b6806d97a74cfab",
            "tests/scripts/test_validate_root_content.py": "432ed062a7f2f71cc0c23ac90c0fc3d06aaa85901c3376965ff6291dd2a306fc",
        }
        for path, expected_sha256 in protected.items():
            self.assertEqual(expected_sha256, hashlib.sha256((ROOT / path).read_bytes()).hexdigest())

        professional = VALIDATION.load_yaml_file(ROOT / "src/registry/professional-skills.yaml")
        foundation = VALIDATION.load_yaml_file(ROOT / "src/registry/foundation-skills.yaml")
        domain = VALIDATION.load_yaml_file(ROOT / "src/registry/domain-skills.yaml")
        selector_authority = VALIDATION.layer3_selector_authority(foundation, professional, domain, context="C1Q data-middleware content witness")
        selector_projection = VALIDATION.layer3_selector_runtime_projection(selector_authority, professional_skill="data-middleware-change-builder", profile="task-agent", selection_owner="main-control-agent", exact_layer3=None)
        evidence_signals = ["database-migration", "distributed-effect-change"]
        receipt = VALIDATION.layer3_selector_runtime_selection_receipt(selector_projection, evidence_signals=evidence_signals)
        self.assertEqual(["data-migration-design", "transaction-consistency", "distributed-workflow-consistency"], receipt["selected_layer3"])
        self.assertEqual("6267555050601288125c263945346b3abdd3f22a54cb2a6337e3de44053e1298", receipt["receipt_sha256"])
        for reduced_signals in (evidence_signals[:1], evidence_signals[1:]):
            reduced = VALIDATION.layer3_selector_runtime_selection_receipt(selector_projection, evidence_signals=reduced_signals)
            self.assertNotEqual(receipt["selected_layer3"], reduced["selected_layer3"])
            self.assertNotEqual(receipt["receipt_sha256"], reduced["receipt_sha256"])
        domain_names = {row["name"] for row in domain["domain_skills"]}
        self.assertEqual(set(), set(receipt["selected_layer3"]) & domain_names)

        authority = VALIDATION.reference_context_admissibility_authority(professional, foundation, domain, context="C1Q data-middleware staged witness")
        staged = VALIDATION.reference_context_staged_plan(authority, references=selected_references, path="direct", profile="task-agent", selection_owner="main-control-agent", available_carrier_fields=[], receipt_replayed=True, brief_current=False, review_fresh=True)
        expected = [list(reference) for reference in selected_references]
        self.assertTrue(staged["reachable"])
        self.assertEqual(expected, staged["selected_union"])
        self.assertEqual(expected, staged["loaded_union"])
        self.assertEqual([[reference] for reference in expected], [stage["loaded_references"] for stage in staged["stages"]])
        self.assertEqual(12, len(staged["required_output_receipts"]))
        self.assertTrue(all(stage["carried_predecessors"] == [] for stage in staged["stages"]))
        self.assertEqual([], staged["carried_predecessors"])
        active_stage = staged["stages"][5]
        self.assertEqual(5, active_stage["stage"])
        self.assertEqual([expected[5]], active_stage["loaded_references"])
        self.assertEqual([{"reference": expected[5], "required_outputs": ["evidence-record", "proof-limit", "residual-risk"]}], active_stage["required_output_receipts"])

        relevant_ledger = [entry for entry in RELOCATION_LEDGER if entry["owner"] in {"data-migration-design", "transaction-consistency", "distributed-workflow-consistency"}]
        self.assertEqual({"data-migration-design", "transaction-consistency", "distributed-workflow-consistency"}, {entry["owner"] for entry in relevant_ledger})
        self.assertTrue(all(entry["route_effect"] == "unchanged" and entry["co_trigger_effect"] == "unchanged" for entry in relevant_ledger))

        component_tokens = [697, 269, 230, 283, 246, 611, 657]
        component_sha256 = [
            "28dde3cc5659529fa79b251dcf71b305372df5533d2050495a174f8782291f7e",
            "22a41125147da43b01da304168205b8840d7ec6649a16c7727bd7719943696f3",
            "f93f83da98b02b86460d186c6b3cb2187caa25234eaf64f2343799ee8bde7483",
            "e8c916c5260c27787c8ac9da1ce9b0f4eebe2972360ea6779f050721a2bd5c75",
            "c8d8f21a9a60dfe588db5a8157791781715b8293758a6d730ee38ad1dc3f65c6",
            "b868feeb34a6b3e3399403c1b96608a6baa46f8768945768c02ff1a517f3ea65",
            "b1dc031dec6d279d689ca18f620a82b8bc28548d12bba49a5233a969837cb1ac",
        ]
        self.assertEqual(7, len(component_sha256))
        self.assertEqual(2_993, sum(component_tokens))
        self.assertEqual(2_992, sum(component_tokens) - 1)
        self.assertEqual(2_999, sum(component_tokens) + 6)
        self.assertLessEqual(sum(component_tokens) + 6, 3_000)
        negative = list(component_tokens)
        negative[5] = 613
        self.assertEqual(3_001, sum(negative) + 6)

    def test_fg_six_authoring_source_only_sections_are_complete_and_projection_neutral(self) -> None:
        source_specs = (
            (
                "change-documentation-gate",
                "src/professional-skills/change-documentation-gate/SKILL.md",
                "a21cca73e6f6eddfecef6a6386668e8dc1d3cb70dbab7f6ed37c06753a16e6eb",
                "426d98046ff139c5cab312acf59abc2e54396e74ce3f451acf9d293930a13407",
                854,
                4_353,
                70,
                354,
                "c56356bd498a15cc00981e09d279575ec9c0200ac67450780397207915a610a7",
                1_813,
                35,
                377,
                "7e99d2a913c43357f8b436e72646c3ae6d2ffbe422b747d4d300a6c54485be3a",
                1_921,
                39,
                {
                    "Role": "1e8dfaf6883899cc125f53bb83697f996152d91f916962b239f957f551a176d1",
                    "Professional Decision Rules": "34525b2b95a7c6d4b6b9f39456df96c2017b05e6853106e2c2c57f58ffde46fd",
                    "Stop / Escalation Conditions": "e231d6c5191bb1e9162cb4e571c90bff84db7a16626db7722e2371c19929fe4f",
                    "Output Contract": "3bb1101cfda146d3fe232f978fdb26bf216a38b14f72c4613ed65b80cdc87774",
                },
                (
                    "- Generated documentation can pass source checks while rendered links or examples remain stale.",
                    "- A no-docs claim can hide audience impact when its evidence omits changed behavior.",
                    "- Safe-disclosure limits still apply to examples, runbooks, migration notes, and incident records.",
                ),
                (
                    "- **Task mode:** Map changed behavior to its owning documentation source and generated origin.",
                    "- **Task mode:** Validate rendered links, examples, commands, and failure guidance against current behavior.",
                    "- **Review mode:** Compare published guidance with current behavior and freshness evidence.",
                    "- Record skipped documentation surfaces as owned residual debt.",
                    "- Minimal validation: render the affected artifact and run its link, example, or command checks.",
                ),
            ),
            (
                "delivery-release-gate",
                "src/professional-skills/delivery-release-gate/SKILL.md",
                "c69b43f87da41ae42eeddda23dc32866e5eae199597490668735e562521ba478",
                "aaf5c2ea8078a3c794725303f2ce7c3372dd96569a4a0d5dc88bc82024fa1fda",
                755,
                3_797,
                68,
                310,
                "58d88e71ba05ce0b36336ac8ef70f3f13ded845a842ac99fcdc01a5911ae7e5c",
                1_500,
                34,
                333,
                "cd91f6ea858e7b988fe1268c0e45d8f3cf38e501ff0a1cbb8d31a6ec0bcb4565",
                1_608,
                38,
                {
                    "Role": "b6fa99364a3025c27dc5debd6aa639c7c75536c84e49b1cb6cfc04f7835c60f9",
                    "Professional Decision Rules": "0349935ee43b54b7c408568f5fdc178bd5d4135e5005da61b2114d1e1546c1aa",
                    "Stop / Escalation Conditions": "4f0798d9ddaa3bebfb61bcc8a78a8fa3c63f682fcf0ca5ff7f5be649687c5c4d",
                    "Output Contract": "039946d3b0c8cf16ed4105320768016e089d99a873143ee1bce2422af4e563df",
                },
                (
                    "- Artifact identity can drift between validation, packaging, promotion, and rollback.",
                    "- Rollback availability does not prove compatibility, data recovery, or restoration time.",
                    "- Mixed-version success can hide an irreversible migration or configuration boundary.",
                ),
                (
                    "- **Analysis mode:** Map blast radius, compatibility order, containment, and recovery authority.",
                    "- **Task mode:** Build the accepted release artifact with provenance and rollback metadata.",
                    "- **Review mode:** Verify built identity, mixed-version evidence, and recovery readiness.",
                    "- Record unproved environments, migrations, and operator actions as residual risk.",
                    "- Minimal validation: inspect built-artifact identity and run the selected compatibility or recovery check.",
                ),
            ),
            (
                "high-risk-design-review",
                "src/professional-skills/high-risk-design-review/SKILL.md",
                "eece057e1b0a494974f40798b0ecfc710876cd0fe6d959a64866a9e9419092e9",
                "cef593ac51134204e4b05992664ac38d6f61ff80362b4ffd8c67f8f06507f1d7",
                513,
                2_629,
                63,
                235,
                "16081ca7a188f5b65f309c18b636a515061584adca9fd9bc37204f2f9d2d1606",
                1_191,
                32,
                258,
                "ddde479e97d3bb10f6fc3de03069fb08ae1897cc9bf28867f60ed7437324eb02",
                1_299,
                36,
                {
                    "Role": "981f0cff17867d6a661cf2986923b48be9120cece6af36788c30cad56f7d8952",
                    "Professional Decision Rules": "58de3e9b912f45c385ac0029f06a02cd3875cb65aeb519575fb67ccd9476b90d",
                    "Stop / Escalation Conditions": "12fdbe8767c1146d600c3efcd916c2c7397bf67924f7b587f29cc2784ab828f5",
                    "Output Contract": "77945aee17b4e54d7cad5f59e7b58b7e8ce9882505872c2c146afdae6fbc3eb6",
                },
                (
                    "- When ownership is ambiguous, an invariant or failure path may be split across decision makers.",
                    "- Reversibility on paper does not prove an executable rollback or forward-repair path.",
                    "- Multiple downstream tasks can preserve local acceptance while breaking the shared boundary.",
                ),
                (
                    "- **Review mode:** Map every material decision to one owner, invariant, failure path, and proof.",
                    "- Compare the selected design with at least one plausible alternative at the critical boundary.",
                    "- Verify rollback or forward repair for each irreversible or cross-task consequence.",
                    "- Record unreviewed decisions and evidence gaps as blocking findings or residual risk.",
                    "- Minimal validation: inspect the brief's named proofs and its recovery path.",
                ),
            ),
            (
                "integration-change-builder",
                "src/professional-skills/integration-change-builder/SKILL.md",
                "3a6c9fb3233b9273f5602f9f3cc42fadbf43c434c98605099a0703d64e985478",
                "617d1818769c1b0fd35289cef58fa998eff25bb47302a9a240e6160afbf5628b",
                716,
                3_703,
                64,
                250,
                "ad2699d376a7049d7512dd5a784632e1500d75b655df1e6be7a935b3464171f4",
                1_293,
                29,
                273,
                "adc848b9f2e31df7137ff465b3ee95c4224ac45f035512b52f45f4081a39e28e",
                1_401,
                33,
                {
                    "Role": "6bb84fc4f2a6abe4d82a459097f58a4a2cad53c96ec1230953883856665089af",
                    "Professional Decision Rules": "ebc33a49a3843727c35528a7137e264e92528c2be4ce2ec0af63b1de38612e1f",
                    "Stop / Escalation Conditions": "03d0111d45fdf646da9c14341e0a60df8a23ade56045d0682a731b0f03942adf",
                    "Output Contract": "b88cd9a10b6b3ed656fce9b9b8e0cff906533f829419b048971dbf54f7de9c06",
                },
                (
                    "- A successful request can still leave a duplicate or unknown external effect.",
                    "- Provider sandbox behavior does not prove production credentials, quotas, ordering, or recovery.",
                    "- Signature, serialization, or adapter drift can invalidate an otherwise correct contract.",
                ),
                (
                    "- **Analysis mode:** Map producer, consumer, provider, credential, contract, and reconciliation authority.",
                    "- **Task mode:** Apply the accepted adapter boundary with idempotency and failure handling.",
                    "- Verify timeout, retry, duplicate, malformed, denied, and unknown-outcome behavior.",
                    "- Record provider assumptions and untested recovery paths as residual risk.",
                    "- Minimal validation: run contract and failure tests at the real adapter or calibrated sandbox.",
                ),
            ),
            (
                "logging-design-gate",
                "src/professional-skills/logging-design-gate/SKILL.md",
                "219b4ff4cc685f9d16fd55ab7e612843c567aca7a06d786f99cc9f7d208a1df0",
                "221679944eb1df243492bc89ac444e3f8b2cd938939ffbdaa2ac933e731a46fa",
                796,
                3_857,
                67,
                293,
                "e6313187ef53df0de6bb2de88839d3589bff2a6f3585d808e0b7df2d922d5067",
                1_375,
                32,
                316,
                "df0cb0d0d21e7d7c2b6aa294147670103e9cf0a5b23057465b406c358662d082",
                1_483,
                36,
                {
                    "Role": "190344031c4db498f84302a25dfa0f1f6db2e1cf5e390c330b537c27bfc58681",
                    "Professional Decision Rules": "4e3755bb0199fdd50294e5e06b6876a3597c977eb6b2862ab64c729ae9d2af45",
                    "Stop / Escalation Conditions": "762fdbbaac2c5a233144f3cb36a5efaec92c7097390250e19ab2d30bd2e8d93d",
                    "Output Contract": "7c6bbd1e32693f64153ffb17c9ed9a1e82abc8ced3ecb883dbf947d028122e58",
                },
                (
                    "- More events can reduce diagnostic value through volume, cardinality, or duplicate noise.",
                    "- Redaction after formatting can expose sensitive values before the sink applies policy.",
                    "- A schema change can silently break alerts, audit consumers, or correlation.",
                ),
                (
                    "- **Task mode:** Map the diagnostic question to its event owner, placement, schema, and sink.",
                    "- **Task mode:** Apply approved field classification, redaction, level, and correlation decisions.",
                    "- **Review mode:** Compare emitted and suppressed paths with purpose and safe-logging evidence.",
                    "- Record unmeasured volume, consumer drift, and inaccessible sink behavior as residual risk.",
                    "- Minimal validation: run emission and suppression tests at the selected sink boundary.",
                ),
            ),
            (
                "repository-tooling-change-builder",
                "src/professional-skills/repository-tooling-change-builder/SKILL.md",
                "e443b342ea9280b972605d35403f1afd66e46d926023eff46870d7b065186c85",
                "5667183572a85ddde75b9caca9d6d07cdbe0c480b580e1fa7a7ae824bdb75d9b",
                758,
                3_771,
                65,
                261,
                "475a286d7143dba32bdab259bc4b121b8d769070b14641c8a12b12287507451b",
                1_268,
                30,
                284,
                "653d7ea0e7aa4f7889760b02d11a36cbfc7ba34718723462815a78e2cc920790",
                1_376,
                34,
                {
                    "Role": "9185d38be4c20cc32d448b07b5d7224c880944f556c108702aa121694682180a",
                    "Professional Decision Rules": "ffec33820c8ebc0ab5d9dc869af652722ea87e6282b3eaa551c142447ffd2197",
                    "Stop / Escalation Conditions": "cef7510f79be015d09307598819cd890473e60c5b1e517b24d233658309d9708",
                    "Output Contract": "68ef9887c2d963c1163956b50ddc293d3b0c3ec1d6b6412322f349e0e8c87029",
                },
                (
                    "- Generated output can look correct while bootstrap order or source authority is wrong.",
                    "- A subprocess can report success before output, cleanup, or child completion is durable.",
                    "- A maintenance command can cross its intended workspace or mutate files on rerun.",
                ),
                (
                    "- **Task mode:** Map source authority, callers, generated outputs, side effects, and cleanup ownership.",
                    "- Reuse the existing command, generator, harness, or process boundary when it owns the behavior.",
                    "- Verify compatibility, deterministic output, atomic completion, and bounded rerun behavior.",
                    "- Record skipped hosts, toolchains, consumers, and recovery paths as proof limits.",
                    "- Minimal validation: run normal, invalid, boundary, rerun, and forbidden-effect tests.",
                ),
            ),
        )
        pending = []
        unexpected = {}
        for owner, path, pre_sha256, post_sha256, *_rest in source_specs:
            actual_sha256 = hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
            if actual_sha256 == pre_sha256:
                pending.append(path)
            elif actual_sha256 != post_sha256:
                unexpected[path] = actual_sha256
        self.assertEqual({}, unexpected)
        self.assertEqual([], pending, f"source-only authoring posts not reached: {pending}")

        expected_headings = [
            "Role",
            "When To Use",
            "Do Not Use",
            "Required Inputs",
            "Professional Decision Rules",
            "High-Value Gotchas",
            "Execution Checklist",
            "Stop / Escalation Conditions",
            "Output Contract",
            "Targeted References",
        ]
        for (
            owner,
            relative_path,
            _pre_sha256,
            post_sha256,
            source_tokens,
            source_bytes,
            source_lf,
            compact_tokens,
            compact_sha256,
            compact_bytes,
            compact_lf,
            dev_tokens,
            dev_sha256,
            dev_bytes,
            dev_lf,
            preserved_sections,
            gotchas,
            checklist,
        ) in source_specs:
            path = ROOT / relative_path
            source_bytes_value = path.read_bytes()
            source = source_bytes_value.decode("utf-8")
            with self.subTest(owner=owner):
                self.assertEqual(post_sha256, hashlib.sha256(source_bytes_value).hexdigest())
                self.assertEqual(source_tokens, VALIDATION.count_o200k_base_tokens(source))
                self.assertEqual(source_bytes, len(source_bytes_value))
                self.assertEqual(source_lf, source_bytes_value.count(b"\n"))
                self.assertTrue(source_bytes_value.endswith(b"\n"))
                _metadata, raw_frontmatter, body = VALIDATION.parse_frontmatter(path)
                h1_titles, sections = BUILD._markdown_heading_sections(body)
                self.assertEqual(1, len(h1_titles))
                self.assertEqual(expected_headings, re.findall(r"^## (.+)$", body, flags=re.MULTILINE))
                self.assertEqual("\n".join(gotchas), sections["High-Value Gotchas"][0])
                self.assertEqual("\n".join(checklist), sections["Execution Checklist"][0])
                for heading, expected_sha256 in preserved_sections.items():
                    self.assertEqual(1, len(sections.get(heading, [])))
                    self.assertEqual(expected_sha256, hashlib.sha256(sections[heading][0].encode("utf-8")).hexdigest())

                compact = ["---", raw_frontmatter, "---", "", f"# {h1_titles[0]}"]
                for heading in BUILD.PROFESSIONAL_BUILT_KERNEL_HEADINGS:
                    values = sections.get(heading, [])
                    self.assertEqual(1, len(values))
                    compact.extend(["", f"## {heading}", "", values[0]])
                compact.extend(BUILD._compact_jit_reference_delivery_lines(owner))
                compact.append("")
                compact_projection = "\n".join(compact)
                self.assertEqual(compact_tokens, VALIDATION.count_o200k_base_tokens(compact_projection))
                self.assertEqual(compact_sha256, hashlib.sha256(compact_projection.encode("utf-8")).hexdigest())
                self.assertEqual(compact_bytes, len(compact_projection.encode("utf-8")))
                self.assertEqual(compact_lf, compact_projection.count("\n"))
                self.assertTrue(compact_projection.endswith("\n"))
                self.assertNotIn("## High-Value Gotchas", compact_projection)
                self.assertNotIn("## Execution Checklist", compact_projection)

                dev_projection = compact_projection.rstrip() + "\n\n## Layer 3 Delivery\n\nFoundation and Domain items are top-level Skills; no Layer 3 references are compiled.\n"
                self.assertEqual(dev_tokens, VALIDATION.count_o200k_base_tokens(dev_projection))
                self.assertEqual(dev_sha256, hashlib.sha256(dev_projection.encode("utf-8")).hexdigest())
                self.assertEqual(dev_bytes, len(dev_projection.encode("utf-8")))
                self.assertEqual(dev_lf, dev_projection.count("\n"))
                self.assertTrue(dev_projection.endswith("\n"))

    def test_fg_c1r_delivery_release_and_iot_frontier_is_lossless_and_bounded(self) -> None:
        source_specs = {
            "src/professional-skills/delivery-release-gate/SKILL.md": (
                "e1ef7ea744f1d43986c8f4b655d057c10b8432d942b90c27b72044857710e8b4",
                "aaf5c2ea8078a3c794725303f2ce7c3372dd96569a4a0d5dc88bc82024fa1fda",
                755,
                3_797,
                68,
                (
                    "Name the release decision owner.",
                    "Load the named Reference for the open output.",
                    "Require authority before action.",
                    "Block stale artifact/environment, authority, containment, compatibility/migration, infrastructure-state, or recovery evidence.",
                    "Refuse destructive, privileged, irreversible, or secret-bearing production action absent authority, sandbox/preview, recovery, and redaction.",
                    "Artifact identity can drift between validation, packaging, promotion, and rollback.",
                    "Rollback availability does not prove compatibility, data recovery, or restoration time.",
                    "Mixed-version success can hide an irreversible migration or configuration boundary.",
                    "**Analysis mode:** Map blast radius, compatibility order, containment, and recovery authority.",
                    "**Task mode:** Build the accepted release artifact with provenance and rollback metadata.",
                    "**Review mode:** Verify built identity, mixed-version evidence, and recovery readiness.",
                    "**Analysis mode (`analysis-agent`):** release plan; authority boundary; rollout and rollback decisions.",
                    "**Task mode (`task-agent`):** release artifact; provenance, compatibility, and rollback metadata.",
                    "**Review mode (`review-agent`):** go/no-go verdict; readiness gaps; unreviewed deployment risk.",
                ),
            ),
            "src/domain-extensions/iot-embedded-extension/references/checklist.md": (
                "400f59603f579553c17a09d48ced899a1ab922474bde1119c01433fdb55ffe0a",
                "771c35d891ee7662d60144c0bab45f6e6956007060d3ab6a97e69aef6051552e",
                482,
                2_517,
                25,
                (
                    "Prove update recovery through image validation, atomic activation, last-known-good boot, power-loss behavior, mixed-fleet compatibility, rollback, and offline recovery.",
                    "Map provisioning, operation, update, reset, retirement, transfer, and loss to authority and credential, binding, protected-state, retained-data, and cloud outcomes.",
                    "Define buffering, retry identity/budget, duplicates/reordering, command expiry, reconnect, reconciliation, and behavior without network recovery.",
                    "Bind firmware/SBOM identity, vulnerabilities, support lifecycle, protocol/command versions, authentication, deprecation, and unsupported-message recovery to releases.",
                    "Define clock trust, drift, no-RTC startup, resynchronization, monotonic time, expiry, and reboot/offline ordering.",
                    "Derive compute, memory, endurance, power, bandwidth, thermal, and real-time budgets plus overload/exhaustion behavior from limits.",
                    "Treat timing evidence as a path bound across interrupts, interference, locking, priority, and scheduling, with observed maxima sampled and unsupported conditions residual.",
                    "Bind physical-impact safe state, emergency action, local override, notification, command rejection, reset, and containment to hazard evidence.",
                    "Map identity, attestation, integrity, clone detection, command authority, credential rotation and revocation, tamper, duplicates, and attestation-loss recovery across affected trust boundaries.",
                    "Bind manufacturing identity, secret injection/derivation, custody, audit, rework, transfer, and invalid credential recovery to its trust chain.",
                    "Select authorization or disablement for production debug from threat/service evidence, including re-enable authority, traceability, secret-exposure behavior, and supported revisions in scope.",
                    "For unsafe old firmware, bind downgrade/recovery to trusted version authority and protected-state behavior under brownout, replacement, reset, and service.",
                    "Stranding/unsafe-boot risk requires boot-loop detection evidence, recovery authority, a bootable, serviceable, or safe target, and behavior when its image or connectivity is unavailable.",
                    "Use simulator, HIL, degraded-network, power-loss, rollback, and fault-injection runs as samples, not worst-case timing proof.",
                    "Monitor fleet health, firmware, boot loops, credentials, telemetry lag, commands, resources, update, connectivity, and safety with bounded labels, alert ownership, and field-recovery action.",
                ),
            ),
        }
        pending = []
        for path, (pre_sha256, post_sha256, tokens, size, line_feeds, anchors) in source_specs.items():
            source_bytes = (ROOT / path).read_bytes()
            actual_sha256 = hashlib.sha256(source_bytes).hexdigest()
            if actual_sha256 not in {pre_sha256, post_sha256}:
                self.fail(f"unexpected C1R source preimage for {path}: {actual_sha256}")
            with self.subTest(source_hash=path):
                self.assertEqual(post_sha256, actual_sha256)
            if actual_sha256 != post_sha256:
                pending.append(path)
                continue
            source = source_bytes.decode("utf-8")
            self.assertEqual(tokens, VALIDATION.count_o200k_base_tokens(source))
            self.assertEqual(size, len(source_bytes))
            self.assertEqual(line_feeds, source_bytes.count(b"\n"))
            self.assertTrue(source_bytes.endswith(b"\n"))
            for anchor in anchors:
                self.assertEqual(1, source.count(anchor))
                self.assertEqual(0, source.replace(anchor, "", 1).count(anchor))
        if pending:
            return

        delivery_path = ROOT / "src/professional-skills/delivery-release-gate/SKILL.md"
        _metadata, raw_frontmatter, delivery_body = VALIDATION.parse_frontmatter(delivery_path)
        h1_titles, delivery_sections = BUILD._markdown_heading_sections(delivery_body)
        self.assertEqual(["delivery-release-gate"], h1_titles)
        self.assertEqual(3, len(re.findall(r"^- ", delivery_sections["Professional Decision Rules"][0], flags=re.MULTILINE)))
        self.assertEqual("0349935ee43b54b7c408568f5fdc178bd5d4135e5005da61b2114d1e1546c1aa", hashlib.sha256(delivery_sections["Professional Decision Rules"][0].encode("utf-8")).hexdigest())
        self.assertEqual("4f0798d9ddaa3bebfb61bcc8a78a8fa3c63f682fcf0ca5ff7f5be649687c5c4d", hashlib.sha256(delivery_sections["Stop / Escalation Conditions"][0].encode("utf-8")).hexdigest())
        for heading, expected_sha256 in {
            "Role": "b6fa99364a3025c27dc5debd6aa639c7c75536c84e49b1cb6cfc04f7835c60f9",
            "High-Value Gotchas": "51bfc5153ccaba7f8648797e4c56a298a54245513624dec2e324376a121ce45a",
            "Execution Checklist": "96245ae2763f3ecee2d938b4e007860ea16c5e7085ca4417a5b3764f0d1958a5",
            "Output Contract": "039946d3b0c8cf16ed4105320768016e089d99a873143ee1bce2422af4e563df",
        }.items():
            self.assertEqual(expected_sha256, hashlib.sha256(delivery_sections[heading][0].encode("utf-8")).hexdigest())
        self.assertNotIn("Own only the selected release decision", delivery_body)

        def projection(path: str, headings: tuple[str, ...], selector: str | None, include_layer3_delivery: bool = False) -> str:
            _metadata, raw, body = VALIDATION.parse_frontmatter(ROOT / path)
            titles, sections = BUILD._markdown_heading_sections(body)
            self.assertEqual(1, len(titles))
            output = ["---", raw, "---", "", f"# {titles[0]}"]
            for heading in headings:
                values = sections.get(heading, [])
                if not values and heading == "Inputs":
                    continue
                self.assertEqual(1, len(values))
                output.extend(["", f"## {heading}", "", values[0]])
            output.extend(BUILD._compact_jit_reference_delivery_lines(selector))
            if include_layer3_delivery:
                output.extend(["", "## Layer 3 Delivery", "", "Foundation and Domain items are top-level Skills; no Layer 3 references are compiled."])
            output.append("")
            return "\n".join(output)

        compact_delivery = projection(
            "src/professional-skills/delivery-release-gate/SKILL.md",
            BUILD.PROFESSIONAL_BUILT_KERNEL_HEADINGS,
            "delivery-release-gate",
        )
        dev_delivery = projection(
            "src/professional-skills/delivery-release-gate/SKILL.md",
            BUILD.PROFESSIONAL_BUILT_KERNEL_HEADINGS,
            "delivery-release-gate",
            True,
        )
        self.assertEqual((310, "58d88e71ba05ce0b36336ac8ef70f3f13ded845a842ac99fcdc01a5911ae7e5c", 1_500, 34), (VALIDATION.count_o200k_base_tokens(compact_delivery), hashlib.sha256(compact_delivery.encode("utf-8")).hexdigest(), len(compact_delivery.encode("utf-8")), compact_delivery.count("\n")))
        self.assertEqual((333, "cd91f6ea858e7b988fe1268c0e45d8f3cf38e501ff0a1cbb8d31a6ec0bcb4565", 1_608, 38), (VALIDATION.count_o200k_base_tokens(dev_delivery), hashlib.sha256(dev_delivery.encode("utf-8")).hexdigest(), len(dev_delivery.encode("utf-8")), dev_delivery.count("\n")))
        self.assertNotIn("## High-Value Gotchas", compact_delivery)
        self.assertNotIn("## Execution Checklist", compact_delivery)

        root_specs = {
            "src/domain-extensions/iot-embedded-extension/SKILL.md": (BUILD.PROFESSIONAL_BUILT_KERNEL_HEADINGS, 338, "94a3e7d66eebc7a8c5c154df3405449473ea05b75b4d072f6828cbca8d197923"),
            "src/foundation/capabilities/release-rollback/SKILL.md": (BUILD.FOUNDATION_BUILT_KERNEL_HEADINGS, 229, "3e2150a21b3997726207b6ac9317c8077856708c87a481ac818898779c78229a"),
            "src/foundation/capabilities/version-compatibility/SKILL.md": (BUILD.FOUNDATION_BUILT_KERNEL_HEADINGS, 250, "989a93e84c8ba897bdc8ba69113da520c11207996f1d64b7ad59b4810284ae91"),
        }
        for path, (headings, tokens, sha256) in root_specs.items():
            built = projection(path, headings, None)
            self.assertEqual(tokens, VALIDATION.count_o200k_base_tokens(built))
            self.assertEqual(sha256, hashlib.sha256(built.encode("utf-8")).hexdigest())

        reference_specs = {
            ("delivery-release-gate", "references/checklist.md"): (125, "9f103563d839016ca66f86aef9a6679584a2dcadceea553964e01ceccb7a65ce", ALL_ROLES, ("checklist-result", "residual-risk")),
            ("delivery-release-gate", "references/delivery-output-and-gates.md"): (393, "e76f8bcbd7b0ae6a0b5aa27afd603fe49b7def9c240bad0eda4da1c336527db4", ALL_ROLES, ("gate-decision", "residual-risk")),
            ("delivery-release-gate", "references/release-evidence-patterns.md"): (399, "b87635cc9fec6209239e4d0458a09acded3d97a2438fe8367dceb447b549add6", ALL_ROLES, ("evidence-record", "proof-limit", "residual-risk")),
            ("iot-embedded-extension", "references/checklist.md"): (482, "771c35d891ee7662d60144c0bab45f6e6956007060d3ab6a97e69aef6051552e", ALL_ROLES, ("checklist-result", "residual-risk")),
            ("release-rollback", "references/benchmarks-and-patterns.md"): (468, "52bbecd74a4ef1a0dc599855dbbd38d4ba08563e2a5fd60e3a27d4bd10dc74c6", ALL_ROLES, ("option-comparison", "selected-approach")),
            ("release-rollback", "references/checklist.md"): (295, "e8a45f93dcb38522492d252a295e5a6dcd61f9899bada1f5001aededf85c4096", ALL_ROLES, ("checklist-result", "residual-risk")),
            ("release-rollback", "references/evidence-patterns.md"): (422, "c0081ac454f9f9fa8a7ebd30b30a41cffdf41db26d3140f9e694672c3c109e58", ALL_ROLES, ("evidence-record", "proof-limit", "residual-risk")),
            ("version-compatibility", "references/checklist.md"): (464, "28af459587f9e62605d26021e65a7473ce105db007c22ea47e9a74147f62ed32", ALL_ROLES, ("checklist-result", "residual-risk")),
            ("version-compatibility", "references/compatibility-benchmarks.md"): (474, "af7766cecc9f29fad1063a16234c6bf69cc7fb62148a6934c7b498de7d5eb893", ALL_ROLES, ("option-comparison", "selected-approach")),
            ("version-compatibility", "references/evidence-patterns.md"): (468, "ccb0ce11c7e7cf4006a9f9b7f898eb2bd2922d846b02bd35d9a9470308dce96c", ALL_ROLES, ("evidence-record", "proof-limit", "residual-risk")),
        }
        selected_references = tuple(reference_specs)
        for (owner, relative_path), (tokens, sha256, roles, outputs) in reference_specs.items():
            if owner == "delivery-release-gate":
                source_root = ROOT / "src/professional-skills" / owner
            elif owner == "iot-embedded-extension":
                source_root = ROOT / "src/domain-extensions" / owner
            else:
                source_root = ROOT / "src/foundation/capabilities" / owner
            path = source_root / relative_path
            source = path.read_text(encoding="utf-8")
            self.assertEqual(sha256, hashlib.sha256(source.encode("utf-8")).hexdigest())
            self.assertEqual(tokens, VALIDATION.count_o200k_base_tokens(source))
            self.assertEqual((roles, outputs), _reference_binding(owner, str(path.relative_to(ROOT))))
        self.assertEqual(482, max(tokens for tokens, _sha256, _roles, _outputs in reference_specs.values()))

        iot_source = (ROOT / "src/domain-extensions/iot-embedded-extension/references/checklist.md").read_text(encoding="utf-8")
        self.assertEqual(["Lifecycle", "Safety And Identity", "Evidence"], re.findall(r"^## (.+)$", iot_source, flags=re.MULTILINE))
        self.assertEqual([6, 7, 2], [len(re.findall(r"^- ", section, flags=re.MULTILINE)) for section in re.split(r"^## .+$", iot_source, flags=re.MULTILINE)[1:]])
        jit_groups = (
            ("credential rotation and revocation", "affected trust boundaries", "attestation-loss recovery"),
            ("secret-exposure behavior", "supported revisions in scope"),
            ("boot-loop detection evidence", "bootable, serviceable, or safe target", "behavior when its image", "connectivity is unavailable"),
        )
        for group in jit_groups:
            self.assertTrue(all(iot_source.count(anchor) == 1 for anchor in group))
            first = group[0]
            self.assertTrue(all(anchor in iot_source[iot_source.index(first):iot_source.index(first) + 700] for anchor in group))
            self.assertEqual(0, iot_source.replace(first, "", 1).count(first))

        relocation = [entry for entry in RELOCATION_LEDGER if entry["source_rule_fingerprint"] == "090161109e5fafe86319cd760118fc6f3b390c91f8ef9e2f828d460d63a4922f"]
        self.assertEqual(1, len(relocation))
        relocation_entry = relocation[0]
        self.assertEqual("iot-embedded-extension", relocation_entry["owner"])
        self.assertEqual("Make updates recoverable", relocation_entry["old_anchor"])
        self.assertEqual("src/domain-extensions/iot-embedded-extension/references/checklist.md", relocation_entry["destination"])
        self.assertEqual("Prove update recovery through image validation, atomic activation, last-known-good boot, power-loss behavior, mixed-fleet compatibility, rollback, and offline recovery.", relocation_entry["new_anchor"])
        self.assertEqual(0, iot_source.count(relocation_entry["old_anchor"]))
        self.assertEqual(1, iot_source.count(relocation_entry["new_anchor"]))
        self.assertEqual(0, iot_source.replace(relocation_entry["new_anchor"], "", 1).count(relocation_entry["new_anchor"]))
        self.assertEqual("unchanged", relocation_entry["route_effect"])
        self.assertEqual("unchanged", relocation_entry["co_trigger_effect"])

        protected = {
            "src/domain-extensions/iot-embedded-extension/SKILL.md": "b36832cb68c5d2611c1c055e9b9efa9eeac6ecd5dd34f5f6e4062180045c38d4",
            "src/foundation/capabilities/release-rollback/SKILL.md": "738e04c280576f5392d91f822c605e2eed1916444aef7bf99b0aae48e2f4d453",
            "src/foundation/capabilities/version-compatibility/SKILL.md": "008bb557182e152938008b0f5e7175f5c2fb32eb44b9a7352b2a28e7591cfd75",
            "src/registry/professional-skills.yaml": "32a3b49da13930f3baccf54dbd8de12064b1f07d273b2948dfaeb12586eaf49a",
            "src/registry/foundation-skills.yaml": "385843496634f9e9ef4426790cacff211858cab4f73c6c15f521fc2732b5b8fd",
            "src/registry/domain-skills.yaml": "2d53ccc4206c94d9850e007d21603f04ba1f06f7721de5da1cd47dcfe6e16129",
            "scripts/build.py": "2543ed2c2cb7498babeae20d1f7bd244f968522f116c90b8b08c4106a25efcf1",
            "scripts/validation_utils.py": "a76092b2d24cdfaec66eb44e1f8d4e48a9f76d9dda8a875a3b5602771649f995",
            "evals/agent-light-trajectories/cases.yaml": "25cc065fde1298111bbc5d3236976f3601b0db30453c805516689f2998c0191b",
            "tests/scripts/test_reference_registry_jit.py": "c4730adbdb7a5bdbae7ab24d979f563a2fab17d5fb634d83326a00d0dd00ad85",
            "tests/scripts/test_eval_rendered_context_budget.py": "9bc52e95f1ad5e6a3d5a8ad164eb789172c6b2b2b374749e42ddc12df9237a5a",
            "scripts/audit-skill-content.py": "19075d5a17baf72de6da658f113e3b029720a927fd8723885b6806d97a74cfab",
            "tests/scripts/test_validate_root_content.py": "432ed062a7f2f71cc0c23ac90c0fc3d06aaa85901c3376965ff6291dd2a306fc",
        }
        for path, expected_sha256 in protected.items():
            self.assertEqual(expected_sha256, hashlib.sha256((ROOT / path).read_bytes()).hexdigest())

        professional = VALIDATION.load_yaml_file(ROOT / "src/registry/professional-skills.yaml")
        foundation = VALIDATION.load_yaml_file(ROOT / "src/registry/foundation-skills.yaml")
        domain = VALIDATION.load_yaml_file(ROOT / "src/registry/domain-skills.yaml")
        selector_authority = VALIDATION.layer3_selector_authority(foundation, professional, domain, context="C1R delivery release witness")
        selector_projection = VALIDATION.layer3_selector_runtime_projection(selector_authority, professional_skill="delivery-release-gate", profile="task-agent", selection_owner="main-control-agent", exact_layer3=None)
        evidence_signals = ["device", "recovery", "changed-surface", "production-apply-or-rollout"]
        receipt = VALIDATION.layer3_selector_runtime_selection_receipt(selector_projection, evidence_signals=evidence_signals)
        self.assertEqual(["iot-embedded-extension", "release-rollback", "version-compatibility"], receipt["selected_layer3"])
        self.assertEqual("0a93ab092e22e6ce4b18a629db71817e23222ed5d89397c5be7434e10a85047a", receipt["receipt_sha256"])
        domain_names = {row["name"] for row in domain["domain_skills"]}
        self.assertEqual({"iot-embedded-extension"}, set(receipt["selected_layer3"]) & domain_names)
        for reduced_signals in (evidence_signals[:1], evidence_signals[1:]):
            reduced = VALIDATION.layer3_selector_runtime_selection_receipt(selector_projection, evidence_signals=reduced_signals)
            self.assertNotEqual(receipt["receipt_sha256"], reduced["receipt_sha256"])

        authority = VALIDATION.reference_context_admissibility_authority(professional, foundation, domain, context="C1R delivery staged witness")
        staged = VALIDATION.reference_context_staged_plan(authority, references=selected_references, path="direct", profile="task-agent", selection_owner="main-control-agent", available_carrier_fields=[], receipt_replayed=True, brief_current=False, review_fresh=True)
        expected = [list(reference) for reference in selected_references]
        self.assertTrue(staged["reachable"])
        self.assertEqual(expected, staged["selected_union"])
        self.assertEqual(expected, staged["loaded_union"])
        self.assertEqual([[reference] for reference in expected], [stage["loaded_references"] for stage in staged["stages"]])
        self.assertEqual(10, len(staged["required_output_receipts"]))
        self.assertTrue(all(stage["carried_predecessors"] == [] for stage in staged["stages"]))
        self.assertEqual([], staged["carried_predecessors"])
        active_stage = staged["stages"][3]
        self.assertEqual(3, active_stage["stage"])
        self.assertEqual([expected[3]], active_stage["loaded_references"])
        self.assertEqual([{"reference": expected[3], "required_outputs": ["checklist-result", "residual-risk"]}], active_stage["required_output_receipts"])

        relevant_ledger = [entry for entry in RELOCATION_LEDGER if entry["owner"] in {"delivery-release-gate", "iot-embedded-extension", "release-rollback", "version-compatibility"}]
        self.assertEqual({"delivery-release-gate", "iot-embedded-extension", "release-rollback", "version-compatibility"}, {entry["owner"] for entry in relevant_ledger})
        self.assertTrue(all(entry["route_effect"] == "unchanged" and entry["co_trigger_effect"] == "unchanged" for entry in relevant_ledger))

        component_tokens = [697, 333, 338, 229, 250, 482, 657]
        component_sha256 = [
            "28dde3cc5659529fa79b251dcf71b305372df5533d2050495a174f8782291f7e",
            "cd91f6ea858e7b988fe1268c0e45d8f3cf38e501ff0a1cbb8d31a6ec0bcb4565",
            "94a3e7d66eebc7a8c5c154df3405449473ea05b75b4d072f6828cbca8d197923",
            "3e2150a21b3997726207b6ac9317c8077856708c87a481ac818898779c78229a",
            "989a93e84c8ba897bdc8ba69113da520c11207996f1d64b7ad59b4810284ae91",
            "771c35d891ee7662d60144c0bab45f6e6956007060d3ab6a97e69aef6051552e",
            "b1dc031dec6d279d689ca18f620a82b8bc28548d12bba49a5233a969837cb1ac",
        ]
        self.assertEqual(7, len(component_sha256))
        self.assertEqual(2_986, sum(component_tokens))
        self.assertEqual(2_985, sum(component_tokens) - 1)
        self.assertEqual(2_992, sum(component_tokens) + 6)
        self.assertLessEqual(sum(component_tokens) + 6, 3_000)
        negative = list(component_tokens)
        negative[5] = 491
        self.assertEqual(3_001, sum(negative) + 6)

    def test_fg_c1s_security_web_frontier_is_lossless_and_bounded(self) -> None:
        source_specs = {
            "src/foundation/capabilities/web-security/SKILL.md": (
                "4298354700632a0c131a219d518d6eafd622cf5423c107352264b8a63fb4c061",
                "4d9a6d9e61de16b63b62b4c5e19ff8857cc96f5661b32f4540aaa7f07960a191",
                521,
                2_676,
                48,
                (
                    "Trace web sources to render, navigation, state-change, fetch, upload, cross-origin, cookie, embedding, or protected-action sinks.",
                    "Own control-placement and bypass proof, not permission or credential policy.",
                    "Map the changed web source through trust transitions.",
                    "Classify its effective web sink.",
                    "Select the owning control or evidence Reference.",
                    "While that decision is active, load only its named Reference.",
                    "Reject generic sanitizer, UI signal, hostname, extension, identity, framework-default, or header claims without final-context and deployed-behavior evidence.",
                    "Escalate unknown reachability, missing request integrity/object authorization, or unbounded server-fetch destinations.",
                    "Escalate ambiguous active content, broadened cross-origin credentials, or unverified deployed controls/bypasses.",
                    "web-security decision with reachable sources and sinks, contextual controls, state-change integrity, fetch and upload boundaries, cross-origin behavior, denial and bypass evidence, and proof limits",
                ),
            ),
            "src/foundation/capabilities/web-security/references/benchmarks-and-patterns.md": (
                "6e10eb10d7318a0b4a78ff8c5fc694dc4592829ca60fe70de4301e4a1391c68d",
                "ba0d3b7172e4fce659dfce92653dfcbd628295d4714ab0b6b81a38e6bd2ab763",
                532,
                2_679,
                31,
                (
                    "| Render | Safe construction, contextual encoding, inert/no interpretation. | Final context/helper, hostile/context-switch path, response transform. |",
                    "| State change | Request authority, trusted origin/binding, owned step-up, no ambient authority. | Credentials/navigation/session/retry/enforcement; denied cross-site. |",
                    "| Server connection | Network policy, intermediary fetch, bounded class, no caller influence. | Accepted/canonical input, bounds, resolution-to-connect, redirects, egress, failure, diagnostics owner. |",
                    "| Upload/publication | Reject/transform/isolate/inspect/private/bounded publish. | Byte/parser bounds, storage/tenant identity, inspection, active content, permission, transition, serving. |",
                    "| Navigation/policy | Same-site, bounded external, cross-origin, framed, no exposure. | Client/destination authority, credentials, effective policy/transform, bypass. |",
                    "| Protected route | Authenticated subject plus permission-owned resource/action. | Trace/provenance, object/tenant scope, wrong subject, denial, audit owner. |",
                    "| Closure | Repair, containment, deployment proof, non-applicability, residual handoff. | Final source, hostile/denied case, sibling scan, relevant artifact, limit, owner. |",
                    "Select from the current browser/server path, boundary, authority, and failure contract.",
                    "Apply framework-, client-, proxy-, and network-specific behavior behind shared labels.",
                    "Route input source/representation/canonical form/constraints/response bounds to `input-validation`.",
                    "Route subject authority/derivation/propagation/handoff to `authentication-authorization`.",
                    "Route credential/session/token lifecycle/replay/recovery/assurance/compromise to `authentication-security`.",
                    "Route subject-resource-action policy to `permission-boundary-modeling`.",
                    "Route cross-graph outcomes/reachability/prioritization/control placement to `threat-modeling`.",
                    "Prove route-to-sink correctness/bypass resistance in `web-security`.",
                    "Re-evaluate framework, middleware, proxy, route, redirect, resolver, cache, storage, or serving changes affecting the sink/boundary.",
                    "Named source, tests, browser artifacts, and deployment configuration prove only inspected routes, clients, intermediaries, environments, and time.",
                    "They exclude undiscovered routes, production resolver/egress state, external consumers, proxy overrides, browser variants, live attackers, and downstream permission policy without independent evidence.",
                ),
            ),
        }
        pending = []
        for path, (pre_sha256, post_sha256, tokens, size, line_feeds, anchors) in source_specs.items():
            source_bytes = (ROOT / path).read_bytes()
            actual_sha256 = hashlib.sha256(source_bytes).hexdigest()
            if actual_sha256 not in {pre_sha256, post_sha256}:
                self.fail(f"unexpected C1S source preimage for {path}: {actual_sha256}")
            with self.subTest(source_hash=path):
                self.assertEqual(post_sha256, actual_sha256)
            if actual_sha256 != post_sha256:
                pending.append(path)
                continue
            source = source_bytes.decode("utf-8")
            self.assertEqual(tokens, VALIDATION.count_o200k_base_tokens(source))
            self.assertEqual(size, len(source_bytes))
            self.assertEqual(line_feeds, source_bytes.count(b"\n"))
            self.assertTrue(source_bytes.endswith(b"\n"))
            for anchor in anchors:
                self.assertEqual(1, source.count(anchor))
                self.assertEqual(0, source.replace(anchor, "", 1).count(anchor))
        if pending:
            return

        web_root_path = ROOT / "src/foundation/capabilities/web-security/SKILL.md"
        _metadata, raw_frontmatter, web_body = VALIDATION.parse_frontmatter(web_root_path)
        h1_titles, web_sections = BUILD._markdown_heading_sections(web_body)
        self.assertEqual(["web-security"], h1_titles)
        self.assertEqual(
            ["Registry Trigger", "Skill Role", "High-Value Rules", "Anti-Patterns", "Stop Conditions", "Output Contract", "Targeted References"],
            re.findall(r"^## (.+)$", web_body, flags=re.MULTILINE),
        )
        self.assertEqual(4, len(re.findall(r"^- ", web_sections["High-Value Rules"][0], flags=re.MULTILINE)))
        self.assertEqual(2, len(re.findall(r"^- ", web_sections["Stop Conditions"][0], flags=re.MULTILINE)))

        def projection(path: str, headings: tuple[str, ...], selector: str | None, include_layer3_delivery: bool = False) -> str:
            _metadata, raw, body = VALIDATION.parse_frontmatter(ROOT / path)
            titles, sections = BUILD._markdown_heading_sections(body)
            self.assertEqual(1, len(titles))
            output = ["---", raw, "---", "", f"# {titles[0]}"]
            for heading in headings:
                values = sections.get(heading, [])
                if not values and heading == "Inputs":
                    continue
                self.assertEqual(1, len(values))
                self.assertTrue(values[0])
                output.extend(["", f"## {heading}", "", values[0]])
            output.extend(BUILD._compact_jit_reference_delivery_lines(selector))
            if include_layer3_delivery:
                output.extend(["", "## Layer 3 Delivery", "", "Foundation and Domain items are top-level Skills; no Layer 3 references are compiled."])
            output.append("")
            return "\n".join(output)

        root_specs = {
            "src/professional-skills/security-privacy-gate/SKILL.md": (BUILD.PROFESSIONAL_BUILT_KERNEL_HEADINGS, "security-privacy-gate", True, 303, "1f5f5d81f6dd59c74a1a43ed9e7710478b16a0657eaa5312fe623ee598fb300e"),
            "src/domain-extensions/cloud-platform-extension/SKILL.md": (BUILD.PROFESSIONAL_BUILT_KERNEL_HEADINGS, None, False, 250, "fcbe9dc653c2d7f98fe01738547701d6ba79fff570c24b176e130d3c17941ad2"),
            "src/foundation/capabilities/threat-modeling/SKILL.md": (BUILD.FOUNDATION_BUILT_KERNEL_HEADINGS, None, False, 311, "559d0467c675e0e77803979cb8f132d547567d236c0dad97efe2a030c6a8225a"),
            "src/foundation/capabilities/web-security/SKILL.md": (BUILD.FOUNDATION_BUILT_KERNEL_HEADINGS, None, False, 234, "ae1207804645b3af4968e354358fcc27b10aa76f9f20fabe31388494d3bf17f1"),
        }
        for path, (headings, selector, layer3_delivery, tokens, sha256) in root_specs.items():
            compact = projection(path, headings, selector, layer3_delivery)
            with self.subTest(root_projection=path):
                self.assertEqual(tokens, VALIDATION.count_o200k_base_tokens(compact))
                self.assertEqual(sha256, hashlib.sha256(compact.encode("utf-8")).hexdigest())

        reference_specs = {
            ("cloud-platform-extension", "references/encryption-kms-and-cost-contracts.md"): (476, "7d5bfd16cca9c4b5a7911c58b14cf15e50e7f200ecedbb87f13a29c7079bfbc6", ("boundary-decision", "failure-decision", "residual-risk")),
            ("cloud-platform-extension", "references/iam-workload-identity-and-network-contracts.md"): (440, "52661d530555b8c0ab6298f9d1288c3877beec6e3878a8a015e891ed76998dc1", ("boundary-decision", "failure-decision", "validation-plan")),
            ("cloud-platform-extension", "references/provider-api-and-managed-service-authority.md"): (430, "4fc9962a94a2fcbdbf89128f7c26f8ea82b00e8532da9d604eccbcc0037381be", ("decision-record", "proof-limit", "validation-plan")),
            ("cloud-platform-extension", "references/region-failure-domain-consistency-and-quota-contracts.md"): (485, "37d6621e04971dad77d5a5820022ace201388b0389bf690d2939356f0dd44eb4", ("decision-record", "proof-limit", "validation-plan")),
            ("cloud-platform-extension", "references/resource-control-and-data-plane-boundaries.md"): (421, "eb9aa5a9b1f760b83825428562293f0afdfa9a4bcdb4af76c2d5081aef3e3fdc", ("boundary-decision", "decision-record", "proof-limit")),
            ("security-privacy-gate", "references/checklist.md"): (136, "059a2463147824418c686f1cd1565ca3cfb85f3fb99eb2dd37f5ff2aa8144514", ("checklist-result", "residual-risk")),
            ("security-privacy-gate", "references/evidence-patterns.md"): (427, "3e368eb8ddcef3e77a22de4d38ff0d2fac022702e9f9cca471811815b5a2fbc8", ("evidence-record", "proof-limit", "residual-risk")),
            ("security-privacy-gate", "references/security-output-and-gates.md"): (625, "05129afaa245591be03b05cd5c2edc5dcfd5b494002d2dd70a9891b2d253f81e", ("gate-decision", "residual-risk")),
            ("threat-modeling", "references/benchmarks-and-patterns.md"): (566, "f1e806daf9f9b3f44364be879504eb93ecb57219259c8fcc61d99d92c22b41e3", ("option-comparison", "selected-approach")),
            ("threat-modeling", "references/checklist.md"): (254, "c6b1fc69a829f0e6c007302aca8af328417db024bd88fac8752a3a703960b077", ("checklist-result", "validation-plan")),
            ("threat-modeling", "references/evidence-patterns.md"): (510, "cbf74fac36410acbeb1407437f48ee3f6464c91b91143fc9ee4c41eacb8e0247", ("evidence-record", "proof-limit", "residual-risk")),
            ("web-security", "references/benchmarks-and-patterns.md"): (532, "ba0d3b7172e4fce659dfce92653dfcbd628295d4714ab0b6b81a38e6bd2ab763", ("option-comparison", "selected-approach")),
            ("web-security", "references/checklist.md"): (391, "c7628358b5fb0826f91276a74eaa81612c99a994e4de46b142b7901b067c5177", ("checklist-result", "residual-risk")),
            ("web-security", "references/evidence-patterns.md"): (564, "b11066a3a14729ed76883e082a7a1fa41252bdec5de244c7d22c2f69092c3fc3", ("evidence-record", "proof-limit", "residual-risk")),
        }
        selected_references = tuple(reference_specs)
        for (owner, relative_path), (tokens, sha256, outputs) in reference_specs.items():
            if owner == "security-privacy-gate":
                source_root = ROOT / "src/professional-skills" / owner
            elif owner == "cloud-platform-extension":
                source_root = ROOT / "src/domain-extensions" / owner
            else:
                source_root = ROOT / "src/foundation/capabilities" / owner
            path = source_root / relative_path
            source = path.read_text(encoding="utf-8")
            with self.subTest(reference=owner + "/" + relative_path):
                self.assertEqual(sha256, hashlib.sha256(source.encode("utf-8")).hexdigest())
                self.assertEqual(tokens, VALIDATION.count_o200k_base_tokens(source))
                self.assertEqual((ALL_ROLES, outputs), _reference_binding(owner, str(path.relative_to(ROOT))))

        professional = VALIDATION.load_yaml_file(ROOT / "src/registry/professional-skills.yaml")
        foundation = VALIDATION.load_yaml_file(ROOT / "src/registry/foundation-skills.yaml")
        domain = VALIDATION.load_yaml_file(ROOT / "src/registry/domain-skills.yaml")
        selector_authority = VALIDATION.layer3_selector_authority(
            foundation, professional, domain, context="C1S security web witness"
        )
        selector_projection = VALIDATION.layer3_selector_runtime_projection(
            selector_authority,
            professional_skill="security-privacy-gate",
            profile="task-agent",
            selection_owner="main-control-agent",
            exact_layer3=None,
        )
        evidence_signals = ["cloud control plane", "account authority", "changed-surface", "ssrf"]
        receipt = VALIDATION.layer3_selector_runtime_selection_receipt(
            selector_projection, evidence_signals=evidence_signals
        )
        self.assertEqual(["cloud-platform-extension", "threat-modeling", "web-security"], receipt["selected_layer3"])
        self.assertEqual("336dfef51f64a686fc616f4fc48cac5451ebd55fe61dee5e402d4e98ca5a90e4", receipt["receipt_sha256"])
        self.assertEqual({"cloud-platform-extension"}, set(receipt["selected_layer3"]) & {row["name"] for row in domain["domain_skills"]})
        for reduced_signals in (evidence_signals[:2], evidence_signals[2:]):
            self.assertNotEqual(receipt["receipt_sha256"], VALIDATION.layer3_selector_runtime_selection_receipt(selector_projection, evidence_signals=reduced_signals)["receipt_sha256"])

        authority = VALIDATION.reference_context_admissibility_authority(
            professional, foundation, domain, context="C1S security web staged witness"
        )
        staged = VALIDATION.reference_context_staged_plan(
            authority,
            references=selected_references,
            path="direct",
            profile="task-agent",
            selection_owner="main-control-agent",
            available_carrier_fields=[],
            receipt_replayed=True,
            brief_current=False,
            review_fresh=True,
        )
        expected = [list(reference) for reference in selected_references]
        self.assertTrue(staged["reachable"])
        self.assertEqual(expected, staged["selected_union"])
        self.assertEqual(expected, staged["loaded_union"])
        self.assertEqual(14, len(staged["stages"]))
        self.assertEqual([[reference] for reference in expected], [stage["loaded_references"] for stage in staged["stages"]])
        self.assertTrue(all(stage["carried_predecessors"] == [] for stage in staged["stages"]))
        self.assertEqual([], staged["carried_predecessors"])
        self.assertEqual(14, len(staged["required_output_receipts"]))
        active_reference = ["web-security", "references/benchmarks-and-patterns.md"]
        active_stage = next(stage for stage in staged["stages"] if stage["loaded_references"] == [active_reference])
        self.assertEqual(11, active_stage["stage"])
        self.assertEqual(
            [{"reference": active_reference, "required_outputs": ["option-comparison", "selected-approach"]}],
            active_stage["required_output_receipts"],
        )

        web_moves = [entry for entry in RELOCATION_LEDGER if entry["owner"] == "web-security"]
        self.assertEqual(7, len(web_moves))
        self.assertEqual(6, sum(entry["destination"] == "src/foundation/capabilities/web-security/references/benchmarks-and-patterns.md" for entry in web_moves))
        self.assertTrue(all(entry["route_effect"] == "unchanged" and entry["co_trigger_effect"] == "unchanged" for entry in web_moves))
        for entry in web_moves:
            destination = (ROOT / entry["destination"]).read_text(encoding="utf-8")
            self.assertEqual(0, destination.count(entry["old_anchor"]))
            self.assertEqual(1, destination.count(entry["new_anchor"]))
            self.assertEqual(0, destination.replace(entry["new_anchor"], "", 1).count(entry["new_anchor"]))

        component_tokens = [697, 303, 250, 311, 234, 532, 657]
        component_sha256 = [
            "28dde3cc5659529fa79b251dcf71b305372df5533d2050495a174f8782291f7e",
            "1f5f5d81f6dd59c74a1a43ed9e7710478b16a0657eaa5312fe623ee598fb300e",
            "fcbe9dc653c2d7f98fe01738547701d6ba79fff570c24b176e130d3c17941ad2",
            "559d0467c675e0e77803979cb8f132d547567d236c0dad97efe2a030c6a8225a",
            "ae1207804645b3af4968e354358fcc27b10aa76f9f20fabe31388494d3bf17f1",
            "ba0d3b7172e4fce659dfce92653dfcbd628295d4714ab0b6b81a38e6bd2ab763",
            "b1dc031dec6d279d689ca18f620a82b8bc28548d12bba49a5233a969837cb1ac",
        ]
        self.assertEqual(7, len(component_sha256))
        self.assertEqual(2_984, sum(component_tokens))
        self.assertEqual(2_983, sum(component_tokens) - 1)
        self.assertEqual(2_990, sum(component_tokens) + 6)
        self.assertLessEqual(sum(component_tokens) + 6, 3_000)
        negative = list(component_tokens)
        negative[5] = 543
        self.assertEqual(3_001, sum(negative) + 6)

        protected = {
            "src/registry/professional-skills.yaml": "32a3b49da13930f3baccf54dbd8de12064b1f07d273b2948dfaeb12586eaf49a",
            "src/registry/foundation-skills.yaml": "385843496634f9e9ef4426790cacff211858cab4f73c6c15f521fc2732b5b8fd",
            "src/registry/domain-skills.yaml": "2d53ccc4206c94d9850e007d21603f04ba1f06f7721de5da1cd47dcfe6e16129",
            "scripts/build.py": "2543ed2c2cb7498babeae20d1f7bd244f968522f116c90b8b08c4106a25efcf1",
            "scripts/validation_utils.py": "a76092b2d24cdfaec66eb44e1f8d4e48a9f76d9dda8a875a3b5602771649f995",
            "tests/scripts/test_eval_rendered_context_budget.py": "9bc52e95f1ad5e6a3d5a8ad164eb789172c6b2b2b374749e42ddc12df9237a5a",
            "scripts/audit-skill-content.py": "19075d5a17baf72de6da658f113e3b029720a927fd8723885b6806d97a74cfab",
            "tests/scripts/test_validate_root_content.py": "432ed062a7f2f71cc0c23ac90c0fc3d06aaa85901c3376965ff6291dd2a306fc",
            "evals/agent-light-trajectories/cases.yaml": "25cc065fde1298111bbc5d3236976f3601b0db30453c805516689f2998c0191b",
        }
        for path, expected_sha256 in protected.items():
            self.assertEqual(expected_sha256, hashlib.sha256((ROOT / path).read_bytes()).hexdigest())


    def test_fg_c1t_installed_client_kotlin_type_frontier_is_lossless_and_bounded(self) -> None:
        source_path = ROOT / "src/foundation/capabilities/kotlin-professional-usage/references/type-interop-and-dsl-contracts.md"
        pre_sha256 = "a0b242ba4aee54d2ad92209496462f275bf339a75e82ed88a5dc1583ac3dea94"
        post_sha256 = "9a78d5b2c4f4428a5583c50a721068cb5d7305d3b5d30ce80c023ba32d815446"
        source_bytes = source_path.read_bytes()
        actual_sha256 = hashlib.sha256(source_bytes).hexdigest()
        self.assertIn(actual_sha256, {pre_sha256, post_sha256})
        self.assertEqual(post_sha256, actual_sha256)
        if actual_sha256 == pre_sha256:
            return
        source = source_bytes.decode("utf-8")
        self.assertEqual(616, VALIDATION.count_o200k_base_tokens(source))
        self.assertEqual(2_848, len(source_bytes))
        self.assertEqual(40, source_bytes.count(b"\n"))
        self.assertTrue(source_bytes.endswith(b"\n"))
        anchors = (
            "Use for these caller-visible decisions.",
            "- **Nullability:** record platform types, flexible generic arguments, collection elements, reflection, serialization, persistence, generated surfaces, and the runtime validation or narrowing location.",
            "- **Sealed hierarchy:** establish the module/package closure, external implementor contract, serialization tags, and how new variants reach compiled consumers.",
            "- **Delegated property:** define the property/delegate owner, `getValue`/`setValue` state semantics, delegate lifecycle/threading, Java/reflection exposure, invalid read/write behavior, and verification output.",
            "| Java | Signature/accessor, exception/default/wildcard/SAM, annotation, caller. |",
            "| Data/value | Identity, equality, order, shallow copy, mutation, inheritance/persistence; boxing, mangling, Java representation, validation. |",
            "| DSL | Receiver, `@DslMarker`, label/escape, mutation, validation, effect. |",
            "- Probe runtime null and emitted ABI through the affected Java/reflection/generated/persisted caller.",
            "- Add an allowed sealed subtype, box a value class through generic/interface/nullable use, and copy a data class with mutable nested state.",
            "- Exercise delegate read/write/teardown/interop and nested same-name DSL receivers; reject partial construction.",
            "Bind compiler, API, backend, Java, and plugin versions.",
            "Documentation does not prove ABI, delegate lifetime, adapters, serializers, persistence, or generated callers.",
            "Kotlin compilation and `val` do not prove Java compatibility or deep immutability.",
            "Record boundary, owner/get-set output, caller/runtime evidence, representation, invalid behavior, compatibility limit, residual risk.",
            "- `!!`, a platform type, or a generated annotation is treated as runtime null proof.",
            "- Data-class `copy`, a value wrapper, sealed `when`, or `remember` is treated as deep immutability, stable ABI, future exhaustiveness, or durable state.",
        )
        for anchor in anchors:
            self.assertEqual(1, source.count(anchor))
            self.assertEqual(0, source.replace(anchor, "", 1).count(anchor))
        source_urls = (
            "https://kotlinlang.org/docs/java-interop.html",
            "https://kotlinlang.org/docs/java-to-kotlin-interop.html",
            "https://kotlinlang.org/docs/null-safety.html",
            "https://kotlinlang.org/docs/sealed-classes.html",
            "https://kotlinlang.org/docs/inline-functions.html",
            "https://kotlinlang.org/docs/inline-classes.html",
            "https://kotlinlang.org/docs/data-classes.html",
            "https://kotlinlang.org/docs/delegated-properties.html",
            "https://kotlinlang.org/docs/type-safe-builders.html",
        )
        for url in source_urls:
            self.assertEqual(1, source.count(url))

        def projection(path: str, headings: tuple[str, ...], selector: str | None, include_layer3_delivery: bool = False) -> str:
            _metadata, raw, body = VALIDATION.parse_frontmatter(ROOT / path)
            titles, sections = BUILD._markdown_heading_sections(body)
            self.assertEqual(1, len(titles))
            output = ["---", raw, "---", "", f"# {titles[0]}"]
            for heading in headings:
                values = sections.get(heading, [])
                if not values and heading == "Inputs":
                    continue
                self.assertEqual(1, len(values))
                self.assertTrue(values[0])
                output.extend(["", f"## {heading}", "", values[0]])
            output.extend(BUILD._compact_jit_reference_delivery_lines(selector))
            if include_layer3_delivery:
                output.extend(["", "## Layer 3 Delivery", "", "Foundation and Domain items are top-level Skills; no Layer 3 references are compiled."])
            output.append("")
            return "\n".join(output)

        root_specs = {
            "src/professional-skills/installed-client-change-builder/SKILL.md": (BUILD.PROFESSIONAL_BUILT_KERNEL_HEADINGS, "installed-client-change-builder", True, 239, "41d925e4295ef95620024fae202294e72f77a322b16aaff351460602dd401565"),
            "src/domain-extensions/cross-platform-client-extension/SKILL.md": (BUILD.PROFESSIONAL_BUILT_KERNEL_HEADINGS, None, False, 265, "e7ae448387f1d7f79e38bdb876d09c80f1b798be00fd2fe4bb6f98c7e9f89b8f"),
            "src/domain-extensions/ios-ipados-platform-extension/SKILL.md": (BUILD.PROFESSIONAL_BUILT_KERNEL_HEADINGS, None, False, 261, "d165e8917475639800aa629514ff1843ab5e3cf7b58a0e7638c06671533b0031"),
            "src/foundation/capabilities/kotlin-professional-usage/SKILL.md": (BUILD.FOUNDATION_BUILT_KERNEL_HEADINGS, None, False, 256, "613a37d611c5d0375b2e8b279b12d181a6dcff09bee7ec1384335ff168a097b3"),
        }
        for path, (headings, selector, layer3_delivery, tokens, sha256) in root_specs.items():
            compact = projection(path, headings, selector, layer3_delivery)
            with self.subTest(root_projection=path):
                self.assertEqual(tokens, VALIDATION.count_o200k_base_tokens(compact))
                self.assertEqual(sha256, hashlib.sha256(compact.encode("utf-8")).hexdigest())

        professional = VALIDATION.load_yaml_file(ROOT / "src/registry/professional-skills.yaml")
        foundation = VALIDATION.load_yaml_file(ROOT / "src/registry/foundation-skills.yaml")
        domain = VALIDATION.load_yaml_file(ROOT / "src/registry/domain-skills.yaml")
        selector_authority = VALIDATION.layer3_selector_authority(
            foundation, professional, domain, context="C1T installed client Kotlin witness"
        )
        selector_projection = VALIDATION.layer3_selector_runtime_projection(
            selector_authority,
            professional_skill="installed-client-change-builder",
            profile="task-agent",
            selection_owner="main-control-agent",
            exact_layer3=None,
        )
        evidence_signals = [
            "shared installed client",
            "concrete platform targets",
            "changed-surface",
            "ios/ipados",
            "application lifecycle",
            "kotlin coroutine flow stateflow null java interop sealed reified value data delegated dsl or compose semantics",
        ]
        receipt = VALIDATION.layer3_selector_runtime_selection_receipt(
            selector_projection, evidence_signals=evidence_signals
        )
        self.assertEqual(
            ["cross-platform-client-extension", "ios-ipados-platform-extension", "kotlin-professional-usage"],
            receipt["selected_layer3"],
        )
        self.assertEqual("83152d299a1aa000b4d2875a107a3b347a3b84e0aac1538eeec0f21301b6a182", receipt["receipt_sha256"])
        self.assertEqual(
            {"cross-platform-client-extension", "ios-ipados-platform-extension"},
            set(receipt["selected_layer3"]) & {row["name"] for row in domain["domain_skills"]},
        )
        for reduced_signals in (evidence_signals[:3], evidence_signals[3:]):
            self.assertNotEqual(
                receipt["receipt_sha256"],
                VALIDATION.layer3_selector_runtime_selection_receipt(
                    selector_projection, evidence_signals=reduced_signals
                )["receipt_sha256"],
            )

        selected_references = (
            ("cross-platform-client-extension", "references/bridge-plugin-and-ffi-contracts.md"),
            ("cross-platform-client-extension", "references/framework-target-evidence-contracts.md"),
            ("cross-platform-client-extension", "references/parity-and-regression-contracts.md"),
            ("cross-platform-client-extension", "references/shared-and-target-ownership-contracts.md"),
            ("installed-client-change-builder", "references/dotnet-maui-framework-contracts.md"),
            ("installed-client-change-builder", "references/electron-framework-contracts.md"),
            ("installed-client-change-builder", "references/flutter-framework-contracts.md"),
            ("installed-client-change-builder", "references/kotlin-multiplatform-framework-contracts.md"),
            ("installed-client-change-builder", "references/native-platform-source-contracts.md"),
            ("installed-client-change-builder", "references/qt-framework-contracts.md"),
            ("installed-client-change-builder", "references/react-native-framework-contracts.md"),
            ("installed-client-change-builder", "references/tauri-framework-contracts.md"),
            ("ios-ipados-platform-extension", "references/compatibility-signing-and-distribution-contracts-implementation-and-review-evidence.md"),
            ("ios-ipados-platform-extension", "references/data-keychain-and-extension-contracts-implementation-and-review-evidence.md"),
            ("ios-ipados-platform-extension", "references/entry-capabilities-and-entitlements-contracts-implementation-and-review-evidence.md"),
            ("ios-ipados-platform-extension", "references/lifecycle-scenes-and-background-contracts-implementation-and-review-evidence.md"),
            ("ios-ipados-platform-extension", "references/special-platform-boundaries-implementation-and-review-evidence.md"),
            ("ios-ipados-platform-extension", "references/ui-form-factor-and-accessibility-contracts-implementation-and-review-evidence.md"),
            ("kotlin-professional-usage", "references/coroutine-flow-state-contracts.md"),
            ("kotlin-professional-usage", "references/type-interop-and-dsl-contracts.md"),
        )
        authority = VALIDATION.reference_context_admissibility_authority(
            professional, foundation, domain, context="C1T installed client Kotlin staged witness"
        )
        staged = VALIDATION.reference_context_staged_plan(
            authority,
            references=selected_references,
            path="direct",
            profile="task-agent",
            selection_owner="main-control-agent",
            available_carrier_fields=[],
            receipt_replayed=True,
            brief_current=False,
            review_fresh=True,
        )
        expected = [list(reference) for reference in selected_references]
        self.assertTrue(staged["reachable"])
        self.assertEqual(expected, staged["selected_union"])
        self.assertEqual(expected, staged["loaded_union"])
        self.assertEqual(20, len(staged["stages"]))
        self.assertEqual([[reference] for reference in expected], [stage["loaded_references"] for stage in staged["stages"]])
        self.assertTrue(all(stage["carried_predecessors"] == [] for stage in staged["stages"]))
        self.assertEqual([], staged["carried_predecessors"])
        self.assertEqual(20, len(staged["required_output_receipts"]))
        active_reference = ["kotlin-professional-usage", "references/type-interop-and-dsl-contracts.md"]
        active_stage = next(stage for stage in staged["stages"] if stage["loaded_references"] == [active_reference])
        self.assertEqual(19, active_stage["stage"])
        self.assertEqual(
            [{"reference": active_reference, "required_outputs": ["decision-record", "residual-risk"]}],
            active_stage["required_output_receipts"],
        )
        self.assertEqual(
            (TASK_FIRST_ROLES, ("decision-record", "residual-risk")),
            _reference_binding(
                "kotlin-professional-usage",
                "src/foundation/capabilities/kotlin-professional-usage/references/type-interop-and-dsl-contracts.md",
            ),
        )

        component_tokens = [697, 239, 265, 261, 256, 616, 657]
        component_sha256 = [
            "28dde3cc5659529fa79b251dcf71b305372df5533d2050495a174f8782291f7e",
            "41d925e4295ef95620024fae202294e72f77a322b16aaff351460602dd401565",
            "e7ae448387f1d7f79e38bdb876d09c80f1b798be00fd2fe4bb6f98c7e9f89b8f",
            "d165e8917475639800aa629514ff1843ab5e3cf7b58a0e7638c06671533b0031",
            "613a37d611c5d0375b2e8b279b12d181a6dcff09bee7ec1384335ff168a097b3",
            post_sha256,
            "b1dc031dec6d279d689ca18f620a82b8bc28548d12bba49a5233a969837cb1ac",
        ]
        self.assertEqual(7, len(component_sha256))
        self.assertEqual(2_991, sum(component_tokens))
        self.assertEqual(2_990, sum(component_tokens) - 1)
        self.assertEqual(2_997, sum(component_tokens) + 6)
        self.assertLessEqual(sum(component_tokens) + 6, 3_000)
        negative = list(component_tokens)
        negative[5] = 620
        self.assertEqual(3_001, sum(negative) + 6)

        protected = {
            "src/professional-skills/installed-client-change-builder/SKILL.md": "40b877e360ef3e6dfb793d13a3a5def396b53c77b177366946a8c7391bf7659c",
            "src/domain-extensions/cross-platform-client-extension/SKILL.md": "9a7c8b21bf06711c2b4a54a1e6b977ef31492cbd68ea709c24042077c4ebb449",
            "src/domain-extensions/ios-ipados-platform-extension/SKILL.md": "7d252fa8cc54ff7aa79c03223019f6531df2946625ebca4814b7511a2eefb7c1",
            "src/foundation/capabilities/kotlin-professional-usage/SKILL.md": "08ec8cf8083d2b0771712dc4b1496266756bde6b740a3565bbed1b9e2c26003f",
            "src/registry/professional-skills.yaml": "32a3b49da13930f3baccf54dbd8de12064b1f07d273b2948dfaeb12586eaf49a",
            "src/registry/foundation-skills.yaml": "385843496634f9e9ef4426790cacff211858cab4f73c6c15f521fc2732b5b8fd",
            "src/registry/domain-skills.yaml": "2d53ccc4206c94d9850e007d21603f04ba1f06f7721de5da1cd47dcfe6e16129",
            "scripts/build.py": "2543ed2c2cb7498babeae20d1f7bd244f968522f116c90b8b08c4106a25efcf1",
            "scripts/validation_utils.py": "a76092b2d24cdfaec66eb44e1f8d4e48a9f76d9dda8a875a3b5602771649f995",
            "tests/scripts/test_eval_rendered_context_budget.py": "9bc52e95f1ad5e6a3d5a8ad164eb789172c6b2b2b374749e42ddc12df9237a5a",
            "tests/scripts/test_reference_registry_jit.py": "c4730adbdb7a5bdbae7ab24d979f563a2fab17d5fb634d83326a00d0dd00ad85",
            "scripts/audit-skill-content.py": "19075d5a17baf72de6da658f113e3b029720a927fd8723885b6806d97a74cfab",
            "tests/scripts/test_validate_root_content.py": "432ed062a7f2f71cc0c23ac90c0fc3d06aaa85901c3376965ff6291dd2a306fc",
            "evals/agent-light-trajectories/cases.yaml": "25cc065fde1298111bbc5d3236976f3601b0db30453c805516689f2998c0191b",
        }
        for path, expected_sha256 in protected.items():
            self.assertEqual(expected_sha256, hashlib.sha256((ROOT / path).read_bytes()).hexdigest())


if __name__ == "__main__":
    unittest.main()
