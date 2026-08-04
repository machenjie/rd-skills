# Testability Seam Evidence Patterns

Use this reference when closure depends on current repository inspection, prior task evidence, observable action sequence, validation freshness, tool permission boundary, or changed-path-to-seam mapping.

## Changed-Path-To-Seam Map

| Seam claim | Minimum evidence | What it proves | What it does not prove |
| --- | --- | --- | --- |
| Public boundary is testable | Current source path, public entry point, observable output/side effect, test path, command, and owner | The inspected behavior can be verified without private-helper export | All callers, integrations, or UI/API translations are covered |
| Private helper remains private | Rejected export or visibility change, replacement public-boundary assertion, and placement rationale | Encapsulation was preserved for the inspected behavior | Future tests will not request the same shortcut |
| Double fidelity is sufficient | Real contract source, fake/stub/mock/spy choice, calibration command or explicit limitation, and recommended next step | The double is adequate for the named risk at the chosen layer | The real provider is fully verified unless contract/integration evidence ran |
| Determinism is controlled | Clock/random/UUID/env/scheduler/IO source, override mechanism, reset/cleanup path, replay command, and flake risk | The test can repeat under declared inputs | CI load, future globals, or external services cannot introduce flake |
| Accepted test-data lifecycle is honored | `test-data-management` decision, seam reset/observation contract, exercised cleanup signal, and proof limits | The inspected seam supports the accepted fixture and cleanup behavior | Fixture meaning, namespace, privacy, asynchronous cleanup, or lifecycle ownership is re-decided |
| Characterization is fresh | Behavior boundary, pre-move command, post-move command, report path, exit code, and preserved-bug decision | The refactor preserved the characterized observable behavior | Uncharacterized branches or hidden side effects are safe |
| Prior task or source evidence claim is current | Prior claim source, current graph/source/test reread, accepted/rejected claims, final validator, and freshness verdict | Old seam evidence still matches current source | Future edits, dynamic imports, skipped suites, or generated artifacts remain safe |

## Current Evidence And Freshness

- Treat repository inspection, prior task evidence, old coverage reports, prior CI logs, generated summaries, and agent notes as discovery inputs until current source and fresh validators confirm them.
- Accept a prior testability claim only while current source, tests, fixtures, doubles, generated inputs, configurations, and command output still match. Examples include "public behavior already covered", "mock is safe", "fixture is owned", "fake matches provider", and "full validation passed".
- Mark evidence stale after edits to production source, tests, fixtures, factories, mocks, fakes, snapshots, golden files, generated inputs, config, lockfiles, reports, build outputs, or targeted-validation-selection mappings.
- Record inspected and skipped boundaries: public entry point, private helper, collaborator, external provider, dependency graph, fixture/golden source, generated input, command selection, and report artifact.
- For each final confidence claim about a seam changed or inspected by the current task, cite a command, test path, report, fixture source, or owner review. An unsupported claim remains unverified with named residual seam risk.

- If fixture, snapshot, golden, generated input, or test-data regeneration is involved, cite the accepted `test-data-management` decision and record only seam-specific reset/observation evidence here.
- If external provider, shared database, telemetry, production sample, or connector export, treat it as not seam evidence by itself; require owner, bounded dataset, redaction, and integration/contract/security handoff.

## Blocking Conditions

Block closure when private-helper export lacks a public-boundary attempt, provider doubles lack fidelity limits, nondeterminism remains uncontrolled, or the accepted test-data decision is absent. Also block late characterization, stale prior evidence, and state-mutating validation without permission, isolation, and rollback disclosure.
