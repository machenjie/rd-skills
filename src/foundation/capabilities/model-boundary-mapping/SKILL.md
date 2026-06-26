---
name: model-boundary-mapping
description: Use when API DTOs, commands, queries, domain objects, value objects, persistence models, ORM entities, event payloads, view models, generated clients, mappers, assemblers, null/default semantics, validation ownership, serialization, or generated/handwritten boundaries can leak across model boundaries.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "112"
changeforge_version: 0.1.0
---

# Mission

Keep models honest at their boundaries by defining what each model represents, who validates it, who maps it, how semantics survive each transformation, and which fields, rules, generated types, persistence concerns, or side effects must not leak. Treat repository graph and project memory as search leads, then prove the boundary against current source, contracts, generated artifacts, tests, and validation output.

# When To Use

Use when API DTOs, command/query objects, domain objects, value objects, persistence models, ORM entities, event payloads, view models, generated clients, serializers, mappers, assemblers, or schema versions are added or changed.

Use when null, default, optional, generated, handwritten, validation, compatibility, or serialization semantics can drift across boundaries.

Use when a mapper, assembler, controller, adapter, repository, generated client, SDK model, or view-model transform may carry business rules, authorization decisions, persistence metadata, provider fields, or side effects across an ownership boundary.

# Do Not Use When

Do not use for a private local value with no boundary crossing and no serialization or persistence semantics.

Do not use to create mapper layers when the local convention intentionally uses a simple direct projection and no boundary leakage exists.

Do not use as a substitute for `dto-schema-design` when field-level transfer schema is primary, `data-model-design` when stored source-of-truth shape is primary, `version-compatibility` when old/new compatibility mechanics are primary, or `consumer-impact-analysis` when consumer inventory and migration are primary.

# Stage Fit

Use during planning, coding, bug-fix, debugging, code-review, refactoring, testing, release readiness, validation mapping, and final handoff when a model crosses API, domain, persistence, event, integration, generated, SDK, view, or storage boundaries. Re-run after edits that change source/target model fields, mapper placement, validation owner, generated artifacts, serializer behavior, event payloads, null/default semantics, or tests; earlier boundary evidence is stale when any of those change.

# Non-Negotiable Rules

- DTO is not a domain object, persistence model, generated provider model, or view model.
- Persistence models, ORM entities, database rows, lazy proxies, internal IDs, audit fields, and storage metadata must not leak to API, SDK, event, or UI contracts.
- Domain objects must not import HTTP, JSON schema, ORM decorators, generated clients, provider SDK models, UI view models, or transport-specific serializers.
- Mapper/assembler code owns translation, allowlisted field selection, and boundary defaults; it must not own pricing, authorization, lifecycle transition, state-machine, or policy decisions unless explicitly routed as policy.
- Validation owner is named for each boundary: trust-boundary DTO validation, domain invariant validation, persistence constraint, event schema validation, or generated-client validation.
- Null, absent, empty, zero, false, unknown, not-applicable, server default, and client omitted semantics must be preserved or intentionally remapped with tests.
- Event payloads, public DTOs, SDK models, and generated clients are versioned contracts; generated models stay at the generated boundary and are not hand-edited.
- Repository graph and project memory are leads, not proof; current source, generated artifacts, and validation freshness decide the boundary.

# Industry Benchmarks

Anchor against domain-driven design model separation, command/query responsibility separation, anti-corruption layer mapping, OpenAPI/JSON Schema/Protobuf compatibility, ORM persistence isolation, versioned event contracts, generated client boundary governance, consumer-driven contract testing, and mapper-as-translation-not-policy discipline.

# Mode Matrix

| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities |
| --- | --- | --- | --- | --- |
| Boundary leakage repair | DTO/domain/persistence/event/view/generated model crosses directly into another layer. | Reassert source/target ownership and reject direct reuse. | Source model, target model, leaked fields/types, callers, rejected leakage alternative. | `dto-schema-design`, `implementation-structure-design` |
| Mapper ownership decision | Mapper, assembler, serializer, adapter, or controller transform changes field meaning or contains rule logic. | Separate translation from business policy, validation, side effects, and persistence. | Mapper owner, validation owner, policy owner, side-effect scan, tests. | `data-side-effect-flow-tracing`, `business-rule-extraction` |
| Null/default semantic preservation | Null, absent, optional, default, empty, zero, false, unknown, or server default crosses boundary. | Preserve semantic meaning and prevent silent compatibility drift. | Semantic table, examples, old/new mapping cases, validation evidence. | `dto-schema-design`, `quality-test-gate` |
| Generated and handwritten boundary | Generated client, provider SDK model, OpenAPI/proto class, ORM generated type, or codegen artifact is reused or hand-edited. | Keep generated surfaces isolated and current. | Source schema, generated artifact, generator command, hand-edit rejection, compile/contract check. | `version-compatibility`, `contract-testing` |
| Public contract boundary | API response, SDK export, event payload, CLI output, or package export maps from internal model. | Avoid internal field exposure and downstream breakage. | Consumer class, compatibility impact, generated client status, contract tests or residual risk. | `consumer-impact-analysis`, `version-compatibility` |
| Testability and proof | Mapping tests require private helpers, mocks, or fixtures that shape implementation. | Prove observable mapping behavior without exporting private internals. | Public behavior boundary, fixture owner, test seam decision, validator freshness. | `testability-seam-design`, `validation-broker` |

# Selection Rules

Select this capability when the primary risk is model leakage, mapping ownership, validation ownership, generated/handwritten boundary drift, or semantic loss across model transformations. Use it before field-by-field DTO design when the first question is "which model owns this concept and who maps it?"

Prefer `dto-schema-design` when the transfer field schema itself is the main work. Prefer `data-model-design` when stored source-of-truth shape, invariants, or relationships are primary. Prefer `api-contract-design` when endpoint operation behavior is primary. Prefer `version-compatibility` when the boundary is already clear but old/new compatibility mechanics dominate. Prefer `consumer-impact-analysis` when downstream inventory and migration dominate. Pair with `implementation-structure-design` when mapper placement, file ownership, or generated-vs-handwritten location is unclear.

# Technical Selection Criteria

Evaluate each boundary by source model, target model, contract surface, actor, validation owner, mapping owner, policy owner, serialization owner, persistence owner, generated artifact source, consumer visibility, null/default semantics, sensitive/internal fields, side-effect risk, test seam, compatibility class, and validation freshness. A model boundary is professionally mapped only when ownership, allowed fields, rejected fields, semantic preservation, generated boundary, behavior preservation, tests, and residual risk are concrete.

# Proactive Professional Triggers

- **Signal:** Controller, service, adapter, mapper, generated client, or UI code passes an API DTO, ORM entity, database row, provider SDK model, event payload, or view model directly into another layer. **Hidden risk:** persistence, provider, transport, or UI details become domain behavior or public contract. **Required professional action:** produce source/target model map and rejected direct-reuse rationale. **Route to:** `implementation-structure-design`, `dto-schema-design`. **Evidence required:** callers, field map, owner boundary, rejected leakage alternative, mapping tests.
- **Signal:** Mapper or assembler calculates price, permission, status transition, lifecycle state, tenant access, retry behavior, or other business policy. **Hidden risk:** policy splits between mapper and domain/service, and tests miss the real invariant owner. **Required professional action:** separate translation from policy or explicitly route the mapper as policy. **Route to:** `business-rule-extraction`, `data-side-effect-flow-tracing`. **Evidence required:** rule owner, side-effect scan, policy test, mapper translation test.
- **Signal:** Null, absent, empty, zero, false, default, unknown, or not-applicable value crosses API/domain/persistence/event/generated boundaries without a semantic table. **Hidden risk:** PATCH, import, mobile, generated client, and persistence behavior silently diverge. **Required professional action:** define semantic preservation or intentional remap. **Route to:** `dto-schema-design`, `quality-test-gate`. **Evidence required:** semantic cases, old/new examples, mapping tests, residual compatibility risk.
- **Signal:** Generated model, provider SDK type, OpenAPI/proto class, ORM entity, or generated client is hand-edited or reused outside its generated boundary. **Hidden risk:** generator reruns erase changes or external schema drift leaks into domain/public contracts. **Required professional action:** isolate generated surface and map through handwritten owned code. **Route to:** `version-compatibility`, `contract-testing`. **Evidence required:** source schema, generated artifact path, generator freshness, handwritten mapper owner.
- **Signal:** Persistence field, internal ID, audit column, tenant/object scope, permission flag, or sensitive provider field appears in API, event, SDK, view model, log, fixture, or generated export. **Hidden risk:** internal details become stable contracts or leak sensitive data. **Required professional action:** classify internal/public split and security/privacy exposure. **Route to:** `security-privacy-gate`, `consumer-impact-analysis`. **Evidence required:** field exposure map, allowed consumer, filtering rule, denied exposure test or residual risk.
- **Signal:** Repository graph, project memory, or prior validation says "no boundary leak", "no consumers", or "mapper already tested" without current source and generated artifact checks. **Hidden risk:** stale memory misses new callers, generated clients, dashboards, event consumers, or changed validators. **Required professional action:** verify current graph, source, generated outputs, tests, and validation freshness. **Route to:** `repository-graph-analysis`, `project-memory-governance`, `validation-broker`. **Evidence required:** inspected paths, accepted/rejected memory, freshness verdict.
- **Signal:** Tests cover only one happy mapping fixture, private mapper internals, or mock calls. **Hidden risk:** null/default, generated boundary, compatibility, and leakage regressions survive. **Required professional action:** map each boundary risk to observable mapping tests or disclose not-verified limits. **Route to:** `testability-seam-design`, `quality-test-gate`. **Evidence required:** public behavior boundary, fixture owner, negative/compatibility cases, validator result.

# Risk Escalation Rules

Escalate to `data-api-contract-changer` when public API, SDK, schema, event, package export, or generated client compatibility changes. Escalate to `domain-impact-modeler` when mapping changes identity, lifecycle, invariant, value-object semantics, or state transitions. Escalate to `consumer-impact-analysis` when existing or unknown consumers may depend on the old shape. Escalate to `security-privacy-gate` when internal, tenant, permission, PII, financial, health, token, audit, or provider-sensitive fields can leak. Escalate to `data-side-effect-flow-tracing` when mapper/assembler code mutates, publishes, caches, logs, calls IO, or reads nondeterministic sources.

# Reference Loading Policy

Current mode is inline-only: this capability has no deep reference files today, so this `SKILL.md` contains the active model-boundary mapping rules.

If deep references are added later, load them only for L3+ work, public contracts, generated clients, DTO/domain/persistence/event leakage, null/default semantic drift, or mapper ownership ambiguity.

Do not load deep references for L1/L2 local mapper changes where source, target, validation owner, compatibility, and rejected leakage alternatives are clear from the inline output contract.

# Critical Details

- API DTO owns transport shape, validation-at-boundary fields, and client compatibility.
- Command/query object owns use-case intent and caller-supplied parameters.
- Domain object owns identity, lifecycle, invariants, and behavior.
- Value object owns validation, normalization, equality, and unit safety for a value.
- Persistence model owns storage shape, ORM annotations, indexes, and database-specific fields.
- Event payload owns versioned producer/consumer contract and immutable historical meaning.
- View model owns UI rendering shape and should not become a domain rule owner.
- Mapper/assembler owns translation and boundary defaults, not hidden business decisions.
- Boundary-specific fields include internal IDs, audit fields, permissions, calculated display fields, ORM metadata, transport links, and generated client fields.
- Null/default/optional semantics must define absent, unknown, empty, zero, false, server default, and client omitted separately when meaningful.
- Mapping direction matters: request DTO to command, command to domain, domain to persistence, persistence to domain/read model, domain to event, event to projection, domain to view model, and provider model to local model each have different validation and compatibility owners.
- Same-pattern scans cover sibling DTOs, mappers, serializers, assemblers, generated wrappers, repository adapters, fixtures, event payloads, SDK exports, and view models that may leak the same boundary.
- Repository graph evidence covers callers, consumers, generated sources, tests, and public exports; project memory can prioritize the search but cannot replace current-source inspection.
- Behavior preservation names old DTOs, old mappers, old generated clients, old fixtures, old events, old persisted rows, and old consumers that remain valid or intentionally migrate.
- Validation evidence must be fresh for the final mapping path; if source, target, mapper, generated artifact, or fixture changes after validation, rerun or downgrade the claim.

# Execution Coupling

- **Repository graph:** inspect current callers, target consumers, mapper/serializer owners, generated artifact sources, test edges, public exports, event producers/consumers, and repository adapters before accepting a boundary map.
- **Project memory:** use previous incidents, fragile mapper notes, known generated-client drift, or old compatibility claims only as search leads; reject memory contradicted by current source.
- **Execution path:** connect planned edits and validators to the boundary map so implementation cannot move mapping logic, validation, generated artifacts, or fixtures without updating proof.
- **Freshness:** mark the map stale when later edits change source/target fields, mapping order, validation owner, generated output, public contract, or tests.
- **Plan consistency:** before handoff, compare selected boundary, actual changed files, generated/report updates, validation results, skipped consumers, and residual risks.

# Failure Modes

- **ORM leak:** Returning ORM entities directly from controllers.
- **DTO-as-domain:** Passing API DTOs into domain methods as if they were domain objects.
- **Framework-tainted domain:** Domain object imports HTTP, JSON schema, ORM decorators, or generated client types.
- **Mapper-owned policy:** Mapper silently calculates price, permission, state transition, or policy decision.
- **Unversioned event drift:** Event payload field is renamed without versioning or upcaster/compatibility plan.
- **Generated boundary leak:** Generated model is edited by hand or leaks into domain code.
- **Null/default semantic loss:** Null becomes default empty value and changes business meaning.
- **Internal field exposure:** Tenant, permission, audit, provider, or persistence metadata becomes part of an API, SDK, event, or view contract.
- **Fixture-shaped proof:** Tests use one happy fixture and miss optional/default/generated boundary drift.
- **Stale graph claim:** Project memory says a mapper is isolated, but current graph exposes a new consumer, generated export, or dashboard fixture.

# Output Contract

Return a Model Boundary Map:

- `mode_selected` (boundary leakage repair, mapper ownership decision, null/default semantic preservation, generated and handwritten boundary, public contract boundary, or testability and proof).
- `boundaries_inspected` (source model, target model, DTO/schema, domain/value object, command/query, persistence/ORM, event payload, view model, generated client/provider model, mapper/assembler, serializers, tests, graph, memory, and skipped boundaries with reason).
- `source_evidence` (current files, callers, consumers, generated artifacts, schemas, fixtures, tests, registry/config, or reports inspected).
- `model_inventory` (model name, layer, owner, contract surface, identity semantics, lifecycle/invariant owner, validation owner, serialization owner, and consumer visibility).
- `mapping_spec` (source, target, direction, allowed fields, rejected fields, mapping owner, mapper placement, validation owner, policy owner, and side-effect owner or no-side-effect proof).
- `semantic_preservation` (null, absent, empty, zero, false, unknown, not-applicable, server default, client omitted, enum/default/value-object semantics, and old/new examples).
- `generated_handwritten_boundary` (source schema or generator, generated artifact path, hand-edit rule, adapter/anti-corruption layer, generated-client freshness, and contract check).
- `compatibility_and_consumer_impact` (public contract impact, event/SDK/API exposure, version or bridge need, known/unknown consumers, and handoff owner).
- `tests_and_validation` (same-pattern scan, mapping tests, negative/compatibility cases, generated-client checks, validator commands, freshness, and not-verified limits).
- `residual_mapping_risk` (remaining leakage, semantic, generated, consumer, privacy, side-effect, validation, or testability risk and next owner).

# Evidence Contract

Close the map only when these answers are concrete:

- **Basis:** changed path, boundary crossing, source model, target model, and why leakage or semantic drift matters.
- **Boundaries inspected:** source/target models, callers, consumers, mappers, serializers, validators, generated artifacts, schemas, events, persistence models, tests, graph leads, memory leads, and skipped boundaries.
- **What evidence proves:** which current-source facts prove model ownership, mapping owner, validation owner, semantic preservation, generated boundary, compatibility, behavior preservation, and rejected leakage alternatives.
- **What evidence does not prove:** unknown consumers, uninspected generated languages, stale project memory, production telemetry gaps, private fixtures, external provider behavior, rollback, or privacy filtering not verified.
- **Validation evidence:** command names, validators, reports, fixtures, artifacts, exit code/result, and freshness after the final material edit.
- **Reuse / placement rationale:** existing mapper, DTO, schema, domain object, repository adapter, generated source, fixture, or test reused or rejected; why no direct model reuse, duplicated mapper, or speculative shared abstraction was introduced.
- **Behavior preservation:** old DTOs, old domain objects, old persistence rows, old generated clients, old validators, old mappers, old events, old fixtures, and rollback behavior remain valid or have migration ownership.
- **Residual risk and next gate:** remaining mapping, compatibility, consumer, privacy, side-effect, generated-artifact, or validation risk has an owner and next capability/gate.

# Benchmark Coverage

This capability covers DTO/domain/persistence/event/view/generated boundary separation, anti-corruption mapping, command/query ownership, mapper-as-translation discipline, null/default/optional semantic preservation, generated/handwritten boundary governance, internal/public field separation, graph-memory-trajectory verification, changed-mapping-to-validation mapping, and evidence-limited handoff.

# Routing Coverage

Routes from `data-api-contract-changer`, `backend-change-builder`, `frontend-change-builder`, `integration-change-builder`, `ai-code-review-refactor`, and `quality-test-gate` should arrive here when model ownership, mapping ownership, validation ownership, semantic preservation, generated boundaries, or leakage rejection is primary. Route away when field schema design, persistence source-of-truth modeling, endpoint behavior, compatibility mechanics, downstream inventory, side-effect ordering, or release approval is primary.

# Quality Gate

1. DTO, domain, persistence, event, and view models have distinct responsibilities where boundaries exist.
2. Persistence model does not leak to API.
3. Domain model does not import framework, transport, serialization, or ORM concerns.
4. Mapper owns translation only unless a policy exception is explicit.
5. Null/default/optional semantics are preserved and tested.
6. Event payload compatibility is versioned.
7. Generated models remain at generated boundaries.
8. Validation owner, mapping owner, policy owner, serialization owner, and generated artifact owner are named or explicitly out of scope.
9. Boundary-specific internal, tenant, permission, audit, provider, ORM, and generated fields are filtered or intentionally exposed with security/consumer review.
10. Same-pattern scan covers sibling mappers, DTOs, serializers, assemblers, generated wrappers, event payloads, fixtures, and SDK exports.
11. Repository graph, project memory, and execution trajectory are reconciled, with memory treated as a lead rather than proof.
12. Mapping tests cover negative, null/default, generated boundary, and compatibility cases where material.
13. Validation evidence is fresh for the final mapping path; stale, partial, missing, or not-verified coverage is disclosed.
14. Residual mapping risk names next owner, rollback or migration note, and next validation gate.

# Used By

- data-api-contract-changer
- backend-change-builder
- frontend-change-builder
- integration-change-builder
- ai-code-review-refactor
- quality-test-gate

# Handoff

Hand off to `dto-schema-design`, `api-contract-design`, `data-model-design`, `version-compatibility`, `implementation-structure-design`, `domain-impact-modeler`, `consumer-impact-analysis`, `input-validation`, `data-side-effect-flow-tracing`, `testability-seam-design`, `security-privacy-gate`, or `validation-broker` depending on which boundary or proof gap remains.

# Completion Criteria

The capability is complete when every boundary-crossing model has an owner, mapping and validation are explicit, generated and handwritten surfaces are separated, null/default/optional and value semantics are preserved, leakage alternatives are rejected, graph/memory claims are current-source verified, mapping tests and validation evidence are fresh, and residual mapping risk is explicit.
