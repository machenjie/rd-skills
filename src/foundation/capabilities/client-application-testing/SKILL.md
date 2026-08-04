---
name: client-application-testing
description: "`analysis-agent`/`task-agent`/`review-agent`: use for installed-client lifecycle, permissions, activation, installation, device, or accessibility tests; skip general quality work."
---

# client-application-testing

## Registry Trigger

**Use when**

- Changed installed-client behavior needs proof across application lifecycle, operating-system integration, installation state, device configuration, or accessibility settings.

**Do not use when**

- The work is a pure backend, API-contract, component-only browser, or general test-portfolio decision without an installed-client risk.

## Skill Role

Select client-specific interruption paths, application artifacts, environment dimensions, observable oracles, and cleanup. Exclude general test strategy, release verdicts, platform API instructions, and accessibility conformance decisions.

## High-Value Rules

- **Derive the matrix from the changed client risk.** Retain only lifecycle, integration, environment, and artifact dimensions that can alter the accepted behavior.
- **Match the test boundary to the failure mechanism.** Keep pure policy tests local while exercising operating-system lifecycle, activation, packaging, and resource pressure in a capable client environment.
- **Separate background and return, UI recreation, process termination and relaunch, crash recovery, and low-memory response into distinct interruption paths.**
- **Exercise permission loss as a state transition.** Cover initial denial, later grant, revocation while inactive, process termination where applicable, and recovery without stale authority.
- **Test every external entry from cold and warm state.** Validate deep links and notifications for duplicate delivery, malformed input, wrong account, unavailable content, and existing-instance activation.
- **Verify storage across artifact transitions.** Test fresh install, upgrade, incompatible data, logout, account switch, and uninstall against the intended preserve, migrate, or clear behavior.
- **Select environment dimensions explicitly.** Name supported device class, operating-system version, architecture, locale, timezone, font scale, assistive technology, and memory class instead of claiming an unbounded matrix.
- **Assert user outcomes and durable effects.** Reset application, server, clock, network, permission, notification, and device state so a passing rerun cannot inherit success.

## Anti-Patterns

- Treat activity or window recreation as proof of full process death and relaunch.
- Promote one simulator, emulator, architecture, or debug build to the supported client matrix.
- Use screenshots or automation-tree presence as the sole oracle for interaction or assistive-technology behavior.

## Stop Conditions

Stop when the supported client matrix, install artifact, required operating-system control, or cleanup authority is unavailable. Report skipped hardware, versions, accessibility checks, and destructive install states rather than converting them to passes.

## Output Contract

- client-test decision with risk matrix interruption and activation cases permission and connectivity transitions artifact and data states environment coverage oracles cleanup unavailable scope and proof limits

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [client test matrix](references/client-test-matrix.md) | targeted | Lifecycle permission activation upgrade device locale scaling assistive-technology or resource-pressure coverage spans several dimensions | One local test already exercises the complete changed client failure mechanism | analysis-agent, task-agent, review-agent | validation-plan, residual-risk |
