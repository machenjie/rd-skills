---
name: e2e-testing
description: "`analysis-agent`/`task-agent`/`review-agent`: use when a critical assembled journey needs proof unavailable below E2E; skip risks proved by component, seam, or contract tests."
---

# e2e-testing

## Registry Trigger

**Use when**

- prove a critical assembled user or business journey across the deployed boundaries it actually depends on

**Do not use when**

- component, integration, contract, or API evidence sufficiently proves the changed acceptance risk

## Skill Role

Prove critical assembled journeys across real participating boundaries. Exclude component-state design, broad compatibility ownership, portfolio selection, and release verdicts.

## High-Value Rules

- Select an E2E journey only when its material failure requires the assembled identity, navigation, service, persistence, event, or external boundary, or a named policy designates assembled proof. The evidence records why a lower level is insufficient.
- Model the journey's role, tenant, starting state, version, dependency state, critical negative or recovery branch, and final user/business outcome. Do not reduce it to a click sequence.
- Assert both the user-visible result and relevant durable side effects or forbidden effects. A successful page transition does not prove authorization, persistence, notification, rollback, or settlement.
- Wait on semantic readiness with bounded polling or framework signals derived from the consequence and system behavior. Fixed sleeps and broad retries hide races and stale-state failures.
- Give each run owned data, session, and external-sandbox scope. Cleanup must cover success, assertion failure, timeout, and cancellation without deleting another run's state.
- Treat intermittent failure as evidence about the system, test, data, or environment. A rerun is diagnostic, not a green result; quarantine needs an owner, release consequence, and repair or removal condition.
- Select browser, device, environment, and version combinations from affected behavior, current usage, support policy, and risk. Untested combinations and stale artifacts remain explicit.
- Require classification, capture minimization, secret/cookie/tenant/personal-data redaction, access control, retention expiry, and safe disposal for retained screenshots, traces, video, console, and network artifacts.

## Anti-Patterns

- Promoting every acceptance criterion to E2E despite cheaper admissible proof.
- Using shared accounts, implementation-only selectors, uncontrolled providers, or order-dependent fixtures.
- Capturing screenshots or traces as proof when the asserted business outcome or durable effect is absent.
- Letting retries, quarantine, or environment drift silently convert an unstable journey into release evidence.

## Stop Conditions

- Escalate when isolation, safe cleanup, environment authority, irreversible side effects, diagnostic-artifact protection, or a deployment-blocking flake cannot be bounded by an owner and policy.

## Output Contract

- assembled-journey proof plan with selected paths, owned data, semantic oracles, cleanup, flake handling, environment coverage, diagnostic-artifact protection, and residual risk

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | Journey admission isolation readiness environment or flake strategies remain open | Lower-level proof closes the risk or one accepted assembled journey has an owned proof path | analysis-agent, task-agent, review-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | Critical journeys cross roles persistence eventual results recovery versions or external sandboxes | No assembled user or business outcome changes | analysis-agent, task-agent, review-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | Journey oracle execution isolation cleanup flake or environment claims need fresh scoped proof | No journey-completeness or flake claim awaits approval | analysis-agent, task-agent, review-agent | evidence-record, proof-limit, residual-risk |
