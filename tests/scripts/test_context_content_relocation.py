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

TEST_BUILD_IDENTITY = "AAECAwQFBgcICQoLDA0ODw"

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
    "skill-authoring-expert/references/routing-maintenance-checklist.md",
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

- Preserve the accepted scope and target behavior through the affected platform and framework boundaries.
- Inspect owner, consumers, tests, and target/package facts before the smallest complete change.
- Record target checks, unavailable evidence, proof limits, and residual risk.""",
    "repository-tooling-change-builder": (
        "Inspect owner, consumer, tests, adjacent utilities, versions, reuse, and "
        "invalid, interrupted, and forbidden outcomes before the smallest complete "
        "change."
    ),
}

G2_BASE_B1_FINGERPRINT_NEW_ANCHORS = {
    "72bd65befa341a90947eae3fa21ad1180c91adf1b702fdc77bb85ce94838593e": """## Professional Decision Rules

- Judge every changed path in the actual latest diff within the fixed boundary.
- Apply the assigned review-risk boundary, severity, evidence, repair, and re-review rules without mutation, scope expansion, or inferred approval.

## High-Value Gotchas

- A summary or self-review is not an independent review of the actual diff.

## Execution Checklist

1. Inspect the actual diff, affected contracts, tests, and fixed review-risk selection.
2. Return reachable findings or an explicit no-finding result with proof limits.""",
    "22ba77cd90166a20d0e0bdb6bcf8812e9eef496e90290c741aea2fd033fc5a66": """## Professional Decision Rules

- Own proof strategy and acceptance-to-signal mapping before command selection.
- Select repository-defined commands and coverage only after strategy selection.
- Treat any material source, test, fixture, schema, or configuration edit as invalidating earlier validation evidence; refresh affected checks after the latest edit.
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
    "c67379d6adc0e93256ba9e75b884bd39b9b4128b26373aac71eef5cbf93ce342": "| Protocol/generic | Associated type, `Self`, specialization, storage, heterogeneous collection, compatibility. Separately store the protocol existential and cross an associated-type boundary; record erased and static relationships independently of lifetime probes. |",
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

## Behavioral And Runtime Assurance

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
        "6ac239405e3076bb3a035b41247931a6878f9c86048c8c3de477ae27fc1a08a1",
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
    ("ai-code-review-refactor", "src/professional-skills/ai-code-review-refactor/SKILL.md", "2df1ba4fb910c602d5915900da27617ecb30f5661e92f25ca40af8d05ddc74ee", "e8e9afe91b657c1d158aa4ba0b4ad9bbadb22ef66bfd8236d0d81f3914f2c8b0", ("independently reviewing", "does not change its assigned scope", "reviewed/unreviewed scope")),
    ("architecture-impact-reviewer", "src/professional-skills/architecture-impact-reviewer/SKILL.md", "422a9f496f9894e430b3db99f13f0b61ef5a8c3cf9213f399e8504b187b1ae99", "fa3fb22c7898106d1defeb7afae6743b3d52bcad8ce7a2710a1f90fccab417cc", ("select a source-backed placement", "Stop structural decisions", "architecture verdict, boundary findings")),
    ("change-documentation-gate", "src/professional-skills/change-documentation-gate/SKILL.md", "c1fadd53b06088dbb0e21ec1da38a5e2ab2f9989a8da3fb32c0033061a3563b4", "472692fdf6ab61063b6e46f27195cd3ee730fc7428f0ebb7c95605a98e09ace1", ("source-owned documentation accuracy", "Stop release", "documentation changes")),
    ("data-api-contract-changer", "src/professional-skills/data-api-contract-changer/SKILL.md", "fae6390621baa0c3081f9d63f908a8b285326ba4944161fd166be6313f1391ba", "c0a371b449b95793909b7ae1349c0084833385038909926356bc7c96dd5f73ed", ("Own evidenced data", "Stop on unresolved compatibility", "producer and consumer changes")),
    ("data-middleware-change-builder", "src/professional-skills/data-middleware-change-builder/SKILL.md", "605b1faa0069e848f428540746f13aac43012451c2d0e021fdc270a6a9932769", "51af820aededb532f57198975c6290b76e6c65b20e9c0ae2817171a9980c5db1", ("Map ownership, failure, recovery, and proof.", "Load one Reference for its open output.", "replay and reconciliation evidence")),
    ("delivery-release-gate", "src/professional-skills/delivery-release-gate/SKILL.md", "02e96a5daea2d9a390314eae547f86e61ed5528fec3eb3c043c6019e75112e2b", "aaf5c2ea8078a3c794725303f2ce7c3372dd96569a4a0d5dc88bc82024fa1fda", ("select rollout", "Block stale artifact/environment, authority, containment, compatibility/migration, infrastructure-state, or recovery evidence.", "go/no-go verdict")),
    ("frontend-change-builder", "src/professional-skills/frontend-change-builder/SKILL.md", "e69b53e752c8faba5e5e47e5e5f2200767abcf0b8eb6e369a9e71f1035276b6a", "6c45536c129fae6306d6bba7ec2c90322bff073d34b9c80c16d75e9cc15f7f42", ("frontend interaction states", "Stop implementation", "residual UX risk")),
    ("high-risk-design-review", "src/professional-skills/high-risk-design-review/SKILL.md", "89755cd877dcf8b55bee60a3da9d450e13cc7cf8c5056222ef773c8e213845b2", "bd0edebe74c3e9600b17623c203b482af80241a39c33c4345b37e0b25b911891", ("high-risk Engineering Brief", "Stop when source evidence", "First Executable Slice assessment")),
    ("installed-client-change-builder", "src/professional-skills/installed-client-change-builder/SKILL.md", "c2ae0c2737397ada23ff0460603bdb78782e12fc8c20dad0841343790ac93b09", "e13f562e7e55fe07421c44cdda3d85d037588516427784c01b465f6d2173afcd", ("Preserve the accepted scope and target behavior through the affected platform and framework boundaries.", "Stop on unresolved target, owner, client contract, artifact, or environment.", "Changed placement, framework/version, native owner/behavior")),
    ("integration-change-builder", "src/professional-skills/integration-change-builder/SKILL.md", "d7b87f093953c972fbf68cf0141678c0daaea60396d60ba247c30ea844e66766", "5a86210d6eaffbe167f445cb3a0a43de5802226e2cbb89f0d5992f53f783d1d5", ("external integration change", "Block unknown provider/environment/credential/reconciliation authority", "unresolved provider risk")),
    ("platform-infrastructure-change-builder", "src/professional-skills/platform-infrastructure-change-builder/SKILL.md", "a679dc02672433337f8a7788454ed5b704744a3debcbcda97adf745cd00740ed", "2543b9cc91b1efa0696905015b5b6a6d11126798e14c386ad95591b12c1ab1da", ("Begin by inspecting target/state/recovery.", "Stop while authority, state/writer/recovery, or effects remain unresolved.", "owner/source, target/version, proposal/effects/recovery, proof limits, release boundary")),
    ("quality-test-gate", "src/professional-skills/quality-test-gate/SKILL.md", "a306349facf66a2c973f5ac3dd98ddfdb9def99de6d454cf27eccdee2c20a33c", "1e694bd93dddec4dd1f6a57ee5400257bd6fe8b82da76485b5898ebf627018cb", ("Map acceptance and failure paths to proving signals.", "**Analysis mode (`analysis-agent`):** Select the proof strategy.", "**Task mode (`task-agent`):** Implement the smallest proving test.", "**Review mode (`review-agent`):** Judge coverage and freshness.", "Stop before production mutation or authority overrun.", "coverage verdict")),
    ("reliability-observability-gate", "src/professional-skills/reliability-observability-gate/SKILL.md", "07ac48ea867816d74e165acfef1ba27018056b724c8fddc940a29b128eea80a9", "8215ee6931408d9742fbf303e1dc04f5cb60763fd832fa8edb015c182f618fb8", ("Bind each objective to consequence, indicator, owner, and action.", "Stop when required reliability closure evidence is incomplete.", "reliability verdict")),
    ("repository-tooling-change-builder", "src/professional-skills/repository-tooling-change-builder/SKILL.md", "edb3823166821757f65b4034a6c6989e4465bdcac4f64f098abd2df5383b6d4f", "b5b0a2a80893614c852ac0cfeee125f24a450f70d3a99cdb9c7c5722f9f2be88", ("Support `task-agent` in changing bounded repository tooling", "Stop on unresolved authority, bootstrap, compatibility, oracle, recovery, or validation.", "cleanup/rollback, proof limits")),
    ("security-privacy-gate", "src/professional-skills/security-privacy-gate/SKILL.md", "69f357e4e7e8e4949dd83a34c1f853e9636b949b5c355fd4bd48c9f069bfd3c2", "f11d7bdde385a27584a4b22e07cd389adc4c59d8933597433238c4ecc5ba7ae5", ("Trace paths.", "Stop on incomplete security closure evidence.", "residual exposure")),
)

G2_BASE_SUCCESSOR_CONTENT_HASHES = {
    path: (old_sha256, new_sha256)
    for _owner, path, old_sha256, new_sha256, _facets in G2_BASE_B1_COMPACTIONS
} | {
    "src/professional-skills/platform-infrastructure-change-builder/references/iac-source-contracts.md": (
        "66e25bbe199f8e7ca2062fe4aa525d574f5eacb40a829e20c91e05b56add90dd",
        "a0265060cbbe58e1ac9771511848498335614965a9110aa2af55298773168570",
    ),
    "src/professional-skills/security-privacy-gate/references/security-output-and-gates.md": (
        "067ac9a3ae149ca3fc2572b1473ebbf5678e5eb3fc634267081a54c70968850a",
        "52f52f7ef03b8143d3f35d08c915ac465d373969b3a7528d2495e349e5c27362",
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
    "src/foundation/capabilities/data-migration-design/SKILL.md": "1c2d3921cfe7f848e03f32fb0031f49b0d5ff55d8e0f65a4bee4c6549cdc1649",
    "src/foundation/capabilities/data-migration-design/references/benchmarks-and-patterns.md": "2b46b6b6480cc0afb931df255730a143988a76d944ab9244a26ff02e0d633005",
    "src/foundation/capabilities/release-rollback/SKILL.md": "05bc0fa788fd635c9ce8948f64c7eb25846a083c1b6d33876ba95f4464ac0830",
    "src/foundation/capabilities/permission-boundary-modeling/SKILL.md": "72ae5933a81a933be7861e8be62e2c033043bcc13e0043db1ab2caeafcf2cf32",
}

C1D_UNCHANGED_REFERENCE_HASHES = {
    "src/professional-skills/data-middleware-change-builder/references/checklist.md": "7913ab5061bcc773b799077d47a02e5f0fee9e66dbe386c4c1bdb5c5d0b9473f",
    "src/professional-skills/data-middleware-change-builder/references/evidence-patterns.md": "c9f9f5090e759139a549b8f2d21bb47c18740d55dbea095686ea6530966b0569",
    "src/professional-skills/data-middleware-change-builder/references/recovery-patterns.md": "6c4f3280cd3ebb9d09d2300d7764472bd9d6089b6e0f2c6cc5b2b479225c2937",
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
    "src/professional-skills/installed-client-change-builder/SKILL.md": "e13f562e7e55fe07421c44cdda3d85d037588516427784c01b465f6d2173afcd",
    "src/foundation/capabilities/client-lifecycle-state-restoration/SKILL.md": "fed428bb4a00aef941f2387398915c1ed4bf719eb4fa1c3cc5620ec5e9f8caf5",
    "src/foundation/capabilities/offline-sync-conflict-resolution/SKILL.md": "9503b7167d0ecbe22c11443217eb1c00340840e477e2ad3f99dcf8bad0ea53d6",
    "src/foundation/capabilities/state-management-design/SKILL.md": "01b485ff00c43de9cae0095f723aa531d82edaece53f7de4c3f7bc7ff75ac305",
    "src/foundation/capabilities/offline-sync-conflict-resolution/references/sync-reconciliation-contracts.md": "12fb8e46272ee7194b1526e97f967589156b15c8b38aae60ccc13d8691b63992",
}

POST_B_TASK_BUILT_TOKENS = {
    "src/professional-skills/installed-client-change-builder/SKILL.md": 228,
    "src/foundation/capabilities/client-lifecycle-state-restoration/SKILL.md": 156,
    "src/foundation/capabilities/offline-sync-conflict-resolution/SKILL.md": 180,
    "src/foundation/capabilities/state-management-design/SKILL.md": 160,
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
    "src/professional-skills/ai-code-review-refactor/references/review-output-and-gates.md": "71d8476168272f9773aadc6137597182801ad7deac6c5f768d827f23f533e651",
}

POST_B_REVIEW_BUILT_TOKENS = {
    "src/domain-extensions/cross-platform-client-extension/SKILL.md": 238,
    "src/professional-skills/ai-code-review-refactor/references/review-output-and-gates.md": 534,
}

POST_B_REVIEW_PROTECTED_HASHES = {
    "src/professional-skills/ai-code-review-refactor/SKILL.md": "e8e9afe91b657c1d158aa4ba0b4ad9bbadb22ef66bfd8236d0d81f3914f2c8b0",
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
    "src/professional-skills/repository-tooling-change-builder/SKILL.md": "b5b0a2a80893614c852ac0cfeee125f24a450f70d3a99cdb9c7c5722f9f2be88",
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
    "src/professional-skills/repository-tooling-change-builder/SKILL.md": ("repository-tooling-change-builder", 355, "77a31ec082a34f84a8f76cb6206f8f85bcac8814d78812dcc1d83c7e185c7b9a"),
    "src/foundation/capabilities/design-pattern-selection/SKILL.md": (None, 195, "3130d22eb8c266fecd01674d0eb4157a394fa44f6daa847eb247a642231402e4"),
    "src/foundation/capabilities/build-tool-professional-usage/SKILL.md": (None, 242, "5e9b7d9061c8a254e2af385f5a68a765df7561e2877acb0717195631a3e8b90c"),
    "src/foundation/capabilities/targeted-validation-selection/SKILL.md": (None, 196, "9a39ae25d5c91b2107be292255491ef256bb590180531377c563dbfde2f29ba4"),
    "src/professional-skills/reliability-observability-gate/SKILL.md": ("reliability-observability-gate", 342, "2636cdd748070c03efd4e8d3e05a65ff083148dbda79626dfea890537171a226"),
    "src/foundation/capabilities/degradation-circuit-breaking/SKILL.md": (None, 182, "9cb58c7134795ab8fa374bc6c99ed56a90a69678e9b4fe4ba3689f1696cc4046"),
    "src/foundation/capabilities/observability/SKILL.md": (None, 153, "7f51058736e2e7138cac6032fb7a7c67e0c75ae7002ed9016e306330e77573ab"),
    "src/foundation/capabilities/backup-recovery/SKILL.md": (None, 197, "1a02c085a6e5f5c64c637e78c6d9fda317b2c8c69fa4727580f3ef68b2f1e512"),
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
    "src/foundation/capabilities/version-compatibility/SKILL.md": "8579ded9475e7b7faf3a740d4526e770be0270113be18090cc9496f3d5190f9f",
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
    "src/foundation/capabilities/release-rollback/SKILL.md": "05bc0fa788fd635c9ce8948f64c7eb25846a083c1b6d33876ba95f4464ac0830",
    "src/foundation/capabilities/release-rollback/references/benchmarks-and-patterns.md": "52bbecd74a4ef1a0dc599855dbbd38d4ba08563e2a5fd60e3a27d4bd10dc74c6",
    "src/foundation/capabilities/release-rollback/references/checklist.md": "e8a45f93dcb38522492d252a295e5a6dcd61f9899bada1f5001aededf85c4096",
    "src/foundation/capabilities/release-rollback/references/evidence-patterns.md": "c0081ac454f9f9fa8a7ebd30b30a41cffdf41db26d3140f9e694672c3c109e58",
    "src/foundation/capabilities/configuration-runtime-policy/references/checklist.md": "55406df248bce907803dffd55d3473109d149526cea056a4d5f7c9113954275d",
    "src/registry/professional-skills.yaml": "509afa24771fbb4b06da6461bdb36091126dd4ebb8afc01d37c51b6c8570b657",
    "src/registry/foundation-skills.yaml": "872172f6afe2b40670ac3a15a707c54ec2e953d0be595212fe61057889c1106e",
}

C1G_BUILT_PROJECTION_SPECS = {
    "src/professional-skills/delivery-release-gate/SKILL.md": (
        "delivery-release-gate",
        314,
        "f4fa8aa340ba020032340b54d27d18218c793f63750e34c109a4f84887d4dc1a",
    ),
    "src/foundation/capabilities/release-rollback/SKILL.md": (
        None,
        202,
        "835e5e1e0293876254330238e293a587e12e0eb1df04785e40cc8e4fb0fbd1f1",
    ),
    "src/foundation/capabilities/version-compatibility/SKILL.md": (
        None,
        223,
        "4a69ac9bc815c56bbc4f1de4633bea953f8f1fabd51609f9a2d4f3ec41b849f8",
    ),
    "src/foundation/capabilities/configuration-runtime-policy/SKILL.md": (
        None,
        156,
        "b091ad3b6d0b1316e5602af5e50852924897ef2d83ca01ffdf9431e78918d4f6",
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
        "Select a bridge from each failing producer-consumer or data direction using current evidence.",
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
    "src/professional-skills/data-middleware-change-builder/references/recovery-patterns.md": "6c4f3280cd3ebb9d09d2300d7764472bd9d6089b6e0f2c6cc5b2b479225c2937",
    "src/foundation/capabilities/concurrency-control/references/checklist.md": "012f1c6db93c813abe0dd0eb710132d810d96dcb08fb21dd654e817a8456715d",
    "src/foundation/capabilities/concurrency-control/references/evidence-patterns.md": "ad0dadf8d15be705a17f62a2844b5295cb0047efa4b87e7851e2b785978765c6",
    "src/foundation/capabilities/transaction-consistency/SKILL.md": "076dff13a9468d13713ec106f5a96586f44635855f9600998209d197a8fb5308",
    "src/foundation/capabilities/transaction-consistency/references/checklist.md": "e588a5f3bd0ee1709ae90944bcdee804c9c243ee61f3c5b96ce1b28154802e9a",
    "src/foundation/capabilities/distributed-workflow-consistency/references/identity-state-and-unknown-outcomes.md": "7a0e547eee5e8b179d2d173058dc46bea0be9191858b6b810e475bbc3d7322d6",
    "src/foundation/capabilities/distributed-workflow-consistency/references/compensation-convergence-and-reconciliation.md": "4b8f50abb517dad40a6092b351e245b0db9ae9f0511189c8c7a625a4c1dcd104",
    "src/registry/professional-skills.yaml": "509afa24771fbb4b06da6461bdb36091126dd4ebb8afc01d37c51b6c8570b657",
    "src/registry/foundation-skills.yaml": "872172f6afe2b40670ac3a15a707c54ec2e953d0be595212fe61057889c1106e",
    "src/registry/domain-skills.yaml": "2d53ccc4206c94d9850e007d21603f04ba1f06f7721de5da1cd47dcfe6e16129",
"scripts/build.py": "7e8f11e45b76b5c32bf4faf20cb34c1c286d9401e9172d94c8309b42b2b559a0",
"scripts/validation_utils.py": "eea023bd38bab4ecd3358c6244956b961f954f50e708b5da6399c0c91410f262",
            "dist/universal/skills/recommended/data-middleware-change-builder/SKILL.md": "3bcc3a9ae53245af5d9580ae9aad887e2dbfef7402454a5c4295dce83e809cec",
}

C1J_BUILT_PROJECTION_SPECS = {
    "src/foundation/capabilities/concurrency-control/SKILL.md": (187, "da86b37fe1bbb867cb3fdb490d2033ae74447ce79b45022368910c93f4455b81"),
    "src/foundation/capabilities/transaction-consistency/SKILL.md": (256, "643b2bf8abc8c6e0722f2cf1ef0cc22186363568672c5df2177cbe4ce2b13f22"),
    "src/foundation/capabilities/distributed-workflow-consistency/SKILL.md": (219, "ece4b6e4da213da984ab4356bb3e868333af33bf3f39ac92a040e25128f4547a"),
}

C1J_REFERENCE_TOKENS = {
    ("data-middleware-change-builder", "references/checklist.md"): 359,
    ("data-middleware-change-builder", "references/evidence-patterns.md"): 374,
    ("data-middleware-change-builder", "references/recovery-patterns.md"): 284,
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
    "src/professional-skills/quality-test-gate/references/test-output-and-gates.md": "0e95e23a81c9f9767bdb8e3e66bdf509ebaa798bf086331ecc4b74836f4d0ac4",
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
    "src/professional-skills/quality-test-gate/references/test-output-and-gates.md": 576,
    "src/foundation/capabilities/test-data-management/SKILL.md": 508,
    "src/foundation/capabilities/test-data-management/references/benchmarks-and-patterns.md": 539,
    "src/foundation/capabilities/test-data-management/references/evidence-patterns.md": 476,
    "src/foundation/capabilities/test-strategy/SKILL.md": 494,
    "src/foundation/capabilities/test-strategy/references/benchmarks-and-patterns.md": 529,
    "src/foundation/capabilities/test-strategy/references/evidence-patterns.md": 537,
}

C1I_PROTECTED_HASHES = {
    "src/professional-skills/quality-test-gate/references/checklist.md": "f915d8148ee0c6e957d3254ce0dd8f121445f1a77a6ac815ea218ac70612bbb0",
    "src/professional-skills/quality-test-gate/references/test-structure-boundaries.md": "86038eeaa916ead150b505246f0308619f21a85e191cf1b772dcb2859a567d95",
    "src/foundation/capabilities/targeted-validation-selection/SKILL.md": "db53a393fa8ca8fa452bc942a594fa242bfbcd457834a9c9f0f87267d0ac490b",
    "src/foundation/capabilities/targeted-validation-selection/references/repository-command-entry-evidence.md": "86d1260cacf6bfa207a326e118239cf1f78363faf06f7c8e48a7631ca0d964e1",
    "src/foundation/capabilities/test-data-management/references/checklist.md": "e23b833747c26a46ae1935a6ec48a6ff78efc5d7e28eb7315c4f7e73e1b76771",
    "src/foundation/capabilities/test-strategy/references/checklist.md": "04883de9a1f8b1c3509a67a32c3720dcc88fafe10b525f74d0a03c96e07cf6f9",
    "src/professional-skills/ai-code-review-refactor/SKILL.md": "e8e9afe91b657c1d158aa4ba0b4ad9bbadb22ef66bfd8236d0d81f3914f2c8b0",
    "src/foundation/capabilities/refactoring/references/split-merge-cleanup-patterns.md": "96b49d2084c6c8834a044ce4700ea6135db4fede99f70a9a6a559c8dba10b2db",
    "src/registry/professional-skills.yaml": "509afa24771fbb4b06da6461bdb36091126dd4ebb8afc01d37c51b6c8570b657",
    "src/registry/foundation-skills.yaml": "872172f6afe2b40670ac3a15a707c54ec2e953d0be595212fe61057889c1106e",
"scripts/build.py": "7e8f11e45b76b5c32bf4faf20cb34c1c286d9401e9172d94c8309b42b2b559a0",
"tests/scripts/test_build_safety.py": "d9ce3b9c01bd0e92f048356ac5e29322bea80512beb4a778c201ee0cdc9152be",
"tests/test_hookless_build_install.py": "bff3019dac8457fa7311a4f8d14963451bb5c30e7092280d814802ddf4743329",
}

C1I_BUILT_PROJECTION_SPECS = {
    "src/professional-skills/quality-test-gate/SKILL.md": (
        "quality-test-gate",
        313,
        "f82a356d2a5fb0194970952ba99c0cf6299a81986198932a546b719efc5f30c4",
    ),
    "src/foundation/capabilities/test-data-management/SKILL.md": (
        None,
        230,
        "3c16dbc47cff347dacbeac21f09f76726a372d1e7831dc9300c6e7519affc6cd",
    ),
    "src/foundation/capabilities/test-strategy/SKILL.md": (
        None,
        205,
        "48919bf53781aedbc92f440355c9481cb8a9046e31090a8bb7fca358f641f79e",
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
        "Refresh affected evidence after the latest material source, test, fixture, schema, or configuration edit; run only authorized commands.",
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
        "removed": ("references/architecture-output-and-gates.md",),
        "references": {
            "references/placement-and-ownership.md": ("targeted", ("analysis-agent", "review-agent"), ("boundary-decision", "selected-approach", "residual-risk"), "route-or-material-unknown", ("acceptance", "scope", "material-risk-floor")),
            "references/consumer-and-data-impact.md": ("targeted", ("analysis-agent", "review-agent"), ("boundary-decision", "validation-plan", "residual-risk"), "route-or-material-unknown", ("acceptance", "scope", "material-risk-floor")),
            "references/dependency-topology-and-enforcement.md": ("targeted", ("analysis-agent", "review-agent"), ("boundary-decision", "gate-decision", "validation-plan", "residual-risk"), "route-or-material-unknown", ("acceptance", "scope", "material-risk-floor")),
            "references/reversibility-evolution-and-proof-limits.md": ("targeted", ("analysis-agent", "review-agent"), ("decision-record", "validation-plan", "proof-limit", "residual-risk"), "route-or-material-unknown", ("acceptance", "scope", "material-risk-floor")),
            "references/checklist.md": ("decision-checklist", ("analysis-agent", "review-agent"), ("checklist-result", "residual-risk"), "route-or-material-unknown", ("acceptance", "scope", "material-risk-floor")),
            "references/solution-optimality.md": ("targeted", ("analysis-agent", "review-agent"), ("selected-approach", "residual-risk"), "route-or-material-unknown", ("acceptance", "scope", "material-risk-floor")),
        },
    },
    "module-boundary-design": {
        "root": "src/foundation/capabilities/module-boundary-design/SKILL.md",
        "registry": "foundation",
        "removed": ("references/module-decomposition.md",),
        "references": {
            "references/boundary-kind-and-authority.md": ("targeted", ("analysis-agent", "review-agent"), ("boundary-decision", "decision-record", "residual-risk"), "route-or-material-unknown", ("acceptance", "scope", "material-risk-floor")),
            "references/split-merge-and-move-decisions.md": ("targeted", ("analysis-agent", "review-agent"), ("boundary-decision", "selected-approach", "residual-risk"), "route-or-material-unknown", ("acceptance", "scope", "material-risk-floor")),
            "references/benchmarks-and-enforcement.md": ("benchmark-pattern", ("analysis-agent", "review-agent"), ("option-comparison", "selected-approach"), "route-or-material-unknown", ("acceptance", "scope", "material-risk-floor")),
        },
    },
    "implementation-structure-design": {
        "root": "src/foundation/capabilities/implementation-structure-design/SKILL.md",
        "registry": "foundation",
        "removed": (),
        "references": {
            "references/object-module-decomposition.md": ("targeted", ("task-agent", "review-agent", "analysis-agent"), ("decision-record", "validation-plan", "proof-limit", "residual-risk"), "route-or-material-unknown", ("acceptance", "scope", "material-risk-floor")),
            "references/reuse-and-placement.md": ("targeted", ("task-agent", "review-agent", "analysis-agent"), ("selected-approach", "validation-plan", "proof-limit", "residual-risk"), "route-or-material-unknown", ("acceptance", "scope", "material-risk-floor")),
            "references/evidence-patterns.md": ("evidence-pattern", ("task-agent", "review-agent", "analysis-agent"), ("evidence-record", "validation-plan", "proof-limit", "residual-risk"), "repo-resolvable-fact", ()),
        },
    },
    "technology-stack-selection": {
        "root": "src/foundation/capabilities/technology-stack-selection/SKILL.md",
        "registry": "foundation",
        "removed": (),
        "references": {
            "references/benchmarks-and-patterns.md": ("benchmark-pattern", ALL_ROLES, ("option-comparison", "selected-approach"), "route-or-material-unknown", ("acceptance", "scope", "material-risk-floor")),
        },
    },
}

REVIEW_JIT_IMMUTABLE_HASHES = {
    "src/professional-skills/architecture-impact-reviewer/references/checklist.md": "e88eda288d2e2e300babdc5be2c34032c747ca12615e63ea9bdfc1c5bdcd978b",
    "src/professional-skills/architecture-impact-reviewer/references/solution-optimality.md": "acbb92d45bdb5b0c8e4898daa50beab915f3db12490e64275b923f325b91c657",
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
        "preserved_facets": ("Treat proposal evidence as non-authorizing unless separate production-mutation authority is confirmed.", "smallest owner", "non-mutating", "outside this Skill's authority"),
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
        "preserved_facets": ("independently reviewing", "non-mutating", "does not change its assigned scope", "actual latest diff"),
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
    def test_frozen_migration_evidence_is_well_formed(self) -> None:
        evidence_pairs = (
            (PAYMENT_ROOT_PREDECESSOR_SHA256, PAYMENT_ROOT_SUCCESSOR_SHA256),
            (PAYMENT_REGISTRY_PREDECESSOR_SHA256, PAYMENT_REGISTRY_SUCCESSOR_SHA256),
            (PAYMENT_RAW_CARD_RULES_SHA256, PAYMENT_RAW_CARD_SUCCESSOR_SHA256),
        )
        for predecessor, successor in evidence_pairs:
            with self.subTest(predecessor=predecessor):
                self.assertRegex(predecessor, r"\A[0-9a-f]{64}\Z")
                self.assertRegex(successor, r"\A[0-9a-f]{64}\Z")
                self.assertNotEqual(predecessor, successor)

        self.assertTrue(RELOCATION_LEDGER)
        identities = [
            (
                entry["owner"],
                entry["source_path"],
                entry["source_rule_fingerprint"],
            )
            for entry in RELOCATION_LEDGER
        ]
        self.assertEqual(len(identities), len(set(identities)))
        for entry in RELOCATION_LEDGER:
            self.assertEqual(LEDGER_FIELDS, set(entry))
            self.assertTrue(entry["required_by"])
            self.assertTrue(entry["required_output"])
            self.assertEqual(
                _fingerprint(str(entry["old_anchor"])),
                entry["source_rule_fingerprint"],
            )
            self.assertRegex(
                str(entry["source_rule_fingerprint"]),
                r"\A[0-9a-f]{64}\Z",
            )

    def test_synthetic_relocation_is_exactly_once_and_preserves_adjacency(
        self,
    ) -> None:
        moved_rule = "- Validate rollback before activation."
        retained_kernel = "- Keep the owner and failure boundary in the root."
        root_before = (
            "# Example\n\n## High-Value Rules\n\n"
            f"{retained_kernel}\n{moved_rule}\n"
        )
        root_after = (
            "# Example\n\n## High-Value Rules\n\n"
            f"{retained_kernel}\n"
        )
        destination_after = (
            "# Recovery\n\n## Activation\n\n"
            f"{moved_rule}\n"
            "- Record the recovery result.\n"
        )

        self.assertEqual(1, root_before.count(moved_rule))
        self.assertEqual(0, root_after.count(moved_rule))
        self.assertEqual(1, destination_after.count(moved_rule))
        self.assertEqual(1, root_after.count(retained_kernel))
        self.assertIn(
            moved_rule + "\n- Record the recovery result.",
            destination_after,
        )
        self.assertNotEqual(
            1,
            (destination_after + "\n" + moved_rule).count(moved_rule),
        )
        self.assertEqual(
            _fingerprint(moved_rule),
            _fingerprint("  - Validate   rollback before activation.  "),
        )

    def test_synthetic_selected_references_are_loaded_without_loss(self) -> None:
        selected = [
            ("synthetic-owner", "references/first.md"),
            ("synthetic-owner", "references/second.md"),
            ("synthetic-owner", "references/third.md"),
        ]
        owner_projection = {
            "reference_types": {path: "targeted" for _owner, path in selected},
            "reference_roles": {
                path: ["task-agent"] for _owner, path in selected
            },
            "reference_outputs": {
                path: ["evidence-record"] for _owner, path in selected
            },
            "declarations": {},
        }
        authority = {
            "contract": VALIDATION.REFERENCE_CONTEXT_ADMISSIBILITY_CONTRACT,
            "owners": {"synthetic-owner": owner_projection},
            "carrier_fields": {},
        }
        plan = VALIDATION.reference_context_staged_plan(
            authority,
            references=selected,
            path="direct",
            profile="task-agent",
            selection_owner="main-control-agent",
            available_carrier_fields=[],
            receipt_replayed=True,
            brief_current=False,
            review_fresh=False,
        )
        self.assertTrue(plan["reachable"])
        self.assertEqual(
            {tuple(row) for row in plan["selected_union"]},
            {tuple(row) for row in plan["loaded_union"]},
        )
        self.assertEqual(
            len(selected),
            len(plan["required_output_receipts"]),
        )
        with self.assertRaisesRegex(
            VALIDATION.ValidationProblem,
            "must be unique",
        ):
            VALIDATION.reference_context_staged_plan(
                authority,
                references=[*selected, selected[0]],
                path="direct",
                profile="task-agent",
                selection_owner="main-control-agent",
                available_carrier_fields=[],
                receipt_replayed=True,
                brief_current=False,
                review_fresh=False,
            )

    def test_exact_layer3_static_boundary_uses_synthetic_cardinalities(self) -> None:
        owner = "synthetic-professional"
        candidates = [f"synthetic-layer3-{index}" for index in range(4)]
        authority = {
            "contract": VALIDATION.LAYER3_SELECTOR_AUTHORITY_CONTRACT,
            "runtime_professionals": {
                owner: {
                    "role_support": ["task-agent"],
                    "candidates_by_role": {"task-agent": candidates},
                    "domain_authorization": [],
                    "reference_records": [],
                }
            },
            "runtime_domains": {},
        }
        for cardinality in (0, 1, 3):
            with self.subTest(cardinality=cardinality):
                projection = VALIDATION.layer3_selector_runtime_projection(
                    authority,
                    professional_skill=owner,
                    profile="task-agent",
                    selection_owner="main-control-agent",
                    exact_layer3=candidates[:cardinality],
                )
                self.assertEqual(
                    candidates[:cardinality],
                    projection["exact_layer3"],
                )
        with self.assertRaisesRegex(
            VALIDATION.ValidationProblem,
            r"ordered unique 0\.\.3 list",
        ):
            VALIDATION.layer3_selector_runtime_projection(
                authority,
                professional_skill=owner,
                profile="task-agent",
                selection_owner="main-control-agent",
                exact_layer3=candidates[:4],
            )
