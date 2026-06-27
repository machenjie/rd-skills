# Design System Evidence Patterns

Use this reference when design-system closure depends on graph, memory, execution output, validation freshness, tool permission boundaries, visual proof limits, accessibility proof limits, responsive proof limits, or final handoff readiness. Keep it as an evidence map, not a second component tutorial.

# Design-System-To-Validation Map

| Design-system claim | Minimum evidence | What it proves | What it does not prove |
| --- | --- | --- | --- |
| Current design-system source is known | Component source, docs, stories, tokens, tests, and relevant registry/config entries inspected | The proposal targets the inspected current component and token surface | Uninspected packages, stale Storybook deployments, or downstream forks are safe |
| Existing component reuse is valid | Accepted component plus rejected closest alternatives, consumer list, and state/story evidence | A new primitive is not needed for the inspected interaction | Future surfaces or uninspected product variants will never need a new primitive |
| Variant or token choice is sanctioned | Axis/value decision, token source, invalid combinations, theme contrast artifact, and owner when non-standard | The selected axis and token follow the design-system contract for inspected themes | Every browser, theme override, or future token rename is safe |
| Accessibility behavior is concrete | WCAG SC list, keyboard path, focus rule, role/name/value rule, live-region rule, and axe/manual artifact | The inspected interactive states have specific accessibility obligations and proof | Full screen-reader certification or specialist accessibility approval is complete |
| Responsive behavior is bounded | Breakpoint map, overflow/truncation rule, touch-target check, and screenshot/story/manual artifact | The task remains represented across inspected viewport classes | Physical-device ergonomics, zoom behavior, or all locales are fully covered |
| New component decision is governed | Three or more current surfaces or approved exception, owner, API, docs/stories/tests plan, and deprecation policy | Shared component creation or rejection has a reviewable governance basis | Future API stability is guaranteed without later review |
| Memory, graph, or prior trajectory is fresh | Current-source confirmation of remembered components, stories, consumers, tokens, and tests | Prior context still matches the inspected source for this decision | Uninspected branches, old generated artifacts, or abandoned prototypes are current |
| Release or build evidence is aligned | Validator, build, install, Storybook, screenshot, accessibility, or report path with exit code when runnable | The authored change produced the cited local artifact or result | Actual production browser behavior, device behavior, or user impact is certified |

# Graph, Memory, And Execution Reconciliation

- Treat repository graph, project memory, previous design reviews, generated UI, old screenshots, Storybook links, and prior validation reports as discovery inputs until current source confirms them.
- Accept a previous "use this component", "variant is supported", "token exists", "accessible", or "responsive" claim only when current component source, stories, tokens, tests, and validation artifacts still match it.
- Mark evidence stale after edits to component APIs, stories, tokens, theming, layout breakpoints, accessibility behavior, fixtures, validators, routing rules, build outputs, or installation outputs.
- Record inspected and skipped surfaces: components, consumers, stories, design tokens, theme files, tests, docs, generated artifacts, browser screenshots, accessibility reports, and release/build outputs.
- Map every final design-system claim to a command, validator, screenshot, story, report, review artifact, or explicit not-run residual risk.

# Tool Permission Boundary

| Action | Boundary record |
| --- | --- |
| Local source reads, `rg`, `find`, parser scripts, report inspection | Read-only local shell action; cite searched paths and avoid full output dumps |
| Local validators, builds, Storybook builds, visual checks, and accessibility checks | State-mutating only for reports, dist, build artifacts, screenshots, or local caches; cite log path and exit code |
| Browser, device, or screenshot verification | Local UI observation; record viewport/device, artifact path, missing states, and whether interaction was manually exercised |
| Production analytics, session replay, customer screenshots, or support exports | Connector-scoped or production data access; require permission, redact tenant/user/secret-bearing values, and state retention limits |
| Design-token publish, package release, or deployed design-system update | State-mutating release action; require approval, version/rollback plan, changelog, and consumer impact record |

# Handoff Evidence Shape

```yaml
design_system_evidence_closure:
  inspected_paths:
    - path: ""
      finding: ""
  accepted_prior_claims:
    - claim: ""
      current_evidence: ""
  rejected_or_stale_claims:
    - claim: ""
      reason: ""
  changed_design_system_to_validation_map:
    - design_system_decision: ""
      validator_or_artifact: ""
      exit_code: ""
      artifact_or_report: ""
      proves: ""
      does_not_prove: ""
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
