# Architecture Enforcement Tooling Benchmarks And Patterns

Use this reference when `architecture-enforcement-tooling` needs more depth than the main `SKILL.md` should carry efficiently.
Keep the body focused on routing, output, and gates.
Use this file for tool fit, enforcement patterns, generated-source policy, public export gates, migration ratchets, and anti-pattern review.

## Benchmark Anchors

- Evolutionary architecture fitness functions: architectural intent should be expressed as repeatable checks.
- ArchUnit, Dependency Cruiser, import-linter, ESLint boundaries, go vet, staticcheck, type strictness, and dead-code tooling: choose tools by rule expressiveness, not popularity.
- CI quality gates: a rule is enforceable only when it runs pre-merge, in CI, or in a timeboxed report-only baseline.
- Public API compatibility practice: export gates need consumer inventory before blocking or removal.
- Generated-source governance: generated paths need narrow exceptions tied to source-of-truth and drift checks.
- Ratcheting practice: large existing violations should move from baseline to progressively lower thresholds.

## Rule-To-Tool Fit Matrix

| Rule type | Strong enforcement shape | Escalate when |
| --- | --- | --- |
| Import or layer boundary | Static import graph rule with failing edge and replacement path. | Dynamic plugin or generated import hides a real edge. |
| Cycle detection | Package/module graph check in CI with current graph inputs. | Cycles cross build tools or generated projects. |
| Public/private export | Export diff plus known consumer inventory and allowed facade. | SDK, generated client, or external package may consume it. |
| Forbidden dependency | Tool rule scoped to source sets and test/generated exceptions. | Broad glob or blanket ignore hides high-risk edges. |
| Type, lint, complexity | Existing language tool with scoped threshold and ratchet. | New dependency is added without supply-chain review. |
| Dead code | Static search plus runtime/generated/config/docs reference search. | Reflection, registration, migration, or CLI entry point is possible. |
| Affected-test and cache | Graph inputs, generated inputs, lockfiles, and full-suite fallback. | Skipped tests depend on invisible transitive edges. |

## Migration Pattern

```yaml
architecture_enforcement_migration:
  mode: block_now | report_only | ratchet
  baseline_count: 0
  block_threshold: 0
  owner: ""
  cleanup_issue: ""
  ratchet_rule: ""
  rollback_or_unblock: ""
```

## Anti-Patterns To Reject

| Anti-pattern | Failure | Safer treatment |
| --- | --- | --- |
| README-only architecture rule. | Drift returns after review memory fades. | Convert to tool-backed check or report-only baseline. |
| Blanket generated-code ignore. | Real violations hide under broad exception. | Scope exception to source-of-truth and generated path pattern. |
| Popular tool without rule fit. | CI cost grows without enforcing the accepted rule. | Compare existing commands and prove a representative failure. |
| Blocking gate with unowned baseline. | Teams disable the gate under pressure. | Baseline, owner, cleanup issue, and ratchet. |
| Public export removal without consumer search. | Downstream packages or generated clients break. | Route consumer impact and compatibility first. |
| Dead-code deletion from static result only. | Runtime registration or migrations disappear. | Search static, runtime, generated, docs, config, and scripts. |

## Handoff Boundaries

- Use `module-boundary-design` when the architecture rule itself is unclear.
- Use `ci-cd` when pipeline placement, cache, runner, or release flow is the primary issue.
- Use `package-dependency-management` when a new tool, action, binary, image, or lockfile change is required.
- Use `consumer-impact-analysis` and `version-compatibility` when public exports or SDK surfaces are affected.
- Use `cleanup-deletion-governance` when violation removal or dead-code cleanup is primary.
- Use `quality-test-gate` or `targeted-validation-selection` when enforcement output becomes release evidence.
