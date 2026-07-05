# TypeScript Evidence Patterns

Use this reference when TypeScript closure depends on repository graph, project memory, execution trajectory, validation freshness, escape-hatch audits, public type compatibility, bundle or accessibility artifacts, security-boundary proof, or changed-surface-to-validation mapping. Keep it as an evidence map, not a TypeScript tutorial.

## Changed-TypeScript-Surface-To-Validation Map

| TypeScript claim | Minimum evidence | What it proves | What it does not prove |
| --- | --- | --- | --- |
| Runtime boundary is safe | Boundary file, schema source, malformed fixture, validation test or command, and error mapping | Inspected external input is parsed before trusted use | All producers, historic payloads, browser variants, or downstream consumers are covered |
| Escape hatch is justified | `any`/`as`/non-null/ignore location, owner, expiration, safer alternative considered, and cleanup trigger | The unsafe construct is intentional and bounded | The escape hatch remains safe after API/schema changes |
| Public type is compatible | api-extractor, tsd, generated-client compile, consumer fixture, or semver review | Covered public types compile for named consumers | Unknown consumers, package adoption, or runtime behavior is safe |
| Async/state path is complete | Promise handling, abort/cancel path, discriminated state model, negative behavior test, and residual browser/API unknowns | Covered UI/service path handles success, error, and cancellation states | All interleavings, stale closures, or production latency are covered |
| Bundle/a11y impact is bounded | Bundle report, Lighthouse/size-limit output, axe/keyboard result, or not-run owner and reason | Inspected user-facing change has measured performance/accessibility signal | Full browser matrix, real-user Core Web Vitals, or every route is proven |
| Security-sensitive TS idiom is safe | Sanitizer/schema decision, pollution/XSS/deserialization test, static analysis or security review artifact | Named trust boundary has a reviewed mitigation | All attack variants or runtime deployment settings are covered |

## Evidence Quality Labels

- **Strong evidence**: current source/config inspected, command or artifact named, exit code or review status recorded, final-edit freshness stated, and proof limits named.
- **Weak evidence**: typecheck alone for external data, old generated-client result, snapshot-only UI test, generic style guide, or memory claim without current source.
- **Missing evidence**: no schema, no malformed fixture, no public-type compatibility check, no owner/expiration for escape hatch, or no command/status.
- **Invalid evidence**: `as any` as proof, non-null assertion at an external boundary, stale generated artifact, compile success used as sanitizer proof, or inaccessible bundle/a11y artifact.

## Graph, Memory, And Execution Reconciliation

- Treat repository graph, project memory, generated summaries, old typecheck output, and prior review notes as discovery inputs until current source, lockfile, generated artifacts, and validation confirm them.
- Accept a prior "typed", "safe", "unused", "generated", "schema-covered", or "bundle unchanged" claim only when the current source/config/lock/generated files still match.
- Mark evidence stale after edits to schemas, DTOs, public exports, generated clients, lockfiles, tsconfig/eslint config, bundler config, package entrypoints, UI routes, or validation fixtures.
- Map every accepted TypeScript claim to a current command, artifact/report, source path, owner approval, or explicit not-run residual risk.

## Tool Permission Boundary

| Action | Boundary record |
| --- | --- |
| Local source reads, graph search, generated artifact inspection, and report review | Read-only local shell action; cite searched paths and avoid full output dumps. |
| Typecheck, lint, tests, bundle analysis, axe, static analysis, and generated reports | State-mutating only for caches, reports, build artifacts, screenshots, or generated output; cite command, exit code, artifact path, and cleanup/rollback if relevant. |
| Dependency install, package upgrade, code generation, fixture refresh, or formatter rewrite | State-mutating development action; record package/version, generated output owner, diff review, rollback path, and lockfile impact. |
| Live browser session, production telemetry, package publishing, registry credential use, or security scanner export | High-risk or connector-scoped action; require bounded scope, redaction, retention limit, rollback or no-write proof, and stop condition. |

## Handoff Evidence Shape

```yaml
typescript_evidence_closure:
  inspected_paths:
    - path: ""
      finding: ""
  accepted_prior_claims:
    - claim: ""
      current_evidence: ""
  rejected_or_stale_claims:
    - claim: ""
      reason: ""
  changed_typescript_surface_to_validation_map:
    - surface: ""
      risk: boundary | escape_hatch | public_type | async_state | bundle_a11y | security
      command_or_artifact: ""
      exit_code_or_status: ""
      proves: ""
      does_not_prove: ""
      freshness: fresh | stale | partial | not_run
      owner: ""
  tool_permission_boundary:
    action_class: ""
    sandbox: ""
    state_mutation: ""
    redaction: ""
  residual_risk:
    - risk: ""
      owner: ""
      next_gate: ""
```
