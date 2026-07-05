# E2E Evidence Patterns

Use this reference when `e2e-testing` closure depends on repository graph,
project memory, old CI output, prior agent claims, validation freshness, command
artifacts, or changed-journey-to-test mapping. Keep it as an evidence map, not
a second E2E tutorial.

## Changed-Journey-To-Test Map

| Claim | Minimum evidence | What it proves | What it does not prove |
| --- | --- | --- | --- |
| Critical journey is covered | Route/source path, user role, entry point, test file, command, trace or screenshot artifact, and owner. | The inspected journey has a runnable browser proof obligation. | Untested journey variants, devices, browsers, locales, or production data are safe. |
| Auth or permission branch is covered | Allowed role, denied role, session state, redirect or denial assertion, and non-leak check. | The inspected browser path distinguishes allowed, denied, expired, or unauthenticated states. | Backend authorization is complete for every tenant/object combination. |
| Durable side effect is covered | User-visible assertion plus DB/API/email/event/audit assertion or lower-level integration evidence link. | The E2E journey proves the business outcome, not only navigation. | All downstream jobs, third-party production behavior, or eventual consistency windows are covered. |
| Flake control is credible | No arbitrary sleeps, semantic selectors, isolated data, controlled stubs, artifact capture, and CI/shard outcome. | The inspected test has deterministic waits, data, and failure diagnostics. | Future route changes, new browser versions, or CI capacity shifts cannot reintroduce flake. |
| Validation is fresh | Command, working directory, exit code/outcome, report or artifact path, and final-edit freshness. | Evidence was produced after the final material change for the mapped journey. | Later source, fixture, route, CI, stub, generated, or report edits are covered. |

## Graph, Memory, And CI Reconciliation

- Treat repository graph, project memory, old screenshots, old traces, prior CI,
  and prior agent summaries as discovery inputs until current source confirms
  them.
- Accept prior "this E2E covers it" claims only when current route, fixture,
  role, selector, stub, CI config, and validation artifact still match.
- Reject or downgrade memory that lacks command, exit code, artifact path, owner,
  journey scope, role scope, fixture source, or validation freshness.
- Mark evidence stale after edits to routes, auth/session setup, fixtures,
  selectors, Playwright/Cypress config, external stubs, CI browser matrix,
  generated reports, or the asserted journey behavior.

## Handoff Evidence Shape

```yaml
e2e_testing_evidence_closure:
  inspected_paths:
    - path: ""
      finding: ""
  accepted_prior_claims:
    - claim: ""
      current_evidence: ""
  rejected_or_stale_claims:
    - claim: ""
      reason: ""
  changed_journey_to_test_map:
    - journey_or_branch: ""
      route_or_source_path: ""
      test_file: ""
      validation_command: ""
      exit_code_or_status: ""
      artifact_or_report: ""
      proves: ""
      does_not_prove: ""
      owner: ""
      freshness: ""
  residual_risk:
    - risk: ""
      owner: ""
      next_gate: ""
```
