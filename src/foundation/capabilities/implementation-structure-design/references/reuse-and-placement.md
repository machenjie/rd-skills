# Reuse And Placement Evidence

- Reuse only when semantics, authority, failure, lifecycle, and evolution match; similarity is insufficient.

These decision patterns compare repository-local reuse, owner-private placement, deliberate separate implementation, and generated-source authority by semantics, ownership, failure, lifecycle, evolution, and current consumers.

## Search Scope

- Inspect the owning file and module for current helpers, exports, callers, tests, generated sources, failure behavior, and repository conventions.
- Expand to sibling modules or shared locations when current consumer scope or boundary risk warrants it.
- Record searched paths and terms, candidate owners, and runtime, generated, plugin, or external consumers that remain uninspected.
- Reject reuse based on naming, visual similarity, or duplicated lines when semantics, authority, failure behavior, or lifecycle differ.
- Do not use a generic shared module as a placement candidate. Export, cross-owner, shared, package, dependency, or cycle decisions route to `module-boundary-design`; distributable SDK/library contracts route to `sdk-library-contract-design`.

## Reuse Decision

| Decision | Accept when | Reject when |
| --- | --- | --- |
| Direct reuse | The current owner already provides the required semantics and failure contract. | Callers would inherit unrelated behavior, authority, or lifecycle. |
| Owner-local extension | New behavior remains cohesive and existing callers stay compatible. | Modes, flags, or unrelated branches split the responsibility. |
| Owner-private composition or adapter | The accepted owner stays intact and a real protocol, shape, or dependency-direction mismatch needs translation. | The wrapper relays calls, hides ownership, exports a new contract, or creates a cycle. |
| Private extraction | Current duplication or mixed responsibility has a named owner and behavior boundary. | Extraction exists for tests, speculative reuse, or line-count reduction. |
| Owner-private new structure | Current owner-local invariants, failures, lifecycle, or cleanup survive reuse and co-location comparison. | The surface is exported, shared, cross-owner, speculative, or justified by convenience. |
| Deliberate separate implementation or copy | Semantics, authority, failure behavior, lifecycle, or evolution differ enough that reuse would couple distinct owners. | Only naming, syntax, or line shape differs. |

For a deliberate separate implementation, record why drift is intentional, how divergence is detected or reviewed, and the delete condition for reconverging or removing the copy.

## Generated-Source Placement

Trace `editable source -> generator/template/config -> artifact -> committed/derived policy -> regen/freshness check`.

- Name the editable source and generator owner before choosing placement.
- Change a derived artifact through its accepted generator, template, or configuration authority.
- Stop on unknown authority and hand off to `repository-context-map`.
- Use `build-tool-professional-usage` to validate declared inputs, graph edges, toolchain identity, regeneration, stale-file cleanup, and committed-versus-derived policy.
- Classify the resulting diff as semantic or mechanical. A semantic diff changes consumer behavior or the generator contract; a mechanical diff only re-expresses authoritative inputs under the fixed generator and formatting policy.
- Record the consumer validation signal and freshness check after the latest material edit.

## Placement Record

- Record the selected owner, name, visibility, location, consumers, dependencies, tests, generated updates, rejected alternatives, and rollback or deletion condition.
- Route a changed module surface to `module-boundary-design`, behavior-preserving movement to `refactoring`, and local flow or readability to `code-clarity-maintainability`.

## Primary Source

Official source accessed on 2026-07-26: [Bazel repositories, packages, and targets](https://bazel.build/versions/7.4.0/concepts/build-ref). Bazel distinguishes source files, generated files, rules, inputs, outputs, packages, and targets. Those build concepts do not identify this repository's semantic owner, editable authority, checked-in artifact policy, or hidden runtime consumers.
