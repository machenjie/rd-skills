# Plan Execution Consistency Evidence Patterns

Use this reference when closure depends on proving that the accepted plan, actual diff, validation order, review scope, generated artifacts, graph/memory/trajectory claims, and final handoff are aligned. Keep the main capability body for routing; load this file only for concrete proof classification.

## Claim To Evidence Map

| Claim | Strong evidence | Weak or invalid evidence | Residual risk if absent |
| --- | --- | --- | --- |
| Actual diff matches plan | Accepted plan items plus final changed-file inventory and variance rationale | Plan summary without final diff | Scope drift hides unreviewed files |
| Validation is fresh | Command ledger run after final material edit with covered paths and exit codes | Green command before later source/report/generated edit | Final state is overclaimed as tested |
| Review covers final diff | Reviewer scope, findings, repair paths, and targeted re-review status | Approval statement without file scope | Repaired or extra diff bypasses review |
| Generated output matches source | Source-of-truth path, generator/build command, profile, generated diff, and validator | Generated file timestamp or report only | Runtime artifact drifts from source |
| Memory/graph/trajectory claim is safe | Current source/diff/command evidence accepts or rejects each claim | Compaction, old report, or graph-only claim | Stale context becomes proof |
| Handoff wording matches evidence | Final claim names done scope, validation limits, rollback, residual risk, and next owner | "All passed" after targeted or stale checks | User receives stronger assurance than proof supports |

## Evidence Labels

- **Strong**: final diff, accepted plan, command ledger, review scope, generated/source mapping, exit code, artifact path, and freshness after final material edits.
- **Weak**: partial diff, stale report, targeted validator reported as full, graph-only evidence, memory-only claim, or approval without file list.
- **Missing**: no plan source, no final inventory, no command outcome, no review scope, no generated source proof, or no rollback note.
- **Invalid**: validation before later edits, generated-only proof, handoff that omits failed/not-run validators, or memory contradicted by current source.

## Closure Checks

- Reject ready closure when validation predates final source, registry, reference, report, package, fixture, generated, or install-output changes.
- Reject ready closure when repair follows review and targeted re-review is missing.
- Downgrade generated-source claims when the build/profile that emitted the artifact is not named.
- Do not treat graph, memory, trajectory, or prior summary as current-state proof without direct source or fresh command evidence.
